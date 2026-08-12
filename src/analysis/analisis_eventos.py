"""
analisis_eventos.py — Validación del constructo IRPM mediante análisis de eventos.

Para cada evento en data/eventos_politicos.json:
  - Calcula el delta del IRPM en una ventana de ±5 ruedas alrededor del evento
  - Verifica si la dirección y magnitud observada coinciden con la esperada
  - Reporta el porcentaje de los 10 mayores shocks explicados por eventos políticos

Criterio de validación (PLAN.md §0.5):
  ≥70% de los 10 shocks más grandes tienen un evento político identificado
  en su ventana (±7 ruedas).

Uso:
    python src/analysis/analisis_eventos.py
    python src/analysis/analisis_eventos.py --guardar   # actualiza irpm_delta_observado en el JSON
"""

import sys
import json
import sqlite3
from pathlib import Path

import pandas as pd
import numpy as np

ROOT       = Path(__file__).parent.parent.parent
DB_PATH    = ROOT / "data" / "iep.db"
JSON_PATH  = ROOT / "data" / "eventos_politicos.json"

WINDOW     = 5    # ruedas antes y después del evento para calcular delta
SHOCK_WIN  = 7    # ventana de búsqueda para el criterio de validación (±7 ruedas)
TOP_N      = 10   # top N shocks para el criterio de validación
MIN_SHOCK  = 2.0  # umbral mínimo (pts) para considerar un movimiento "señal"


# ── Carga ──────────────────────────────────────────────────────────────────────

def load_irpm() -> pd.Series:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT fecha, iep_total FROM iep_diario WHERE iep_total IS NOT NULL ORDER BY fecha",
        conn, parse_dates=["fecha"],
    )
    conn.close()
    return df.set_index("fecha")["iep_total"]


def load_eventos() -> list:
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── Análisis de eventos individuales ──────────────────────────────────────────

def irpm_en_fecha(irpm: pd.Series, fecha: pd.Timestamp, offset_ruedas: int) -> float | None:
    """Retorna el IRPM en la fecha más cercana a fecha ± offset_ruedas (en días hábiles)."""
    bdays = pd.bdate_range(start="2020-01-01", end="2030-12-31")
    try:
        pos = bdays.get_loc(fecha)
    except KeyError:
        # fecha no es día hábil → buscar el más cercano
        pos = bdays.searchsorted(fecha)
    target = bdays[pos + offset_ruedas]
    idx = irpm.index.get_indexer([target], method="nearest")[0]
    if idx < 0 or idx >= len(irpm):
        return None
    # verificar que no está demasiado lejos (máximo 3 días calendario)
    if abs((irpm.index[idx] - target).days) > 3:
        return None
    return float(irpm.iloc[idx])


def analizar_evento(ev: dict, irpm: pd.Series) -> dict:
    fecha = pd.Timestamp(ev["fecha"])
    v_before = irpm_en_fecha(irpm, fecha, -WINDOW)
    v_after  = irpm_en_fecha(irpm, fecha, +WINDOW)
    delta    = None
    acierto  = None

    if v_before is not None and v_after is not None:
        delta = round(v_after - v_before, 2)
        # Verificar dirección
        dir_esp = ev.get("direccion", "incierto")
        if dir_esp == "positivo":
            dir_ok = delta > MIN_SHOCK
        elif dir_esp == "negativo":
            dir_ok = delta < -MIN_SHOCK
        else:
            dir_ok = True  # incierto → siempre ok

        # Verificar magnitud (si está en el rango esperado)
        d_min = ev.get("irpm_delta_esperado_min", -999)
        d_max = ev.get("irpm_delta_esperado_max", 999)
        mag_ok = d_min <= delta <= d_max

        acierto = dir_ok and mag_ok

    return {
        "fecha":           ev["fecha"],
        "titulo":          ev["titulo"],
        "tipo":            ev["tipo"],
        "severidad":       ev["severidad_esperada"],
        "direccion_esp":   ev.get("direccion", "incierto"),
        "rango_esperado":  f"[{ev.get('irpm_delta_esperado_min','')} , {ev.get('irpm_delta_esperado_max','')}]",
        "irpm_antes":      round(v_before, 1) if v_before else None,
        "irpm_despues":    round(v_after,  1) if v_after  else None,
        "delta_observado": delta,
        "acierto":         acierto,
    }


# ── Criterio de validación: top shocks ────────────────────────────────────────

