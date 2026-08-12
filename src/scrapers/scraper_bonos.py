"""
scraper_bonos.py — Descarga precios históricos de GD30D, AL30D y GD35D desde PPI API.

Los precios en USD ("D" = dólar cable) representan directamente la paridad del bono
(precio como % del valor par). Son la materia prima de la Capa 2 del IEP.

Uso:
    python src/scrapers/scraper_bonos.py               # hoy
    python src/scrapers/scraper_bonos.py --backfill    # 2022-01-01 → hoy
    python src/scrapers/scraper_bonos.py --desde 2023-06-01 --hasta 2024-01-01
"""

import sys
import os
import sqlite3
import re
from datetime import datetime, timedelta, date
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).parent.parent.parent
import sys; sys.path.insert(0, str(ROOT))
from src.config import CFG
DB_PATH   = CFG.db_path
CRED_PATH = CFG.cred_ppi

# ── Activos a descargar ────────────────────────────────────────────────────────
BONOS = [
    ("GD30D", "BONOS", "A-48HS"),   # Global 2030, ley NY, USD
    ("AL30D", "BONOS", "A-48HS"),   # ANSES 2030, ley AR, USD
    ("GD35D", "BONOS", "A-48HS"),   # Global 2035, ley NY, USD
    ("AL30",  "BONOS", "A-48HS"),   # ANSES 2030, ley AR, ARS — para calcular MEP
]

# PPI paginación: máximo ~365 días por request
MAX_DAYS = 365


# ── Credenciales ───────────────────────────────────────────────────────────────

def _read_credentials():
    with open(CRED_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    api_key    = re.search(r"KEY PUBLICA\s+(\S+)", content, re.IGNORECASE)
    api_secret = re.search(r"KEY PRIVADA\s+(\S+)", content, re.IGNORECASE)
    if not api_key or not api_secret:
        raise ValueError("No se encontraron KEY PUBLICA / KEY PRIVADA en el archivo de credenciales")
    return api_key.group(1), api_secret.group(1)


# ── Conectar PPI ───────────────────────────────────────────────────────────────

def _connect_ppi():
    try:
        from ppi_client.ppi import PPI
    except ImportError:
        print("[ERROR] pip install ppi-client")
        sys.exit(1)
    api_key, api_secret = _read_credentials()
    ppi = PPI(sandbox=False)
    ppi.account.login_api(api_key=api_key, api_secret=api_secret)
    return ppi


# ── Fetch con paginación ───────────────────────────────────────────────────────

def fetch_historico(ppi, ticker: str, tipo: str, settlement: str,
                    date_from: datetime, date_to: datetime) -> list[dict]:
    """Descarga toda la historia entre date_from y date_to, paginando de MAX_DAYS en MAX_DAYS."""
    all_rows = []
    cursor = date_from
    while cursor < date_to:
        chunk_end = min(cursor + timedelta(days=MAX_DAYS), date_to)
        try:
            rows = ppi.marketdata.search(ticker, tipo, settlement, cursor, chunk_end)
            if rows:
                all_rows.extend(rows)
        except Exception as e:
            print(f"  [WARN] {ticker} {cursor.date()} → {chunk_end.date()}: {e}")
        cursor = chunk_end + timedelta(days=1)
    return all_rows


# ── Guardar en SQLite ──────────────────────────────────────────────────────────

def save_to_db(rows: list[dict], activo: str, fuente: str = "PPI"):
    """Inserta o reemplaza filas en raw_prices."""
    if not rows:
        return 0

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    saved = 0
    for row in rows:
        fecha_raw = row.get("date", "")
        # ISO datetime: "2024-01-02T00:00:00-03:00" → "2024-01-02"
        fecha = fecha_raw[:10] if fecha_raw else None
        valor = row.get("price")
        if not fecha or valor is None:
            continue
        cur.execute("""
            INSERT OR REPLACE INTO raw_prices (activo, fecha, valor, fuente)
            VALUES (?, ?, ?, ?)
        """, (activo, fecha, float(valor), fuente))
        saved += 1

    conn.commit()
    conn.close()
    return saved


# ── Main ───────────────────────────────────────────────────────────────────────

def parse_args():
    args = sys.argv[1:]
    backfill = "--backfill" in args
    date_from = datetime(2022, 1, 1) if backfill else datetime.now() - timedelta(days=7)
    date_to   = datetime.now()

    if "--desde" in args:
        idx = args.index("--desde")
        date_from = datetime.fromisoformat(args[idx + 1])
    if "--hasta" in args:
        idx = args.index("--hasta")
        date_to = datetime.fromisoformat(args[idx + 1])

    return date_from, date_to, backfill


def main():
    date_from, date_to, backfill = parse_args()
    mode = "BACKFILL 2022-hoy" if backfill else f"{date_from.date()} - {date_to.date()}"
    print(f"scraper_bonos | {mode}")
    print(f"DB: {DB_PATH}")

    ppi = _connect_ppi()
    print("PPI conectado OK\n")

    total = 0
    for ticker, tipo, settlement in BONOS:
        print(f"  Descargando {ticker}...", end=" ", flush=True)
        rows = fetch_historico(ppi, ticker, tipo, settlement, date_from, date_to)
        n = save_to_db(rows, activo=ticker)
        total += n
        print(f"{n} filas guardadas")

    print(f"\nTotal: {total} filas en {DB_PATH}")


if __name__ == "__main__":
    main()
