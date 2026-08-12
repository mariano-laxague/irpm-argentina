"""
calcular_rem_icm.py — Indice de Consenso Macro del REM (ICM-REM).

Construye un indice mensual que resume como evolucionan las expectativas
de los analistas del BCRA sobre la marcha del programa economico.

Metodologia:
  - 4 componentes del REM, cada uno normalizado con z-score rolling 36 meses
  - Pesos: IPC 12M (40% inv) + PIB anual (25%) + TC MoM (20% inv) + Fiscal (15%)
  - Baseline = 100 al 11-dic-2023 (inicio gestion Milei)
  - Escala = 10 pts por unidad z (misma convencion que IRPM)

Direcciones:
  - IPC 12M:   INVERTIDO — menor inflacion esperada = mejor
  - PIB anual: DIRECTO   — mayor crecimiento = mejor
  - TC MoM %:  INVERTIDO — menor aceleracion de expectativas = mejor
  - Fiscal:    DIRECTO   — mayor superavit = mejor

Salida: data/rem_icm.csv  (fecha YYYY-MM, icm)
"""

from pathlib import Path
import pandas as pd
import numpy as np

ROOT        = Path(__file__).parent.parent.parent
REM_PATH    = ROOT / "data" / "rem.csv"
ICM_PATH    = ROOT / "data" / "rem_icm.csv"

BASELINE    = "2023-12"
WINDOW      = 36        # meses para rolling z-score
MIN_PERIODS = 12        # minimo para calcular z-score
SCALE       = 10.0      # puntos de ICM por unidad z (igual al IRPM)

WEIGHTS = {
    "ipc_12m":   (0.40, "inv"),   # invertido
    "pib_anio":  (0.25, "dir"),   # directo
    "tc_mom":    (0.20, "inv"),   # invertido — MoM % change en tc_12m
    "fiscal_anio":(0.15, "dir"),  # directo
}


def rolling_zscore(series: pd.Series, window: int, min_periods: int) -> pd.Series:
    """Z-score rolling: (x - rolling_mean) / rolling_std."""
    mu  = series.rolling(window, min_periods=min_periods).mean()
    std = series.rolling(window, min_periods=min_periods).std(ddof=1)
    return (series - mu) / std.replace(0, np.nan)


def build_icm(df: pd.DataFrame) -> pd.Series:
    """
    Construye el ICM crudo (sin baseline) a partir de los componentes.
    Devuelve una Series con index=fecha, valores en escala z-score * SCALE.
    """
    df = df.set_index("fecha").sort_index().copy()

    # TC MoM: variacion porcentual mensual en las expectativas de TC 12M
    df["tc_mom"] = df["tc_12m"].pct_change() * 100   # en %

    scores = {}
    for col, (w, direction) in WEIGHTS.items():
        if col not in df.columns:
            continue
        series = df[col].copy()
        # forward-fill puntual (fiscal no siempre se publica cada mes)
        series = series.ffill(limit=2)
        z = rolling_zscore(series, WINDOW, MIN_PERIODS)
        if direction == "inv":
            z = -z
        scores[col] = z * w

    # Suma ponderada normalizada por pesos disponibles
    score_df = pd.DataFrame(scores)
    w_avail  = score_df.notna().multiply([WEIGHTS[c][0] for c in score_df.columns]).sum(axis=1)
    icm_z    = score_df.sum(axis=1, skipna=True) / w_avail.replace(0, np.nan)

    # Escalar: 1 unidad z = SCALE puntos de ICM
    return icm_z * SCALE


def main():
    print("calcular_rem_icm | construyendo ICM-REM...")

    if not REM_PATH.exists():
        print("  ERROR: data/rem.csv no existe. Correr scraper_rem.py primero.")
        return

    df = pd.read_csv(REM_PATH)
    if df.empty:
        print("  ERROR: rem.csv esta vacio.")
        return

    icm_raw = build_icm(df)

    # Anclar baseline: el mes que contiene BASELINE vale 100
    if BASELINE not in icm_raw.index:
        # usar el mes mas cercano
        idx = icm_raw.index.get_indexer([BASELINE], method="nearest")[0]
        baseline_val = icm_raw.iloc[idx]
    else:
        baseline_val = icm_raw.loc[BASELINE]

    if pd.isna(baseline_val):
        print(f"  WARN: baseline {BASELINE} tiene z-score NaN — usando primer valor valido.")
        baseline_val = icm_raw.dropna().iloc[0]

    icm = icm_raw - baseline_val + 100.0

    # Guardar solo desde 2016 (historia minima para z-scores estables)
    result = icm.reset_index()
    result.columns = ["fecha", "icm"]
    result["icm"] = result["icm"].round(2)
    result = result.dropna(subset=["icm"])

    result.to_csv(ICM_PATH, index=False, encoding="utf-8")

    # Reporte
    post = result[result["fecha"] >= BASELINE]
    last = result.iloc[-1]
    print(f"  ICM total: {len(result)} meses | desde {BASELINE}: {len(post)}")
    print(f"  Rango: {result['icm'].min():.1f} - {result['icm'].max():.1f}")
    print(f"  Ultimo ({last['fecha']}): ICM = {last['icm']:.1f}")
    if len(post) >= 2:
        mx = post.loc[post["icm"].idxmax()]
        mn = post.loc[post["icm"].idxmin()]
        print(f"  Maximo post-baseline: {mx['icm']:.1f} ({mx['fecha']})")
        print(f"  Minimo post-baseline: {mn['icm']:.1f} ({mn['fecha']})")


if __name__ == "__main__":
    main()
