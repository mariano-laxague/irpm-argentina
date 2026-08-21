"""
generate_dashboard.py — IRPM Argentina
Diseño: página única scrollable — fondo crema (#faf7f2), Lora serif, acento terracotta (#b45309)
Uso: python src/dashboard/generate_dashboard.py
"""

import calendar
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = Path(os.environ.get("IRPM_DB_PATH", ROOT / "data" / "iep.db"))
OUTPUT = Path(os.environ.get("IRPM_DASHBOARD_OUTPUT", ROOT / "outputs" / "dashboard.html"))
DOCS_OUTPUT = Path(os.environ.get("IRPM_DASHBOARD_DOCS_OUTPUT", ROOT / "docs" / "index.html"))
DEPLOY_MANIFEST_OUTPUT = Path(os.environ.get(
    "IRPM_DASHBOARD_MANIFEST_OUTPUT", DOCS_OUTPUT.parent / "deploy_manifest.json"
))

UTDT_ICG_PATH = ROOT / "data" / "utdt_icg.csv"
UTDT_ICC_PATH = ROOT / "data" / "utdt_icc.csv"
REM_CSV_PATH  = ROOT / "data" / "rem.csv"
REM_ICM_PATH  = ROOT / "data" / "rem_icm.csv"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.dashboard.templates import css, html_body, javascript


