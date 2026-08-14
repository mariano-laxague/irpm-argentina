"""
calcular_capa1.py — Calcula el sub-índice Capa 1 del IEP.

Componentes activos:
  MEP (Dólar bolsa): AL30_ARS / AL30D_USD — señal cambiaria corriente.
  ROFEX_1M_EQUIV:   serie unificada construida por calcular_rofex_signal.py.

Blend (donde ROFEX_1M_EQUIV disponible):
  capa1 = 0.5 × z_mep + 0.5 × z_rofex
  Donde:
    z_mep   = −rolling_zscore(log(MEP))          [MEP alto = malo]
    z_rofex = −rolling_zscore(ROFEX_equiv/MEP-1) [premium alto = malo]
  Donde solo MEP disponible: capa1 = z_mep.

Componente futuro (activación ~mar-2027):
  ROFEX electoral kink: DLR_DIC27 / DLR_ENE27 - 1
  DLR_ENE27: 69 filas desde ~feb-2026 (umbral cumplido).
  DLR_DIC27: no listado en PPI aun — aparece ~dic-2026 (~12m antes de su vencimiento).
  Activar cuando DLR_DIC27 tenga >= MIN_PERIODS (63) filas en raw_prices.

Normalización: z-score rolling 252 días hábiles, min_periods=63.

Uso:
    py src/pipeline/calcular_capa1.py
    py src/pipeline/calcular_capa1.py --diagnosticos
"""

import sys
import sqlite3
from pathlib import Path

import pandas as pd
import numpy as np

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / "data" / "iep.db"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WINDOW      = 252
MIN_PERIODS = 63

DIAG = "--diagnosticos" in sys.argv


# ── Carga ──────────────────────────────────────────────────────────────────────

def load_series(activo: str) -> pd.Series:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT fecha, valor FROM raw_prices WHERE activo=? ORDER BY fecha",
        conn, params=(activo,), parse_dates=["fecha"],
    )
    conn.close()
    return df.set_index("fecha")["valor"]


# ── MEP ────────────────────────────────────────────────────────────────────────

def compute_mep() -> pd.Series:
    al30_ars = load_series("AL30")    # precio en ARS por unidad de bono
    al30d_usd = load_series("AL30D")  # precio en USD por unidad de bono
    mep = (al30_ars / al30d_usd).rename("MEP")
    return mep.dropna()


def save_mep(mep: pd.Series) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    saved = 0
    for fecha, valor in mep.items():
        if pd.isna(valor) or valor <= 0:
            continue
        cur.execute("""
            INSERT OR REPLACE INTO raw_prices (activo, fecha, valor, fuente)
            VALUES (?, ?, ?, ?)
        """, ("MEP", fecha.strftime("%Y-%m-%d"), float(valor), "PPI_AL30_ratio"))
        saved += 1
    conn.commit()
    conn.close()
    return saved


# ── Z-score rolling ────────────────────────────────────────────────────────────

def rolling_zscore(s: pd.Series) -> pd.Series:
    m  = s.rolling(WINDOW, min_periods=MIN_PERIODS).mean()
    sd = s.rolling(WINDOW, min_periods=MIN_PERIODS).std()
    return (s - m) / sd.replace(0, float("nan"))


# ── Cálculo Capa 1 (blend MEP + ROFEX) ────────────────────────────────────────

def compute_capa1(mep: pd.Series) -> pd.Series:
    # z_mep: MEP alto relativo = señal mala → negativo para IEP
    z_mep = -rolling_zscore(np.log(mep))

    # Cargar ROFEX_1M_EQUIV si existe
    rofex = load_series("ROFEX_1M_EQUIV")
    if rofex.empty:
        return z_mep.dropna().rename("capa1")

    # Premium de devaluación implícita (ROFEX/MEP - 1)
    # No usar precios de otra fecha: si falta MEP en la rueda de ROFEX,
    # la señal queda incompleta y el compuesto usa el fallback documentado.
    mep_aligned = mep.reindex(rofex.index)
    premium = rofex / mep_aligned - 1

    # z_rofex: premium bajo (ROFEX ≈ MEP) = menos miedo devaluatorio = buena señal
    # Se invierte: cuando premium < media histórica = menos devaluación esperada = positivo para IEP
    z_rofex = -rolling_zscore(premium)

    # Blend 50/50 donde ambos disponibles; fallback a z_mep puro donde no hay ROFEX
    blend = 0.5 * z_mep + 0.5 * z_rofex
    capa1 = blend.combine_first(z_mep)

    return capa1.dropna().rename("capa1")


# ── Guardar Capa 1 en iep_diario ───────────────────────────────────────────────

def save_capa1(capa1: pd.Series) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    saved = 0
    for fecha, valor in capa1.items():
        if pd.isna(valor):
            continue
        cur.execute("""
            INSERT OR REPLACE INTO iep_diario (fecha, capa1, pesos_version)
            VALUES (?, ?, ?)
            ON CONFLICT(fecha) DO UPDATE SET capa1=excluded.capa1
        """, (fecha.strftime("%Y-%m-%d"), float(valor), "50-50-0"))
        saved += 1
    conn.commit()
    conn.close()
    return saved


