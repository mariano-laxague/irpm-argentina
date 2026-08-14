"""Contratos deterministas de cálculo para el IRPM.

Estas pruebas no leen la DB productiva ni llaman APIs. Protegen los invariantes
de fórmula y hacen visible la composición cuando faltan componentes.
"""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.pipeline import calcular_capa1, calcular_capa2, calcular_capa3, calcular_iep


class TestCapa1(unittest.TestCase):
    def setUp(self):
        self.index = pd.bdate_range("2024-01-02", periods=70)
        self.mep = pd.Series(np.linspace(900, 1100, len(self.index)), index=self.index)
        self.rofex = pd.Series(np.linspace(910, 1160, len(self.index)), index=self.index)

    def test_mep_alto_empeora_la_senal(self):
        z = calcular_capa1.rolling_zscore(np.log(self.mep))
        self.assertLess((-z).iloc[-1], 0)

    def test_sin_rofex_usa_mep_sin_renormalizar(self):
        with patch.object(calcular_capa1, "load_series", return_value=pd.Series(dtype=float)):
            result = calcular_capa1.compute_capa1(self.mep)

        expected = (-calcular_capa1.rolling_zscore(np.log(self.mep))).dropna()
        pd.testing.assert_series_equal(result, expected.rename("capa1"))

    def test_rofex_disponible_aplica_blend_mitad_y_mitad(self):
        with patch.object(calcular_capa1, "load_series", return_value=self.rofex):
            result = calcular_capa1.compute_capa1(self.mep)

        z_mep = -calcular_capa1.rolling_zscore(np.log(self.mep))
        premium = self.rofex / self.mep - 1
        z_rofex = -calcular_capa1.rolling_zscore(premium)
        expected = (0.5 * z_mep + 0.5 * z_rofex).combine_first(z_mep).dropna()
        pd.testing.assert_series_equal(result, expected.rename("capa1"))


class TestCapa2(unittest.TestCase):
    def test_pago_mecanico_se_corrige_sin_mutar_el_input(self):
        index = pd.to_datetime(["2026-07-06", "2026-07-07", "2026-07-08", "2026-07-09"])
        prices = pd.Series([100.0, 90.0, 88.0, 87.0], index=index)

        adjusted, fixes = calcular_capa2.ffill_payment_dates(prices, "GD30D")

        pd.testing.assert_series_equal(prices, pd.Series([100.0, 90.0, 88.0, 87.0], index=index))
        pd.testing.assert_series_equal(adjusted, pd.Series([100.0, 100.0, 100.0, 100.0], index=index))
        self.assertEqual(len(fixes), 3)

    def test_caida_normal_en_ventana_de_pago_no_se_corrige(self):
        index = pd.to_datetime(["2026-07-06", "2026-07-07"])
        prices = pd.Series([100.0, 98.0], index=index)

        adjusted, fixes = calcular_capa2.ffill_payment_dates(prices, "GD30D")

        pd.testing.assert_series_equal(adjusted, prices)
        self.assertEqual(fixes, [])

    def test_embi_faltante_degrada_capa2_sin_renormalizar_pesos(self):
        index = pd.bdate_range("2024-01-02", periods=70)
        series = {
            "GD30D": pd.Series(np.linspace(60, 70, len(index)), index=index),
            "AL30D": pd.Series(np.linspace(58, 67, len(index)), index=index),
            "GD35D": pd.Series(np.linspace(55, 64, len(index)), index=index),
            "EMBI": pd.Series(np.linspace(1000, 800, len(index)), index=index),
        }
        series["EMBI"].iloc[-1] = np.nan

        with patch.object(calcular_capa2, "load_series", side_effect=lambda activo: series[activo]):
            result = calcular_capa2.compute_capa2()

        self.assertEqual(result.loc[index[-2], "n_componentes"], 5)
        self.assertEqual(result.loc[index[-1], "n_componentes"], 4)
        self.assertTrue(pd.isna(result.loc[index[-1], "capa2"]))


class TestCapa3(unittest.TestCase):
    def test_split_ajusta_solo_precios_anteriores_y_no_muta_input(self):
        index = pd.to_datetime(["2026-07-31", "2026-08-03"])
        prices = pd.Series([100.0, 10.0], index=index)

        adjusted = calcular_capa3.apply_splits(prices, "YPFD")

        pd.testing.assert_series_equal(prices, pd.Series([100.0, 10.0], index=index))
        pd.testing.assert_series_equal(adjusted, pd.Series([10.0, 10.0], index=index))


