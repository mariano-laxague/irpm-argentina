"""Restaura una DB SQLite desde un snapshot exportado por create_snapshot.py.

Uso:
    python src/pipeline/restore_snapshot.py \
        --snapshot data/snapshots/2026-08-14-v0.1-experimental \
        --db data/iep-restaurado.db
"""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent.parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def restore_snapshot(snapshot: Path, db_path: Path) -> dict:
    manifest_path = snapshot / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for relative_name, details in manifest["files"].items():
        path = snapshot / relative_name
        if not path.exists() or sha256(path) != details["sha256"]:
            raise ValueError(f"Integridad inválida: {relative_name}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        for relative_name in manifest["files"]:
            if relative_name.startswith("inputs/"):
                continue
            table = Path(relative_name).stem
            frame = pd.read_csv(snapshot / relative_name)
            frame.to_sql(table, conn, if_exists="replace", index=False)
    finally:
        conn.close()
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--db", required=True, type=Path)
    args = parser.parse_args()
    snapshot = args.snapshot if args.snapshot.is_absolute() else ROOT / args.snapshot
    db_path = args.db if args.db.is_absolute() else ROOT / args.db
    manifest = restore_snapshot(snapshot, db_path)
    print(f"Snapshot restaurado en: {db_path}")
    print(f"Archivos verificados: {len(manifest['files'])}")


if __name__ == "__main__":
    main()
