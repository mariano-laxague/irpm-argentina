"""
calcular_capa3.py — Calcula el sub-indice Capa 3 del IEP.

Señal: semi-volatilidad a la baja del mercado accionario argentino.
Captura SOLO el miedo del mercado (dias de caidas), no la euforia (dias de subas).
Es un proxy de la volatilidad implicita put / put-call ratio de opciones BYMA.

La diferencia clave con la volatilidad realizada completa:
  - Vol completa: alta en crisis (ok) PERO tambien alta en rallies post-eleccion (incorrecto)
  - Semi-vol a la baja: alta en crisis (ok) y BAJA en rallies (correcto)

Basket:
  YPFD  — YPF S.A. (sensible a politica energetica)
  GGAL  — Grupo Galicia (sensible a politica economica / bancaria)
  PAMP  — Pampa Energia (sensible a tarifas / regulacion energetica)
  TECO2 — Telecom Argentina (sensible a regulacion de telecomunicaciones)

Calculo:
  1. Log returns diarios por accion: r_t = log(P_t / P_{t-1})
  2. Semi-vol 20d: std(min(r_t, 0)) * sqrt(252) — solo dias negativos
  3. Promedio del basket
  4. Z-score rolling 252d (min 63 periodos)
  5. Invertido: semi-vol alta = miedo politico = señal mala para el IEP

Sustituir por IV de opciones BYMA cuando se cuente con el acceso a BYMA DataFeed.

Uso:
    python src/pipeline/calcular_capa3.py
    python src/pipeline/calcular_capa3.py --diagnosticos
"""

import sys
import sqlite3
from pathlib import Path

import pandas as pd
import numpy as np

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / "data" / "iep.db"

BASKET      = ["YPFD", "GGAL", "PAMP", "TECO2"]
RV_WINDOW   = 20    # dias habiles para vol realizada
ZSCORE_WIN  = 252   # ventana z-score
MIN_PERIODS = 63

# Splits accionarios — ajuste retroactivo a base post-split para retornos continuos.
# Agregar aquí cualquier split futuro con fecha de vigencia y ratio (n:1).
STOCK_SPLITS = {
    "YPFD": [
        {"fecha": "2026-08-03", "ratio": 10},  # split 10:1 confirmado (82.900 → 8.105 ARS)
    ],
}

DIAG = "--diagnosticos" in sys.argv


def apply_splits(prices: pd.Series, activo: str) -> pd.Series:
    """Divide los precios pre-split por el ratio para mantener retornos continuos."""
    for split in STOCK_SPLITS.get(activo, []):
        split_date = pd.Timestamp(split["fecha"])
        mask = prices.index < split_date
        if mask.any():
            prices = prices.copy()
            prices[mask] = prices[mask] / split["ratio"]
            print(f"  [SPLIT] {activo} {split_date.date()} {split['ratio']}:1 — {mask.sum()} precios ajustados")
    return prices


def load_series(activo):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT fecha, valor FROM raw_prices WHERE activo=? ORDER BY fecha",
        conn, params=(activo,), parse_dates=["fecha"],
    )
    conn.close()
    return df.set_index("fecha")["valor"]


def rolling_zscore(s, window=ZSCORE_WIN, min_periods=MIN_PERIODS):
    m  = s.rolling(window, min_periods=min_periods).mean()
    sd = s.rolling(window, min_periods=min_periods).std()
    return (s - m) / sd.replace(0, float("nan"))


