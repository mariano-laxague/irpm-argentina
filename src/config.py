"""
config.py — Lectura centralizada de configuración del proyecto IEP.

Uso en cualquier script:
    from src.config import CFG
    cred_path = CFG.cred_ppi
    db_path   = CFG.db_path
"""

import configparser
from pathlib import Path

ROOT = Path(__file__).parent.parent
_INI = ROOT / "config.ini"


class _Config:
    def __init__(self):
        if not _INI.exists():
            raise FileNotFoundError(
                f"No se encontró config.ini en {ROOT}. "
                "Copiá config.ini.example y actualizá las rutas."
            )
        p = configparser.ConfigParser()
        p.read(_INI, encoding="utf-8")

        self.cred_ppi   = Path(p["paths"]["cred_ppi"])
        self.db_path    = ROOT / p["database"]["db_path"]
        self.backup_dir = ROOT / p["database"]["backup_dir"]
        self.backup_retain_days = int(p["database"]["backup_retain_days"])

        self.irpm_min             = float(p["pipeline"]["irpm_min"])
        self.irpm_max             = float(p["pipeline"]["irpm_max"])
        self.irpm_max_daily_change = float(p["pipeline"]["irpm_max_daily_change"])
        self.capa_zscore_max      = float(p["pipeline"]["capa_zscore_max"])
        self.data_staleness_days  = int(p["pipeline"]["data_staleness_days"])

    def validate(self):
        """Verifica que las rutas críticas existen."""
        errors = []
        if not self.cred_ppi.exists():
            errors.append(f"  ✗ cred_ppi no encontrado: {self.cred_ppi}")
        if not self.db_path.exists():
            errors.append(f"  ✗ db_path no encontrado: {self.db_path}")
        if errors:
            raise FileNotFoundError("Errores de configuración:\n" + "\n".join(errors))
        return True


CFG = _Config()
