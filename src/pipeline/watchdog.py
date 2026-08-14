"""Vigila el heartbeat del pipeline desde un proceso independiente.

Ejecutar después de la hora límite en un scheduler separado del pipeline:
    python src/pipeline/watchdog.py --deadline 20:30

Si falta una corrida hábil, queda un estado en logs/watchdog_status.json, el
proceso devuelve 1 y, si IRPM_WATCHDOG_WEBHOOK está configurada, envía una
alerta JSON por POST a esa URL.
"""

import argparse
import json
import os
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).parent.parent.parent
LOG_DIR = ROOT / "logs"
LAST_RUN = LOG_DIR / "last_run.txt"
STATUS_PATH = LOG_DIR / "watchdog_status.json"


def parse_deadline(value: str) -> time:
    try:
        return time.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("La hora debe tener formato HH:MM") from error


def expected_run_date(now: datetime, deadline: time) -> str | None:
    """Última rueda que ya debía contar con heartbeat, o None antes del deadline."""
    if now.weekday() >= 5:
        return None
    if now.time() < deadline:
        return None
    return now.date().isoformat()


def read_last_run(path: Path) -> tuple[datetime, str]:
    content = path.read_text(encoding="utf-8").strip()
    timestamp, status = content.rsplit(maxsplit=1)
    return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S"), status


def evaluate(now: datetime, deadline: time, last_run_path: Path = LAST_RUN) -> dict:
    required = expected_run_date(now, deadline)
    result = {
        "checked_at": now.isoformat(timespec="seconds"),
        "deadline": deadline.strftime("%H:%M"),
        "required_run_date": required,
        "status": "OK",
        "message": "Aún no hay corrida hábil exigible." if required is None else "Heartbeat vigente.",
    }
    if required is None:
        return result
    if not last_run_path.exists():
        result.update(status="ALERT", message="No existe logs/last_run.txt.")
        return result
    try:
        timestamp, pipeline_status = read_last_run(last_run_path)
    except (OSError, ValueError) as error:
        result.update(status="ALERT", message=f"Heartbeat inválido: {error}")
        return result

    result["last_run_at"] = timestamp.isoformat(timespec="seconds")
    result["pipeline_status"] = pipeline_status
    if timestamp.date().isoformat() < required:
        result.update(status="ALERT", message=f"No hay corrida para {required} antes de {result['deadline']}.")
    elif pipeline_status != "OK":
        result.update(status="ALERT", message=f"La última corrida reportó {pipeline_status}.")
    return result


def notify(result: dict, webhook_url: str) -> None:
    payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
    request = Request(webhook_url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=15) as response:
            if response.status >= 300:
                raise RuntimeError(f"Webhook respondió HTTP {response.status}")
    except URLError as error:
        raise RuntimeError(f"No se pudo entregar la alerta: {error}") from error


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deadline", type=parse_deadline, default=time(20, 30))
    parser.add_argument("--now", help="Solo para prueba: AAAA-MM-DDTHH:MM:SS")
    args = parser.parse_args()
    now = datetime.fromisoformat(args.now) if args.now else datetime.now()
    result = evaluate(now, args.deadline)

    LOG_DIR.mkdir(exist_ok=True)
    STATUS_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[{result['status']}] {result['message']}")

    webhook = os.getenv("IRPM_WATCHDOG_WEBHOOK")
    if result["status"] == "ALERT" and webhook:
        try:
            notify(result, webhook)
            print("Alerta entregada al webhook configurado.")
        except RuntimeError as error:
            print(f"[ALERT] {error}", file=sys.stderr)
            return 2
    return 0 if result["status"] == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
