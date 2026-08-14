"""
update_daily.py — Pipeline de actualizacion diaria del IEP Argentina.

Ejecuta los pasos en secuencia. Si un paso falla, los siguientes NO corren
(los calculos dependen de los datos anteriores). El exit code indica exito/falla
para que Task Scheduler pueda detectar el resultado.

Pasos:
  0. backup_db()              — copia iep.db a data/backups/ antes de modificar nada
  1. scraper_bonos.py          — precios PPI (ultimos 7 dias: GD30D, AL30D, GD35D, AL30)
  2. scraper_acciones.py       — acciones AR basket Capa 3 (ultimos 7d)
  3. scraper_rofex.py          — contratos DLR futuros PPI (acumulador electoral kink)
  4. scraper_embi_historico.py — EMBI completo desde dolarito.ar (un solo GET)
  5. scraper_utdt.py           — ICG e ICC UTDT (solo actualiza si hay mes nuevo)
  6. scraper_rem.py            — REM BCRA: TC consenso analistas (solo actualiza si hay mes nuevo)
  7. scraper_vix.py            — VIX diario via yfinance (control global para ajuste)
  8. calcular_rofex_signal.py  — ROFEX_1M_EQUIV unificado (SSPM+BCR+PPI)
  9. calcular_capa1.py         — sub-indice Capa 1 (blend MEP + ROFEX)
 10. calcular_capa2.py         — sub-indice Capa 2 (bonos soberanos + EMBI)
 11. calcular_capa3.py         — sub-indice Capa 3 (semi-vol accionaria AR)
 12. calcular_iep.py           — indice compuesto (35/40/25)
 13. calcular_ajuste_global.py — IRPM ajustado por VIX (Bekaert/Nogues-Grandes)
 14. generate_dashboard.py     — regenera outputs/dashboard.html
 15. check_pipeline_health.py  — valida rangos, escribe logs/last_run.txt

Uso:
    py src/pipeline/update_daily.py         # update normal
    py src/pipeline/update_daily.py --dry   # solo imprime pasos, no ejecuta

Task Scheduler: ver run_update.bat en la raiz del proyecto.
Log: logs/update_YYYYMMDD.log
"""

import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT    = Path(__file__).parent.parent.parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
DEPLOY_STATUS = LOG_DIR / "deploy_status.json"

sys.path.insert(0, str(ROOT))
from src.config import CFG
from src.pipeline.deploy_observability import alert_if_configured, write_status

DRY = "--dry" in sys.argv


# ── Backup del DB (paso 0, antes de cualquier modificación) ────────────────────

def backup_db():
    """Copia iep.db a data/backups/iep_YYYYMMDD.db y elimina backups > 7 días."""
    db = CFG.db_path
    if not db.exists():
        print(f"  [backup] DB no encontrada en {db} — se omite backup")
        return

    backup_dir = CFG.backup_dir
    backup_dir.mkdir(parents=True, exist_ok=True)

    ts   = datetime.now().strftime("%Y%m%d")
    dest = backup_dir / f"iep_{ts}.db"

    if DRY:
        print(f"  [DRY] backup {db.name} → {dest.name}")
        return

    shutil.copy2(db, dest)
    print(f"  [backup] {db.name} → {dest.name} ({dest.stat().st_size / 1024:.0f} KB)")

    # Rotación: borrar backups más viejos que retain_days
    cutoff = datetime.now() - timedelta(days=CFG.backup_retain_days)
    removed = 0
    for f in sorted(backup_dir.glob("iep_*.db")):
        try:
            file_date = datetime.strptime(f.stem.replace("iep_", ""), "%Y%m%d")
            if file_date < cutoff:
                f.unlink()
                removed += 1
        except ValueError:
            pass
    if removed:
        print(f"  [backup] {removed} backup(s) antiguo(s) eliminado(s)")

