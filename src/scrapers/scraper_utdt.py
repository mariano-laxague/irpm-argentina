"""
scraper_utdt.py — Actualiza ICG e ICC UTDT en data/utdt_icg.csv y data/utdt_icc.csv.

Lógica:
  - Verifica si el último mes disponible en los CSVs ya es el mes anterior al actual.
  - Si no, intenta scrapearlo desde UTDT (con User-Agent de Chrome).
  - ICG: extrae el valor del texto de la página ("El ICG de [mes] fue de X,XX puntos").
  - ICC: descarga el PDF del último mes y extrae el ICC Nacional de la tabla de cierre.
  - Solo escribe si encuentra un dato nuevo.

Se corre mensualmente desde update_daily.py (primer día hábil del mes).
"""

import re
import sys
import tempfile
import requests
import pdfplumber
import pandas as pd
from pathlib import Path
from datetime import date, datetime

ROOT      = Path(__file__).parent.parent.parent
ICG_PATH  = ROOT / "data" / "utdt_icg.csv"
ICC_PATH  = ROOT / "data" / "utdt_icc.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

ICG_URL = "https://www.utdt.edu/ver_contenido.php?id_contenido=1439&id_item_menu=2964"
ICC_URL = "https://www.utdt.edu/ver_contenido.php?id_contenido=2575&id_item_menu=4982"

MESES_ES = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
    "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12",
}


def _fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
    r.raise_for_status()
    return r.text


def _latest_month_in_csv(path):
    """Retorna el último mes en el CSV (e.g. '2026-04') o None."""
    if not path.exists():
        return None
    df = pd.read_csv(path)
    if df.empty:
        return None
    return df["fecha"].max()


def _target_month():
    """Mes que debería estar publicado: mes anterior al actual."""
    today = date.today()
    if today.month == 1:
        return f"{today.year - 1}-12"
    return f"{today.year}-{today.month - 1:02d}"


# ── ICG ───────────────────────────────────────────────────────────────────────

def scrape_icg(target_month):
    """Extrae el valor ICG para target_month desde la página UTDT.
    Retorna float o None si no lo encuentra.
    """
    html = _fetch(ICG_URL)
    # Patrón: "El ICG de abril fue de 2,02 puntos"
    for mes_es, mes_num in MESES_ES.items():
        anio = target_month[:4]
        if f"{anio}-{mes_num}" != target_month:
            continue
        pattern = rf"El ICG de {mes_es} fue de ([\d,\.]+) puntos"
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            return float(m.group(1).replace(",", "."))
    return None


# ── ICC ───────────────────────────────────────────────────────────────────────

def _find_icc_pdf_url(html, target_month):
    """Busca en el HTML la URL del PDF del mes objetivo."""
    anio = target_month[:4]
    mes_num = target_month[5:7]
    mes_es = {v: k for k, v in MESES_ES.items()}[mes_num].capitalize()

    # Buscar el patrón "[Mes Año]" seguido o precedido del link al PDF
    pattern = rf'{mes_es}\s*{anio}.{{0,300}}?(download\.php\?fname=[^"\'<> ]+\.pdf)'
    m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    if m:
        return "https://www.utdt.edu/" + m.group(1)
    # Alternativa: PDF aparece antes del texto del mes
    pattern2 = rf'(download\.php\?fname=[^"\'<> ]+\.pdf).{{0,300}}?{mes_es}\s*{anio}'
    m = re.search(pattern2, html, re.IGNORECASE | re.DOTALL)
    if m:
        return "https://www.utdt.edu/" + m.group(1)
    return None


def scrape_icc(target_month):
    """Descarga el PDF ICC del mes y extrae el ICC Nacional. Retorna float o None."""
    html = _fetch(ICC_URL)
    pdf_url = _find_icc_pdf_url(html, target_month)
    if not pdf_url:
        print(f"  [ICC] No se encontró URL del PDF para {target_month}")
        return None

    r = requests.get(pdf_url, headers=HEADERS, timeout=30, allow_redirects=True)
    r.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(r.content)
        tmp_path = f.name

    try:
        with pdfplumber.open(tmp_path) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages[:4])

        # Patrón en tabla: "ICC 39,64 -5,68%"
        m = re.search(r"ICC\s+([\d,\.]+)\s+-?[\d,\.]+%", text)
        if m:
            return float(m.group(1).replace(",", "."))
        # Alternativa: "el ICC se ubicó en 39,64 puntos"
        m = re.search(r"ICC se ubic[oó] en ([\d,\.]+) puntos", text, re.IGNORECASE)
        if m:
            return float(m.group(1).replace(",", "."))
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return None


# ── Actualizar CSVs ───────────────────────────────────────────────────────────

def update_icg(target_month):
    latest = _latest_month_in_csv(ICG_PATH)
    if latest and latest >= target_month:
        print(f"  [ICG] Ya está actualizado ({latest}). Nada que hacer.")
        return False
    print(f"  [ICG] Scrapeando {target_month}...")
    val = scrape_icg(target_month)
    if val is None:
        print(f"  [ICG] No se encontró valor para {target_month}.")
        return False
    df = pd.read_csv(ICG_PATH) if ICG_PATH.exists() else pd.DataFrame(columns=["fecha", "icg_general"])
    df = pd.concat([df, pd.DataFrame([{"fecha": target_month, "icg_general": round(val, 4)}])],
                   ignore_index=True)
    df.to_csv(ICG_PATH, index=False, encoding="utf-8")
    print(f"  [ICG] {target_month} = {val:.4f} → guardado.")
    return True


def update_icc(target_month):
    latest = _latest_month_in_csv(ICC_PATH)
    if latest and latest >= target_month:
        print(f"  [ICC] Ya está actualizado ({latest}). Nada que hacer.")
        return False
    print(f"  [ICC] Scrapeando {target_month}...")
    val = scrape_icc(target_month)
    if val is None:
        print(f"  [ICC] No se encontró valor para {target_month}.")
        return False
    df = pd.read_csv(ICC_PATH) if ICC_PATH.exists() else pd.DataFrame(
        columns=["fecha", "icc_nacional", "icc_capital", "icc_interior", "icc_gba"])
    df = pd.concat([df, pd.DataFrame([{
        "fecha": target_month, "icc_nacional": round(val, 4),
        "icc_capital": None, "icc_interior": None, "icc_gba": None,
    }])], ignore_index=True)
    df.to_csv(ICC_PATH, index=False, encoding="utf-8")
    print(f"  [ICC] {target_month} = {val:.2f} → guardado.")
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    target = _target_month()
    print(f"scraper_utdt | target: {target}")
    update_icg(target)
    update_icc(target)


if __name__ == "__main__":
    main()
