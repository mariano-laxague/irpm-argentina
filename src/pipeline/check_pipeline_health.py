"""
check_pipeline_health.py — Validación post-pipeline del IRPM.

Corre como paso 15 (último) del update diario. Verifica que el pipeline
produjo resultados dentro de rangos esperados. Si detecta algo fuera de
rango, lo registra en logs/health_alerts.log y sale con exit code 1
(lo que detiene cualquier proceso supervisor).

También escribe logs/last_run.txt con el timestamp del último run exitoso.
Usar ese archivo para monitorear que el scheduler está corriendo.

Checks:
  1. El IRPM bruto del último día está en [irpm_min, irpm_max]
  2. El delta diario del IRPM es < irpm_max_daily_change pts
  3. Cada capa (1, 2, 3) tiene datos dentro de los últimos data_staleness_days días hábiles
  4. Los z-scores de cada capa del último día están en [-capa_zscore_max, +capa_zscore_max]

Umbrales configurables en config.ini [pipeline].

Uso:
    python src/pipeline/check_pipeline_health.py
    python src/pipeline/check_pipeline_health.py --solo  # corre sin depender del pipeline
"""

import sys
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
from src.config import CFG

LOG_DIR    = ROOT / "logs"
ALERT_LOG  = LOG_DIR / "health_alerts.log"
LAST_RUN   = LOG_DIR / "last_run.txt"
LOG_DIR.mkdir(exist_ok=True)

SEP = "-" * 60


# ── Helpers ────────────────────────────────────────────────────────────────────

