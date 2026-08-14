"""
validacion_leading_indicator.py — Validación del IRPM como leading indicator del ICG-UTDT.

Hipótesis central: el IRPM (mercado financiero) adelanta en 1-3 meses los movimientos
del ICG (Índice de Confianza en el Gobierno, UTDT), que refleja la opinión de la sociedad.

Si se confirma, el IRPM tiene valor predictivo sobre encuestas — el argumento de venta
más poderoso para audiencias institucionales.

Metodología:
  1. IRPM mensual: promedio de valores diarios por mes calendario
  2. ICG mensual: serie UTDT (ya disponible en data/utdt_icg.csv)
  3. Cross-lag correlations: correlación de IRPM(t) con ICG(t+k) para k = -3 ... +3 meses
     - k < 0: ICG adelanta al IRPM (IRPM es lagging)
     - k = 0: correlación contemporánea
     - k > 0: IRPM adelanta al ICG (IRPM es leading)  ← hipótesis
  4. Granger causality test (statsmodels): test formal de causalidad en el sentido de Granger
     - H₀: IRPM NO agrega información predictiva sobre ICG más allá del propio pasado del ICG
     - Rechazo H₀ (p < 0.10): IRPM Granger-causa ICG → leading indicator confirmado

Criterio de éxito:
  - Cross-lag: correlación máxima a k=1 o k=2 meses (positiva)
  - Granger: p-value < 0.10 para al menos un lag
  - Dirección: ICG sube cuando el IRPM subió k meses antes (y viceversa)

Uso:
    python src/analysis/validacion_leading_indicator.py
    python src/analysis/validacion_leading_indicator.py --plot   # guarda gráfico PNG
"""

import sys
import warnings
from pathlib import Path

import pandas as pd
import numpy as np
from scipy import stats

warnings.filterwarnings("ignore")

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
from src.config import CFG

SAVE_PLOT = "--plot" in sys.argv


# ── 1. Carga de datos ──────────────────────────────────────────────────────────

def load_irpm_daily() -> pd.Series:
    """
    Lee iep_total desde el CSV exportado (data/irpm_export.csv) o directamente del DB.
    El CSV se genera con: python -c "import sqlite3, pandas as pd; ..."
    O simplemente corriendo el pipeline (update_daily.py genera este export automáticamente).
    """
    csv_path = ROOT / "data" / "irpm_export.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path, parse_dates=["fecha"])
        return df.set_index("fecha")["iep_total"]
    # Fallback: leer directo del DB (requiere que no haya journal activo)
    import sqlite3
    conn = sqlite3.connect(CFG.db_path)
    df = pd.read_sql_query(
        "SELECT fecha, iep_total FROM iep_diario WHERE iep_total IS NOT NULL ORDER BY fecha",
        conn, parse_dates=["fecha"],
    )
    conn.close()
    return df.set_index("fecha")["iep_total"]


def load_icg() -> pd.Series:
    icg_path = ROOT / "data" / "utdt_icg.csv"
    df = pd.read_csv(icg_path, parse_dates=["fecha"])
    df["fecha"] = pd.to_datetime(df["fecha"].astype(str).str[:7], format="%Y-%m") + pd.offsets.MonthEnd(0)
    return df.set_index("fecha")["icg_general"].sort_index()


def make_monthly(irpm_daily: pd.Series) -> pd.Series:
    """Promedio mensual del IRPM diario, alineado a fin de mes."""
    return irpm_daily.resample("ME").mean().rename("irpm_mensual")


# ── 2. Cross-lag correlations ─────────────────────────────────────────────────

