"""
scraper_rofex_bcr.py — Descarga precios de ajuste ROFEX DLR desde boletines BCR.

Fuente: Bolsa de Comercio de Rosario (BCR)
URL: https://www.bcr.com.ar/sites/default/files/boletin-mercado-granos-{id}.pdf
Cobertura: cada boletin cubre un dia habil. Para el gap: IDs ~18541 a ~18905.

El precio de ajuste del contrato mas proximo (1M) se guarda como ROFEX_BCR_1M.
Tambien se guardan 2M y 3M para calcular la curva.

Uso:
    python src/scrapers/scraper_rofex_bcr.py             # gap completo (IDs 18540-18910)
    python src/scrapers/scraper_rofex_bcr.py --dry       # probar sin guardar
    python src/scrapers/scraper_rofex_bcr.py --desde 18700 --hasta 18750
"""

import sys, ssl, re, io, sqlite3, time
from datetime import datetime
from pathlib import Path

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / "data" / "iep.db"

BASE_URL = "https://www.bcr.com.ar/sites/default/files/boletin-mercado-granos-{id}.pdf"

DRY = "--dry" in sys.argv

# ── Args ──────────────────────────────────────────────────────────────────────

def parse_args():
    args = sys.argv[1:]
    id_desde = 18540
    id_hasta = 18910
    if "--desde" in args:
        id_desde = int(args[args.index("--desde") + 1])
    if "--hasta" in args:
        id_hasta = int(args[args.index("--hasta") + 1])
    return id_desde, id_hasta


# ── Descarga y extraccion ─────────────────────────────────────────────────────

def download_pdf(id_num):
    import urllib.request
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    url = BASE_URL.format(id=id_num)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
            if resp.status != 200:
                return None
            data = resp.read()
            return data if len(data) > 50000 else None
    except:
        return None


def extract_text(pdf_bytes):
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    except Exception as e:
        return None


def parse_fecha_boletin(text):
    """Extrae la fecha del boletin del encabezado."""
    m = re.search(r'(?:lunes|martes|miércoles|miercoles|jueves|viernes),?\s+'
                  r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',
                  text, re.IGNORECASE)
    if not m:
        # Formato alternativo DD/MM/YYYY en encabezado ROFEX
        m2 = re.search(r'ROFEX.*?(\d{1,2}/\d{1,2}/\d{4})', text, re.IGNORECASE)
        if m2:
            try:
                return datetime.strptime(m2.group(1), "%d/%m/%Y").strftime("%Y-%m-%d")
            except:
                return None
        return None

    MESES = {"enero":"01","febrero":"02","marzo":"03","abril":"04","mayo":"05",
             "junio":"06","julio":"07","agosto":"08","septiembre":"09",
             "octubre":"10","noviembre":"11","diciembre":"12"}
    mes = MESES.get(m.group(2).lower())
    if not mes:
        return None
    return f"{m.group(3)}-{mes}-{int(m.group(1)):02d}"


def parse_dlr_contracts(text):
    """
    Extrae todos los contratos DLR del texto.
    Formato: DLR{MMYYYY} {ultimo_dia} {Aj.Ant} {open} {min} {max} {ultimo} {vol} {AJUSTE} ...

    Retorna lista de (contrato, expiry_str, ajuste_float)
    """
    # Patron: DLRmmYYYY fecha num num num num num num num ...
    # El numero de posicion es MMYYYY (mes 2 digitos + anio 4 digitos)
    pattern = re.compile(
        r'DLR(\d{2})(\d{4})\s+'          # grupo 1=MM, grupo 2=YYYY
        r'(\d{1,2}/\d{1,2}/\d{4})\s+'    # ultimo dia negociacion
        r'([\d.,]+)\s+'                   # Aj.Ant
        r'([\d.,]+)\s+'                   # Apertura
        r'([\d.,]+)\s+'                   # Min
        r'([\d.,]+)\s+'                   # Max
        r'([\d.,]+)\s+'                   # Ultimo
        r'[\d.,]+\s+'                     # Vol (sin capturar)
        r'([\d.,]+)'                      # AJUSTE <-- lo que queremos
    )

    def to_float(s):
        # Formato argentino: 1.037,5000 -> 1037.5
        return float(s.replace(".", "").replace(",", "."))

    results = []
    for m in pattern.finditer(text):
        mes = int(m.group(1))
        anio = int(m.group(2))
        expiry_str = m.group(3)
        ajuste = to_float(m.group(9))
        try:
            expiry = datetime.strptime(expiry_str, "%d/%m/%Y")
        except:
            continue
        results.append((f"DLR{m.group(1)}{m.group(2)}", expiry, ajuste))

    return results


