"""Registro durable de ajustes extraordinarios aplicados al cálculo."""

import json
import sqlite3
from datetime import date


AJUSTES_REGISTRADOS = (
    (
        "bonos_pagos_v1", "pago_amortizacion", "GD30D,AL30D,GD35D", "2022-01-01",
        "2026-08-12", {"dias_pre_pago": 2, "umbral_caida": 0.025, "fechas_pago": ["01-09", "07-09"]},
        "Evita interpretar cupón y amortización programados como deterioro político.",
        "Calendario de pagos de los bonos; ver tasks/lessons.md 2026-08-12.",
        "tests/test_calculations.py::TestCapa2.test_pago_mecanico_se_corrige_sin_mutar_el_input",
    ),
    (
        "ypfd_split_20260803", "split_accionario", "YPFD", "2026-08-03",
        "2026-08-12", {"ratio": 10, "ajuste": "divide precios pre-split"},
        "Mantiene continuos los retornos logarítmicos tras el split 10:1.",
        "Split YPFD 10:1 confirmado; ver tasks/lessons.md 2026-08-12.",
        "tests/test_calculations.py::TestCapa3.test_split_ajusta_solo_precios_anteriores_y_no_muta_input",
    ),
    (
        "backfill_ppi_20260724_20260804", "backfill_datos", "bonos_y_acciones", "2026-07-24",
        "2026-08-12", {"hasta": "2026-08-04", "fuente": "PPI"},
        "Repone ocho ruedas ausentes tras una interrupción del scheduler.",
        "Backfill manual PPI; ver CONTEXTO.md sesión 21.",
        "tests/test_calculations.py::TestComposicion.test_metadata_expone_fecha_senales_pesos_y_degradacion",
    ),
)


def ensure_adjustment_registry(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS iep_ajustes_extraordinarios (
            ajuste_id               TEXT PRIMARY KEY,
            tipo                    TEXT NOT NULL,
            activos                 TEXT NOT NULL,
            fecha_efectiva          DATE NOT NULL,
            fecha_implementacion    DATE NOT NULL,
            regla_json              TEXT NOT NULL,
            razon                   TEXT NOT NULL,
            fuente                  TEXT NOT NULL,
            prueba_regresion        TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS iep_ajustes_aplicados (
            ajuste_id               TEXT NOT NULL,
            fecha_calculo           DATE NOT NULL,
            fecha_afectada          DATE NOT NULL,
            activo                  TEXT NOT NULL,
            detalle_json            TEXT NOT NULL,
            PRIMARY KEY (ajuste_id, fecha_calculo, fecha_afectada, activo),
            FOREIGN KEY (ajuste_id) REFERENCES iep_ajustes_extraordinarios(ajuste_id)
        );
    """)
    conn.executemany("""
        INSERT INTO iep_ajustes_extraordinarios
            (ajuste_id, tipo, activos, fecha_efectiva, fecha_implementacion,
             regla_json, razon, fuente, prueba_regresion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ajuste_id) DO NOTHING
    """, [(*row[:5], json.dumps(row[5], sort_keys=True), *row[6:]) for row in AJUSTES_REGISTRADOS])


def record_payment_fixes(conn: sqlite3.Connection, fixes: list[tuple]) -> None:
    """Registra cada forward-fill aplicado, conservando el dato crudo intacto."""
    ensure_adjustment_registry(conn)
    calculated = date.today().isoformat()
    conn.executemany("""
        INSERT INTO iep_ajustes_aplicados
            (ajuste_id, fecha_calculo, fecha_afectada, activo, detalle_json)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(ajuste_id, fecha_calculo, fecha_afectada, activo)
        DO UPDATE SET detalle_json=excluded.detalle_json
    """, [
        ("bonos_pagos_v1", calculated, fecha.isoformat(), activo,
         json.dumps({"caida_vs_pre_ventana": drop}, sort_keys=True))
        for fecha, activo, drop in fixes
    ])
