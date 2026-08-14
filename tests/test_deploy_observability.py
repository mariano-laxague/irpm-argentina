"""Contratos del estado separado de deploy."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.pipeline import deploy_observability


class TestDeployObservability(unittest.TestCase):
    def test_persiste_estado_failed_con_detalle_y_revision(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "deploy_status.json"
            result = deploy_observability.write_status(path, "FAILED", "Pages no responde", "abc123")
            stored = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(result, stored)
        self.assertEqual(stored["status"], "FAILED")
        self.assertEqual(stored["source_revision"], "abc123")

    def test_sin_webhook_no_intenta_entrega(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(deploy_observability.alert_if_configured({"status": "FAILED"}))