EVENTS_RICH = [
    {
        "n": 1, "date": "2024-04-17", "start": "2023-12-11", "end": "2024-07-12", "lane": 0, "short": "Honeymoon", "tag": "Dic 2023–Jul 2024",
        "title": "Honeymoon: mejora inicial y meseta",
        "impact": "positive",
        "body": "Desde el baseline del 11 de diciembre de 2023 (100,0), el IRPM sube hasta un máximo de 112,9 el 17 de abril y se mantiene en 110,2 al cierre del período, antes de la primera corrección de julio. En la etapa coincidieron superávit fiscal, desaceleración de la inflación mensual y una mejora de las señales financieras incluidas. Son hechos de contexto: el IRPM no permite atribuirles causalidad ni separar su efecto de otros factores locales y globales.",
    },
    {
        "n": 2, "date": "2024-12-16", "start": "2024-08-12", "end": "2024-12-30", "lane": 0, "short": "Credibilidad", "tag": "12 ago–30 dic 2024",
        "title": "Credibilidad: recuperación y máximo de 2024",
        "impact": "positive",
        "body": "Desde la recuperación posterior al shock de agosto, el IRPM sube de 107,7 el 12 de agosto a un máximo histórico de 115,1 el 16 de diciembre y cierra diciembre en 111,9. La tendencia coincide con desinflación, continuidad del ancla fiscal y mejores señales financieras en las capas del índice. “Credibilidad” es una lectura editorial de ese patrón: el IRPM no estima convicción política ni identifica el aporte causal de cada factor.",
    },
    {
        "n": 3, "date": "2025-09-15", "start": "2025-06-02", "end": "2025-10-24", "lane": 0, "short": "Legislativas", "tag": "2 jun–24 oct 2025",
        "title": "Legislativas: deterioro preelectoral",
        "impact": "negative",
        "body": "Desde el cierre de mayo, el IRPM baja de 106,2 el 2 de junio a 94,1 en la rueda previa a las legislativas, con un mínimo histórico de 75,7 el 15 de septiembre. Durante la etapa se deterioran las tres capas del índice: cambiaria, deuda soberana y volatilidad accionaria. El proceso coincide con la campaña electoral, pero el IRPM no permite separar ese contexto de otros factores macroeconómicos y financieros.",
    },
    {
        "n": 4, "date": "2025-11-03", "start": "2025-10-27", "end": "2025-12-30", "lane": 0, "short": "Post-legislativas", "tag": "27 oct–30 dic 2025",
        "title": "Post-legislativas: recuperación gradual",
        "impact": "positive",
        "body": "Tras las legislativas, el IRPM salta de 94,1 en la rueda previa a 102,3 el 27 de octubre y continúa recuperándose hasta 106,3 el 30 de diciembre. En el tramo mejora la capa de deuda soberana y se sostienen las señales accionarias. La elección es contexto contemporáneo: el índice no permite atribuirle causalidad exclusiva ni separar su efecto de otros factores financieros y macroeconómicos.",
    },
    {
        "n": 5, "date": "2024-08-02", "start": "2024-07-15", "end": "2024-08-09", "lane": 1, "short": "Corrección", "tag": "15 jul–9 ago 2024",
        "title": "Corrección",
        "impact": "negative",
        "body": "Después del cierre del honeymoon, el IRPM cae de 110,2 el 12 de julio a 102,6 el 15 de julio y permanece entre 101 y 103 hasta el 9 de agosto. La primera fase coincide con la reacción del mercado al nuevo marco monetario y cambiario anunciado en julio; la segunda incorpora la volatilidad global del 5 de agosto. En el índice, el salto inicial proviene principalmente de mayor volatilidad bajista del basket accionario. Son factores contemporáneos: el IRPM no identifica el peso causal de cada uno.",
    },
    {
        "n": 6, "date": "2025-04-08", "start": "2024-12-30", "end": "2025-04-14", "lane": 2, "short": "Deterioro", "tag": "Dic 2024–Abr 2025",
        "title": "Deterioro y shock de abril",
        "impact": "negative",
        "body": "Después del máximo de diciembre, el IRPM se debilita gradualmente desde 111,9 hasta 104,3 al cierre de marzo y acelera la caída hasta un mínimo de 95,7 el 8 de abril. La etapa combina un deterioro progresivo de las señales de deuda y volatilidad accionaria con la turbulencia global de abril y la transición al nuevo régimen cambiario. La coincidencia no permite atribuir el movimiento a un factor único.",
    },
    {
        "n": 7, "date": "2025-05-21", "start": "2025-04-15", "end": "2025-05-30", "lane": 1, "short": "Recuperación", "tag": "15 abr–30 may 2025",
        "title": "Recuperación",
        "impact": "positive",
        "body": "Tras el cambio de régimen de abril, el IRPM pasa de 103,2 el 15 de abril a 110,5 al cierre de mayo, con un máximo de 111,9 el 21 de mayo. La recuperación coincide con la implementación del nuevo marco cambiario y el acuerdo con el FMI. Son elementos de contexto: el índice no identifica el aporte causal de cada factor ni mide expectativas electorales.",
    },
    {
        "n": 8, "date": "2026-04-17", "start": "2026-03-16", "end": "2026-05-15", "lane": 0, "short": "Pax política", "tag": "Mar–May 2026",
        "title": "Pax política: el riesgo alternativo comprime",
        "impact": "positive",
        "body": "Nuevo pico local (~105 pts), unos 35 puntos por encima del mínimo preelectoral de septiembre de 2025. La lectura editorial lo ubica en un período de menor tensión política visible y oposición fragmentada. El IRPM no observa candidaturas, probabilidades electorales ni distribuciones de escenarios post-2027; esas interpretaciones requieren evidencia externa.",
    },
    {
        "n": 9, "date": "2026-08-01", "start": "2026-05-01", "end": "2026-08-20", "lane": 1, "short": "Deterioro", "tag": "May–Ago 2026",
        "title": "Pendiente negativa: compresión de la ventana política",
        "impact": "negative",
        "body": "Tras el pico de abril (~112 pts), el IRPM muestra una pendiente negativa: promedia ~109 pts en mayo, baja de 110 en junio y toca un mínimo local cercano a 101 en julio. Agosto se estabiliza alrededor de 103–105 pts. La serie describe un deterioro relativo de las señales incluidas; asociarlo con la ventana preelectoral de 2027 es una hipótesis editorial aún no validada.",
    },
]

BASELINE_PRESETS = [
    {"value": "2023-12-11", "label": "Inicio de gestión Milei · Dic 2023"},
    {"value": "2024-04-08", "label": "Peak honeymoon · Abr 2024"},
    {"value": "2024-12-09", "label": "Máximo histórico · Dic 2024"},
    {"value": "2025-10-27", "label": "Legislativas 2025"},
]


# ── Python helpers ─────────────────────────────────────────────────────────────

