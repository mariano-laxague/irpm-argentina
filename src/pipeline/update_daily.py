"""
update_daily.py — Pipeline de actualizacion diaria del IEP Argentina.

Ejecuta los pasos en secuencia. Si un paso falla, los siguientes NO corren
(los calculos dependen de los datos anteriores). El exit code indica exito/falla
para que Task Scheduler pueda detectar el resultado.

Pasos:
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

Uso:
    py src/pipeline/update_daily.py         # update normal
    py src/pipeline/update_daily.py --dry   # solo imprime pasos, no ejecuta

Task Scheduler: ver run_update.bat en la raiz del proyecto.
Log: logs/update_YYYYMMDD.log
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT    = Path(__file__).parent.parent.parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

DRY = "--dry" in sys.argv

STEPS = [
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

    deploy_github(ROOT)
    sys.exit(0)


def deploy_github(root: Path) -> None:
    """Pushea docs/index.html a GitHub Pages. Falla silenciosamente para no romper el pipeline."""
    docs_index = root / "docs" / "index.html"
    if not docs_index.exists():
        print("  [deploy] docs/index.html no encontrado — skip")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    cmds = [
        ["git", "add", "docs/index.html"],
        ["git", "commit", "-m", f"dashboard: update {today}"],
        ["git", "push", "origin", "main"],
    ]
    for cmd in cmds:
        r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        if r.returncode != 0:
            out = r.stdout + r.stderr
            if "nothing to commit" in out:
                print("  [deploy] sin cambios — skip push")
                return
            print(f"  [deploy] warning: {r.stderr.strip()[:120]}")
            return
    print(f"  [deploy] GitHub Pages actualizado — {today}")


if __name__ == "__main__":
    main()
