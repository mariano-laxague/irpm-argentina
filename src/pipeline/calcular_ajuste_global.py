"""
calcular_ajuste_global.py — Ajusta el IRPM sustrayendo el componente atribuible al VIX.

Metodología (Bekaert et al. 2014, Nogués-Grandes 2001):
  Para cada sub-índice (capa1, capa2, capa3), corre una regresión rolling OLS de la
  capa contra z_vix (z-score rolling del VIX). El residuo captura lo que el contexto
  financiero global NO explica — la señal específicamente argentina.

  capa_adj = capa - (α + β * z_vix)   [regresión rolling 252d]
  iep_ajustado = 100 + (raw_adj - raw_adj_baseline) * 10

Columnas nuevas en iep_diario:
  capa1_adj     residuo de capa1 ~ z_vix
  capa2_adj     residuo de capa2 ~ z_vix
  capa3_adj     residuo de capa3 ~ z_vix
  iep_ajustado  IRPM ajustado, misma escala y baseline que iep_total

Uso:
    py src/pipeline/calcular_ajuste_global.py
    py src/pipeline/calcular_ajuste_global.py --diagnosticos
"""

import sys
import sqlite3
from pathlib import Path

import pandas as pd

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / "data" / "iep.db"

WINDOW        = 252
MIN_PERIODS   = 63
BASELINE_DATE = pd.Timestamp("2023-12-11")  # Inicio gestión Milei
ESCALA        = 10.0

DIAG = "--diagnosticos" in sys.argv


# ── Migración de schema ────────────────────────────────────────────────────────

def migrate_schema():
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    existing = {row[1] for row in cur.execute("PRAGMA table_info(iep_diario)")}
    for col in ("capa1_adj", "capa2_adj", "capa3_adj", "iep_ajustado"):
        if col not in existing:
            cur.execute(f"ALTER TABLE iep_diario ADD COLUMN {col} REAL")
            print(f"  Schema: columna '{col}' agregada a iep_diario")
    conn.commit()
    conn.close()


# ── Carga ──────────────────────────────────────────────────────────────────────

def load_vix() -> pd.Series:
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql_query(
        "SELECT fecha, valor FROM raw_prices WHERE activo='VIX' ORDER BY fecha",
        conn, parse_dates=["fecha"],
    )
    conn.close()
    return df.set_index("fecha")["valor"]


def load_capas() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql_query(
        "SELECT fecha, capa1, capa2, capa3, iep_total FROM iep_diario ORDER BY fecha",
        conn, parse_dates=["fecha"],
    )
    conn.close()
    return df.set_index("fecha")


# ── Z-score rolling ────────────────────────────────────────────────────────────

def rolling_zscore(s: pd.Series) -> pd.Series:
    m  = s.rolling(WINDOW, min_periods=MIN_PERIODS).mean()
    sd = s.rolling(WINDOW, min_periods=MIN_PERIODS).std()
    return (s - m) / sd.replace(0, float("nan"))


# ── Regresión rolling OLS — vectorizada ───────────────────────────────────────

def rolling_ols_residuals(y: pd.Series, x: pd.Series) -> pd.Series:
    """
    Residuo de regresión rolling OLS: y = α + β·x + ε
    Vectorizado via rolling cov/var de pandas (O(n), sin loops).
    Solo opera sobre índice común no-nulo.
    """
    aligned  = pd.DataFrame({"y": y, "x": x}).dropna(how="any")
    y_a, x_a = aligned["y"], aligned["x"]

    roll_cov = y_a.rolling(WINDOW, min_periods=MIN_PERIODS).cov(x_a)
    roll_var = x_a.rolling(WINDOW, min_periods=MIN_PERIODS).var()
    roll_my  = y_a.rolling(WINDOW, min_periods=MIN_PERIODS).mean()
    roll_mx  = x_a.rolling(WINDOW, min_periods=MIN_PERIODS).mean()

    beta    = roll_cov / roll_var.replace(0, float("nan"))
    alpha   = roll_my - beta * roll_mx
    fitted  = alpha + beta * x_a
    residual = y_a - fitted

    return residual.reindex(y.index)


# ── Cálculo principal ──────────────────────────────────────────────────────────

def compute_adjusted(capas: pd.DataFrame, vix: pd.Series) -> pd.DataFrame:
    z_vix  = rolling_zscore(vix)
    result = pd.DataFrame(index=capas.index)

    for col in ("capa1", "capa2", "capa3"):
        s = capas[col].dropna()
        if s.empty:
            result[f"{col}_adj"] = float("nan")
        else:
            result[f"{col}_adj"] = rolling_ols_residuals(s, z_vix)

    # iep_ajustado con mismos pesos que iep_total
    c1 = result["capa1_adj"]
    c2 = result["capa2_adj"]
    c3 = result["capa3_adj"]

    has3 = c1.notna() & c2.notna() & c3.notna()
    has2 = c1.notna() & c2.notna() & ~has3

    raw3 = 0.35 * c1[has3] + 0.40 * c2[has3] + 0.25 * c3[has3]
    raw2 = 0.50 * c1[has2] + 0.50 * c2[has2]
    raw_adj = pd.concat([raw2, raw3]).sort_index()

    idx_base    = raw_adj.index.get_indexer([BASELINE_DATE], method="nearest")[0]
    baseline_v  = raw_adj.iloc[idx_base]
    result["iep_ajustado"] = 100 + (raw_adj - baseline_v) * ESCALA

    return result