def load_capa_signals():
    """Lee z-scores de las 3 capas del último día hábil disponible."""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            """SELECT capa1, capa2, capa3 FROM iep_diario
               WHERE iep_total IS NOT NULL
               ORDER BY fecha DESC LIMIT 1""",
            conn
        )
        conn.close()
        if df.empty:
            return {"capa1": 0.0, "capa2": 0.0, "capa3": 0.0}
        return {
            "capa1": float(df.iloc[0]["capa1"]),
            "capa2": float(df.iloc[0]["capa2"]),
            "capa3": float(df.iloc[0]["capa3"]),
        }
    except Exception:
        return {"capa1": 0.0, "capa2": 0.0, "capa3": 0.0}


def get_capa_signal(z):
    """Returns CSS class and plain-language label for a z-score."""
    if z > 0.3:
        return {"cls": "sig-pos", "label": "Por encima de su media móvil orientada"}
    if z < -0.3:
        return {"cls": "sig-neg", "label": "Por debajo de su media móvil orientada"}
    return {"cls": "sig-neu", "label": "Cerca de su media móvil orientada"}


def get_headline(v):
    if v > 115:
        return "El compuesto se ubica <em>más de 15 puntos sobre el baseline</em>"
    if v > 110:
        return "El compuesto se ubica <em>más de 10 puntos sobre el baseline</em>"
    if v >= 100:
        return "El compuesto se ubica <em>por encima del baseline</em>"
    if v >= 90:
        return "El compuesto se ubica <em>por debajo del baseline</em>"
    return "El compuesto se ubica <em>más de 10 puntos debajo del baseline</em>"


# ── UTDT loader ───────────────────────────────────────────────────────────────

def load_utdt_data():
    """ICG e ICC UTDT — valores crudos desde dic-2023."""
    icg = pd.read_csv(UTDT_ICG_PATH)
    icc = pd.read_csv(UTDT_ICC_PATH)[["fecha", "icc_nacional"]]

    merged = (
        pd.merge(icg[["fecha", "icg_general"]], icc[["fecha", "icc_nacional"]], on="fecha", how="outer")
        .sort_values("fecha")
        .query("fecha >= '2023-12'")
    )

    result = []
    for _, row in merged.iterrows():
        y, m = map(int, row["fecha"].split("-"))
        last_day = calendar.monthrange(y, m)[1]
        result.append({
            "d": f"{y:04d}-{m:02d}-{last_day:02d}",
            "icg": round(float(row["icg_general"]), 4) if pd.notna(row["icg_general"]) else None,
            "icc": round(float(row["icc_nacional"]), 4) if pd.notna(row["icc_nacional"]) else None,
        })
    return result


# ── REM loaders ───────────────────────────────────────────────────────────────

def load_rem_data():
    if not REM_CSV_PATH.exists():
        return []
    df = pd.read_csv(REM_CSV_PATH).query("fecha >= '2023-12'")
    if df.empty:
        return []
    result = []
    for _, row in df.iterrows():
        result.append({
            "d":       row["fecha"],
            "tc_12m":  round(float(row["tc_12m"]), 0)   if pd.notna(row["tc_12m"])  else None,
            "ipc_12m": round(float(row["ipc_12m"]), 1)  if pd.notna(row["ipc_12m"]) else None,
            "pib":     round(float(row["pib_anio"]), 1)  if pd.notna(row["pib_anio"]) else None,
        })
    return result


def load_rem_icm():
    if not REM_ICM_PATH.exists():
        return []
    df = pd.read_csv(REM_ICM_PATH).query("fecha >= '2023-12'")
    if df.empty:
        return []
    return [{"d": row["fecha"], "icm": round(float(row["icm"]), 2)}
            for _, row in df.iterrows() if pd.notna(row["icm"])]


# ── Helpers ────────────────────────────────────────────────────────────────────

