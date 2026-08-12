"""
scraper_vix.py — Descarga el VIX (CBOE Volatility Index) diario via yfinance.

El VIX es el indicador canónico de apetito por riesgo global. Se usa en
calcular_ajuste_global.py como regresor para separar la señal política argentina
del ruido proveniente del contexto financiero internacional.

Uso:
    py src/scrapers/scraper_vix.py
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / "data" / "iep.db"

ACTIVO        = "VIX"
FUENTE        = "YFINANCE"
TICKER        = "^VIX"
HISTORY_START = "2021-01-01"   # ventana suficiente para z-score rolling 252d desde 2022


def last_date_in_db() -> date | None:
    conn = sqlite3.connect(DB_PATH)
    row  = conn.execute(
        "SELECT MAX(fecha) FROM raw_prices WHERE activo=?", (ACTIVO,)
    ).fetchone()
    conn.close()
    return date.fromisoformat(row[0]) if row[0] else None


def fetch_vix(start: str, end: str) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError:
        raise ImportError(
            "yfinance no instalado. Ejecutar: pip install yfinance"
        )
    df = yf.download(TICKER, start=start, end=end, progress=False, auto_adjust=True)
    if df.empty:
        return pd.DataFrame()
    # Normalizar columnas (yfinance puede retornar MultiIndex)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    close = df["Close"].dropna()
    close.index = pd.to_datetime(close.index).normalize()
    return close.reset_index().rename(columns={"Date": "fecha", "Close": "valor"})


def save_vix(df: pd.DataFrame) -> int:
    if df.empty:
        return 0
    conn  = sqlite3.connect(DB_PATH)
    cur   = conn.cursor()
    saved = 0
    for _, row in df.iterrows():
        if pd.isna(row["valor"]):
            continue
        cur.execute(
            "INSERT OR REPLACE INTO raw_prices (activo, fecha, valor, fuente) VALUES (?,?,?,?)",
            (ACTIVO, row["fecha"].strftime("%Y-%m-%d"), float(row["valor"]), FUENTE),
        )
        saved += 1
    conn.commit()
    conn.close()
    return saved


def main():
    print("scraper_vix | VIX (^VIX) via yfinance")
    print(f"DB: {DB_PATH}")

    last = last_date_in_db()
    if last is None:
        start = HISTORY_START
        print(f"  Sin historia previa — descargando desde {start}")
    else:
        # Solapamiento de 5 días para no perder ruedas en fronteras de semana
        start = (last - timedelta(days=5)).strftime("%Y-%m-%d")
        print(f"  Última fecha en DB: {last} — descargando desde {start}")

    end = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

    df = fetch_vix(start, end)
    if df.empty:
        print("  Sin datos nuevos.")
        return

    saved = save_vix(df)
    print(f"  Filas guardadas: {saved}")
    if not df.empty:
        print(f"  VIX último: {df.iloc[-1]['valor']:.2f}")


if __name__ == "__main__":
    main()
