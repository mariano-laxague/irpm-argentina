"""
calcular_capa2.py — Calcula el sub-índice Capa 2 del IEP.

Componentes (Bonos soberanos USD):
  GD30D     Paridad Global 2030, ley NY       → z-score directo
  AL30D     Paridad ANSES 2030, ley AR        → z-score directo
  GD35D     Paridad Global 2035, ley NY       → z-score directo
  law_spread  GD30D - AL30D                   → z-score invertido (spread alto = peor)
  EMBI        Riesgo país en bps (Rava)       → z-score invertido (spread alto = peor)

Todos los z-scores quedan orientados: positivo = mejor expectativa política.

Normalización: z-score rolling 252 días hábiles, min_periods=63.

Pesos (OPT-1 — Ses. 14, Bekaert et al. 2014):
  law_spread: 35%  — único componente beta-neutral (cancela factores globales)
  gd30d:      20%  — bono ley NY 2030
  al30d:      20%  — bono ley AR 2030
  gd35d:      10%  — bono ley NY 2035 (mayor contaminación secular)
  embi:       15%  — spread soberano genérico (señal macro, no política)

Política de completitud: las cinco señales son obligatorias. Si falta una,
Capa 2 se marca como no publicable; los pesos no se renormalizan.

Uso:
    python src/pipeline/calcular_capa2.py
    python src/pipeline/calcular_capa2.py --diagnosticos
"""

import sys
import sqlite3
from pathlib import Path

import pandas as pd

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / "data" / "iep.db"

WINDOW      = 252
MIN_PERIODS = 63

# Pesos explícitos por componente (OPT-1 — Bekaert et al. 2014)
# law_spread tiene el mayor peso por ser el único componente beta-neutral.
PESOS_CAPA2 = {
    "z_law_spread": 0.35,
    "z_gd30d":      0.20,
    "z_al30d":      0.20,
    "z_gd35d":      0.10,
    "z_embi":       0.15,
}

# ── OPT-7: Ajuste por fechas de pago de cupón/amortización ────────────────────
# GD30, AL30, GD35 pagan cupón + amortización el 9 de enero y 9 de julio.
# En la fecha ex-pago, la paridad cae mecánicamente (ej: -13.1% el 8-jul-2026).
# El z-score rolling interpreta esa caída como deterioro político — forward-fill
# evita el spike espurio. Solo actúa si AMBAS condiciones se cumplen:
#   (a) la fecha está en la ventana pre-pago y
#   (b) la caída supera el umbral (por encima de volatilidad diaria normal).
_PAYMENT_MONTHS_DAYS = [(1, 9), (7, 9)]   # GD30/AL30/GD35: ene-9 y jul-9
_PAYMENT_YEARS       = range(2022, 2036)
_FFILL_THRESHOLD     = 0.025              # >2.5% → caída mecánica (amortiz. ~13%)
_FFILL_WINDOW_DAYS   = 2                  # días calendario antes del pago


def _build_payment_window() -> set:
    window = set()
    for year in _PAYMENT_YEARS:
        for month, day in _PAYMENT_MONTHS_DAYS:
            try:
                base = pd.Timestamp(year, month, day)
                for offset in range(_FFILL_WINDOW_DAYS + 1):
                    window.add(base - pd.Timedelta(days=offset))
            except ValueError:
                pass
    return window


_PAYMENT_WINDOW = _build_payment_window()