def get_zone(v):
    if v > 110:
        return {"tag": "> 110", "label": "Más de 10 puntos sobre el baseline",
                "color": "#16a34a", "id": "gt110"}
    elif v >= 90:
        return {"tag": "90-110", "label": "Entorno del baseline convencional",
                "color": "#2563eb", "id": "b90_110"}
    elif v >= 70:
        return {"tag": "70-89",  "label": "Más de 10 puntos bajo el baseline",
                "color": "#ca8a04", "id": "b70_89"}
    elif v >= 40:
        return {"tag": "40-69",  "label": "Distancia negativa elevada respecto del baseline",
                "color": "#ea580c", "id": "b40_69"}
    else:
        return {"tag": "< 40",   "label": "Extremo inferior de la escala observada",
                "color": "#dc2626", "id": "lt40"}


def build_comparativa_data():
    """Monthly EMBI-proxy index for Macri / Alberto / Milei, all rebased to 100.
    Formula: idx = 100 × (EMBI_t0 / EMBI_t)  → higher = more market confidence.
    """
    conn = sqlite3.connect(str(DB_PATH))
    terms = [
        ("macri",   "2015-12-10", "2019-12-09"),
        ("alberto", "2019-12-10", "2023-12-09"),
        ("milei",   "2023-12-10", None),
    ]
    result = {}
    for slug, start, end in terms:
        where = f"activo='EMBI' AND fecha >= '{start}'"
        if end:
            where += f" AND fecha <= '{end}'"
        df = pd.read_sql(
            f"SELECT fecha, valor FROM raw_prices WHERE {where} ORDER BY fecha",
            conn, parse_dates=["fecha"]
        )
        if df.empty:
            continue
        df = df.set_index("fecha").resample("MS").mean(numeric_only=True).reset_index()
        base = df["valor"].iloc[0]
        df["months"] = range(len(df))
        df["idx"] = (base / df["valor"] * 100).round(2)
        result[slug] = [{"m": int(r.months), "v": float(r.idx)} for _, r in df.iterrows()]
    conn.close()
    return json.dumps(result)


def build_gauge_svg(v):
    import math
    frac  = max(0.0, min(1.0, (v - 70) / 60))
    angle = 180.0 - frac * 180.0   # 180°=left(70), 0°=right(130)

    cx, cy = 100, 90
    r  = 72
    sw = 10   # track stroke width

    def pt(deg, rad=r):
        a = math.radians(deg)
        return cx + rad * math.cos(a), cy - rad * math.sin(a)

    pL = pt(180)    # left  (9-o'clock)
    pT = pt(90)     # top   (12-o'clock)
    pR = pt(0)      # right (3-o'clock)
    pA = pt(angle)  # current value position

    # -- gray background track (clockwise, sweep=1, two 90° arcs → unambiguous) --
    track_d = (f"M{pL[0]:.1f},{pL[1]:.1f} "
               f"A{r},{r} 0 0,1 {pT[0]:.1f},{pT[1]:.1f} "
               f"A{r},{r} 0 0,1 {pR[0]:.1f},{pR[1]:.1f}")
    track = (f'<path d="{track_d}" fill="none" stroke="#ddd5c8" '
             f'stroke-width="{sw}" stroke-linecap="round"/>')

    # -- zone color --
    color = (
        "#ef4444" if v < 83 else
        "#f97316" if v < 92 else
        "#b8a99a" if v < 102 else
        "#4ade80" if v < 112 else
        "#16a34a"
    )

    # -- colored fill: clockwise from left to current position --
    fill = ""
    if frac > 0.01:
        if angle >= 90:
            # single arc: left → current (≤ 90° sweep, unambiguous)
            fill_d = (f"M{pL[0]:.1f},{pL[1]:.1f} "
                      f"A{r},{r} 0 0,1 {pA[0]:.1f},{pA[1]:.1f}")
        else:
            # two arcs: left → top → current
            fill_d = (f"M{pL[0]:.1f},{pL[1]:.1f} "
                      f"A{r},{r} 0 0,1 {pT[0]:.1f},{pT[1]:.1f} "
                      f"A{r},{r} 0 0,1 {pA[0]:.1f},{pA[1]:.1f}")
        fill = (f'<path d="{fill_d}" fill="none" stroke="{color}" '
                f'stroke-width="{sw}" stroke-linecap="round"/>')

    # -- needle --
    nr = math.radians(angle)
    tip_r = r - sw / 2 - 2
    nx, ny = cx + tip_r * math.cos(nr), cy - tip_r * math.sin(nr)
    needle = (
        f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{nx:.1f}" y2="{ny:.1f}" '
        f'stroke="#292524" stroke-width="1.5" stroke-linecap="round"/>'
        f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="#292524"/>'
        f'<circle cx="{cx}" cy="{cy}" r="2"   fill="#fafaf9"/>'
    )

    # -- labels --
    lr = r + 14
    labels = ""
    for deg, txt, anchor in ((180, "70", "end"), (90, "100", "middle"), (0, "130", "start")):
        lx, ly = pt(deg, lr)
        labels += (f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
                   f'dominant-baseline="middle" font-size="8" fill="#a8a29e">{txt}</text>')

    vb_h = int(cy + 8)
    return (f'<svg viewBox="0 0 200 {vb_h}" xmlns="http://www.w3.org/2000/svg" '
            f'width="100%" style="max-width:220px;display:block;margin:0 auto;">'
            f'{track}{fill}{needle}{labels}</svg>')


