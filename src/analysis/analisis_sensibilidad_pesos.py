"""
analisis_sensibilidad_pesos.py — H2.2: sensibilidad de la narrativa a variaciones de pesos.

Objetivo: verificar que la narrativa del IRPM (mínimo, máximo, baseline) es robusta
a variaciones de ±10% en cada capa respecto a los pesos base (35/40/25).

Si ningún escenario cambia el mínimo o máximo más de ±3 pts IRPM → conclusión:
"los resultados son robustos a variaciones de ±10% en cada peso".

Uso:
    python src/analysis/analisis_sensibilidad_pesos.py
"""

import sys
import sqlite3
import shutil
from pathlib import Path
from itertools import product

import pandas as pd
import numpy as np

ROOT = Path(__file__).parent.parent.parent
DB_PATH = ROOT / "data" / "iep.db"

BASELINE_DATE = pd.Timestamp("2023-12-11")
ESCALA = 10.0

# Grid de pesos a explorar
W1_RANGE = [0.25, 0.30, 0.35, 0.40, 0.45]  # Capa 1 (cambiaria)
W2_RANGE = [0.35, 0.40, 0.45, 0.50]          # Capa 2 (bonos soberanos)
W3_RANGE = [0.15, 0.20, 0.25, 0.30]          # Capa 3 (vol accionaria)

PESOS_BASE = (0.35, 0.40, 0.25)