STEPS = [
    ("Schema: migraciones y registro de ajustes",
     ROOT / "src" / "pipeline" / "init_db.py"),
    ("Scrapers: bonos PPI (ultimos 7d)",
     ROOT / "src" / "scrapers" / "scraper_bonos.py"),
    ("Scrapers: acciones AR — basket Capa 3 (ultimos 7d)",
     ROOT / "src" / "scrapers" / "scraper_acciones.py"),
    ("Scrapers: ROFEX DLR futuros PPI (acumulador electoral kink)",
     ROOT / "src" / "scrapers" / "scraper_rofex.py"),
    ("Scrapers: EMBI dolarito.ar (historia completa)",
     ROOT / "src" / "scrapers" / "scraper_embi_historico.py"),
    ("Scrapers: UTDT ICG + ICC (actualiza si hay mes nuevo)",
     ROOT / "src" / "scrapers" / "scraper_utdt.py"),
    ("Scrapers: REM BCRA — consenso analistas IPC/TC/PIB/Fiscal (actualiza si hay mes nuevo)",
     ROOT / "src" / "scrapers" / "scraper_rem.py"),
    ("Pipeline: ICM-REM — indice compuesto de consenso de analistas",
     ROOT / "src" / "pipeline" / "calcular_rem_icm.py"),
    ("Scrapers: VIX diario via yfinance (control global)",
     ROOT / "src" / "scrapers" / "scraper_vix.py"),
    ("Pipeline: ROFEX_1M_EQUIV unificado (SSPM+BCR+PPI)",
     ROOT / "src" / "pipeline" / "calcular_rofex_signal.py"),
    ("Pipeline: Capa 1 — blend MEP + ROFEX",
     ROOT / "src" / "pipeline" / "calcular_capa1.py"),
    ("Pipeline: Capa 2 — bonos soberanos + EMBI",
     ROOT / "src" / "pipeline" / "calcular_capa2.py"),
    ("Pipeline: Capa 3 — semi-vol accionaria AR",
     ROOT / "src" / "pipeline" / "calcular_capa3.py"),
    ("Pipeline: IEP compuesto (35/40/25)",
     ROOT / "src" / "pipeline" / "calcular_iep.py"),
    ("Pipeline: IRPM ajustado por VIX (Bekaert/Nogues-Grandes)",
     ROOT / "src" / "pipeline" / "calcular_ajuste_global.py"),
    ("Dashboard: generar HTML estatico",
     ROOT / "src" / "dashboard" / "generate_dashboard.py"),
    ("Pipeline: healthcheck — rangos, staleness, last_run.txt",
     ROOT / "src" / "pipeline" / "check_pipeline_health.py"),
]

SEP = "-" * 60


def run_step(label: str, script: Path) -> int:
    print(f"\n{SEP}")
    print(f"  {label}")
    print(SEP)
    if DRY:
        print(f"  [DRY] py {script.relative_to(ROOT)}")
        return 0
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
    )
    return result.returncode


def main():
    now = datetime.now()
    ts  = now.strftime("%Y-%m-%d %H:%M:%S")
    day = now.strftime("%A")

    print(f"\n{'='*60}")
    print(f"  IEP Argentina — Update diario")
    print(f"  {ts}  ({day})")
    print(f"{'='*60}")

    if DRY:
        print("  Modo --dry: imprime pasos sin ejecutar\n")

    # Paso 0: backup del DB antes de cualquier modificación
    print(f"\n{'-'*60}")
    print(f"  Paso 0: backup DB")
    print(f"{'-'*60}")
    backup_db()

    for i, (label, script) in enumerate(STEPS, 1):
        code = run_step(label, script)
        if code != 0:
            print(f"\n{'='*60}")
            print(f"  ERROR en paso {i}/{len(STEPS)}: {label}")
            print(f"  Exit code: {code}")
            print(f"  Los pasos siguientes fueron cancelados.")
            print(f"{'='*60}\n")
            sys.exit(code)

    print(f"\n{'='*60}")
    print(f"  OK — {len(STEPS)} pasos completados")
    print(f"  {now.strftime('%H:%M:%S')} -> {datetime.now().strftime('%H:%M:%S')}")
    print(f"  Dashboard: outputs/dashboard.html")
    print(f"{'='*60}\n")

    deploy_ok = deploy_github(ROOT)
    sys.exit(0 if deploy_ok else 2)


def deploy_github(root: Path) -> bool:
    """Publica y prueba Pages; el fallo queda separado del cálculo exitoso."""
    def failed(detail: str) -> bool:
        result = write_status(DEPLOY_STATUS, "FAILED", detail)
        print(f"  [deploy] FAILED — {detail}")
        try:
            delivered = alert_if_configured(result)
            if delivered:
                print(f"  [deploy] {delivered}")
            else:
                print("  [deploy] sin webhook configurado para alertar")
        except RuntimeError as error:
            print(f"  [deploy] alerta no entregada: {error}")
        return False

    docs_index = root / "docs" / "index.html"
    if not docs_index.exists():
        return failed("docs/index.html no encontrado")

    today = datetime.now().strftime("%Y-%m-%d")
    cmds = [
        ["git", "add", "docs/index.html", "docs/deploy_manifest.json"],
        ["git", "commit", "-m", f"dashboard: update {today}"],
        ["git", "push", "origin", "main"],
    ]
    for cmd in cmds:
        r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        if r.returncode != 0:
            out = r.stdout + r.stderr
            if "nothing to commit" in out:
                print("  [deploy] sin cambios — se verifica Pages existente")
                break
            return failed(f"{' '.join(cmd)}: {r.stderr.strip()[:300]}")
    else:
        print(f"  [deploy] GitHub Pages actualizado — {today}")

    probe = subprocess.run(
        [sys.executable, str(root / "src" / "pipeline" / "verify_public_deploy.py")],
        cwd=root,
    )
    if probe.returncode != 0:
        return failed("GitHub Pages no refleja el build local")
    write_status(DEPLOY_STATUS, "OK", "GitHub Pages coincide con el build local")
    print("  [deploy] OK — GitHub Pages verificado")
    return True


if __name__ == "__main__":
    main()