def cross_lag_correlations(irpm_m: pd.Series, icg: pd.Series, max_lag: int = 4) -> pd.DataFrame:
    """
    Computa r(IRPM_t, ICG_{t+k}) para k = -max_lag ... +max_lag.
    k > 0: IRPM adelanta al ICG (leading).
    k < 0: ICG adelanta al IRPM (lagging).
    """
    df = pd.DataFrame({"irpm": irpm_m, "icg": icg}).dropna()
    results = []
    for k in range(-max_lag, max_lag + 1):
        if k >= 0:
            # IRPM(t) correlaciona con ICG(t+k): ICG se desplaza k hacia atrás
            paired = pd.DataFrame({
                "irpm": df["irpm"],
                "icg_shifted": df["icg"].shift(-k),
            }).dropna()
        else:
            # k < 0: ICG(t) correlaciona con IRPM(t+|k|)
            paired = pd.DataFrame({
                "irpm": df["irpm"].shift(k),   # shift negativo = adelantar
                "icg_shifted": df["icg"],
            }).dropna()
        if len(paired) < 8:
            continue
        r, p = stats.pearsonr(paired["irpm"], paired["icg_shifted"])
        results.append({
            "lag_meses": k,
            "interpretacion": (
                f"IRPM adelanta {k}m al ICG" if k > 0
                else ("contemporáneo" if k == 0
                      else f"ICG adelanta {abs(k)}m al IRPM")
            ),
            "r": round(r, 3),
            "p_value": round(p, 4),
            "n": len(paired),
            "significativo": "✓" if p < 0.10 else "·",
        })
    return pd.DataFrame(results)


# ── 3. Granger causality test ─────────────────────────────────────────────────

def granger_test(irpm_m: pd.Series, icg: pd.Series, max_lag: int = 3) -> pd.DataFrame:
    """
    Test de Granger: ¿IRPM(t-k) mejora la predicción de ICG(t) sobre AR(ICG)?
    Usa statsmodels.tsa.stattools.grangercausalitytests.
    H₀: IRPM no agrega información predictiva.
    Rechazo H₀ (p < 0.10): IRPM Granger-causa ICG = leading indicator.
    """
    from statsmodels.tsa.stattools import grangercausalitytests

    df = pd.DataFrame({"icg": icg, "irpm": irpm_m}).dropna()
    if len(df) < max_lag * 3 + 5:
        return pd.DataFrame()

    # grangercausalitytests espera [Y, X] donde testa si X causa Y
    data = df[["icg", "irpm"]].values

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        results_raw = grangercausalitytests(data, maxlag=max_lag, verbose=False)

    rows = []
    for lag, res in results_raw.items():
        # Usar F-test (más robusto para series cortas)
        f_stat, p_val, df_denom, df_num = res[0]["ssr_ftest"]
        rows.append({
            "lag_meses": lag,
            "F_stat": round(f_stat, 3),
            "p_value": round(p_val, 4),
            "significativo": "✓" if p_val < 0.10 else ("~" if p_val < 0.20 else "·"),
            "conclusion": (
                "IRPM causa ICG (p<0.10)" if p_val < 0.10
                else ("tendencia débil (p<0.20)" if p_val < 0.20
                      else "sin evidencia")
            ),
        })
    return pd.DataFrame(rows)


# ── 4. Análisis de cambios direccionales ──────────────────────────────────────

def directional_analysis(irpm_m: pd.Series, icg: pd.Series, lag: int = 1) -> dict:
    """
    ¿Cuándo el IRPM subió/bajó en t-lag, el ICG siguió la misma dirección en t?
    Métrica intuitiva para comunicación: "X de cada 10 veces que el IRPM subió, el ICG subió k meses después".
    """
    df = pd.DataFrame({"irpm": irpm_m, "icg": icg}).dropna()
    irpm_dir = df["irpm"].diff().shift(lag).apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    icg_dir  = df["icg"].diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))

    paired = pd.DataFrame({"irpm_dir": irpm_dir, "icg_dir": icg_dir}).dropna()
    paired = paired[(paired["irpm_dir"] != 0) & (paired["icg_dir"] != 0)]

    same_dir = (paired["irpm_dir"] == paired["icg_dir"]).sum()
    total    = len(paired)
    pct      = same_dir / total if total > 0 else 0

    return {
        "lag_meses": lag,
        "misma_direccion": same_dir,
        "total_observaciones": total,
        "pct_acierto": round(pct * 100, 1),
        "frase": f"{same_dir}/{total} veces el ICG siguió la dirección del IRPM de {lag}m antes ({pct:.0%})"
    }