def load_capas() -> pd.DataFrame:
    """Carga capa1, capa2, capa3 desde SQLite. Copia a /tmp si hay I/O error."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        df = pd.read_sql_query(
            "SELECT fecha, capa1, capa2, capa3 FROM iep_diario ORDER BY fecha",
            conn, parse_dates=["fecha"],
        )
        conn.close()
    except sqlite3.OperationalError:
        tmp = Path("/tmp/iep_sens.db")
        shutil.copy(str(DB_PATH), str(tmp))
        conn = sqlite3.connect(str(tmp))
        df = pd.read_sql_query(
            "SELECT fecha, capa1, capa2, capa3 FROM iep_diario ORDER BY fecha",
            conn, parse_dates=["fecha"],
        )
        conn.close()
    return df.set_index("fecha").dropna(subset=["capa1", "capa2", "capa3"])


def compute_irpm(df: pd.DataFrame, w1: float, w2: float, w3: float) -> pd.Series:
    raw = w1 * df["capa1"] + w2 * df["capa2"] + w3 * df["capa3"]
    idx_base = raw.index.get_indexer([BASELINE_DATE], method="nearest")[0]
    baseline_val = raw.iloc[idx_base]
    return 100 + (raw - baseline_val) * ESCALA


def main():
    print("H2.2 — Análisis de sensibilidad de pesos del IRPM")
    print(f"Pesos base: Capa1={PESOS_BASE[0]:.0%} | Capa2={PESOS_BASE[1]:.0%} | Capa3={PESOS_BASE[2]:.0%}")
    print()

    df = load_capas()
    print(f"Datos: {df.index[0].date()} → {df.index[-1].date()} ({len(df)} ruedas con las 3 capas)\n")

    # Serie base
    irpm_base = compute_irpm(df, *PESOS_BASE)
    base_min = irpm_base.min()
    base_max = irpm_base.max()
    base_min_date = irpm_base.idxmin()
    base_max_date = irpm_base.idxmax()
    base_now = irpm_base.iloc[-1]

    print(f"Serie base (35/40/25):")
    print(f"  Min: {base_min:.1f} ({base_min_date.date()})")
    print(f"  Max: {base_max:.1f} ({base_max_date.date()})")
    print(f"  Hoy: {base_now:.1f}")
    print()

    # Grid search — todas las combinaciones que sumen 100%
    results = []
    for w1, w2, w3 in product(W1_RANGE, W2_RANGE, W3_RANGE):
        if abs(w1 + w2 + w3 - 1.0) > 0.001:
            continue

        irpm = compute_irpm(df, w1, w2, w3)
        r = float(np.corrcoef(irpm_base.values, irpm.values)[0, 1])

        results.append({
            "w1": w1, "w2": w2, "w3": w3,
            "label": f"{w1:.0%}/{w2:.0%}/{w3:.0%}",
            "r_vs_base": r,
            "min_irpm": irpm.min(),
            "max_irpm": irpm.max(),
            "min_date": irpm.idxmin().strftime("%Y-%m-%d"),
            "max_date": irpm.idxmax().strftime("%Y-%m-%d"),
            "delta_min": irpm.min() - base_min,
            "delta_max": irpm.max() - base_max,
            "now_irpm": irpm.iloc[-1],
            "delta_now": irpm.iloc[-1] - base_now,
        })

    res = pd.DataFrame(results)
    n_combos = len(res)

    print(f"Combinaciones evaluadas: {n_combos}")
    print(f"Rango de correlaciones vs. base: r = {res['r_vs_base'].min():.4f} – {res['r_vs_base'].max():.4f}")
    print(f"Δ mínimo (vs. base):  {res['delta_min'].min():+.1f} a {res['delta_min'].max():+.1f} pts")
    print(f"Δ máximo (vs. base):  {res['delta_max'].min():+.1f} a {res['delta_max'].max():+.1f} pts")
    print(f"Δ hoy (vs. base):     {res['delta_now'].min():+.1f} a {res['delta_now'].max():+.1f} pts")
    print()

    # Conclusión de robustez
    threshold = 3.0
    max_delta_min = max(abs(res['delta_min'].min()), abs(res['delta_min'].max()))
    max_delta_max = max(abs(res['delta_max'].min()), abs(res['delta_max'].max()))

    if max_delta_min <= threshold and max_delta_max <= threshold:
        print(f"✓ ROBUSTO: ningún escenario altera el mínimo o máximo en más de {threshold:.0f} pts.")
        print(f"  Δmin máximo={max_delta_min:.1f} pts | Δmax máximo={max_delta_max:.1f} pts")
    else:
        print(f"! SENSIBLE: algunos escenarios alteran min/max en más de {threshold:.0f} pts.")
        print(f"  Δmin máximo={max_delta_min:.1f} pts | Δmax máximo={max_delta_max:.1f} pts")

    print()

    # Top 5 escenarios con mayor desviación del mínimo
    extremos = res.reindex(res['delta_min'].abs().nlargest(5).index)
    print("Top 5 escenarios con mayor desviación en el mínimo histórico:")
    print(f"{'Pesos':>12} {'r':>6} {'Min':>7} {'ΔMin':>6} {'Max':>7} {'ΔMax':>6} {'Hoy':>7} {'ΔHoy':>6}")
    print("-" * 66)
    for _, row in extremos.iterrows():
        print(f"{row['label']:>12} {row['r_vs_base']:>6.4f} {row['min_irpm']:>7.1f} {row['delta_min']:>+6.1f} "
              f"{row['max_irpm']:>7.1f} {row['delta_max']:>+6.1f} {row['now_irpm']:>7.1f} {row['delta_now']:>+6.1f}")

    print()

    # Coherencia narrativa: ¿el mínimo y el máximo siempre caen en las mismas fechas?
    unique_min_dates = res['min_date'].value_counts()
    unique_max_dates = res['max_date'].value_counts()

    print(f"Distribución de fechas del mínimo histórico ({len(unique_min_dates)} fechas distintas):")
    for d, cnt in unique_min_dates.items():
        pct = 100 * cnt / n_combos
        print(f"  {d}: {cnt}/{n_combos} combinaciones ({pct:.0f}%)")

    print(f"\nDistribución de fechas del máximo histórico ({len(unique_max_dates)} fechas distintas):")
    for d, cnt in unique_max_dates.items():
        pct = 100 * cnt / n_combos
        print(f"  {d}: {cnt}/{n_combos} combinaciones ({pct:.0f}%)")

    if len(unique_min_dates) == 1:
        print(f"\n✓ Narrativa estable: el mínimo siempre cae en {unique_min_dates.index[0]}.")
    else:
        print(f"\n! La fecha del mínimo varía según los pesos.")

    if len(unique_max_dates) == 1:
        print(f"✓ Narrativa estable: el máximo siempre cae en {unique_max_dates.index[0]}.")
    else:
        print(f"! La fecha del máximo varía según los pesos.")

    # Exportar tabla completa
    out = ROOT / "data" / "sensibilidad_pesos.csv"
    res.sort_values("r_vs_base", ascending=False).to_csv(out, index=False)
    print(f"\nTabla completa exportada: {out}")


if __name__ == "__main__":
    main()