def ffill_payment_dates(s: pd.Series, activo: str = "") -> tuple:
    """
    Forward-fill caídas mecánicas en ventanas de fechas de pago.
    Usa el precio pre-ventana como referencia fija para TODOS los días de la ventana,
    evitando el efecto en cadena cuando la caída se reparte en 2 días consecutivos.
    Retorna (serie_ajustada, lista_de_(fecha, activo, drop_pct)).
    """
    s = s.copy()
    fixes = []
    for year in _PAYMENT_YEARS:
        for month, day in _PAYMENT_MONTHS_DAYS:
            try:
                payment_date = pd.Timestamp(year, month, day)
            except ValueError:
                continue
            window_dates = [
                payment_date - pd.Timedelta(days=offset)
                for offset in range(_FFILL_WINDOW_DAYS + 1)
            ]
            locs = sorted(s.index.get_loc(d) for d in window_dates if d in s.index)
            if not locs or locs[0] == 0:
                continue
            pre_price = s.iloc[locs[0] - 1]  # precio del último día hábil antes de la ventana
            if pd.isna(pre_price) or pre_price == 0:
                continue
            for loc in locs:
                curr = s.iloc[loc]
                if pd.isna(curr):
                    continue
                drop = (curr - pre_price) / pre_price
                if drop < -_FFILL_THRESHOLD:
                    s.iloc[loc] = pre_price
                    fixes.append((s.index[loc].date(), activo, f"{drop:.1%}"))
    return s, fixes

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


# ── Z-score rolling ────────────────────────────────────────────────────────────

def rolling_zscore(s: pd.Series, window: int = WINDOW, min_periods: int = MIN_PERIODS) -> pd.Series:
    m = s.rolling(window, min_periods=min_periods).mean()
    sd = s.rolling(window, min_periods=min_periods).std()
    return (s - m) / sd.replace(0, float("nan"))


# ── Cálculo ────────────────────────────────────────────────────────────────────

def compute_capa2() -> pd.DataFrame:
    gd30d_raw = load_series("GD30D")
    al30d_raw = load_series("AL30D")
    gd35d_raw = load_series("GD35D")
    embi      = load_series("EMBI")

    # OPT-7: forward-fill caídas mecánicas en fechas ex-pago antes del z-score
    gd30d, fixes_gd30 = ffill_payment_dates(gd30d_raw, "GD30D")
    al30d, fixes_al30 = ffill_payment_dates(al30d_raw, "AL30D")
    gd35d, fixes_gd35 = ffill_payment_dates(gd35d_raw, "GD35D")
    all_fixes = fixes_gd30 + fixes_al30 + fixes_gd35
    if all_fixes:
        for dt, activo, drop in sorted(all_fixes):
            print(f"  [OPT-7] ffill {dt} {activo}: caída mecánica {drop}")
    else:
        print("  [OPT-7] sin caídas mecánicas detectadas")

    # Law spread: GD30D − AL30D (en USD, puntos de paridad)
    law_spread = gd30d - al30d

    # Z-scores orientados (positivo = mejor señal política)
    z = pd.DataFrame({
        "z_gd30d":      rolling_zscore(gd30d),
        "z_al30d":      rolling_zscore(al30d),
        "z_gd35d":      rolling_zscore(gd35d),
        "z_law_spread": -rolling_zscore(law_spread),   # invertido
        "z_embi":       -rolling_zscore(embi),         # invertido
    })

    # Media ponderada con composición fija: un faltante deja Capa 2 no publicable.
    num = pd.Series(0.0, index=z.index)
    for col, w in PESOS_CAPA2.items():
        mask = z[col].notna()
        num[mask] += z.loc[mask, col] * w
    n_componentes = z.notna().sum(axis=1)
    capa2 = num.where(n_componentes == len(PESOS_CAPA2))

    result = pd.DataFrame({
        "law_spread": law_spread,
        **z,
        "capa2": capa2,
        "n_componentes": n_componentes,
    })
    return result


# ── Guardar en SQLite ──────────────────────────────────────────────────────────

def save_capa2(result: pd.DataFrame) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    saved = 0
    for fecha, row in result.iterrows():
        n = int(row["n_componentes"])
        pesos = "35-20-20-10-15-v4-full" if n == 5 else "incompleta-v4"
        cur.execute("""
            INSERT INTO iep_diario (fecha, capa2, pesos_version)
            VALUES (?, ?, ?)
            ON CONFLICT(fecha) DO UPDATE SET
                capa2=excluded.capa2,
                pesos_version=excluded.pesos_version
        """, (fecha.strftime("%Y-%m-%d"),
              None if pd.isna(row["capa2"]) else float(row["capa2"]), pesos))
        saved += 1
    conn.commit()
    conn.close()
    return saved