def _log_alert(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(f"  [ALERTA] {msg}")
    with open(ALERT_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _business_days_ago(n: int) -> date:
    """Retorna la fecha n días hábiles atrás (lun-vie)."""
    d, count = date.today(), 0
    while count < n:
        d -= timedelta(days=1)
        if d.weekday() < 5:  # lunes=0 ... viernes=4
            count += 1
    return d


# ── Carga de datos ─────────────────────────────────────────────────────────────

def load_iep_recent(days: int = 10) -> list[dict]:
    """Devuelve las últimas `days` filas de iep_diario ordenadas por fecha."""
    conn = sqlite3.connect(CFG.db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT d.fecha, d.capa1, d.capa2, d.capa3, d.iep_total,
               c.estado_publicacion, c.motivo_degradacion
        FROM iep_diario d
        LEFT JOIN iep_composicion c USING(fecha)
        WHERE d.iep_total IS NOT NULL
          AND d.capa1 IS NOT NULL
          AND d.capa2 IS NOT NULL
          AND d.capa3 IS NOT NULL
        ORDER BY d.fecha DESC
        LIMIT ?
    """, (days,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows  # más reciente primero


# ── Checks ─────────────────────────────────────────────────────────────────────

def check_irpm_range(rows: list[dict]) -> bool:
    """Check 1: IRPM del último día dentro de [irpm_min, irpm_max]."""
    if not rows:
        _log_alert("iep_diario está vacía — no hay datos para validar")
        return False

    ultimo = rows[0]
    irpm   = ultimo.get("iep_total")
    fecha  = ultimo.get("fecha", "?")

    if irpm is None:
        if ultimo.get("estado_publicacion") == "degradado":
            _log_alert(
                f"dato degradado para {fecha}: {ultimo.get('motivo_degradacion')}; "
                "publicación bloqueada"
            )
            return False
        _log_alert(f"iep_total es NULL para {fecha}")
        return False

    ok = CFG.irpm_min <= irpm <= CFG.irpm_max
    if ok:
        print(f"  [OK] IRPM {fecha}: {irpm:.1f}  (rango esperado {CFG.irpm_min:.0f}–{CFG.irpm_max:.0f})")
    else:
        _log_alert(
            f"IRPM fuera de rango: {irpm:.1f} el {fecha}  "
            f"(esperado {CFG.irpm_min:.0f}–{CFG.irpm_max:.0f})"
        )
    return ok


def check_daily_delta(rows: list[dict]) -> bool:
    """Check 2: cambio diario del IRPM < irpm_max_daily_change."""
    if len(rows) < 2:
        print("  ~ Delta diario: insuficientes datos (< 2 filas) — omitido")
        return True

    irpm_hoy  = rows[0].get("iep_total")
    irpm_ayer = rows[1].get("iep_total")
    fecha_hoy = rows[0].get("fecha", "?")

    if irpm_hoy is None or irpm_ayer is None:
        print("  ~ Delta diario: algún valor NULL — omitido")
        return True

    delta = abs(irpm_hoy - irpm_ayer)
    ok    = delta <= CFG.irpm_max_daily_change

    if ok:
        signo = "+" if irpm_hoy >= irpm_ayer else ""
        print(f"  [OK] Delta diario: {signo}{irpm_hoy - irpm_ayer:+.1f} pts el {fecha_hoy}")
    else:
        _log_alert(
            f"Delta diario anómalo: {delta:.1f} pts el {fecha_hoy}  "
            f"(umbral {CFG.irpm_max_daily_change:.0f} pts) — "
            f"verificar si hay evento político o error de datos"
        )
    return ok


def check_data_freshness(rows: list[dict]) -> bool:
    """Check 3: cada capa tiene datos dentro de los últimos data_staleness_days días hábiles."""
    if not rows:
        _log_alert("Sin filas — no se puede verificar freshness")
        return False

    cutoff = _business_days_ago(CFG.data_staleness_days)
    ultimo_fecha_str = rows[0].get("fecha", "")
    try:
        ultimo_fecha = date.fromisoformat(ultimo_fecha_str)
    except ValueError:
        _log_alert(f"Fecha inválida en última fila: {ultimo_fecha_str!r}")
        return False

    ok = ultimo_fecha >= cutoff
    if ok:
        print(f"  [OK] Datos frescos: última fecha {ultimo_fecha}  (cutoff {cutoff})")
    else:
        _log_alert(
            f"Datos desactualizados: última fecha {ultimo_fecha}  "
            f"(cutoff {cutoff}, {CFG.data_staleness_days} días hábiles) — "
            f"posible falla del Task Scheduler"
        )
    return ok


def check_zscore_range(rows: list[dict]) -> bool:
    """Check 4: z-scores de cada capa dentro de [-max, +max]."""
    if not rows:
        return False

    ultimo = rows[0]
    fecha  = ultimo.get("fecha", "?")
    all_ok = True

    for capa, key in [("Capa 1", "capa1"), ("Capa 2", "capa2"), ("Capa 3", "capa3")]:
        val = ultimo.get(key)
        if val is None:
            print(f"  ~ {capa}: NULL el {fecha} — omitido")
            continue
        within = abs(val) <= CFG.capa_zscore_max
        if within:
            print(f"  [OK] {capa} z-score: {val:+.2f}  (límite ±{CFG.capa_zscore_max:.0f})")
        else:
            _log_alert(
                f"{capa} z-score fuera de rango: {val:+.2f} el {fecha}  "
                f"(límite ±{CFG.capa_zscore_max:.0f}) — posible error de datos o split accionario"
            )
            all_ok = False

    return all_ok


# ── Last-run timestamp ─────────────────────────────────────────────────────────

def write_last_run(all_ok: bool):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "OK" if all_ok else "WARNING"
    LAST_RUN.write_text(f"{ts}  {status}\n", encoding="utf-8")
    print(f"\n  {'[OK]' if all_ok else '[ALERTA]'} last_run.txt actualizado: {ts}  [{status}]")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{SEP}")
    print("  Healthcheck del pipeline IRPM")
    print(SEP)

    rows = load_iep_recent(days=10)
    if not rows:
        _log_alert("iep_diario está vacía — pipeline no produjo datos")
        write_last_run(all_ok=False)
        sys.exit(1)

    results = [
        check_irpm_range(rows),
        check_daily_delta(rows),
        check_data_freshness(rows),
        check_zscore_range(rows),
    ]

    all_ok = all(results)
    write_last_run(all_ok)

    if all_ok:
        print(f"\n  [OK] Todos los checks pasaron.")
    else:
        n_fail = results.count(False)
        print(f"\n  [ALERTA] {n_fail}/{len(results)} check(s) fallaron — ver {ALERT_LOG.name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
