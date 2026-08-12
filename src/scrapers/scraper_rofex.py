"""
scraper_rofex.py — Descarga precios de ajuste de futuros DLR (ROFEX) via PPI.

Fuente: PPI API (tipo=FUTUROS, settlement=A-48HS)
Activos almacenados: DLR_MES_ANO (ej. DLR_JUN26)

Cobertura historica via PPI: desde oct-2025 (los contratos expirados antes
de esa fecha ya no estan disponibles en PPI).

El z-score del indice ROFEX necesita min_periods=63 dias habiles (~3 meses).
Fecha estimada de activacion del kink electoral: mar-2027 (DLR_DIC27 entra al mercado ~dic-2026,
luego 63 dias habiles para el z-score). DLR_ENE27 puede aparecer ya (8m adelante).

Uso:
    python src/scrapers/scraper_rofex.py           # contratos activos, ultimos 7d
    python src/scrapers/scraper_rofex.py --backfill # desde 2025-10-01
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

# Abreviaciones en espanol para los meses
MESES_ES = ["ENE","FEB","MAR","ABR","MAY","JUN","JUL","AGO","SEP","OCT","NOV","DIC"]

BACKFILL_FROM = datetime(2025, 10, 1)  # minima historia disponible en PPI


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


def active_contracts(n_months=8):
    """Genera tickers de los proximos n_months contratos activos."""
    contracts = []
    today = datetime.now()
    for i in range(n_months):
        # Contratos mensuales: el mas cercano primero
        dt = today + timedelta(days=30 * i)
        ticker = f"DLR/{MESES_ES[dt.month - 1]}{dt.strftime('%y')}"
        # Fecha de vencimiento aproximada (ultimo dia del mes)
        if dt.month == 12:
            expiry = datetime(dt.year + 1, 1, 1) - timedelta(days=1)
        else:
            expiry = datetime(dt.year, dt.month + 1, 1) - timedelta(days=1)
        contracts.append((ticker, expiry))
    return contracts


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
        """, (activo, fecha, float(valor), "PPI_FUTUROS"))
        saved += 1
    conn.commit()
    conn.close()
    return saved


def main():
    backfill = "--backfill" in sys.argv
    date_from = BACKFILL_FROM if backfill else datetime.now() - timedelta(days=7)
    date_to   = datetime.now()
    mode = f"BACKFILL desde {BACKFILL_FROM.date()}" if backfill else f"{date_from.date()} - {date_to.date()}"
    print(f"scraper_rofex | {mode}")
    print(f"DB: {DB_PATH}\n")

    ppi = _connect_ppi()
    print("PPI conectado OK\n")

    contracts = active_contracts(n_months=14)
    total = 0
    for ticker, expiry in contracts:
        # El activo se guarda como DLR_JUN26 (sin slash)
        activo = ticker.replace("/", "_")
        try:
            rows = ppi.marketdata.search(ticker, "FUTUROS", "A-48HS", date_from, date_to)
            if rows:
                n = save_to_db(rows, activo)
                total += n
                print(f"  {ticker}: {n} filas (vence {expiry.date()})")
            else:
                print(f"  {ticker}: sin datos en el rango")
        except Exception as e:
            if "not found" not in str(e).lower():
                print(f"  {ticker}: {e}")

    print(f"\nTotal: {total} filas guardadas en raw_prices")
    print("\nNOTA: historia disponible desde oct-2025.")
    print("      Kink electoral (DLR_DIC27/DLR_ENE27): DIC27 entra al mercado ~dic-2026.")
    print("      Activacion estimada del kink: mar-2027 (63 dias habiles tras aparecer DIC27).")


if __name__ == "__main__":
    main()