# ── Guardar en DB ──────────────────────────────────────────────────────────────

def save_adjusted(result: pd.DataFrame) -> int:
    conn  = sqlite3.connect(DB_PATH)
    cur   = conn.cursor()
    saved = 0
    for fecha, row in result.iterrows():
        iep_adj = row.get("iep_ajustado")
        if pd.isna(iep_adj):
            continue
        def _f(v):
            return float(v) if pd.notna(v) else None
        cur.execute(
            """UPDATE iep_diario
               SET capa1_adj=?, capa2_adj=?, capa3_adj=?, iep_ajustado=?
               WHERE fecha=?""",
            (_f(row.get("capa1_adj")), _f(row.get("capa2_adj")),
             _f(row.get("capa3_adj")), float(iep_adj),
             fecha.strftime("%Y-%m-%d")),
        )
        if cur.rowcount:
            saved += 1
    conn.commit()
    conn.close()
    return saved


# ── Diagnósticos ───────────────────────────────────────────────────────────────

def print_diagnostics(result: pd.DataFrame, capas: pd.DataFrame, vix: pd.Series) -> None:
    adj   = result["iep_ajustado"].dropna()
    bruto = capas["iep_total"].dropna()

    print("\n=== IRPM ajustado vs. IRPM bruto ===")
    print(f"  Filas ajustado:    {len(adj)}")
    print(f"  Rango ajustado:    {adj.min():.1f} — {adj.max():.1f}")
    print(f"  Hoy  bruto:        {bruto.iloc[-1]:.1f}")
    print(f"  Hoy  ajustado:     {adj.iloc[-1]:.1f}")
    print(f"  Gap  hoy:          {adj.iloc[-1] - bruto.iloc[-1]:+.1f} pts")
    print(f"  (gap > 0 = bruto sobreestima riesgo / < 0 = subestima)")

    print("\n=== Correlación de cada capa con VIX (muestra la exposición global) ===")
    z_vix = rolling_zscore(vix)
    for col in ("capa1", "capa2", "capa3"):
        s = capas[col].dropna()
        if s.empty:
            continue
        aligned = pd.DataFrame({"y": s, "x": z_vix}).dropna()
        if len(aligned) < MIN_PERIODS:
            continue
        r    = aligned["y"].corr(aligned["x"])
        beta = (((aligned.y - aligned.y.mean()) * (aligned.x - aligned.x.mean())).sum() /
                ((aligned.x - aligned.x.mean()) ** 2).sum())
        print(f"  {col}: r(VIX)={r:+.3f}  b={beta:+.3f}  R2={r**2:.3f}")

    print("\n=== Valores en fechas clave (bruto vs. ajustado) ===")
    key_dates = {
        "2022-07-01": "Crisis Guzmán",
        "2024-12-09": "Máximo histórico",
        "2025-09-18": "Mínimo histórico",
        "2025-10-27": "Legislativas (BASELINE)",
    }
    for d, label in key_dates.items():
        ts  = pd.Timestamp(d)
        ib  = bruto.index.get_indexer([ts], method="nearest")[0]
        ia  = adj.index.get_indexer([ts], method="nearest")[0]
        if ib >= 0 and ia >= 0:
            bv = bruto.iloc[ib]
            av = adj.iloc[ia]
            print(f"  {d}  {label:<32}  bruto={bv:>7.1f}  adj={av:>7.1f}  gap={av-bv:+.1f}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("calcular_ajuste_global | IRPM ajustado por VIX (Bekaert/Nogués-Grandes)")
    print(f"DB: {DB_PATH}")

    migrate_schema()

    vix = load_vix()
    if vix.empty:
        print("  ERROR: VIX no disponible. Ejecutar scraper_vix.py primero.")
        sys.exit(1)
    print(f"  VIX: {len(vix)} filas ({vix.index[0].date()} a {vix.index[-1].date()})  último={vix.iloc[-1]:.1f}")

    capas = load_capas()
    print(f"  Capas: {len(capas)} filas en iep_diario")

    result = compute_adjusted(capas, vix)
    n      = save_adjusted(result)
    print(f"  Filas iep_ajustado guardadas: {n}")

    adj   = result["iep_ajustado"].dropna()
    bruto = capas["iep_total"].dropna()
    if not adj.empty and not bruto.empty:
        print(f"\n  IRPM bruto    ({bruto.index[-1].date()}):  {bruto.iloc[-1]:.1f}")
        print(f"  IRPM ajustado ({adj.index[-1].date()}):  {adj.iloc[-1]:.1f}")
        print(f"  Gap hoy: {adj.iloc[-1] - bruto.iloc[-1]:+.1f} pts")

    if DIAG:
        print_diagnostics(result, capas, vix)
    else:
        print("\nCorrer con --diagnosticos para correlaciones y fechas clave.")


if __name__ == "__main__":
    main()
