"""
scraper_rem.py — Descarga el historico REM del BCRA y extrae consenso de analistas.

Fuente: BCRA — "Base de Datos Completa" del Excel historico
URL: https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/historico-relevamiento-expectativas-mercado.xlsx

Variables extraidas (mediana del consenso):
  - tc_12m         : TC $/USD a proximos 12 meses
  - tc_fin_anio    : TC $/USD a fin del ano corriente
  - tc_fin_proximo : TC $/USD a fin del proximo ano
  - ipc_12m        : IPC % i.a. a proximos 12 meses
  - pib_anio       : PIB var. % anual del ano corriente
  - fiscal_anio    : Resultado Primario SPNF del ano corriente (miles de mm $)

Salida: data/rem.csv

Logica de actualizacion:
  - Si el ultimo mes del CSV >= mes objetivo -> nada que hacer.
  - Si hay mes nuevo -> re-descarga el Excel historico y reprocesa.
"""

import io
import requests
import pandas as pd
from pathlib import Path
from datetime import date

ROOT     = Path(__file__).parent.parent.parent
REM_PATH = ROOT / "data" / "rem.csv"

HISTORICO_URL = (
    "https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/"
    "informes/historico-relevamiento-expectativas-mercado.xlsx"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Referer": "https://www.bcra.gob.ar/",
}

COLS = ["fecha", "tc_12m", "tc_fin_anio", "tc_fin_proximo",
        "ipc_12m", "pib_anio", "fiscal_anio"]


def _target_month() -> str:
    today = date.today()
    if today.month == 1:
        return f"{today.year - 1}-12"
    return f"{today.year}-{today.month - 1:02d}"


def _latest_in_csv() -> str | None:
    if not REM_PATH.exists():
        return None
    df = pd.read_csv(REM_PATH)
    return df["fecha"].max() if not df.empty else None


def _download_excel() -> bytes:
    r = requests.get(HISTORICO_URL, headers=HEADERS, timeout=60)
    r.raise_for_status()
    if not r.content[:4].startswith(b"PK"):
        raise ValueError(
            f"Respuesta no es ZIP/xlsx (primeros bytes: {r.content[:8]!r}). "
            "El BCRA puede haber cambiado la URL."
        )
    return r.content


def _year_from_period(per) -> int | None:
    """
    Extrae el anio de un valor de periodo del REM.
    Maneja formatos historicos: int, str, datetime(dic).
    """
    if isinstance(per, (int, float)) and not pd.isna(per):
        val = int(per)
        return val if 2000 <= val <= 2050 else None
    if isinstance(per, str) and per.strip().isdigit():
        val = int(per.strip())
        return val if 2000 <= val <= 2050 else None
    if hasattr(per, "month") and per.month == 12:
        return per.year
    return None


def _parse_rem(content: bytes) -> pd.DataFrame:
    """
    Lee 'Base de Datos Completa' y extrae 6 variables de consenso.

    Estructura:
      col 0: Fecha de pronostico (datetime fin de mes)
      col 1: Variable (str)
      col 2: Referencia (str)
      col 3: Periodo (datetime | 'Prox. 12 meses' | int/str anio)
      col 4: Mediana (float)
    """
    df_raw = pd.read_excel(
        io.BytesIO(content),
        sheet_name="Base de Datos Completa",
        header=1,
        engine="openpyxl",
    )
    df_raw.columns = (
        ["fecha_prono", "variable", "referencia", "periodo", "mediana",
         "promedio", "desvio", "maximo", "minimo", "p90", "p75", "p25", "p10", "n"]
        + list(df_raw.columns[14:])
    )
    df_raw["fecha_prono"] = pd.to_datetime(df_raw["fecha_prono"], errors="coerce")
    df_raw = df_raw[df_raw["fecha_prono"].notna()].copy()
    df_raw["anio_prono"] = df_raw["fecha_prono"].dt.year
    df_raw["mes_key"]   = df_raw["fecha_prono"].dt.strftime("%Y-%m")

    records = {}

    def _ensure(key):
        if key not in records:
            records[key] = {c: None for c in COLS}
            records[key]["fecha"] = key

    def _set(key, field, med):
        if records[key][field] is None and pd.notna(med):
            records[key][field] = round(float(med), 4)

    # ── TC nominal ────────────────────────────────────────────────────────────
    tc = df_raw[df_raw["variable"].str.contains("Tipo de cambio nominal", na=False)]
    for _, row in tc.iterrows():
        key, per, med, anio = row["mes_key"], row["periodo"], row["mediana"], int(row["anio_prono"])
        _ensure(key)
        if isinstance(per, str) and "12 meses" in per:
            _set(key, "tc_12m", med)
        else:
            y = _year_from_period(per)
            if y == anio:     _set(key, "tc_fin_anio",    med)
            elif y == anio+1: _set(key, "tc_fin_proximo", med)

    # ── IPC Prox. 12 meses ───────────────────────────────────────────────────
    ipc = df_raw[
        df_raw["variable"].str.contains("Precios minoristas", na=False) &
        df_raw["variable"].str.contains("INDEC", na=False) &
        ~df_raw["variable"].str.contains("GBA", na=False)   # preferir serie nacional
    ]
    for _, row in ipc.iterrows():
        key, per, med = row["mes_key"], row["periodo"], row["mediana"]
        _ensure(key)
        if isinstance(per, str) and "12 meses" in per:
            _set(key, "ipc_12m", med)

    # ── PIB var. % anual del ano corriente ────────────────────────────────────
    pib = df_raw[
        df_raw["variable"].str.contains("PIB", na=False) &
        df_raw["referencia"].str.contains("prom. anual", na=False)
    ]
    for _, row in pib.iterrows():
        key, per, med, anio = row["mes_key"], row["periodo"], row["mediana"], int(row["anio_prono"])
        _ensure(key)
        if _year_from_period(per) == anio:
            _set(key, "pib_anio", med)

    # ── Resultado Primario SPNF ano corriente ─────────────────────────────────
    fiscal = df_raw[df_raw["variable"].str.contains("Resultado", na=False)]
    for _, row in fiscal.iterrows():
        key, per, med, anio = row["mes_key"], row["periodo"], row["mediana"], int(row["anio_prono"])
        _ensure(key)
        if _year_from_period(per) == anio:
            _set(key, "fiscal_anio", med)

    df_out = pd.DataFrame(sorted(records.values(), key=lambda x: x["fecha"]))
    return df_out[COLS]


def update_rem(target_month: str) -> bool:
    latest = _latest_in_csv()
    if latest and latest >= target_month:
        print(f"  [REM] Ya actualizado ({latest}). Nada que hacer.")
        return False

    print(f"  [REM] Descargando historico BCRA (objetivo: {target_month})...")
    content = _download_excel()
    print(f"  [REM] Excel descargado ({len(content):,} bytes). Procesando...")

    df = _parse_rem(content)
    df.to_csv(REM_PATH, index=False, encoding="utf-8")

    n_post = (df["fecha"] >= "2023-01").sum()
    coverage = df[df["fecha"] >= "2023-01"][["ipc_12m","pib_anio","fiscal_anio"]].notna().mean().round(2).to_dict()
    print(f"  [REM] {len(df)} meses | desde 2023: {n_post} | cobertura {coverage} -> guardado.")
    return True


def main():
    target = _target_month()
    print(f"scraper_rem | target: {target}")
    update_rem(target)


if __name__ == "__main__":
    main()
