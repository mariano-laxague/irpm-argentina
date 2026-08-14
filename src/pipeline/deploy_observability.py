"""Estado y alertas del deploy, separado del resultado del cálculo."""

import json
import os
from datetime import datetime
from pathlib import Path

from src.pipeline.watchdog import notify


def write_status(status_path: Path, status: str, detail: str, revision: str = "unknown") -> dict:
    result = {
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "detail": detail,
        "source_revision": revision,
    }
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return result


def alert_if_configured(result: dict) -> str | None:
    webhook = os.getenv("IRPM_WATCHDOG_WEBHOOK")
    if not webhook:
        return None
    notify(result, webhook)
    return "Alerta de deploy entregada al webhook configurado."
