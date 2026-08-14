"""Contratos de recuperación segura desde un backup SQLite."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.pipeline.restore_backup import restore_backup


class TestRestoreBackup(unittest.TestCase):
    def test_restaura_en_destino_nuevo_y_preserva_datos(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            backup, target = root / "backup.db", root / "restaurada.db"
            conn = sqlite3.connect(backup)
            try:
                conn.execute("CREATE TABLE evidencia (valor TEXT)")
                conn.execute("INSERT INTO evidencia VALUES ('ok')")
                conn.commit()
            finally:
                conn.close()
            restore_backup(backup, target)
            conn = sqlite3.connect(target)
            try:
                self.assertEqual(conn.execute("SELECT valor FROM evidencia").fetchone()[0], "ok")
            finally:
                conn.close()

    def test_no_sobrescribe_destino_existente(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            backup, target = root / "backup.db", root / "restaurada.db"
            backup.touch()
            target.touch()
            with self.assertRaises(FileExistsError):
                restore_backup(backup, target)
