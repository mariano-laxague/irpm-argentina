"""Contratos estáticos mínimos de semántica y teclado del dashboard."""

import unittest

from src.dashboard.templates import css, html_body, javascript


class TestDashboardAccessibility(unittest.TestCase):
    def test_incluye_landmarks_y_salto_al_contenido(self):
        body = html_body()
        self.assertIn('href="#main-content"', body)
        self.assertIn('<main id="main-content">', body)
        self.assertIn('<h1 class="sr-only">', body)
        self.assertIn('aria-label="Navegación principal"', body)

    def test_rango_es_slider_operable_y_anuncia_fechas(self):
        body, script = html_body(), javascript()
        self.assertEqual(body.count('role="slider"'), 2)
        self.assertIn('aria-live="polite"', body)
        self.assertIn("addEventListener('keydown'", script)
        self.assertIn("event.key === 'Home'", script)
        self.assertIn("aria-valuetext", script)

    def test_estilos_incluyen_foco_visible_y_texto_solo_lector(self):
        styles = css()
        self.assertIn('.sr-only', styles)
        self.assertIn('.skip-link:focus', styles)
        self.assertIn('.chart-toggle:focus-visible', styles)

    def test_incluye_alternativa_tabular_y_descarga_csv(self):
        body, script = html_body(), javascript()
        self.assertIn('id="datos"', body)
        self.assertIn('id="data-table-body"', body)
        self.assertIn('id="download-csv"', body)
        self.assertIn("download: 'irpm_serie.csv'", script)
        self.assertIn('Última observación:', script)