def validar_top_shocks(irpm: pd.Series, eventos: list) -> dict:
    """
    Identifica los TOP_N mayores shocks (negativos y positivos) del IRPM
    y verifica qué proporción tiene un evento político en su ventana ±SHOCK_WIN.
    """
    delta5 = irpm.diff(WINDOW)

    # Top N caídas y subidas
    top_neg = delta5.nsmallest(TOP_N)
    top_pos = delta5.nlargest(TOP_N)
    top_all = pd.concat([top_neg, top_pos]).sort_values()

    # Fechas de eventos (±SHOCK_WIN días hábiles de búsqueda)
    event_dates = [pd.Timestamp(ev["fecha"]) for ev in eventos
                   if ev.get("tipo") in ("electoral", "fiscal", "institucional")]

    results = []
    for fecha, delta in top_all.items():
        # ¿hay algún evento político en la ventana ±SHOCK_WIN?
        found = False
        matching_event = None
        for ev_date in event_dates:
            # calcular distancia en días calendario
            dist = abs((fecha - ev_date).days)
            if dist <= SHOCK_WIN * 2:  # ±SHOCK_WIN ruedas ≈ ±14 días calendario
                found = True
                ev = next(e for e in eventos if e["fecha"] == ev_date.strftime("%Y-%m-%d"))
                matching_event = ev["titulo"]
                break
        results.append({
            "fecha":   fecha.date(),
            "delta":   round(delta, 1),
            "irpm":    round(irpm.loc[fecha], 1),
            "tiene_evento": found,
            "evento":  matching_event,
        })

    n_explicados = sum(1 for r in results if r["tiene_evento"])
    pct          = n_explicados / len(results) * 100

    return {
        "shocks":          results,
        "total":           len(results),
        "explicados":      n_explicados,
        "pct_explicados":  round(pct, 1),
        "criterio_ok":     pct >= 70,
    }


# ── Guardar deltas en JSON ─────────────────────────────────────────────────────

def guardar_deltas(eventos: list, resultados: list) -> None:
    for ev, res in zip(eventos, resultados):
        ev["irpm_delta_observado"] = res["delta_observado"]
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(eventos, f, ensure_ascii=False, indent=2)
    print(f"\n  JSON actualizado: {JSON_PATH}")


# ── Reporte ────────────────────────────────────────────────────────────────────

def imprimir_reporte(resultados: list, validacion: dict) -> None:
    print("\n" + "=" * 72)
    print("  IRPM — Análisis de Eventos Políticos")
    print("=" * 72)

    aciertos = [r for r in resultados if r["acierto"] is True]
    fallos   = [r for r in resultados if r["acierto"] is False]
    sin_dato = [r for r in resultados if r["acierto"] is None]

    print(f"\n{'FECHA':<12} {'ΔIRPM':>7} {'ANTES':>6} {'DESP':>6} {'OK':>4}  EVENTO")
    print("-" * 72)
    for r in resultados:
        if r["delta_observado"] is None:
            delta_str = "  N/A"
            ok_str    = " —"
        else:
            delta_str = f"{r['delta_observado']:+6.1f}"
            ok_str    = " ✓" if r["acierto"] else " ✗"
        antes_str = f"{r['irpm_antes']:5.1f}" if r["irpm_antes"] else "  N/A"
        desp_str  = f"{r['irpm_despues']:5.1f}" if r["irpm_despues"] else "  N/A"
        titulo    = r["titulo"][:50]
        print(f"  {r['fecha']:<10} {delta_str}  {antes_str}  {desp_str}  {ok_str}  {titulo}")

    print(f"\n  Aciertos: {len(aciertos)} / {len(resultados) - len(sin_dato)} evaluados  "
          f"({len(sin_dato)} sin dato)")

    print("\n" + "=" * 72)
    print("  CRITERIO DE VALIDACIÓN — Top shocks explicados por eventos políticos")
    print("=" * 72)
    print(f"\n  Ventana de búsqueda: ±{SHOCK_WIN} ruedas (~{SHOCK_WIN*2} días calendario)")
    print(f"  {'FECHA':<12} {'ΔIRPM':>7} {'IRPM':>6}  {'EVENTO'}")
    print("  " + "-" * 68)
    for r in validacion["shocks"]:
        ev_str = r["evento"][:45] if r["evento"] else "(sin evento identificado)"
        marca  = "✓" if r["tiene_evento"] else "✗"
        print(f"  {str(r['fecha']):<12} {r['delta']:+6.1f}  {r['irpm']:5.1f}  [{marca}] {ev_str}")

    pct = validacion["pct_explicados"]
    ok  = "✓ APROBADO" if validacion["criterio_ok"] else "✗ REPROBADO"
    print(f"\n  Shocks explicados: {validacion['explicados']} / {validacion['total']} "
          f"= {pct:.0f}%  →  {ok}  (umbral: ≥70%)")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    guardar = "--guardar" in sys.argv

    irpm    = load_irpm()
    eventos = load_eventos()

    print(f"IRPM: {len(irpm)} ruedas ({irpm.index[0].date()} → {irpm.index[-1].date()})")
    print(f"Eventos: {len(eventos)} en {JSON_PATH.name}")
    print(f"Ventana análisis: ±{WINDOW} ruedas")

    resultados = [analizar_evento(ev, irpm) for ev in eventos]
    validacion = validar_top_shocks(irpm, eventos)

    imprimir_reporte(resultados, validacion)

    if guardar:
        guardar_deltas(eventos, resultados)


if __name__ == "__main__":
    main()