"""Contratos del probe de GitHub Pages."""

import hashlib
import unittest

from src.pipeline import verify_public_deploy


class TestPublicDeploy(unittest.TestCase):
    def test_acepta_contenido_con_hash_del_manifest(self):
        content = b"dashboard de prueba"
        verify_public_deploy.verify(
            {"dashboard_sha256": hashlib.sha256(content).hexdigest()}, content
        )

    def test_rechaza_contenido_distinto(self):
        with self.assertRaisesRegex(ValueError, "Hash público distinto"):
            verify_public_deploy.verify(
                {"dashboard_sha256": "0" * 64}, b"dashboard de prueba"
            )

    def test_rechaza_manifest_incompleto(self):
        with self.assertRaisesRegex(ValueError, "dashboard_sha256"):
            verify_public_deploy.verify({}, b"dashboard de prueba")