def build_scale_rows_html(iep_now):
    rows_def = [
        ("> 110", "#16a34a", "pos", "+10 pts vs. baseline", iep_now > 110),
        ("90-110", "#64748b", "neu", "±10 pts vs. baseline", 90 <= iep_now <= 110),
        ("< 90",  "#dc2626", "neg", "-10 pts vs. baseline", iep_now < 90),
    ]
    out = []
    for (disp, color, rid, label, current) in rows_def:
        cls = ' current' if current else ''
        badge = "<span class='scale-now'>AHORA</span>" if current else ""
        out.append(
            f'<div class="scale-row{cls}" id="scale-row-{rid}">'
            f'<div class="scale-dot" style="background:{color}"></div>'
            f'<div class="scale-range" style="color:{color}">{disp}</div>'
            f'<div class="scale-label">{label}</div>'
            f'{badge}</div>'
        )
    return "\n".join(out)


def build_baseline_options():
    return "\n".join(
        f'<option value="{p["value"]}">{p["label"]}</option>'
        for p in BASELINE_PRESETS
    )


def load_data():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            """SELECT fecha, iep_total, iep_ajustado
               FROM iep_diario
               WHERE iep_total IS NOT NULL AND fecha >= '2023-12-10'
               ORDER BY fecha""",
            conn, parse_dates=["fecha"],
        )
    except Exception:
        df = pd.read_sql_query(
            "SELECT fecha, iep_total FROM iep_diario WHERE iep_total IS NOT NULL AND fecha >= '2023-12-10' ORDER BY fecha",
            conn, parse_dates=["fecha"],
        )
        df["iep_ajustado"] = None
    conn.close()
    df["smooth"] = df["iep_total"].rolling(5, center=True).mean()
    return [
        {
            "d": row["fecha"].strftime("%Y-%m-%d"),
            "v": round(row["iep_total"], 2),
            "s": round(row["smooth"], 2) if pd.notna(row["smooth"]) else None,
            "a": round(row["iep_ajustado"], 2) if pd.notna(row["iep_ajustado"]) else None,
        }
        for _, row in df.iterrows()
    ]


# ── Build ──────────────────────────────────────────────────────────────────────

