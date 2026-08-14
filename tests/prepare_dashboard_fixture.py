"""Crea una DB mínima para verificar la generación del dashboard en CI."""

import argparse
import sqlite3
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, type=Path)
    args = parser.parse_args()
    args.db.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(args.db)
    conn.executescript("""
        CREATE TABLE iep_diario (
            fecha DATE PRIMARY KEY, capa1 REAL, capa2 REAL, capa3 REAL,
            iep_total REAL, iep_ajustado REAL
        );
        CREATE TABLE raw_prices (
            activo TEXT NOT NULL, fecha DATE NOT NULL, valor REAL NOT NULL,
            fuente TEXT NOT NULL, PRIMARY KEY (activo, fecha)
        );
    """)
    conn.executemany(
        "INSERT INTO iep_diario VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("2023-12-11", 0.0, 0.0, 0.0, 100.0, None),
            ("2023-12-12", 0.1, 0.2, 0.1, 101.4, None),
        ],
    )
    conn.execute("INSERT INTO raw_prices VALUES ('EMBI', '2023-12-11', 2000, 'fixture')")
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