class TestIndiceCompuesto(unittest.TestCase):
    def test_pesos_definitivos_y_baseline_exactos(self):
        index = pd.to_datetime(["2023-12-11", "2023-12-12"])
        df = pd.DataFrame(
            {"capa1": [1.0, 2.0], "capa2": [3.0, 4.0], "capa3": [5.0, 6.0]},
            index=index,
        )

        result = calcular_iep.compute_iep(df)

        self.assertEqual(result.loc[index[0]], 100.0)
        self.assertEqual(result.loc[index[1]], 110.0)

    def test_sin_capa3_degrada_y_no_publica_un_indice_50_50(self):
        index = pd.to_datetime(["2023-12-11", "2023-12-12"])
        df = pd.DataFrame(
            {"capa1": [1.0, 3.0], "capa2": [3.0, 5.0], "capa3": [5.0, np.nan]},
            index=index,
        )

        result = calcular_iep.compute_iep(df)

        self.assertEqual(list(result.index), [index[0]])


class TestComposicion(unittest.TestCase):
    def test_metadata_expone_fecha_senales_pesos_y_degradacion(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "iep.db"
            conn = sqlite3.connect(db_path)
            conn.executescript("""
                CREATE TABLE raw_prices (activo TEXT, fecha DATE, valor REAL, fuente TEXT);
                CREATE TABLE iep_composicion (
                    fecha DATE PRIMARY KEY, version_metodologia TEXT,
                    estado_publicacion TEXT, fecha_efectiva DATE,
                    componentes_json TEXT, pesos_json TEXT, motivo_degradacion TEXT,
                    calculado_en DATETIME
                );
            """)
            activos = ["MEP", "ROFEX_1M_EQUIV", "GD30D", "AL30D", "GD35D", "EMBI",
                       "YPFD", "GGAL", "PAMP", "TECO2"]
            conn.executemany(
                "INSERT INTO raw_prices VALUES (?, '2023-12-11', 1, 'test')",
                [(activo,) for activo in activos],
            )
            conn.executemany(
                "INSERT INTO raw_prices VALUES (?, '2023-12-12', 1, 'test')",
                [(activo,) for activo in activos if activo != "EMBI"],
            )
            conn.commit()
            conn.close()
            index = pd.to_datetime(["2023-12-11", "2023-12-12"])
            df = pd.DataFrame(
                {"capa1": [1.0, 1.0], "capa2": [1.0, np.nan], "capa3": [1.0, 1.0]}, index=index
            )

            with patch.object(calcular_iep, "DB_PATH", db_path):
                calcular_iep.save_composition(df)

            conn = sqlite3.connect(db_path)
            rows = conn.execute(
                "SELECT fecha, estado_publicacion, componentes_json, pesos_json, motivo_degradacion "
                "FROM iep_composicion ORDER BY fecha"
            ).fetchall()
            conn.close()

        self.assertEqual(rows[0][1], "publicable")
        self.assertEqual(json.loads(rows[0][2])["capa2"]["disponibles"],
                         ["GD30D", "AL30D", "GD35D", "EMBI"])
        self.assertEqual(json.loads(rows[0][3])["capas"],
                         {"capa1": 0.35, "capa2": 0.4, "capa3": 0.25})
        self.assertEqual(rows[1][1], "degradado")
        self.assertIn("capa2", rows[1][4])

    def test_falla_si_no_existe_el_baseline_exacto(self):
        index = pd.to_datetime(["2023-12-12"])
        df = pd.DataFrame(
            {"capa1": [1.0], "capa2": [3.0], "capa3": [5.0]}, index=index
        )

        with self.assertRaisesRegex(ValueError, "Baseline exacto no disponible"):
            calcular_iep.compute_iep(df)

    def test_no_publica_un_valor_si_falta_capa1_o_capa2(self):
        index = pd.to_datetime(["2023-12-11", "2023-12-12", "2023-12-13"])
        df = pd.DataFrame(
            {"capa1": [1.0, np.nan, 3.0], "capa2": [3.0, 4.0, np.nan], "capa3": [5.0, 6.0, 7.0]},
            index=index,
        )

        result = calcular_iep.compute_iep(df)

        self.assertEqual(list(result.index), [index[0]])


if __name__ == "__main__":
    unittest.main()
