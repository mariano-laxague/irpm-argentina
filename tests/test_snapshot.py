"""Pruebas del snapshot reproducible de IRPM."""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.pipeline import create_snapshot, restore_snapshot


class TestSnapshot(unittest.TestCase):
    def test_exporta_verifica_y_restaura_tablas(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_db = root / "origen.db"
            snapshot_dir = root / "snapshot"
            restored_db = root / "restaurada.db"

            conn = sqlite3.connect(source_db)
            try:
                for table in create_snapshot.TABLES:
                    pd.DataFrame({"id": [1, 2], "valor": ["a", "b"]}).to_sql(
                        table, conn, index=False
                    )
            finally:
                conn.close()

            with patch.object(create_snapshot, "DB_PATH", source_db), patch.object(
                create_snapshot, "INPUTS", ()
            ):
                manifest = create_snapshot.build_snapshot(snapshot_dir, "test-ref")

            self.assertEqual(manifest["code_ref"], "test-ref")
            self.assertEqual(manifest["files"]["raw_prices.csv"]["rows"], 2)
            self.assertTrue((snapshot_dir / "manifest.json").exists())
            self.assertEqual(
                json.loads((snapshot_dir / "manifest.json").read_text(encoding="utf-8")),
                manifest,
            )

            restore_snapshot.restore_snapshot(snapshot_dir, restored_db)
            conn = sqlite3.connect(restored_db)
            try:
                rows = conn.execute("SELECT COUNT(*) FROM iep_diario").fetchone()[0]
            finally:
                conn.close()
            self.assertEqual(rows, 2)

            (snapshot_dir / "raw_prices.csv").write_text("alterado\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Integridad inválida"):
                restore_snapshot.restore_snapshot(snapshot_dir, root / "corrupta.db")

