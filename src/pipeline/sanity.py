"""
sanity.py — Checks de calidad post-cálculo para cada capa del IRPM.

Uso estándar al final del main() de cada calcular_capa*.py:

    from src.pipeline.sanity import assert_capa_sanity
    assert_capa_sanity("capa1")   # o "capa2" / "capa3"

Si algún check falla: imprime el detalle, escribe en health_alerts.log,
y sale con exit code 1 (detiene el pipeline en ese paso).

Umbrales:
  ZSCORE_LIMIT   = 5.0   z-scores del último día dentro de [-5, +5]
  DELTA_LIMIT    = 3.0   cambio diario < 3 z-score units
  STALE_DAYS     = 5     datos frescos en los últimos 5 días hábiles
  MIN_ROWS       = 10    serie no vacía (al menos 10 filas no-NaN)
"""

import sys
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
from src.config import CFG

ALERT_LOG   = ROOT / "logs" / "health_alerts.log"
ZSCORE_LIMIT = CFG.capa_zscore_max   # desde config.ini [pipeline]
DELTA_LIMIT  = 3.0
STALE_DAYS   = CFG.data_staleness_days
MIN_ROWS     = 10


def _log_alert(msg: str):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(f"  [FAIL] SANITY: {msg}")
    ALERT_LOG.parent.mkdir(exist_ok=True)
    with open(ALERT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _business_days_ago(n: int) -> date:
    d, count = date.today(), 0
    while count < n:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            count += 1
    return d


def _load_capa(col: str, n: int = 10) -> list[tuple]:
    """Devuelve las últimas n filas (fecha, valor) de iep_diario para la columna dada."""
    conn = sqlite3.connect(CFG.db_path)
    cur  = conn.cursor()
    cur.execute(f"""
        SELECT fecha, {col}
        FROM iep_diario
        WHERE {col} IS NOT NULL
        ORDER BY fecha DESC
        LIMIT ?
    """, (n,))
    rows = cur.fetchall()
    conn.close()
    return rows  # [(fecha_str, valor), ...]  — más reciente primero


def assert_capa_sanity(capa: str) -> None:
    """
    Corre los 4 checks de sanidad para la capa indicada ("capa1", "capa2" o "capa3").
    Si alguno falla, imprime el detalle y sale con sys.exit(1).
    """
    print(f"\n--- Sanity check: {capa} ---")
    rows = _load_capa(capa, n=15)
    failures = []

    # Check 0: serie no vacía
    if len(rows) < MIN_ROWS:
        msg = f"{capa}: solo {len(rows)} filas (mínimo {MIN_ROWS}) — pipeline incompleto"
        _log_alert(msg)
        failures.append(msg)
        _exit_if_failures(failures)
        return

    ultimo_fecha, ultimo_val = rows[0]
    penultimo_fecha, penultimo_val = rows[1] if len(rows) > 1 else (None, None)

    # Check 1: z-score del último día dentro de [-limit, +limit]
    if abs(ultimo_val) > ZSCORE_LIMIT:
        msg = (
            f"{capa}: z-score fuera de rango el {ultimo_fecha}: {ultimo_val:+.2f}  "
            f"(límite ±{ZSCORE_LIMIT:.0f}) — posible split accionario, gap de datos o bug"
        )
        _log_alert(msg)
        failures.append(msg)
    else:
        print(f"  [OK] z-score último día ({ultimo_fecha}): {ultimo_val:+.2f}  [±{ZSCORE_LIMIT:.0f}]")

    # Check 2: delta diario < DELTA_LIMIT
    if penultimo_val is not None:
        delta = abs(ultimo_val - penultimo_val)
        if delta > DELTA_LIMIT:
            msg = (
                f"{capa}: delta diario anómalo: {delta:.2f} z-units "
                f"({penultimo_fecha} → {ultimo_fecha})  (límite {DELTA_LIMIT:.0f}) — "
                f"posible gap de datos o evento extremo"
            )
            _log_alert(msg)
            failures.append(msg)
        else:
            print(f"  [OK] Delta diario: {ultimo_val - penultimo_val:+.2f} z-units")

    # Check 3: datos frescos en los últimos STALE_DAYS días hábiles
    cutoff = _business_days_ago(STALE_DAYS)
    try:
        ultimo_date = date.fromisoformat(ultimo_fecha)
        if ultimo_date < cutoff:
            msg = (
                f"{capa}: última fecha {ultimo_fecha} está desactualizada  "
                f"(cutoff {cutoff}, {STALE_DAYS}d hábiles) — "
                f"Task Scheduler posiblemente fallido"
            )
            _log_alert(msg)
            failures.append(msg)
        else:
            print(f"  [OK] Freshness: última fecha {ultimo_fecha}  (cutoff {cutoff})")
    except ValueError:
        pass

    _exit_if_failures(failures)
    print(f"  [OK] Sanity {capa}: OK")


def _exit_if_failures(failures: list[str]) -> None:
    if failures:
        print(f"\n  {len(failures)} check(s) fallaron para esta capa.")
        print(f"  Ver logs/health_alerts.log para el detalle.")
        sys.exit(1)
