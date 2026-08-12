"""
Inicializa la base de datos SQLite del IEP.
Crea las tablas raw_prices e iep_diario si no existen.
Idempotente — se puede correr múltiples veces sin problema.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "iep.db"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS raw_prices (
            activo          TEXT    NOT NULL,
            fecha           DATE    NOT NULL,
            valor           REAL    NOT NULL,
            fuente          TEXT    NOT NULL,
            timestamp_carga DATETIME DEFAULT (datetime('now', 'localtime')),
            PRIMARY KEY (activo, fecha)
        );

        CREATE TABLE IF NOT EXISTS iep_diario (
            fecha           DATE    PRIMARY KEY,
            capa1           REAL,
            capa2           REAL,
            capa3           REAL,
            iep_total       REAL,
            pesos_version   TEXT    NOT NULL DEFAULT '50-50-0'
        );

        CREATE INDEX IF NOT EXISTS idx_raw_activo_fecha
            ON raw_prices (activo, fecha);
    """)

    conn.commit()
    conn.close()
    print(f"DB inicializada: {DB_PATH}")


if __name__ == "__main__":
    init_db()