def build_html(data, utdt_data, capa_signals):
    iep_now  = data[-1]["v"]
    date_now = data[-1]["d"]
    diff     = iep_now - 100.0

    # MoM: compare vs value ~30 calendar days ago (closest available)
    from datetime import date as _date, timedelta
    target_mom = _date.fromisoformat(date_now) - timedelta(days=30)
    mom_entry  = min(data, key=lambda r: abs((_date.fromisoformat(r["d"]) - target_mom).days))
    mom_diff   = iep_now - mom_entry["v"]

    data_json   = json.dumps(data)
    events_json = json.dumps(EVENTS_RICH, ensure_ascii=False)
    utdt_json   = json.dumps(utdt_data)
    comp_json   = build_comparativa_data()

    c1 = get_capa_signal(capa_signals["capa1"])
    c2 = get_capa_signal(capa_signals["capa2"])
    c3 = get_capa_signal(capa_signals["capa3"])

    page = (
        "<!DOCTYPE html>\n<html lang='es'>\n<head>\n"
        "<meta charset='UTF-8'>\n"
        "<meta name='viewport' content='width=device-width,initial-scale=1.0'>\n"
        "<title>IRPM — Índice de Riesgo Político de Mercado</title>\n"
        "<link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Lora:ital,wght@0,400;0,600;1,400;1,600&display=swap' rel='stylesheet'>\n"
        "<script src='https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js'></script>\n"
        "<script src='https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js'></script>\n"
        "<style>\n" + css() + "\n</style>\n"
        "</head>\n<body>\n<div id=\"page-wrap\">\n"
        + html_body() + "\n"
        "</div>\n<script>\n" + javascript() + "\n</script>\n"
        "</body>\n</html>"
    )

    page = (page
        .replace("__DATA__",         data_json)
        .replace("__UTDT_DATA__",    utdt_json)
        .replace("__EVENTS__",       events_json)
        .replace("__IEP_NOW__",      f"{iep_now:.1f}")
        .replace("__DATE_NOW__",     date_now)
        .replace("__HEADLINE__",     get_headline(iep_now))
        .replace("__DIFF_ARROW__",   "↑" if diff >= 0 else "↓")
        .replace("__DIFF_SIGN__",    "+" if diff >= 0 else "")
        .replace("__DIFF_ABS__",     f"{abs(diff):.1f}")
        .replace("__DIFF_COLOR__",   "#15803d" if diff >= 0 else "#dc2626")
        .replace("__DIFF_BG__",      "#f0fdf4" if diff >= 0 else "#fef2f2")
        .replace("__DIFF_BORDER__",  "#bbf7d0" if diff >= 0 else "#fecaca")
        .replace("__CAPA1_CLS__",    c1["cls"])
        .replace("__CAPA1_LABEL__",  c1["label"])
        .replace("__CAPA2_CLS__",    c2["cls"])
        .replace("__CAPA2_LABEL__",  c2["label"])
        .replace("__CAPA3_CLS__",    c3["cls"])
        .replace("__CAPA3_LABEL__",  c3["label"])
        .replace("__MOM_ARROW__",    "↑" if mom_diff >= 0 else "↓")
        .replace("__MOM_SIGN__",     "+" if mom_diff >= 0 else "")
        .replace("__MOM_ABS__",      f"{abs(mom_diff):.1f}")
        .replace("__MOM_COLOR__",    "#15803d" if mom_diff >= 0 else "#dc2626")
        .replace("__MOM_BG__",       "#f0fdf4" if mom_diff >= 0 else "#fef2f2")
        .replace("__MOM_BORDER__",   "#bbf7d0" if mom_diff >= 0 else "#fecaca")
        .replace("__GAUGE_SVG__",    build_gauge_svg(iep_now))
        .replace("__COMP_DATA__",    comp_json)
    )
    return page


# ── CSS ────────────────────────────────────────────────────────────────────────


def main():
    print("generate_dashboard.py | IRPM Argentina")
    data      = load_data()
    utdt_data = load_utdt_data()
    capa_sigs = load_capa_signals()

    html = build_html(data, utdt_data, capa_sigs)

    for dest in [OUTPUT, DOCS_OUTPUT]:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8", newline="\n")
        print(f"  -> {dest}")

    source_revision = os.environ.get("IRPM_SOURCE_REVISION")
    if not source_revision:
        try:
            source_revision = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            source_revision = "unknown"
    manifest = {
        "schema_version": 1,
        "dashboard_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "latest_data_date": data[-1]["d"],
        "source_revision": source_revision,
    }
    DEPLOY_MANIFEST_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DEPLOY_MANIFEST_OUTPUT.write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"  -> {DEPLOY_MANIFEST_OUTPUT}")

    print(f"Valor actual: {data[-1]['v']:.1f}")
    print(f"Ruedas: {len(data)}")
    print(f"Capas: {capa_sigs}")


if __name__ == "__main__":
    main()
