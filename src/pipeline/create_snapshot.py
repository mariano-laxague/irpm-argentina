"""Exporta un snapshot auditable de la DB y de sus inputs CSV.

Uso:
    python src/pipeline/create_snapshot.py --output data/snapshots/2026-08-14-v0.1-experimental
"""

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).parent.parent.parent
DB_PATH = ROOT / "data" / "iep.db"
TABLES = (
    "raw_prices",
    "iep_diario",
    "iep_composicion",
    "iep_ajustes_extraordinarios",
    "iep_ajustes_aplicados",
)
INPUTS = ("utdt_icg.csv", "utdt_icc.csv", "rem.csv", "rem_icm.csv")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(df: pd.DataFrame, path: Path) -> int:
    df.to_csv(path, index=False, lineterminator="\n")
    return len(df)


def build_snapshot(output: Path, code_ref: str) -> dict:
    if output.exists():
        raise FileExistsError(f"El snapshot ya existe: {output}")
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DB no encontrada: {DB_PATH}")

    output.mkdir(parents=True)
    inputs_dir = output / "inputs"
    inputs_dir.mkdir()
    manifest_files = {}

    conn = sqlite3.connect(DB_PATH)
    try:
        for table in TABLES:
            df = pd.read_sql_query(f"SELECT * FROM {table} ORDER BY 1", conn)
            path = output / f"{table}.csv"
            rows = write_csv(df, path)
            manifest_files[path.name] = {"sha256": sha256(path), "rows": rows}
    finally:
        conn.close()

    for name in INPUTS:
        source = ROOT / "data" / name
        if source.exists():
            dest = inputs_dir / name
            shutil.copyfile(source, dest)
            manifest_files[str(dest.relative_to(output))] = {"sha256": sha256(dest), "rows": None}

    manifest = {
        "snapshot_version": "v0.1-experimental",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "code_ref": code_ref,
        "source_database": "data/iep.db",
        "files": manifest_files,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--code-ref", default="v0.1-experimental")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    manifest = build_snapshot(output, args.code_ref)
    print(f"Snapshot creado: {output}")
    for name, details in manifest["files"].items():
        print(f"  {name}: {details['rows'] if details['rows'] is not None else 'input'} filas")


if __name__ == "__main__":
    main()
