"""
calcular_rofex_signal.py — Señal ROFEX unificada 2022-hoy.

Construye ROFEX_1M_EQUIV: serie continua del precio forward a 1 mes, unificando tres fuentes:
  · SSPM datos.gob.ar :  2022-01-03 → 2024-04-17  (ROFEX_1M)
  · BCR Boletines PDF :  2024-04-18 → 2025-10-07  (ROFEX_BCR_1M)
  · PPI FUTUROS       :  2025-10-08 → hoy          (DLR front-month, normalizado a 1M)

Normalización PPI → equivalente 1-mes:
    equiv = MEP × (DLR_front / MEP)^(1 / meses_al_vto)
    Ejemplo: DLR_MAY26 a 7 meses de distancia con ratio DLR/MEP=1.01/mes ×7
    → extrae la tasa mensual implícita y la proyecta a 1 mes.

Señal resultante (guardada como activo ROFEX_1M_EQUIV, fuente ROFEX_UNIFIED):
    Valor alto relativo → mercado espera devaluación → señal mala → IEP baja.

Uso:
    py src/pipeline/calcular_rofex_signal.py
    py src/pipeline/calcular_rofex_signal.py --diagnosticos
"""

import sys
import sqlite3
from pathlib import Path

import pandas as pd
import numpy as np

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / "data" / "iep.db"

DIAG = "--diagnosticos" in sys.argv

MES_MAP = {
    "ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4,
    "MAY": 5, "JUN": 6, "JUL": 7, "AGO": 8,
    "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12,
}


# ── Carga ─────────────────────────────────────────────────────────────────────

def load_series(activo: str) -> pd.Series:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT fecha, valor FROM raw_prices WHERE activo=? ORDER BY fecha",
        conn, params=(activo,), parse_dates=["fecha"],
    )
    conn.close()
    return df.set_index("fecha")["valor"]


