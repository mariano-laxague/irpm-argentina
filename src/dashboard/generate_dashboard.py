"""
generate_dashboard.py — IRPM Argentina
Diseño: página única scrollable — fondo crema (#faf7f2), Lora serif, acento terracotta (#b45309)
Uso: python src/dashboard/generate_dashboard.py
"""

import calendar
import json
import os
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = Path(os.environ.get("IRPM_DB_PATH", ROOT / "data" / "iep.db"))
OUTPUT = Path(os.environ.get("IRPM_DASHBOARD_OUTPUT", ROOT / "outputs" / "dashboard.html"))
DOCS_OUTPUT = Path(os.environ.get("IRPM_DASHBOARD_DOCS_OUTPUT", ROOT / "docs" / "index.html"))

UTDT_ICG_PATH = ROOT / "data" / "utdt_icg.csv"
UTDT_ICC_PATH = ROOT / "data" / "utdt_icc.csv"
REM_CSV_PATH  = ROOT / "data" / "rem.csv"
REM_ICM_PATH  = ROOT / "data" / "rem_icm.csv"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.dashboard.templates import css, html_body, javascript


EVENTS_RICH = [
    {
        "n": 1, "date": "2024-04-08", "tag": "Abr 2024",
        "title": "Peak del honeymoon",
        "impact": "positive",
        "body": "Primer pico del período de honeymoon (~111 pts). En la misma etapa se observaron superávit primario, desaceleración de la inflación mensual, compresión de la brecha cambiaria y una caída marcada del EMBI respecto del inicio de la gestión. La coincidencia es consistente con una mejora de las condiciones financieras observadas, pero el IRPM no identifica por sí solo su causa ni mide viabilidad política.",
    },
    {
        "n": 2, "date": "2024-12-09", "tag": "Dic 2024",
        "title": "Máximo histórico",
        "impact": "positive",
        "body": "El IRPM alcanza su nivel más alto de la serie disponible (~115 pts). El período coincide con superávit fiscal primario, inflación mensual más baja que al inicio de la gestión, acumulación de reservas y condiciones globales relativamente favorables. Es una lectura editorial de contexto: el índice registra señales financieras estandarizadas y no estima convicción ni continuidad política.",
    },
    {
        "n": 3, "date": "2025-09-12", "tag": "Sep 2025",
        "title": "Mínimo histórico",
        "impact": "negative",
        "body": "El IRPM toca su mínimo de la serie disponible (~70 pts), unos 30 puntos por debajo del baseline, semanas antes de las legislativas. En esa ventana aumentaron el EMBI y la brecha MEP, mientras cedieron los bonos soberanos. La proximidad electoral es un contexto plausible, no una atribución causal demostrada por el índice.",
    },
    {
        "n": 4, "date": "2025-11-03", "tag": "Oct-Nov 2025",
        "title": "Legislativas 2025",
        "impact": "positive",
        "body": "Después de las legislativas del 26 de octubre, el IRPM recupera terreno (~97 pts). En la misma ventana se observa compresión del EMBI, estabilización del MEP y recuperación de bonos. El movimiento es temporalmente compatible con una reacción al resultado, aunque esta visualización no separa ese efecto de otros factores concurrentes.",
    },
    {
        "n": 5, "date": "2024-08-06", "tag": "Ago 2024",
        "title": "Corrección post-honeymoon",
        "impact": "negative",
        "body": "Primer valle significativo desde el inicio de la gestión (~95 pts). Coincide con una corrección global de activos de riesgo alrededor del 5 de agosto y con señales domésticas menos favorables, entre ellas una menor acumulación de reservas y tensiones cambiarias. Son factores contemporáneos posibles; el diseño actual no permite descomponer cuánto explica cada uno.",
    },
    {
        "n": 6, "date": "2025-04-08", "tag": "Abr 2025",
        "title": "Doble shock: tarifas Trump + tensión cambiaria",
        "impact": "negative",
        "body": "El IRPM cae a ~91 pts en una ventana que combina dos cambios relevantes. En el frente global, el anuncio arancelario de Estados Unidos del 2 de abril coincide con una venta de activos de riesgo. En el frente local, Argentina transita hacia un esquema de bandas cambiarias. La concurrencia dificulta atribuir el movimiento a una sola causa.",
    },
    {
        "n": 7, "date": "2025-06-04", "tag": "Jun 2025",
        "title": "Recuperación: acuerdo FMI + convergencia electoral",
        "impact": "positive",
        "body": "El IRPM sube a ~107 pts antes del período de mayor tensión preelectoral. La recuperación coincide con el nuevo acuerdo con el FMI, mejora de reservas, menor inflación y señales de cohesión oficialista. El acuerdo es una explicación plausible del contexto, pero el índice no permite identificarlo como driver principal ni cuantificar expectativas electorales.",
    },
    {
        "n": 8, "date": "2026-04-17", "tag": "Abr 2026",
        "title": "Pax política: el riesgo alternativo comprime",
        "impact": "positive",
        "body": "Nuevo pico local (~105 pts), unos 35 puntos por encima del mínimo preelectoral de septiembre de 2025. La lectura editorial lo ubica en un período de menor tensión política visible y oposición fragmentada. El IRPM no observa candidaturas, probabilidades electorales ni distribuciones de escenarios post-2027; esas interpretaciones requieren evidencia externa.",
    },
    {
        "n": 9, "date": "2026-08-01", "tag": "Ago 2026",
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

    print(f"Valor actual: {data[-1]['v']:.1f}")
    print(f"Ruedas: {len(data)}")
    print(f"Capas: {capa_sigs}")


if __name__ == "__main__":
    main()