def nearest_contracts(contracts, boletin_date_str):
    """
    Dado el boletin date, devuelve los contratos 1M, 2M, 3M (los 3 mas proximos no vencidos).
    """
    try:
        bd = datetime.strptime(boletin_date_str, "%Y-%m-%d")
    except:
        return None, None, None

    # Filtrar contratos que no han vencido (expiry > boletin_date)
    activos = [(name, exp, ajuste) for name, exp, ajuste in contracts if exp > bd]
    activos.sort(key=lambda x: x[1])  # ordenar por vencimiento

    c1 = activos[0][2] if len(activos) >= 1 else None
    c2 = activos[1][2] if len(activos) >= 2 else None
    c3 = activos[2][2] if len(activos) >= 3 else None
    return c1, c2, c3


# ── Guardar en DB ─────────────────────────────────────────────────────────────

def save_to_db(fecha, activo, valor):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO raw_prices (activo, fecha, valor, fuente)
        VALUES (?, ?, ?, ?)
    """, (activo, fecha, valor, "BCR_BOLETIN"))
    conn.commit()
    conn.close()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    id_desde, id_hasta = parse_args()
    print(f"scraper_rofex_bcr | BCR Boletines | IDs {id_desde} a {id_hasta}")
    print(f"DB: {DB_PATH}")
    if DRY:
        print("Modo --dry: no se guarda nada\n")
    else:
        print()

    total_ok = 0
    total_skip = 0
    total_err = 0

    for id_num in range(id_desde, id_hasta + 1):
        # Descargar PDF
        pdf = download_pdf(id_num)
        if pdf is None:
            total_skip += 1
            continue

        # Extraer texto
        text = extract_text(pdf)
        if not text or "ROFEX" not in text.upper():
            total_skip += 1
            continue

        # Fecha del boletin
        fecha = parse_fecha_boletin(text)
        if not fecha:
            total_err += 1
            continue

        # Contratos DLR
        contracts = parse_dlr_contracts(text)
        if not contracts:
            print(f"  [{id_num}] {fecha} — sin contratos DLR")
            total_err += 1
            continue

        c1, c2, c3 = nearest_contracts(contracts, fecha)
        if c1 is None:
            total_err += 1
            continue

        s2 = f"{c2:.2f}" if c2 else "N/A"
        s3 = f"{c3:.2f}" if c3 else "N/A"
        print(f"  [{id_num}] {fecha} | 1M={c1:.2f} | 2M={s2} | 3M={s3} | {len(contracts)} contratos")

        if not DRY:
            if c1:
                save_to_db(fecha, "ROFEX_BCR_1M", c1)
            if c2:
                save_to_db(fecha, "ROFEX_BCR_2M", c2)
            if c3:
                save_to_db(fecha, "ROFEX_BCR_3M", c3)

        total_ok += 1
        # Pequena pausa para no sobrecargar el servidor BCR
        time.sleep(0.3)

    print(f"\nResumen: {total_ok} OK | {total_skip} no disponibles | {total_err} errores")
    if not DRY:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        for act in ["ROFEX_BCR_1M", "ROFEX_BCR_2M", "ROFEX_BCR_3M"]:
            row = cur.execute(
                "SELECT COUNT(*), MIN(fecha), MAX(fecha) FROM raw_prices WHERE activo=?",
                (act,)).fetchone()
            print(f"  {act}: {row[0]} filas | {row[1]} -> {row[2]}")
        conn.close()


if __name__ == "__main__":
    main()