# ── Diagnósticos ───────────────────────────────────────────────────────────────

def print_diagnostics(result: pd.DataFrame) -> None:
    capa2 = result["capa2"].dropna()

    print("\n=== Capa 2 — Serie completa ===")
    print(f"  Desde:   {capa2.index[0].date()}")
    print(f"  Hasta:   {capa2.index[-1].date()}")
    print(f"  Filas:   {len(capa2)}")

    print("\n=== Estadísticas de la serie ===")
    print(f"  Media:   {capa2.mean():.4f}")
    print(f"  Std:     {capa2.std():.4f}")
    print(f"  Min:     {capa2.min():.4f}  ({capa2.idxmin().date()})")
    print(f"  Max:     {capa2.max():.4f}  ({capa2.idxmax().date()})")

    print("\n=== Valores en fechas clave ===")
    key_dates = {
        "2022-07-01": "Crisis Guzmán",
        "2023-08-14": "PASO 2023",
        "2024-01-01": "Inicio Milei",
        "2024-07-01": "H2 2024",
        "2025-10-27": "Legislativas 2025 (BASELINE)",
        "2026-05-08": "Ayer (ultima lectura)",
    }
    for d, label in key_dates.items():
        try:
            v = capa2.loc[pd.Timestamp(d)]
            print(f"  {d}  {label:<35} Capa2={v:+.4f}")
        except KeyError:
            nearest = capa2.index.get_indexer([pd.Timestamp(d)], method="nearest")
            if len(nearest):
                idx = capa2.index[nearest[0]]
                v = capa2.iloc[nearest[0]]
                print(f"  {d}  {label:<35} Capa2={v:+.4f} (fecha real: {idx.date()})")

    print("\n=== Correlaciones (validación) ===")
    # Capa2 vs GD30D (deberían correlacionar positivamente)
    merged = pd.DataFrame({
        "capa2": capa2,
        "gd30d": load_series("GD30D"),
        "embi":  load_series("EMBI"),
    }).dropna()
    if len(merged) > 10:
        print(f"  Capa2 ~ GD30D:  r = {merged.capa2.corr(merged.gd30d):+.3f}  (esperado > 0.80)")
        print(f"  Capa2 ~ EMBI:   r = {merged.capa2.corr(merged.embi):+.3f}  (esperado < -0.80)")

    print("\n=== Completitud de Capa 2 ===")
    con_embi = result["n_componentes"] == 5
    print(f"  Completas (5 comp): {con_embi.sum()} filas")
    print(f"  Degradadas:         {(~con_embi).sum()} filas (no publicables)")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("calcular_capa2 | IEP Capa 2 — Bonos soberanos USD")
    print(f"DB: {DB_PATH}")
    print(f"Ventana z-score: {WINDOW}d | min_periods: {MIN_PERIODS}d\n")

    result = compute_capa2()
    n = save_capa2(result)
    print(f"Filas guardadas en iep_diario: {n}")

    if DIAG:
        print_diagnostics(result)
    else:
        capa2 = result["capa2"].dropna()
        baseline_date = pd.Timestamp("2025-10-27")
        idx = capa2.index.get_indexer([baseline_date], method="nearest")[0]
        v_baseline = capa2.iloc[idx]
        v_now      = capa2.iloc[-1]
        print(f"Rango:     {capa2.index[0].date()} -> {capa2.index[-1].date()}")
        print(f"Baseline (oct-2025):  {v_baseline:+.4f}")
        print(f"Ultimo ({capa2.index[-1].date()}): {v_now:+.4f}")
        print(f"Diferencia vs. baseline: {v_now - v_baseline:+.4f}")
        print()
        print("Correr con --diagnosticos para ver detalles completos.")


if __name__ == "__main__":
    main()
