"""
scraper_acciones.py — Descarga precios historicos de acciones argentinas desde PPI.

Basket Capa 3 (volatilidad realizada):
  YPFD  — YPF S.A. (sensible a politica energetica)
  GGAL  — Grupo Galicia (sensible a politica economica / bancaria)
  PAMP  — Pampa Energia (sensible a tarifas / regulacion energetica)
  TECO2 — Telecom Argentina (sensible a regulacion de telecomunicaciones)

Uso:
    python src/scrapers/scraper_acciones.py               # ultimos 7 dias
    python src/scrapers/scraper_acciones.py --backfill    # 2022-01-01 hasta hoy
    python src/scrapers/scraper_acciones.py --desde 2023-01-01 --hasta 2024-12-31
"""

import sys
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

ROOT      = Path(__file__).parent.parent.parent
import sys; sys.path.insert(0, str(ROOT))
from src.config import CFG
DB_PATH   = CFG.db_path
CRED_PATH = CFG.cred_ppi

ACCIONES = ["YPFD", "GGAL", "PAMP", "TECO2"]
MAX_DAYS = 365


def _connect_ppi():
    try:
        from ppi_client.ppi import PPI
    except ImportError:
        print("[ERROR] pip install ppi-client")
        sys.exit(1)
    with open(CRED_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    api_key    = re.search(r"KEY PUBLICA\s+(\S+)", content, re.IGNORECASE).group(1)
    api_secret = re.search(r"KEY PRIVADA\s+(\S+)", content, re.IGNORECASE).group(1)
    ppi = PPI(sandbox=False)
    ppi.account.login_api(api_key=api_key, api_secret=api_secret)
    return ppi


def fetch_historico(ppi, ticker, date_from, date_to):
    all_rows = []
    cursor = date_from
    while cursor < date_to:
        chunk_end = min(cursor + timedelta(days=MAX_DAYS), date_to)
        try:
            rows = ppi.marketdata.search(ticker, "ACCIONES", "A-48HS", cursor, chunk_end)
            if rows:
                all_rows.extend(rows)
        except Exception as e:
            print(f"  [WARN] {ticker} {cursor.date()} -> {chunk_end.date()}: {e}")
        cursor = chunk_end + timedelta(days=1)
    return all_rows


def save_to_db(rows, activo):
    if not rows:
        return 0
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    saved = 0
    for row in rows:
        fecha_raw = row.get("date", "")
        fecha = fecha_raw[:10] if fecha_raw else None
        valor = row.get("price")
        if not fecha or valor is None:
            continue
        cur.execute("""
            INSERT OR REPLACE INTO raw_prices (activo, fecha, valor, fuente)
            VALUES (?, ?, ?, ?)
        """, (activo, fecha, float(valor), "PPI"))
        saved += 1
    conn.commit()
    conn.close()
    return saved


def parse_args():
    args = sys.argv[1:]
    backfill = "--backfill" in args
    date_from = datetime(2022, 1, 1) if backfill else datetime.now() - timedelta(days=7)
    date_to   = datetime.now()
    if "--desde" in args:
        date_from = datetime.fromisoformat(args[args.index("--desde") + 1])
    if "--hasta" in args:
        date_to = datetime.fromisoformat(args[args.index("--hasta") + 1])
    return date_from, date_to, backfill


def main():
    date_from, date_to, backfill = parse_args()
    mode = "BACKFILL 2022-hoy" if backfill else f"{date_from.date()} - {date_to.date()}"
    print(f"scraper_acciones | {mode}")
    print(f"DB: {DB_PATH}\n")

    ppi = _connect_ppi()
    print("PPI conectado OK\n")

    total = 0
    for ticker in ACCIONES:
        print(f"  {ticker}...", end=" ", flush=True)
        rows = fetch_historico(ppi, ticker, date_from, date_to)
        n = save_to_db(rows, ticker)
        total += n
        print(f"{n} filas")

    print(f"\nTotal: {total} filas en raw_prices")


if __name__ == "__main__":
    main()
