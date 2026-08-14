"""Contratos del watchdog independiente del pipeline."""

import tempfile
import unittest
from datetime import datetime, time
from pathlib import Path

from src.pipeline import watchdog


class TestWatchdog(unittest.TestCase):
    def test_antes_del_deadline_no_exige_heartbeat(self):
        result = watchdog.evaluate(datetime(2026, 8, 14, 20, 29), time(20, 30))
        self.assertEqual(result["status"], "OK")
        self.assertIsNone(result["required_run_date"])

    def test_sin_heartbeat_alerta_despues_del_deadline(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = watchdog.evaluate(
                datetime(2026, 8, 14, 20, 35), time(20, 30), Path(temporary) / "missing.txt"
            )
        self.assertEqual(result["status"], "ALERT")
        self.assertIn("No existe", result["message"])

    def test_heartbeat_viejo_alerta(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "last_run.txt"
            path.write_text("2026-08-13 20:00:00  OK\n", encoding="utf-8")
            result = watchdog.evaluate(datetime(2026, 8, 14, 20, 35), time(20, 30), path)
        self.assertEqual(result["status"], "ALERT")
        self.assertIn("No hay corrida", result["message"])

    def test_warning_del_pipeline_alerta(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "last_run.txt"
            path.write_text("2026-08-14 20:00:00  WARNING\n", encoding="utf-8")
            result = watchdog.evaluate(datetime(2026, 8, 14, 20, 35), time(20, 30), path)
        self.assertEqual(result["status"], "ALERT")
        self.assertIn("WARNING", result["message"])

    def test_heartbeat_ok_del_dia_pasa(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "last_run.txt"
            path.write_text("2026-08-14 20:00:00  OK\n", encoding="utf-8")
            result = watchdog.evaluate(datetime(2026, 8, 14, 20, 35), time(20, 30), path)
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["required_run_date"], "2026-08-14")