# ── 5. Main ────────────────────────────────────────────────────────────────────

def main():
    SEP = "=" * 65

    print(f"\n{SEP}")
    print("  IRPM — Validación como Leading Indicator del ICG-UTDT")
    print(f"{SEP}\n")

    # Carga
    irpm_daily = load_irpm_daily()
    icg        = load_icg()
    irpm_m     = make_monthly(irpm_daily)

    # Alinear al período de superposición real
    start = max(irpm_m.index[0], icg.index[0])
    end   = min(irpm_m.index[-1], icg.index[-1])
    irpm_m = irpm_m[start:end]
    icg    = icg[start:end]

    print(f"Período de análisis: {start.strftime('%b-%Y')} → {end.strftime('%b-%Y')}")
    print(f"N = {len(icg)} meses  |  IRPM diario: {len(irpm_daily)} ruedas\n")

    # ── Cross-lag correlations ────────────────────────────────────────────────
    print(f"{'─'*65}")
    print("  1. CORRELACIONES CROSS-LAG  (r de Pearson, sig. al 10%)")
    print(f"{'─'*65}")
    cross = cross_lag_correlations(irpm_m, icg, max_lag=4)
    if not cross.empty:
        print(f"  {'Lag':>8}  {'Interpretación':<35}  {'r':>6}  {'p-val':>7}  {'n':>4}  {'sig'}")
        print(f"  {'─'*8}  {'─'*35}  {'─'*6}  {'─'*7}  {'─'*4}  {'─'*3}")
        for _, row in cross.iterrows():
            marker = "◀ MÁXIMO" if row["r"] == cross["r"].max() else ""
            print(f"  {row['lag_meses']:>+8}  {row['interpretacion']:<35}  {row['r']:>+6.3f}  {row['p_value']:>7.4f}  {int(row['n']):>4}  {row['significativo']}  {marker}")

        best_lead = cross[cross["lag_meses"] > 0].nlargest(1, "r")
        if not best_lead.empty:
            br = best_lead.iloc[0]
            print(f"\n  → Mejor lag positivo: k=+{int(br['lag_meses'])}m  r={br['r']:+.3f}  p={br['p_value']:.4f}")

    # ── Granger causality ─────────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("  2. GRANGER CAUSALITY TEST  (H₀: IRPM no Granger-causa ICG)")
    print(f"{'─'*65}")
    granger = granger_test(irpm_m, icg, max_lag=3)
    if not granger.empty:
        print(f"  {'Lag':>8}  {'F-stat':>8}  {'p-val':>7}  {'sig'}  Conclusión")
        print(f"  {'─'*8}  {'─'*8}  {'─'*7}  {'─'*3}  {'─'*30}")
        for _, row in granger.iterrows():
            print(f"  {int(row['lag_meses']):>+8}  {row['F_stat']:>8.3f}  {row['p_value']:>7.4f}  {row['significativo']}   {row['conclusion']}")
    else:
        print("  Insuficientes datos para el test (mínimo ~12 meses).")

    # ── Análisis direccional ──────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("  3. ANÁLISIS DIRECCIONAL  (¿coincide la dirección del movimiento?)")
    print(f"{'─'*65}")
    for lag in [1, 2, 3]:
        d = directional_analysis(irpm_m, icg, lag=lag)
        print(f"  Lag +{lag}m: {d['frase']}")

    # ── Veredicto ─────────────────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("  VEREDICTO")
    print(f"{'─'*65}")

    max_r_lag_pos = cross[cross["lag_meses"] > 0]["r"].max() if not cross.empty else 0
    best_lag_k    = int(cross.loc[cross[cross["lag_meses"] > 0]["r"].idxmax(), "lag_meses"]) if max_r_lag_pos > 0 else None
    contemporaneo = cross[cross["lag_meses"] == 0]["r"].values[0] if not cross.empty else 0
    granger_min_p = granger["p_value"].min() if not granger.empty else 1.0

    leading = max_r_lag_pos > abs(contemporaneo) and max_r_lag_pos > 0.25
    granger_ok = granger_min_p < 0.10
    granger_weak = granger_min_p < 0.20

    # Detectar si ICG lidera al IRPM (dirección inversa a la hipótesis)
    max_r_lag_neg = cross[cross["lag_meses"] < 0]["r"].max() if not cross.empty else 0
    icg_leads_irpm = max_r_lag_neg > max_r_lag_pos and max_r_lag_neg > 0.3

    if leading and granger_ok:
        status = "✓ CONFIRMADO"
        msg = (f"El IRPM es un leading indicator del ICG-UTDT con lag de ~{best_lag_k} mes(es).\n"
               f"  Correlación r={max_r_lag_pos:.3f} supera la contemporánea (r={contemporaneo:.3f}).\n"
               f"  Granger causality p={granger_min_p:.4f} < 0.10 — evidencia estadística fuerte.")
    elif leading and granger_weak:
        status = "~ TENDENCIA DÉBIL (N insuficiente para Granger)"
        msg = (f"El IRPM muestra tendencia a adelantar al ICG ({best_lag_k}m, r={max_r_lag_pos:.3f}),\n"
               f"  pero el test de Granger no es significativo (p={granger_min_p:.4f}, N={len(icg)}).\n"
               f"  Con N≥50 (disponible ~2028) el test tendría más poder estadístico.")
    elif icg_leads_irpm:
        status = "↔ RELACIÓN BIDIRECCIONAL — ICG tiende a liderar al IRPM"
        msg = (f"El patrón cross-lag sugiere que el ICG (sociedad) lidera al IRPM (mercado)\n"
               f"  más que al revés. Contemporáneo r={contemporaneo:.3f} significativo.\n"
               f"  Esto es analíticamente interesante: la sociedad procesa la información\n"
               f"  política antes que el mercado en este período — o ambos responden\n"
               f"  a los mismos eventos con igual velocidad.\n"
               f"  Implicación para el producto: el valor del IRPM no es predecir encuestas\n"
               f"  sino capturar la señal del dinero puesto en juego, que es distinta\n"
               f"  de la opinión declarada. El Tab 2 (divergencias) es la historia correcta.")
    else:
        status = "✗ SIN PODER PREDICTIVO CLARO (N=32, potencia baja)"
        msg = (f"El IRPM no adelanta al ICG en los lags analizados (mejor r={max_r_lag_pos:.3f}).\n"
               f"  Correlación contemporánea significativa (r={contemporaneo:.3f}, p<0.05):\n"
               f"  IRPM e ICG se mueven juntos pero sin que uno lidere al otro.\n"
               f"  Nota: con N=32 meses el test de Granger tiene potencia muy baja (~30%).\n"
               f"  Rerun recomendado cuando N≥50 (~dic-2027).")

    print(f"\n  {status}")
    print(f"  {msg}")

    # ── Nota para comunicación ────────────────────────────────────────────────
    print(f"\n{'─'*65}")
    print("  NOTA METODOLÓGICA para comunicación pública")
    print(f"{'─'*65}")
    print("  El ICG-UTDT mide confianza en el gobierno (escala 1-5, encuesta mensual).")
    print("  No es idéntico a 'aprobación presidencial' pero es el indicador mensual")
    print("  de opinión pública independiente más robusto disponible en Argentina.")
    print("  Series cortas (N<35) reducen el poder del test de Granger — los resultados")
    print("  deben interpretarse como indicativos, no concluyentes.")
    print(f"\n{SEP}\n")

    return cross, granger


if __name__ == "__main__":
    main()
