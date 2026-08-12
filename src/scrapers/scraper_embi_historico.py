"""
scraper_embi_historico.py — Descarga el EMBI+ Argentina completo desde 1998.

Fuente: api.dolarito.ar (endpoint de datos históricos)
Formato respuesta: {"DD-MM-YYYY": bps, ...} — dict con todas las fechas

Uso:
    python src/scrapers/scraper_embi_historico.py         # carga todo
    python src/scrapers/scraper_embi_historico.py --dry   # imprime sin guardar
"""

import sys
import json
import sqlite3
import ssl
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / "data" / "iep.db"

API_URL = "https://api.dolarito.ar/api/frontend/indices/riesgoPais"
AUTH_CLIENT = "f7d471ab0a4ff2b7947759d985ed1db0"
DRY = "--dry" in sys.argv


def fetch_embi_dolarito() -> list[dict]:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(API_URL, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.dolarito.ar/",
        "Origin": "https://www.dolarito.ar",
        "auth-client": AUTH_CLIENT,
    })
    with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
        raw = json.loads(resp.read())

    rows = []
    for date_str, value in raw.items():
        try:
            # Formato DD-MM-YYYY → YYYY-MM-DD
            fecha = datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
            rows.append({"fecha": fecha, "cierre": float(value)})
        except (ValueError, TypeError):
            continue
    rows.sort(key=lambda r: r["fecha"])
    return rows


def save_to_db(rows: list[dict]) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    saved = 0
    for row in rows:
        cur.execute("""
            INSERT OR REPLACE INTO raw_prices (activo, fecha, valor, fuente)
            VALUES (?, ?, ?, ?)
        """, ("EMBI", row["fecha"], row["cierre"], "DOLARITO_API"))
        saved += 1
    conn.commit()
    conn.close()
    return saved


def main():
    print("scraper_embi_historico | Fuente: api.dolarito.ar")
    print(f"DB: {DB_PATH}")
    print("Descargando...", end=" ", flush=True)

    rows = fetch_embi_dolarito()
    print(f"{len(rows)} registros obtenidos")

    if rows:
        print(f"Rango: {rows[0]['fecha']} (EMBI={rows[0]['cierre']}) -> {rows[-1]['fecha']} (EMBI={rows[-1]['cierre']})")

    if DRY:
        print("Modo --dry: no se guardó nada.")
        # Mostrar muestra 2022-2026
        from_2022 = [r for r in rows if r["fecha"] >= "2022-01-01"]
        print(f"Registros desde 2022-01-01: {len(from_2022)}")
        for r in from_2022[:5]:
            print(f"  {r['fecha']}  {r['cierre']} bps")
        print("  ...")
        for r in from_2022[-5:]:
            print(f"  {r['fecha']}  {r['cierre']} bps")
        return

    n = save_to_db(rows)
    print(f"{n} filas guardadas en DB (activo=EMBI, fuente=DOLARITO_API)")
    print("Nota: incluye historia completa desde 1998. El calculo del indice")
    print("      usara solo desde 2022 en adelante (inicio de raw_prices de bonos).")


if __name__ == "__main__":
    main()
