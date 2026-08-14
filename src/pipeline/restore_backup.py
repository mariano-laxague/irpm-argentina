"""Restaura un backup SQLite a un destino nuevo sin tocar la DB activa."""

import argparse
import shutil
import sqlite3
from pathlib import Path


def restore_backup(backup: Path, target: Path) -> None:
    if not backup.exists():
        raise FileNotFoundError(f"Backup no encontrado: {backup}")
    if target.exists():
        raise FileExistsError(f"El destino ya existe: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup, target)
    conn = None
    try:
        conn = sqlite3.connect(target)
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
    except sqlite3.DatabaseError as error:
        target.unlink(missing_ok=True)
        raise ValueError(f"Backup SQLite inválido: {error}") from error
    finally:
        if conn is not None:
            conn.close()
    if result != "ok":
        target.unlink(missing_ok=True)
        raise ValueError(f"Integridad SQLite inválida: {result}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    args = parser.parse_args()
    restore_backup(args.backup, args.target)
    print(f"Backup restaurado y verificado: {args.target}")


if __name__ == "__main__":
    main()
