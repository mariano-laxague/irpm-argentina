"""Verifica que GitHub Pages sirve el mismo dashboard que el manifest local."""

import argparse
import hashlib
import json
import sys
from urllib.error import URLError
from urllib.request import urlopen

DEFAULT_DASHBOARD_URL = "https://marianolaxague-crypto.github.io/irpm-argentina/"
DEFAULT_MANIFEST_URL = DEFAULT_DASHBOARD_URL + "deploy_manifest.json"


def verify(manifest: dict, dashboard_bytes: bytes) -> None:
    actual_hash = hashlib.sha256(dashboard_bytes).hexdigest()
    expected_hash = manifest.get("dashboard_sha256")
    if not expected_hash:
        raise ValueError("El manifest no contiene dashboard_sha256")
    if actual_hash != expected_hash:
        raise ValueError(
            f"Hash público distinto: esperado {expected_hash}, recibido {actual_hash}"
        )


def fetch(url: str) -> bytes:
    try:
        with urlopen(url, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status} en {url}")
            return response.read()
    except URLError as error:
        raise RuntimeError(f"No se pudo consultar {url}: {error}") from error


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dashboard-url", default=DEFAULT_DASHBOARD_URL)
    parser.add_argument("--manifest-url", default=DEFAULT_MANIFEST_URL)
    args = parser.parse_args()
    try:
        manifest = json.loads(fetch(args.manifest_url).decode("utf-8"))
        verify(manifest, fetch(args.dashboard_url))
    except (RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"[ALERT] Deploy público no verificado: {error}", file=sys.stderr)
        return 1
    print(
        f"[OK] Deploy público verificado: {manifest['latest_data_date']} "
        f"({manifest['source_revision'][:12]})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
