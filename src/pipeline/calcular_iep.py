"""
calcular_iep.py — Calcula el IEP compuesto y lo escala a baseline = 100.

Pesos (arquitectura definitiva Fase 0):
    35% Capa 1 — MEP/CCL (cambiaria)
    40% Capa 2 — Bonos soberanos USD + EMBI
    25% Capa 3 — Semi-volatilidad accionaria AR (proxy put-side opciones BYMA)

Compatibilidad retroactiva (primeros ~12 dias habiles sin Capa 3):
    50% Capa 1 + 50% Capa 2

Escalado a indice con baseline = 100 el 11-dic-2023 (inicio gestión Milei):
    IEP = 100 + (IEP_raw - IEP_raw_baseline) * ESCALA

ESCALA = 10 por defecto (1 unidad de z-score = 10 puntos IEP).

Pendiente Fase 1:
    - Incorporar ROFEX en Capa 1 (requiere registro en Primary/Matba-Rofex)
    - Cuando ROFEX activo: recalibrar pesos finales
    - Sustituir semi-vol por IV real de opciones BYMA cuando disponible

Uso:
    python src/pipeline/calcular_iep.py
    python src/pipeline/calcular_iep.py --diagnosticos
"""

import sys
import sqlite3
from pathlib import Path

import pandas as pd

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / "data" / "iep.db"

BASELINE_DATE = pd.Timestamp("2023-12-11")  # Inicio gestión Milei
ESCALA        = 10.0   # 1 z-score unit = 10 IEP points

DIAG = "--diagnosticos" in sys.argv


# ── Carga desde iep_diario ─────────────────────────────────────────────────────

def load_iep_diario() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT fecha, capa1, capa2, capa3 FROM iep_diario ORDER BY fecha",
        conn, parse_dates=["fecha"],
    )
    conn.close()
    return df.set_index("fecha")


# ── Compuesto y escalado ───────────────────────────────────────────────────────

def compute_iep(df: pd.DataFrame) -> pd.Series:
    # Fechas con las 3 capas: pesos definitivos 35/40/25
    has3 = df["capa1"].notna() & df["capa2"].notna() & df["capa3"].notna()
    # Fechas sin Capa 3 (primeros dias): compatibilidad 50/50
    has2 = df["capa1"].notna() & df["capa2"].notna() & ~has3

    raw3 = (0.35 * df.loc[has3, "capa1"]
          + 0.40 * df.loc[has3, "capa2"]
          + 0.25 * df.loc[has3, "capa3"])
    raw2 = (0.50 * df.loc[has2, "capa1"]
          + 0.50 * df.loc[has2, "capa2"])

    raw = pd.concat([raw2, raw3]).sort_index().rename("iep_raw")

    # Baseline
    idx_base = raw.index.get_indexer([BASELINE_DATE], method="nearest")[0]
    baseline_val = raw.iloc[idx_base]

    iep = 100 + (raw - baseline_val) * ESCALA
    return iep.rename("iep_total")


# ── Guardar ────────────────────────────────────────────────────────────────────

def save_iep(iep: pd.Series) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    saved = 0
    for fecha, valor in iep.items():
        if pd.isna(valor):
            continue
        cur.execute("""
            INSERT OR REPLACE INTO iep_diario (fecha, iep_total, pesos_version)
            VALUES (?, ?, ?)
            ON CONFLICT(fecha) DO UPDATE SET iep_total=excluded.iep_total
        """, (fecha.strftime("%Y-%m-%d"), float(valor), "50-50-0"))
        saved += 1
    conn.commit()
    conn.close()
    return saved


# ── Diagnósticos ───────────────────────────────────────────────────────────────

def print_diagnostics(df: pd.DataFrame, iep: pd.Series) -> None:
    print("\n=== IEP compuesto provisional (50/50) ===")
    print(f"  Filas:  {len(iep)}")
    print(f"  Desde:  {iep.index[0].date()}")
    print(f"  Hasta:  {iep.index[-1].date()}")
    print(f"  Min:    {iep.min():.1f}  ({iep.idxmin().date()})")
    print(f"  Max:    {iep.max():.1f}  ({iep.idxmax().date()})")

    print("\n=== Valores en fechas clave ===")
    key_dates = {
        "2022-07-01": "Crisis Guzman",
        "2023-08-14": "PASO 2023",
        "2024-01-02": "Inicio Milei",
        "2024-04-08": "Honeymoon peak",
        "2024-07-01": "H2 2024",
        "2025-09-20": "Pre-electoral min",
        "2025-10-27": "Legislativas (BASELINE)",
        "2026-05-08": "Hoy",
    }
    for d, label in key_dates.items():
        try:
            v  = iep.loc[pd.Timestamp(d)]
            c1 = df.loc[pd.Timestamp(d), "capa1"]
            c2 = df.loc[pd.Timestamp(d), "capa2"]
            c3 = df.loc[pd.Timestamp(d), "capa3"]
            c3s = f", c3={c3:+.2f}" if pd.notna(c3) else ""
            print(f"  {d}  {label:<30}  IEP={v:>7.1f}  (c1={c1:+.2f}, c2={c2:+.2f}{c3s})")
        except KeyError:
            idx = iep.index.get_indexer([pd.Timestamp(d)], method="nearest")[0]
            fecha_r = iep.index[idx]
            v  = iep.iloc[idx]
            c1 = df.loc[fecha_r, "capa1"]
            c2 = df.loc[fecha_r, "capa2"]
            c3 = df.loc[fecha_r, "capa3"]
            c3s = f", c3={c3:+.2f}" if pd.notna(c3) else ""
            print(f"  {d}  {label:<30}  IEP={v:>7.1f}  (c1={c1:+.2f}, c2={c2:+.2f}{c3s})  real:{fecha_r.date()}")

    # Escala de interpretación
    print("\n=== Escala IEP ===")
    print("  > 110  Mercado pricea reelección con más convicción que baseline")
    print("  90-110 Zona baseline — continuidad del programa creíble")
    print("   70-89 Optimismo moderado con ruido")
    print("   40-69 Incertidumbre activa")
    print("   < 40  Stress político severo")
    v_now = iep.iloc[-1]
    zona = ("> 110" if v_now > 110
            else "90-110" if v_now >= 90
            else "70-89" if v_now >= 70
            else "40-69" if v_now >= 40
            else "< 40")
    print(f"\n  Hoy:  IEP = {v_now:.1f}  [{zona}]")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("calcular_iep | IEP compuesto (35% Capa1 + 40% Capa2 + 25% Capa3)")
    print(f"Baseline: {BASELINE_DATE.date()} = 100 | Escala: 1 z-unit = {ESCALA} pts\n")

    df  = load_iep_diario()
    iep = compute_iep(df)
    n   = save_iep(iep)
    print(f"IEP guardado en iep_diario: {n} filas")

    if DIAG:
        print_diagnostics(df, iep)
    else:
        v_now  = iep.iloc[-1]
        v_base = iep.iloc[iep.index.get_indexer([BASELINE_DATE], method="nearest")[0]]
        print(f"Baseline (11-dic-2023): {v_base:.1f}")
        print(f"Ultimo ({iep.index[-1].date()}):   {v_now:.1f}")
        print(f"Diferencia:             {v_now - 100:+.1f} pts sobre baseline")
        print("\nCorrer con --diagnosticos para detalle completo.")


if __name__ == "__main__":
    main()