def compute_capa3():
    rv_series = {}
    for ticker in BASKET:
        prices = load_series(ticker)
        prices = apply_splits(prices, ticker)
        if len(prices) < RV_WINDOW + 5:
            continue
        log_ret = np.log(prices / prices.shift(1))
        # Semi-volatilidad: solo dias negativos (proxy del put-side de opciones)
        downside = log_ret.clip(upper=0)
        rv = downside.rolling(RV_WINDOW, min_periods=RV_WINDOW // 2).std() * np.sqrt(252)
        rv_series[ticker] = rv

    if not rv_series:
        raise ValueError("Sin datos de acciones. Correr scraper_acciones.py --backfill primero.")

    vol_basket = pd.DataFrame(rv_series).mean(axis=1, skipna=True)
    vol_basket.name = "vol_basket"

    z = rolling_zscore(vol_basket)
    capa3 = -z  # invertido: vol alta = señal mala
    capa3.name = "capa3"

    return vol_basket, capa3


def save_capa3(capa3):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    saved = 0
    for fecha, valor in capa3.items():
        if pd.isna(valor):
            continue
        cur.execute("""
            INSERT INTO iep_diario (fecha, capa3, pesos_version)
            VALUES (?, ?, ?)
            ON CONFLICT(fecha) DO UPDATE SET capa3=excluded.capa3
        """, (fecha.strftime("%Y-%m-%d"), float(valor), "50-50-0"))
        saved += 1
    conn.commit()
    conn.close()
    return saved


def print_diagnostics(vol_basket, capa3):
    c3 = capa3.dropna()

    print("\n=== Vol Basket (anualizada) ===")
    print(f"  Desde:  {vol_basket.dropna().index[0].date()}")
    print(f"  Hasta:  {vol_basket.dropna().index[-1].date()}")
    print(f"  Media:  {vol_basket.mean():.1%}")
    print(f"  Min:    {vol_basket.min():.1%}  ({vol_basket.idxmin().date()})")
    print(f"  Max:    {vol_basket.max():.1%}  ({vol_basket.idxmax().date()})")
    print(f"  Actual: {vol_basket.iloc[-1]:.1%}")

    print("\n=== Capa 3 — z-score invertido ===")
    print(f"  Desde:  {c3.index[0].date()}")
    print(f"  Hasta:  {c3.index[-1].date()}")
    print(f"  Filas:  {len(c3)}")
    print(f"  Min:    {c3.min():.4f}  ({c3.idxmin().date()})")
    print(f"  Max:    {c3.max():.4f}  ({c3.idxmax().date()})")

    print("\n=== Valores en fechas clave ===")
    key_dates = {
        "2022-07-01": "Crisis Guzman",
        "2023-08-14": "PASO 2023",
        "2024-01-02": "Inicio Milei",
        "2024-04-08": "Honeymoon peak",
        "2025-09-18": "Minimo IEP",
        "2025-10-27": "Legislativas (BASELINE)",
        "2026-05-12": "Hoy",
    }
    for d, label in key_dates.items():
        try:
            v  = c3.loc[pd.Timestamp(d)]
            vb = vol_basket.loc[pd.Timestamp(d)]
            print(f"  {d}  {label:<30}  Capa3={v:+.4f}  vol={vb:.1%}")
        except KeyError:
            idx = c3.index.get_indexer([pd.Timestamp(d)], method="nearest")[0]
            fecha_r = c3.index[idx]
            v  = c3.iloc[idx]
            vb = vol_basket.reindex([fecha_r]).iloc[0]
            print(f"  {d}  {label:<30}  Capa3={v:+.4f}  vol={vb:.1%}  (real: {fecha_r.date()})")


def main():
    print("calcular_capa3 | IEP Capa 3 — Volatilidad realizada acciones AR")
    print(f"DB: {DB_PATH}")
    print(f"Basket: {', '.join(BASKET)}")
    print(f"Vol realizada: {RV_WINDOW}d | Z-score: {ZSCORE_WIN}d rolling\n")

    vol_basket, capa3 = compute_capa3()
    n = save_capa3(capa3)
    print(f"Capa 3 guardada en iep_diario: {n} filas")

    if DIAG:
        print_diagnostics(vol_basket, capa3)
    else:
        c3 = capa3.dropna()
        baseline = pd.Timestamp("2025-10-27")
        idx = c3.index.get_indexer([baseline], method="nearest")[0]
        v_base = c3.iloc[idx]
        v_now  = c3.iloc[-1]
        print(f"Baseline (27-oct-2025):  {v_base:+.4f}")
        print(f"Ultimo ({c3.index[-1].date()}):    {v_now:+.4f}")
        print(f"Vol actual basket:       {vol_basket.iloc[-1]:.1%}")
        print("\nCorrer con --diagnosticos para detalle completo.")


if __name__ == "__main__":
    main()
    from src.pipeline.sanity import assert_capa_sanity
    assert_capa_sanity("capa3")