# ── ROFEX Electoral Kink (PENDIENTE — activar ~mar-2027) ─────────────────────
#
# Señal: DLR_DIC27 / DLR_ENE27 - 1
# Captura la prima de riesgo devaluatorio post-electoral implícita en ROFEX.
# DLR_ENE27: pre-elección (ene-2027). YA disponible: 69 filas desde ~feb-2026.
# DLR_DIC27: post-elección (dic-2027). No listado aún — entra al mercado ~dic-2026.
#
# Condición de activación: DLR_DIC27 debe tener >= MIN_PERIODS (63) filas.
# (ENE27 ya supera el umbral; DIC27 es el cuello de botella.)
# Estimación: DIC27 disponible en PPI desde ~dic-2026 → 63 filas acumuladas ~mar-2027.
#
# Blend con MEP+ROFEX cuando activo (sujeto a revisión):
#   capa1 = 0.75 * (z_mep + z_rofex) / 2 + 0.25 * z_rofex_kink

ROFEX_KINK_ACTIVO = False   # cambiar a True en agosto 2026 si condición cumplida

def compute_rofex_electoral_kink() -> pd.Series | None:
    """
    Devuelve z-score invertido del spread DLR_DIC27/DLR_ENE27-1.
    Retorna None si no hay suficientes datos (< MIN_PERIODS).
    """
    dlr_ene27 = load_series("DLR_ENE27")
    dlr_dic27 = load_series("DLR_DIC27")
    if len(dlr_ene27) < MIN_PERIODS or len(dlr_dic27) < MIN_PERIODS:
        return None
    kink = (dlr_dic27 / dlr_ene27 - 1).dropna()
    z = rolling_zscore(kink)
    return (-z).rename("z_rofex_kink")   # invertido: kink alto = miedo = señal mala


# ── Diagnósticos ───────────────────────────────────────────────────────────────

def print_diagnostics(mep: pd.Series, capa1: pd.Series) -> None:
    print("\n=== MEP — Serie completa ===")
    print(f"  Desde:  {mep.index[0].date()}")
    print(f"  Hasta:  {mep.index[-1].date()}")
    print(f"  Min:    {mep.min():.1f} ARS/USD  ({mep.idxmin().date()})")
    print(f"  Max:    {mep.max():.1f} ARS/USD  ({mep.idxmax().date()})")
    print(f"  Ultimo: {mep.iloc[-1]:.1f} ARS/USD")

    print("\n=== Capa 1 — Serie completa ===")
    print(f"  Desde:  {capa1.index[0].date()}")
    print(f"  Hasta:  {capa1.index[-1].date()}")
    print(f"  Min:    {capa1.min():.4f}  ({capa1.idxmin().date()})")
    print(f"  Max:    {capa1.max():.4f}  ({capa1.idxmax().date()})")

    print("\n=== Valores en fechas clave ===")
    key_dates = {
        "2022-07-01": "Crisis Guzman (brecha alta)",
        "2023-08-14": "PASO 2023",
        "2024-01-02": "Inicio Milei (post-devaluacion)",
        "2024-07-01": "H2 2024 (crawling peg estable)",
        "2025-04-14": "Flotacion libre",
        "2025-10-27": "Legislativas 2025 (BASELINE)",
        "2026-05-08": "Ultimo",
    }
    for d, label in key_dates.items():
        try:
            mep_v  = mep.loc[pd.Timestamp(d)]
            cap_v  = capa1.loc[pd.Timestamp(d)]
            print(f"  {d}  {label:<38}  MEP={mep_v:>7.1f}  Capa1={cap_v:+.4f}")
        except KeyError:
            idx = capa1.index.get_indexer([pd.Timestamp(d)], method="nearest")[0]
            fecha_r = capa1.index[idx]
            mep_v  = mep.reindex([fecha_r]).iloc[0]
            cap_v  = capa1.iloc[idx]
            print(f"  {d}  {label:<38}  MEP={mep_v:>7.1f}  Capa1={cap_v:+.4f}  (real: {fecha_r.date()})")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("calcular_capa1 | IEP Capa 1 — MEP (AL30_ARS / AL30D_USD)")
    print(f"DB: {DB_PATH}")
    print(f"Ventana z-score: {WINDOW}d sobre log(MEP)\n")

    mep = compute_mep()
    n_mep = save_mep(mep)
    print(f"MEP calculado: {len(mep)} filas | guardadas en raw_prices: {n_mep}")

    capa1 = compute_capa1(mep)
    n_c1  = save_capa1(capa1)
    print(f"Capa 1 guardada en iep_diario: {n_c1} filas")

    if DIAG:
        print_diagnostics(mep, capa1)
    else:
        baseline = pd.Timestamp("2025-10-27")
        idx = capa1.index.get_indexer([baseline], method="nearest")[0]
        v_base = capa1.iloc[idx]
        v_now  = capa1.iloc[-1]
        mep_now = mep.iloc[-1]
        print(f"\nMEP actual:              {mep_now:.1f} ARS/USD")
        print(f"Baseline (27-oct-2025):  {v_base:+.4f}")
        print(f"Ultimo ({capa1.index[-1].date()}):  {v_now:+.4f}")
        print(f"Diferencia vs. baseline: {v_now - v_base:+.4f}")
        print("\nCorrer con --diagnosticos para detalle completo.")


if __name__ == "__main__":
    main()
    from src.pipeline.sanity import assert_capa_sanity
    assert_capa_sanity("capa1")