def load_ppi_contracts() -> pd.DataFrame:
    """Carga todos los contratos DLR_* de PPI: DataFrame wide (fecha × contrato)."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT fecha, activo, valor FROM raw_prices WHERE fuente='PPI_FUTUROS' ORDER BY fecha",
        conn, parse_dates=["fecha"],
    )
    conn.close()
    if df.empty:
        return pd.DataFrame()
    return df.pivot(index="fecha", columns="activo", values="valor")


# ── Fecha de vencimiento aproximada ──────────────────────────────────────────

def contract_expiry(activo: str) -> pd.Timestamp | None:
    """
    DLR_MAY26 → 2026-05-15 (proxy del tercer miércoles del mes).
    """
    parts = activo.split("_")
    if len(parts) < 2:
        return None
    suffix = parts[-1]
    mes_str = suffix[:3].upper()
    anio_str = suffix[3:]
    mes = MES_MAP.get(mes_str)
    if mes is None or len(anio_str) != 2:
        return None
    try:
        return pd.Timestamp(f"20{anio_str}-{mes:02d}-15")
    except ValueError:
        return None


# ── Equivalente 1-mes para período PPI ───────────────────────────────────────

def compute_ppi_equiv(ppi: pd.DataFrame, mep: pd.Series) -> pd.Series:
    """
    Para cada fecha, elige el contrato DLR de menor vencimiento no expirado y
    normaliza a equivalente 1-mes via: MEP × (DLR_front / MEP)^(1 / meses_al_vto).
    """
    expiries = {col: contract_expiry(col) for col in ppi.columns}
    expiries = {k: v for k, v in expiries.items() if v is not None}

    results = {}
    for fecha, row in ppi.iterrows():
        mep_val = mep.get(fecha, np.nan)
        if pd.isna(mep_val) or mep_val <= 0:
            continue

        # Contratos con al menos 20 días al vencimiento (evitar amplificación en expiry)
        min_expiry = fecha + pd.Timedelta(days=20)
        validos = {
            col: (expiries[col], row[col])
            for col in expiries
            if col in row.index and not pd.isna(row[col]) and expiries[col] >= min_expiry
        }
        if not validos:
            continue

        # Front month: menor vencimiento
        front = min(validos, key=lambda c: validos[c][0])
        expiry, dlr_val = validos[front]

        if dlr_val <= 0:
            continue

        # Meses al vencimiento (mínimo 0.1 para evitar división por cero)
        meses = max((expiry - fecha).days / 30.44, 0.1)

        # Tasa mensual implícita: (DLR/MEP)^(1/meses). Proyección a 1M.
        equiv = mep_val * (dlr_val / mep_val) ** (1.0 / meses)
        results[fecha] = equiv

    return pd.Series(results, name="ROFEX_1M_EQUIV").sort_index()


# ── Serie unificada ───────────────────────────────────────────────────────────

def build_unified(mep: pd.Series) -> pd.Series:
    sspm = load_series("ROFEX_1M")      # 2022-01-03 → 2024-04-18
    bcr  = load_series("ROFEX_BCR_1M")  # 2024-04-18 → 2025-10-07
    ppi_df = load_ppi_contracts()

    # SSPM hasta 2024-04-17 inclusive; BCR toma el overlap del 2024-04-18
    cut_sspm = pd.Timestamp("2024-04-17")
    # BCR hasta 2025-10-07; PPI desde 2025-10-08
    cut_bcr  = pd.Timestamp("2025-10-07")

    segments = [sspm[sspm.index <= cut_sspm]]

    if not bcr.empty:
        segments.append(bcr[(bcr.index > cut_sspm) & (bcr.index <= cut_bcr)])

    if not ppi_df.empty:
        ppi_equiv = compute_ppi_equiv(ppi_df, mep)
        if not ppi_equiv.empty:
            segments.append(ppi_equiv[ppi_equiv.index > cut_bcr])

    unified = pd.concat(segments).sort_index()
    unified.name = "ROFEX_1M_EQUIV"
    return unified


# ── Guardar en raw_prices ─────────────────────────────────────────────────────

def save_unified(s: pd.Series) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    saved = 0
    for fecha, valor in s.items():
        if pd.isna(valor) or valor <= 0:
            continue
        cur.execute("""
            INSERT OR REPLACE INTO raw_prices (activo, fecha, valor, fuente)
            VALUES (?, ?, ?, ?)
        """, ("ROFEX_1M_EQUIV", fecha.strftime("%Y-%m-%d"), float(valor), "ROFEX_UNIFIED"))
        saved += 1
    conn.commit()
    conn.close()
    return saved


# ── Diagnósticos ──────────────────────────────────────────────────────────────

def print_diagnostics(s: pd.Series, mep: pd.Series) -> None:
    mep_aligned = mep.reindex(s.index, method="nearest")
    premium = s / mep_aligned - 1

    print("\n=== ROFEX_1M_EQUIV — Serie completa ===")
    print(f"  Desde: {s.index[0].date()}  |  Hasta: {s.index[-1].date()}  |  Filas: {len(s)}")
    print(f"  Min:   {s.min():.1f}  ({s.idxmin().date()})")
    print(f"  Max:   {s.max():.1f}  ({s.idxmax().date()})")

    print("\n=== Premium ROFEX sobre MEP (devaluación implícita 1M) ===")
    print(f"  Min:   {premium.min():.4f}  ({premium.idxmin().date()})")
    print(f"  Max:   {premium.max():.4f}  ({premium.idxmax().date()})")
    print(f"  Media: {premium.mean():.4f}  |  Mediana: {premium.median():.4f}")

    print("\n=== Fechas clave ===")
    hdr = f"  {'Fecha':<12}  {'Hito':<38}  {'ROFEX':>8}  {'MEP':>7}  {'Prem':>7}  Fuente"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    key_dates = {
        "2022-07-01": "Crisis Guzmán",
        "2023-08-14": "PASO 2023",
        "2023-11-19": "Ballotage — gana Milei",
        "2024-01-02": "Inicio Milei (post-devaluación)",
        "2024-04-08": "Peak honeymoon",
        "2024-12-09": "Máximo IEP histórico",
        "2025-09-18": "Mínimo IEP pre-electoral",
        "2025-10-27": "Legislativas 2025 (BASELINE)",
    }
    for d, label in key_dates.items():
        ts  = pd.Timestamp(d)
        idx = s.index.get_indexer([ts], method="nearest")[0]
        if idx < 0:
            continue
        fr   = s.index[idx]
        rv   = s.iloc[idx]
        mv   = mep_aligned.iloc[idx]
        pv   = rv / mv - 1
        src  = "SSPM" if fr <= pd.Timestamp("2024-04-17") else ("BCR" if fr <= pd.Timestamp("2025-10-07") else "PPI")
        print(f"  {str(fr.date()):<12}  {label:<38}  {rv:>8.1f}  {mv:>7.1f}  {pv:>7.4f}  {src}")

    print("\n=== Validaciones económicas ===")
    checks = [
        ("2025-09-18", "ROFEX máximo pre-electoral (esperado 1400-1500)", 1300, 1600),
        ("2024-12-09", "ROFEX estable crawling peg (esperado 1030-1100)",  900, 1150),
        ("2022-07-01", "Crisis Guzmán — ROFEX elevado (esperado 180-400)", 100,  500),
    ]
    for d, desc, lo, hi in checks:
        ts  = pd.Timestamp(d)
        idx = s.index.get_indexer([ts], method="nearest")[0]
        v   = s.iloc[idx]
        ok  = "OK" if lo <= v <= hi else "FALLO"
        print(f"  [{ok:^5}] {d}: {v:.1f}  — {desc}")


# ── Main ──────────────────────────────────────────────────────────────────────

def load_mep() -> pd.Series:
    """
    MEP = AL30_ARS / AL30D_USD, calculado on-the-fly desde raw_prices.
    No depende de que calcular_capa1.py haya corrido antes.
    Fallback: si ya existe MEP guardado, combina ambas fuentes tomando la más reciente.
    """
    conn = sqlite3.connect(DB_PATH)
    al30_ars = pd.read_sql_query(
        "SELECT fecha, valor FROM raw_prices WHERE activo='AL30_ARS' ORDER BY fecha",
        conn, parse_dates=["fecha"],
    ).set_index("fecha")["valor"]
    al30d = pd.read_sql_query(
        "SELECT fecha, valor FROM raw_prices WHERE activo='AL30D' ORDER BY fecha",
        conn, parse_dates=["fecha"],
    ).set_index("fecha")["valor"]
    mep_saved = pd.read_sql_query(
        "SELECT fecha, valor FROM raw_prices WHERE activo='MEP' ORDER BY fecha",
        conn, parse_dates=["fecha"],
    ).set_index("fecha")["valor"]
    conn.close()

    mep_calc = (al30_ars / al30d).dropna()
    mep_calc = mep_calc[mep_calc > 0]

    # Combina: el MEP guardado por calcular_capa1 si existe, completado con el cálculo on-the-fly
    if mep_saved.empty:
        return mep_calc
    combined = mep_saved.combine_first(mep_calc)
    return combined.sort_index()


def main():
    print("calcular_rofex_signal | ROFEX_1M_EQUIV unificado 2022-hoy")
    print(f"DB: {DB_PATH}\n")

    mep = load_mep()
    if mep.empty:
        print("ERROR: no hay datos de AL30_ARS/AL30D en raw_prices. Correr scraper_bonos.py primero.")
        sys.exit(1)

    unified = build_unified(mep)
    if unified.empty:
        print("ERROR: no se pudo construir la serie unificada.")
        sys.exit(1)

    print(f"Serie unificada: {len(unified)} filas  "
          f"({unified.index[0].date()} -> {unified.index[-1].date()})")

    n = save_unified(unified)
    print(f"Guardadas en raw_prices (fuente=ROFEX_UNIFIED): {n} filas")

    if DIAG:
        print_diagnostics(unified, mep)
    else:
        last_date = unified.index[-1]
        rv = unified.iloc[-1]
        mv = mep.reindex([last_date], method="nearest").iloc[0]
        prem = rv / mv - 1
        src = "SSPM" if last_date <= pd.Timestamp("2024-04-17") else (
              "BCR"  if last_date <= pd.Timestamp("2025-10-07") else "PPI")
        print(f"\nÚltimo ({last_date.date()}): ROFEX_equiv={rv:.1f}  MEP={mv:.1f}  "
              f"premium={prem:+.4f}  [{src}]")
        print("Correr con --diagnosticos para validación completa.")


if __name__ == "__main__":
    main()
