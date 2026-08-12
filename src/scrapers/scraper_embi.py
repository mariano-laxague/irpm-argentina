"""
scraper_embi.py — Descarga el EMBI+ Argentina (riesgo país) desde Rava Bursátil.

Fuente: https://www.rava.com/perfil/RIESGO%20PAIS
Método: extrae el array _chartData embebido en el HTML (últimos ~366 días, OHLC diario).

La API interna de Rava (/api/chart-history) no expone datos históricos para RIESGO PAIS
más allá del año embebido. Para el período 2022-2025 usar GD30D como proxy (ver PLAN.md).

Activo almacenado: 'EMBI' — cierre diario en basis points (bps).

Uso:
    python src/scrapers/scraper_embi.py        # carga los ~366 días disponibles
"""

import sys
import re
import json
import sqlite3
import ssl
import urllib.request
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / "data" / "iep.db"

RAVA_URL = "https://www.rava.com/perfil/RIESGO%20PAIS"


# ── Scraping ───────────────────────────────────────────────────────────────────

def _fetch_html(url: str) -> str:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html",
    })
    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
        return resp.read().decode("latin-1", errors="replace")


def fetch_embi_rava() -> list[dict]:
    """
    Extrae el array _chartData del HTML de Rava.
    Devuelve lista de dicts con claves: fecha (str), cierre (float).
    El cierre está en basis points (bps) — el valor del EMBI/riesgo país.
    """
    html = _fetch_html(RAVA_URL)
    match = re.search(r"_chartData\s*=\s*(\[.+?\]);", html, re.DOTALL)
    if not match:
        raise ValueError("No se encontro _chartData en el HTML de Rava")
    raw = json.loads(match.group(1))
    return [
        {"fecha": row["fecha"], "cierre": float(row["cierre"])}
        for row in raw
        if row.get("fecha") and row.get("cierre") is not None
    ]


# ── Guardar en SQLite ──────────────────────────────────────────────────────────

def save_to_db(rows: list[dict]) -> int:
    if not rows:
        return 0
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    saved = 0
    for row in rows:
        cur.execute("""
            INSERT OR REPLACE INTO raw_prices (activo, fecha, valor, fuente)
            VALUES (?, ?, ?, ?)
        """, ("EMBI", row["fecha"], row["cierre"], "RAVA_SCRAPING"))
        saved += 1
    conn.commit()
    conn.close()
    return saved


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("scraper_embi | Fuente: Rava Bursatil")
    print(f"DB: {DB_PATH}")

    print("Descargando...", end=" ", flush=True)
    rows = fetch_embi_rava()
    print(f"{len(rows)} filas en pagina")

    n = save_to_db(rows)
    print(f"{n} filas guardadas en DB")

    if rows:
        print(f"Rango: {rows[0]['fecha']} (EMBI={rows[0]['cierre']}) -> {rows[-1]['fecha']} (EMBI={rows[-1]['cierre']})")
    print("Nota: cubre solo los ultimos ~366 dias. Backfill 2022-2025 = GD30D proxy (ver PLAN.md)")


if __name__ == "__main__":
    main()
