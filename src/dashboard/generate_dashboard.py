"""
generate_dashboard.py — IRPM Argentina
Diseño: página única scrollable — fondo crema (#faf7f2), Lora serif, acento terracotta (#b45309)
Uso: python src/dashboard/generate_dashboard.py
"""

import calendar
import json
import sqlite3
from pathlib import Path

import pandas as pd

ROOT    = Path(__file__).parent.parent.parent
DB_PATH = ROOT / "data" / "iep.db"
OUTPUT      = ROOT / "outputs" / "dashboard.html"
DOCS_OUTPUT = ROOT / "docs" / "index.html"

UTDT_ICG_PATH = ROOT / "data" / "utdt_icg.csv"
UTDT_ICC_PATH = ROOT / "data" / "utdt_icc.csv"
REM_CSV_PATH  = ROOT / "data" / "rem.csv"
REM_ICM_PATH  = ROOT / "data" / "rem_icm.csv"


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
            "SELECT capa1, capa2, capa3 FROM iep_diario WHERE capa1 IS NOT NULL ORDER BY fecha DESC LIMIT 1",
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
        "<style>\n" + _css() + "\n</style>\n"
        "</head>\n<body>\n<div id=\"page-wrap\">\n"
        + _html_body() + "\n"
        "</div>\n<script>\n" + _js() + "\n</script>\n"
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

def _css():
    return """
/* === RESET & BASE === */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  height: 100%;
  margin: 0; padding: 0;
  overflow: hidden;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  color: #1c1917;
  -webkit-font-smoothing: antialiased;
  background: #fff;
}
#page-wrap {
  max-width: 1180px;
  margin: 0 auto;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #faf7f2;
  border-left: 1px solid #e8e0d5;
  border-right: 1px solid #e8e0d5;
}
#slides-container {
  flex: 1;
  overflow-y: scroll;
  scroll-snap-type: y mandatory;
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
}
.slide {
  height: 100%;
  scroll-snap-align: start;
  overflow: hidden;
  position: relative;
}

/* === NAV === */
.site-nav {
  flex-shrink: 0;
  position: relative;
  z-index: 100;
  background: #1c1917;
  border-bottom: 1px solid #292524;
  padding: 0 32px; height: 54px;
  display: flex; align-items: center; justify-content: space-between;
}
.nav-brand {
  font-family: 'Lora', Georgia, serif;
  font-size: 18px; font-weight: 600; color: #faf7f2;
  text-decoration: none; letter-spacing: -0.01em;
  display: flex; flex-direction: column; line-height: 1;
  gap: 3px;
}
.nav-brand b { color: #e8a455; }
.nav-brand-sub {
  font-family: 'Inter', sans-serif;
  font-size: 9px; font-weight: 500; letter-spacing: 0.04em;
  color: #78716c; text-transform: uppercase; line-height: 1;
}
.nav-links { display: flex; gap: 24px; align-items: center; }
.nav-links a { font-size: 13px; color: #a8a29e; text-decoration: none; font-weight: 500; }
.nav-links a:hover { color: #faf7f2; }
.nav-cta {
  font-size: 12px; font-weight: 600;
  padding: 7px 16px; border-radius: 20px;
  background: transparent; color: #e8a455 !important;
  border: 1px solid #e8a455;
}
.nav-cta:hover { background: rgba(232,164,85,0.1); }

/* === WHAT SECTION === */
.what-section {
  padding: 0;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.what-card-header {
  margin-bottom: 28px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e8e0d5;
}
.what-card {
  background: #fff;
  border-radius: 16px;
  border: 1px solid #e8e0d5;
  padding: 48px 52px;
  margin: 24px 32px;
  width: 100%;
  box-sizing: border-box;
}
.what-inner {
  max-width: 100%;
  margin: 0;
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 48px;
  align-items: start;
}
.what-left {
  display: flex; flex-direction: column; align-items: center; text-align: center;
}
.what-eyebrow {
  font-size: 11px; font-weight: 700; letter-spacing: 0.12em;
  text-transform: uppercase; color: #b45309; margin-bottom: 20px;
  display: flex; align-items: center; gap: 8px;
}
.what-eyebrow::before {
  content: '';
  display: block; width: 24px; height: 1px; background: #b45309;
}
.what-title {
  font-family: 'Lora', Georgia, serif;
  font-size: 32px; font-weight: 400; line-height: 1.25;
  color: #1c1917; margin-bottom: 0;
  font-style: italic;
}
.what-title strong { font-style: normal; font-weight: 700; color: #b45309; }
.what-right {}
.what-text {
  font-size: 15px; line-height: 1.8; color: #44403c;
  margin-bottom: 20px;
}
.what-text em { font-style: normal; color: #b45309; font-weight: 600; }
.what-text p { margin-bottom: 14px; }
.what-text p:last-child { margin-bottom: 0; }
.what-divider {
  width: 32px; height: 2px; background: #e8e0d5;
  margin: 20px 0;
}
.what-name-exp {
  font-size: 12px; color: #78716c; line-height: 1.75;
}
.what-name-exp strong { color: #44403c; }
.what-pills {
  display: flex; flex-direction: column; gap: 10px;
  margin-top: 24px;
}
.what-pill {
  font-size: 12px; color: #57534e;
  display: flex; align-items: center; gap: 10px;
  line-height: 1.4;
}
.what-pill::before {
  content: '';
  display: block;
  width: 4px; height: 4px;
  border-radius: 50%;
  background: #b45309;
  flex-shrink: 0;
}
.what-live-label-top {
  font-size: 10px; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: #a8a29e; margin-bottom: 10px;
}
.what-live-num {
  font-family: 'Lora', Georgia, serif;
  font-size: 80px; font-weight: 700; line-height: 1;
  letter-spacing: -0.03em; color: #1c1917;
  margin-bottom: 12px;
}
.what-live-meta {
  display: flex; flex-direction: column; gap: 6px; margin-bottom: 20px;
}
.what-mom-badge {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 12px; font-weight: 600;
  padding: 5px 12px; border-radius: 20px; border: 1px solid;
  width: fit-content;
}
.what-update-date {
  font-size: 11px; color: #a8a29e;
}
.what-gauge-labels {
  display: flex; justify-content: space-between;
  font-size: 9px; color: #a8a29e; margin-top: 4px;
}

/* === CONTENT CARD === */
.content-card {
  background: #fff;
  border: 1px solid #e8e0d5;
  border-radius: 12px;
  padding: 28px 32px;
}

/* === HERO SECTION === */
.hero-section {
  min-height: calc(92vh - 56px);
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 60px 40px 40px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}
.hero-kicker {
  font-size: 11px; font-weight: 600; letter-spacing: 0.1em;
  text-transform: uppercase; color: #78716c;
  margin-bottom: 28px; display: flex; align-items: center; gap: 7px;
}
.live-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #22c55e; display: inline-block;
  animation: blink 2s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
.hero-num-label {
  font-size: 12px; font-weight: 600; letter-spacing: 0.1em;
  text-transform: uppercase; color: #a8a29e; margin-bottom: 8px;
}
.hero-num {
  font-family: 'Lora', Georgia, serif;
  font-size: 120px; font-weight: 700; line-height: 0.9;
  letter-spacing: -0.04em; color: #1c1917;
  margin-bottom: 20px;
}
.hero-headline {
  font-family: 'Lora', Georgia, serif;
  font-size: 22px; font-weight: 400; line-height: 1.4;
  color: #57534e; margin-bottom: 24px; max-width: 600px;
  font-style: italic;
}
.hero-headline em { font-style: normal; color: #b45309; font-weight: 600; }
.hero-meta-row {
  display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
  margin-bottom: 48px;
}
.hero-diff {
  font-size: 13px; font-weight: 600;
  padding: 6px 14px; border-radius: 20px;
  border: 1px solid; display: inline-flex; align-items: center; gap: 4px;
}
.hero-num-sub { font-size: 12px; color: #a8a29e; }
.hero-scroll-hint {
  margin-top: auto;
  padding-top: 32px;
  font-size: 11px; color: #a8a29e;
  letter-spacing: 0.06em; text-transform: uppercase;
  display: flex; align-items: center; gap: 8px;
}
.hero-scroll-hint::after {
  content: '';
  display: block; width: 1px; height: 32px;
  background: linear-gradient(to bottom, #a8a29e, transparent);
}

/* === GAUGE === */
.what-mini-gauge {
  margin-top: 12px;
}
.gauge-bar-wrap { position: relative; margin-bottom: 8px; }
.gauge-bar {
  height: 4px; border-radius: 5px;
  background: linear-gradient(to right,
    #ef4444 0%, #ef4444 17%,
    #f97316 17%, #f97316 33%,
    #d6cfc4 33%, #d6cfc4 58%,
    #86efac 58%, #86efac 75%,
    #16a34a 75%);
}
.gauge-needle {
  position: absolute; top: -5px;
  width: 3px; height: 14px;
  background: #1c1917; border-radius: 2px;
  transform: translateX(-50%);
  transition: left 0.6s cubic-bezier(.34,1.56,.64,1);
}
.gauge-needle::before {
  content: '';
  position: absolute; top: -5px; left: 50%;
  transform: translateX(-50%);
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-bottom: 5px solid #1c1917;
}
/* === SECTION DIVIDER === */
.section-divider { border: none; border-top: 1px solid #e8e0d5; }

/* === BASIS SECTION === */
.basis-section {
  background: #f5f0e8;
  border-top: 1px solid #e8e0d5;
  border-bottom: 1px solid #e8e0d5;
  padding: 48px 32px;
}
.basis-inner { max-width: 760px; margin: 0 auto; }
.section-eyebrow {
  font-size: 11px; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: #a8a29e; margin-bottom: 8px;
}
.section-title {
  font-family: 'Lora', Georgia, serif;
  font-size: 22px; font-weight: 600; color: #1c1917;
  letter-spacing: -0.01em; margin-bottom: 6px;
}
.section-sub { font-size: 13px; color: #78716c; margin-bottom: 12px; }
.basis-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; }
.basis-card {
  background: #fff;
  border: 1px solid #e8e0d5;
  border-radius: 10px;
  padding: 18px;
}
.basis-card-top {
  display: flex; align-items: center;
  justify-content: space-between; margin-bottom: 10px;
}
.basis-card-name { font-size: 13px; font-weight: 700; color: #1c1917; }
.basis-card-pct {
  font-size: 11px; font-weight: 700;
  color: #b45309; background: #fef3c7;
  border: 1px solid #fde68a; padding: 2px 8px; border-radius: 3px;
}
.basis-card-q {
  font-family: 'Lora', Georgia, serif;
  font-size: 13px; font-style: italic;
  color: #57534e; line-height: 1.55; margin-bottom: 10px;
}
.sig-badge {
  font-size: 11px; font-weight: 600;
  padding: 3px 9px; border-radius: 4px; display: inline-block;
}
.sig-pos { color: #15803d; background: #f0fdf4; border: 1px solid #bbf7d0; }
.sig-neu { color: #57534e; background: #f5f0e8; border: 1px solid #e8e0d5; }
.sig-neg { color: #b91c1c; background: #fef2f2; border: 1px solid #fecaca; }

/* === CHART SECTION === */
.chart-section {
  padding: 0 40px 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: hidden;
}
.chart-wrap { position: relative; min-height: 0; }

/* === CHART HEADER === */
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 20px 0 12px;
  flex-shrink: 0;
}
.chart-hint-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #a8a29e;
  font-style: italic;
}
.hint-dot-icon {
  font-size: 14px;
  color: #b45309;
}

/* === EVENTS NAV STRIP (removed) === */
.event-chip-pos { border-left: 2px solid #15803d; }
.event-chip-neg { border-left: 2px solid #b91c1c; }

/* === EVENT DETAIL PANEL === */
.events-detail-panel {
  flex-shrink: 0;
  background: #fff;
  border: 1px solid #e8e0d5;
  border-radius: 8px;
  padding: 12px 16px;
  display: none;
  grid-template-columns: 1fr auto;
  gap: 4px 16px;
  align-items: start;
}
.events-detail-panel.visible { display: grid; }
.events-detail-tag {
  font-size: 10px; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: #b45309;
  grid-column: 1;
}
.events-detail-title {
  font-size: 13px; font-weight: 700; color: #1c1917;
  grid-column: 1; margin-bottom: 4px;
}
.events-detail-text {
  font-size: 11px; color: #57534e; line-height: 1.6;
  grid-column: 1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
#event-card-impact { grid-column: 1; }
.event-card-impact {
  font-size: 11px;
  font-weight: 600;
}
.event-card-impact.impact-pos { color: #15803d; }
.event-card-impact.impact-neg { color: #b91c1c; }
.event-card-impact.impact-neu { color: #78716c; }

/* === RANGE SELECTOR === */
.range-selector-wrap {
  margin: 12px 0 20px;
  padding: 0 4px;
}
.range-track {
  position: relative;
  height: 6px;
  background: #e8e0d5;
  border-radius: 3px;
  margin-bottom: 8px;
  cursor: pointer;
}
.range-fill {
  position: absolute;
  top: 0; bottom: 0;
  background: #b45309;
  border-radius: 3px;
  opacity: 0.3;
  pointer-events: none;
}
.range-handle {
  position: absolute;
  top: 50%;
  width: 16px; height: 16px;
  background: #fff;
  border: 2px solid #b45309;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  cursor: grab;
  transition: box-shadow .12s;
  z-index: 2;
}
.range-handle:hover, .range-handle.dragging {
  box-shadow: 0 0 0 4px rgba(180,83,9,0.15);
  cursor: grabbing;
}
.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #a8a29e;
}
.impact-pos { color: #15803d; }
.impact-neg { color: #b91c1c; }

/* read-guide removed — replaced by chart-hint-bar */

/* === DIVERGENCE SECTION (mirrors .chart-section) === */
.div-section {
  padding: 0 40px 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: hidden;
}
.div-chart-wrap { position: relative; flex: 1; min-height: 0; }
.div-legend {
  display: flex; gap: 20px; flex-wrap: wrap;
  flex-shrink: 0; margin-bottom: 8px;
}
.div-leg-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #78716c; }
.div-leg-dot { width: 28px; height: 3px; border-radius: 2px; }
.corr-tooltip {
  position: absolute; pointer-events: none; z-index: 200; width: 220px;
  background: #fff; border: 1px solid #e8e0d5; border-radius: 8px;
  padding: 11px 13px; box-shadow: 0 6px 24px rgba(0,0,0,0.08); display: none;
}
.corr-tip-title { font-size: 11px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 5px; }
.corr-tip-body { font-size: 12px; color: #57534e; line-height: 1.55; }
/* div-strip below chart (compact) */
.div-strip-bar {
  flex-shrink: 0;
  display: none;
  background: #fff;
  border: 1px solid #e8e0d5;
  border-radius: 8px;
  padding: 10px 14px;
  margin-top: 8px;
  font-size: 12px;
}
.div-strip-bar.visible { display: flex; align-items: center; gap: 12px; }
.div-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.div-label { font-size: 11px; font-weight: 600; color: #1c1917; }
.div-period { font-size: 10px; color: #a8a29e; }
.div-vals { font-size: 10px; color: #78716c; }
.div-gap { font-size: 11px; font-weight: 600; }

/* === COMPARATIVA SECTION (mirrors .chart-section) === */
.comp-section {
  padding: 0 40px 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  overflow: hidden;
}
.comp-chart-wrap { position: relative; flex: 1; min-height: 0; }
.comp-legend {
  display: flex; gap: 24px; flex-wrap: wrap;
  flex-shrink: 0; margin-bottom: 8px;
}
.comp-leg-item { display: flex; align-items: center; gap: 7px; font-size: 12px; color: #78716c; }
.comp-leg-dot { width: 28px; height: 3px; border-radius: 2px; }
.comp-note {
  flex-shrink: 0; font-size: 11px; color: #a8a29e;
  margin-top: 6px; font-style: italic;
}

/* === METHODOLOGY SECTION === */
.met-section {
  padding: 40px;
  display: flex;
  align-items: center;
}
.met-inner {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;
  align-items: start;
  width: 100%;
}

.formula-box {
  background: #1c1917; color: #f5f0e8;
  border-radius: 10px; padding: 20px;
  font-family: 'Courier New', monospace;
  font-size: 13px; line-height: 1.8; margin-bottom: 20px;
}
.formula-main { font-size: 14px; margin-bottom: 10px; }
.formula-comment { color: #78716c; font-size: 12px; }
.met-text { font-size: 14px; color: #57534e; line-height: 1.75; }
.met-text p { margin-bottom: 12px; }
.met-text a { color: #b45309; }

/* === NEWSLETTER === */
.nl-section { background: #1c1917; padding: 56px 32px; text-align: center; }
.nl-tag { font-size: 11px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #57534e; margin-bottom: 12px; }
.nl-hed {
  font-family: 'Lora', Georgia, serif;
  font-size: 26px; font-weight: 600; color: #faf7f2;
  line-height: 1.3; margin-bottom: 10px;
}
.nl-sub { font-size: 14px; color: #57534e; line-height: 1.6; margin-bottom: 24px; max-width: 380px; margin-left: auto; margin-right: auto; }
.nl-link {
  display: inline-block; font-size: 14px; font-weight: 600;
  padding: 11px 28px; background: #b45309; color: #fff;
  border-radius: 8px; text-decoration: none;
}
.nl-link:hover { background: #92400e; }
.nl-note { font-size: 11px; color: #44403c; margin-top: 12px; }

/* === FOOTER === */
.site-footer {
  border-top: 1px solid #e8e0d5; padding: 20px 32px;
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 12px; background: #faf7f2;
}
.footer-left { font-size: 13px; color: #78716c; }
.footer-left strong { color: #1c1917; }
.footer-right { display: flex; gap: 20px; font-size: 12px; }
.footer-right a { color: #a8a29e; text-decoration: none; }
.footer-right a:hover { color: #b45309; }
"""


# ── HTML body ──────────────────────────────────────────────────────────────────

def _html_body():
    return """
<nav class="site-nav">
  <a href="#" class="nav-brand">
    <span>IRPM<b>.</b></span>
    <span class="nav-brand-sub">&#205;ndice de Riesgo Pol&#237;tico del Mercado</span>
  </a>
  <div class="nav-links">
    <a href="#evolucion">Evolución</a>
    <a href="#op">Mercado vs. OP</a>
    <a href="#metodologia">Metodología</a>
    <a href="https://elindice.substack.com" target="_blank" class="nav-cta">Newsletter &#8594;</a>
  </div>
</nav>
<div id="slides-container">
<section class="what-section slide">
  <div class="what-card">
    <div class="what-card-header">
      <div class="what-eyebrow">&#191;Qué es el IRPM?</div>
      <h2 class="what-title">Señales de mercado para leer <strong>el contexto argentino</strong></h2>
    </div>
    <div class="what-inner">
      <div class="what-left">
        <div class="what-live-label-top">IRPM · Base 100 = dic 2023</div>
        <div class="what-live-num" id="what-live-num">__IEP_NOW__</div>
        <div class="what-live-meta">
          <span class="what-mom-badge" style="color:__MOM_COLOR__;background:__MOM_BG__;border-color:__MOM_BORDER__;">
            __MOM_ARROW__ __MOM_SIGN____MOM_ABS__ pts vs. mes anterior
          </span>
          <span class="what-update-date">Actualizado __DATE_NOW__</span>
        </div>
        __GAUGE_SVG__
      </div>
      <div class="what-right">
        <div class="what-text">
          <p>
            El IRPM es un índice experimental que sintetiza condiciones de mercado a partir de señales financieras
            sensibles al escenario político y económico argentino.
          </p>
          <p>
            No es una probabilidad electoral ni identifica causalidad política. Las explicaciones de hitos son lecturas
            editoriales que deben considerarse junto con factores macroeconómicos locales y globales.
          </p>
        </div>
        <div class="what-pills">
          <span class="what-pill">Complementa las encuestas de opinión pública</span>
          <span class="what-pill">Representa activos observados, no a la sociedad</span>
          <span class="what-pill">Con el ojo puesto en 2027</span>
        </div>
      </div>
    </div>
  </div>
</section>



<section class="chart-section slide" id="evolucion">
  <div class="chart-header">
    <div>
      <div class="section-eyebrow">Evolución histórica</div>
      <div class="section-title">Condiciones de mercado en el tiempo</div>
    </div>
    <div class="chart-hint-bar">
      <span class="hint-dot-icon">⬦</span>
      <span>Hacé clic en los puntos de la barra inferior para ver el detalle de cada hito</span>
    </div>
  </div>

  <!-- RANGE SELECTOR (zoom — above chart) -->
  <div class="range-selector-wrap">
    <div class="range-track" id="range-track">
      <div class="range-fill" id="range-fill"></div>
      <div class="range-handle" id="range-handle-left" data-side="left"></div>
      <div class="range-handle" id="range-handle-right" data-side="right"></div>
    </div>
    <div class="range-labels" id="range-labels"></div>
  </div>

  <!-- CHART — dominant element -->
  <div class="chart-wrap" style="position:relative;flex:1;min-height:0;">
    <canvas id="iepChart"></canvas>
  </div>


  <!-- EVENT DETAIL PANEL (shown when a chip is selected) -->
  <div class="events-detail-panel" id="events-detail-panel">
    <div class="events-detail-tag" id="event-card-tag"></div>
    <div class="events-detail-title" id="event-card-title"></div>
    <div class="events-detail-text" id="event-card-text"></div>
    <div class="event-card-impact" id="event-card-impact"></div>
  </div>
</section>

<section class="div-section slide" id="op">
  <div class="chart-header">
    <div>
      <div class="section-eyebrow">Panel comparativo</div>
      <div class="section-title">Mercado vs. Opinión Pública</div>
    </div>
    <div class="chart-hint-bar">
      <span class="hint-dot-icon">⬦</span>
      <span>Las divergencias son descriptivas: no demuestran que una serie anticipe a la otra</span>
    </div>
  </div>
  <div class="div-legend">
    <span class="div-leg-item"><span class="div-leg-dot" style="background:#1c1917"></span>IRPM (mercado, diario &#8594; mensual)</span>
    <span class="div-leg-item"><span class="div-leg-dot" style="background:#b45309;border-top:2px dashed #b45309;background:transparent"></span>ICG-UTDT (aprobación gestión)</span>
  </div>
  <div class="div-chart-wrap">
    <canvas id="divChart"></canvas>
    <div class="corr-tooltip" id="corr-tooltip">
      <div class="corr-tip-title" id="corr-tip-title"></div>
      <div class="corr-tip-body" id="corr-tip-body"></div>
    </div>
  </div>
  <div class="div-strip-bar" id="div-strip-bar">
    <span class="div-dot" id="div-bar-dot" style="background:#15803d"></span>
    <span class="div-label" id="div-bar-label"></span>
    <span class="div-period" id="div-bar-period"></span>
    <span class="div-vals" id="div-bar-vals"></span>
    <span class="div-gap" id="div-bar-gap"></span>
  </div>
</section>

<section class="comp-section slide" id="comparativa">
  <div class="chart-header">
    <div>
      <div class="section-eyebrow">Comparativa histórica</div>
      <div class="section-title">Confianza de mercado por gestión</div>
    </div>
    <div class="chart-hint-bar">
      <span class="hint-dot-icon">⬦</span>
      <span>Proxy EMBI · todos arrancan en 100 el día 1 de gestión &mdash; las líneas verticales marcan las legislativas de medio término</span>
    </div>
  </div>
  <div class="comp-legend">
    <span class="comp-leg-item"><span class="comp-leg-dot" style="background:#6366f1"></span>Macri (dic 2015)</span>
    <span class="comp-leg-item"><span class="comp-leg-dot" style="background:#f97316"></span>Alberto (dic 2019)</span>
    <span class="comp-leg-item"><span class="comp-leg-dot" style="background:#1c1917"></span>Milei (dic 2023)</span>
  </div>
  <div class="comp-chart-wrap">
    <canvas id="compChart"></canvas>
  </div>
  <div class="comp-note">
    Proxy = 100 × (EMBI inicio de gestión / EMBI mes N). Mayor valor = mayor confianza del mercado en el programa político.
    Legislativas: Macri oct 2017 · Alberto nov 2021 · Milei oct 2025.
  </div>
</section>

<section class="met-section slide" id="metodologia">
  <div class="met-inner">
    <div class="met-left">
      <div class="section-eyebrow">Composición y metodología</div>
      <div class="section-title">&#191;En qué se basa el índice?</div>
      <div class="section-sub">Tres capas de señales ponderadas mediante una especificación experimental</div>
      <div class="basis-grid">
        <div class="basis-card">
          <div class="basis-card-top">
            <span class="basis-card-name">Mercado cambiario</span>
            <span class="basis-card-pct">35%</span>
          </div>
          <div class="basis-card-q">&#191;Cuánto paga el mercado para cubrirse del dólar?</div>
          <span class="sig-badge __CAPA1_CLS__">__CAPA1_LABEL__</span>
        </div>
        <div class="basis-card">
          <div class="basis-card-top">
            <span class="basis-card-name">Deuda soberana</span>
            <span class="basis-card-pct">40%</span>
          </div>
          <div class="basis-card-q">&#191;A qué precio están los bonos y qué descuentan para el futuro?</div>
          <span class="sig-badge __CAPA2_CLS__">__CAPA2_LABEL__</span>
        </div>
        <div class="basis-card">
          <div class="basis-card-top">
            <span class="basis-card-name">Volatilidad accionaria</span>
            <span class="basis-card-pct">25%</span>
          </div>
          <div class="basis-card-q">&#191;Qué tan nerviosas están las acciones argentinas?</div>
          <span class="sig-badge __CAPA3_CLS__">__CAPA3_LABEL__</span>
        </div>
      </div>
    </div>
    <div class="met-right">
      <div class="section-eyebrow">Construcción y evidencia</div>
      <div class="section-title">Metodología</div>
      <div class="section-sub">Para quienes quieren entender cómo se construye el índice</div>

      <div class="formula-box">
        <div class="formula-main">IRPM(t) = 100 + (0.35&#183;z&#8321; + 0.40&#183;z&#8322; + 0.25&#183;z&#8323; &#8722; z_baseline) &#215; 10</div>
        <div class="formula-comment">// Baseline = 11 dic 2023 &#8594; IRPM = 100</div>
        <div class="formula-comment">// z&#8321; = Mercado cambiario  (MEP + ROFEX) &#183; 35%</div>
        <div class="formula-comment">// z&#8322; = Deuda soberana (GD30, AL30, EMBI, law spread) &#183; 40%</div>
        <div class="formula-comment">// z&#8323; = Semi-vol realizada (YPFD/GGAL/PAMP/TECO2) &#183; 25%</div>
      </div>
      <div class="met-text">
        <p>Cada z-score mide cuántos desvíos estándar se aleja la señal de su media rolling de 252 ruedas. Los tres se combinan y se reescalan como distancia respecto de un baseline convencional.</p>
        <p>El EMBI (riesgo país) está incluido como uno de varios inputs de la capa de deuda soberana, no como el único indicador. Esto permite capturar divergencias: el riesgo país puede estar tranquilo mientras el mercado cambiario muestra presión, o viceversa.</p>
        <p>Una grilla de 14 combinaciones mostró estabilidad de las fechas extremas, con variaciones de magnitud de hasta ~5,5 puntos. Es evidencia de robustez acotada, no validación del constructo ni de pesos óptimos. <a href="metodologia_publica.md">Ver metodología experimental &#8594;</a></p>
      </div>
    </div>
  </div>
</section>
</div>

<footer class="site-footer">
  <div class="footer-left">Elaborado por <strong>Mariano Laxague</strong> &#183; <a href="https://elindice.substack.com" target="_blank" style="color:#b45309;text-decoration:none">El Índice</a></div>
  <div class="footer-right">
    <a href="#metodologia">Metodología</a>
    <a href="https://github.com/marianolaxague-crypto/irpm-argentina" target="_blank">GitHub</a>
    <a href="mailto:mariano.laxague@gmail.com">mariano.laxague@gmail.com</a>
    <a href="https://elindice.substack.com" target="_blank">Substack</a>
  </div>
</footer>
"""



# ── JavaScript ─────────────────────────────────────────────────────────────────

def _js():
    return r"""
const ALL_DATA    = __DATA__;
const UTDT_DATA   = __UTDT_DATA__;
const EVENTS_RICH = __EVENTS__;

let iepChart           = null;
let divChart           = null;
let currentZoom        = null;
let currentDivZoom     = null;
let showDots           = true;
let showSmooth         = true;
let showAdj            = false;
let currentBaseline    = null;
let currentGranularity = 'daily';
let selectedEvent      = null;
let popupCloseTimer    = null;

// ── Data helpers ───────────────────────────────────────────────────────────────
function findNearest(arr, dateStr) {
  const t = new Date(dateStr + 'T12:00:00').getTime();
  let best = arr[0], bestD = Infinity;
  for (const pt of arr) {
    const d = Math.abs(new Date(pt.d + 'T12:00:00').getTime() - t);
    if (d < bestD) { bestD = d; best = pt; }
  }
  return best;
}

function applyBaseline(data, baseDate) {
  const basePoint = data.find(d => d.d === baseDate) || findNearest(data, baseDate);
  const shift_v = basePoint.v - 100;
  const shift_a = basePoint.a != null ? basePoint.a - 100 : 0;
  return data.map(d => ({
    d: d.d,
    v: +(d.v - shift_v).toFixed(2),
    s: d.s !== null ? +(d.s - shift_v).toFixed(2) : null,
    a: d.a != null ? +(d.a - shift_a).toFixed(2) : null,
  }));
}

function applyGranularity(data, gran) {
  if (gran === 'daily') return data;
  const groups = {}, aGroups = {};
  data.forEach(d => {
    let key;
    if (gran === 'weekly') {
      const dt  = new Date(d.d);
      const day = dt.getDay() || 7;
      const mon = new Date(dt);
      mon.setDate(dt.getDate() - day + 1);
      key = mon.toISOString().slice(0, 10);
    } else {
      key = d.d.slice(0, 7) + '-01';
    }
    if (!groups[key]) groups[key] = [];
    groups[key].push(d.v);
    if (d.a != null) {
      if (!aGroups[key]) aGroups[key] = [];
      aGroups[key].push(d.a);
    }
  });
  const avg = arr => +(arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(2);
  return Object.entries(groups)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, vals]) => ({
      d: key, v: avg(vals), s: null,
      a: aGroups[key] ? avg(aGroups[key]) : null,
    }));
}

function applyZoom(data, months) {
  if (months === null) return data;
  let cutoff;
  if (months === 'milei') {
    cutoff = '2023-12-11';
  } else if (months === 0) {
    cutoff = new Date().getFullYear() + '-01-01';
  } else {
    const dt = new Date();
    dt.setMonth(dt.getMonth() - months);
    cutoff = dt.toISOString().slice(0, 10);
  }
  return data.filter(d => d.d >= cutoff);
}

function reanchorToBaseline(data, baseDate, gran) {
  if (gran === 'daily' || !data.length) return data;
  let baseKey;
  if (gran === 'monthly') {
    baseKey = baseDate.slice(0, 7) + '-01';
  } else {
    const dt  = new Date(baseDate + 'T12:00:00');
    const day = dt.getDay() || 7;
    const mon = new Date(dt);
    mon.setDate(dt.getDate() - day + 1);
    baseKey = mon.toISOString().slice(0, 10);
  }
  const basePt = data.find(d => d.d === baseKey);
  if (!basePt) return data;
  const sv = basePt.v - 100;
  const sa = basePt.a != null ? basePt.a - 100 : 0;
  return data.map(d => ({
    d: d.d,
    v: +(d.v - sv).toFixed(2),
    s: d.s != null ? +(d.s - sv).toFixed(2) : null,
    a: d.a != null ? +(d.a - sa).toFixed(2) : null,
  }));
}

function getDisplayData() {
  const gran = currentGranularity;
  const base = currentBaseline || '2023-12-11';
  const data = applyGranularity(applyZoom(applyBaseline(ALL_DATA, base), currentZoom), gran);
  return reanchorToBaseline(data, base, gran);
}

// ── Zone & headline helpers ────────────────────────────────────────────────────
function getZone(v) {
  if (v >= 110) return { label: '>10 pts sobre baseline', color: '#15803d', bg: '#f0fdf4', border: '#bbf7d0' };
  if (v >= 100) return { label: 'Sobre baseline · 100-110', color: '#b45309', bg: '#fef3c7', border: '#fde68a' };
  if (v >= 90)  return { label: 'Bajo baseline · 90-100', color: '#d97706', bg: '#fffbeb', border: '#fde68a' };
  return { label: '>10 pts bajo baseline', color: '#dc2626', bg: '#fef2f2', border: '#fecaca' };
}

function getHeadline(v) {
  if (v > 110) return 'El compuesto se ubica <em>más de 10 puntos sobre el baseline</em>';
  if (v >= 100) return 'El compuesto se ubica <em>por encima del baseline</em>';
  if (v >= 90)  return 'El compuesto se ubica <em>por debajo del baseline</em>';
  return 'El compuesto se ubica <em>más de 10 puntos debajo del baseline</em>';
}

function getIEPAtDate(dateStr) {
  const adj = applyBaseline(ALL_DATA, currentBaseline || '2023-12-11');
  const pt  = findNearest(adj, dateStr);
  return pt.v;
}

// ── Hero update ───────────────────────────────────────────────────────────────
function updateHero() {
  const last = ALL_DATA[ALL_DATA.length - 1];
  const v    = last.v;
  const diff = v - 100;
  const pct  = Math.max(0, Math.min(100, (v - 70) / 60 * 100));

  const valEl = document.getElementById('hero-value');
  if (valEl) valEl.textContent = v.toFixed(1);

  const hlEl = document.getElementById('hero-headline');
  if (hlEl) hlEl.innerHTML = getHeadline(v);

  const diffEl = document.getElementById('hero-diff');
  if (diffEl) {
    const arrow = diff >= 0 ? '↑' : '↓';
    const sign  = diff >= 0 ? '+' : '';
    diffEl.innerHTML = arrow + ' ' + sign + diff.toFixed(1) + ' pts vs. baseline';
    diffEl.style.color       = diff >= 0 ? '#15803d' : '#dc2626';
    diffEl.style.background  = diff >= 0 ? '#f0fdf4' : '#fef2f2';
    diffEl.style.borderColor = diff >= 0 ? '#bbf7d0' : '#fecaca';
  }

  const needle = document.getElementById('gauge-needle');
  if (needle) needle.style.left = pct.toFixed(1) + '%';

  const zoneEl = document.getElementById('gauge-zone');
  if (zoneEl) {
    const z = getZone(v);
    zoneEl.textContent = z.label;
    zoneEl.style.color = z.color;
  }

  const nRu = document.getElementById('n-ruedas');
  if (nRu) nRu.textContent = ALL_DATA.length;
}

// ── Annotations ───────────────────────────────────────────────────────────────
const ANIO_MARKS = [
  { date: '2024-12-10', label: 'Año 1' },
  { date: '2025-12-10', label: 'Año 2' },
  { date: '2026-12-10', label: 'Año 3' },
];

function buildAnnotations(displayData = [], withHitos = true) {
  const anns = {
    zonePos: {
      type: 'box', drawTime: 'beforeDatasetsDraw',
      yMin: 110, yMax: 130,
      backgroundColor: 'rgba(21,128,61,0.06)', borderWidth: 0,
    },
    zoneBaseline: {
      type: 'box', drawTime: 'beforeDatasetsDraw',
      yMin: 100, yMax: 110,
      backgroundColor: 'rgba(180,83,9,0.05)', borderWidth: 0,
    },
    zoneSub: {
      type: 'box', drawTime: 'beforeDatasetsDraw',
      yMin: 90, yMax: 100,
      backgroundColor: 'rgba(217,119,6,0.06)', borderWidth: 0,
    },
    zoneNeg: {
      type: 'box', drawTime: 'beforeDatasetsDraw',
      yMin: 60, yMax: 90,
      backgroundColor: 'rgba(220,38,38,0.06)', borderWidth: 0,
    },
    baseline: {
      type: 'line', yMin: 100, yMax: 100,
      borderColor: '#b45309', borderWidth: 1.5, borderDash: [4, 3],
      label: {
        display: true, content: '100',
        position: 'end', color: '#b45309',
        font: { size: 9, weight: '600' },
        backgroundColor: 'transparent', yAdjust: -8,
      },
    },
  };

  if (withHitos && displayData.length) {
    ANIO_MARKS.forEach(({ date, label }) => {
      const nearest = findNearest(displayData, date);
      const daysDiff = Math.abs(new Date(nearest.d + 'T12:00:00') - new Date(date + 'T12:00:00')) / 86400000;
      if (daysDiff > 60) return;
      anns['anio_' + label] = {
        type: 'line', scaleID: 'x', value: nearest.d,
        borderColor: 'rgba(100,116,139,0.45)',
        borderWidth: 1.5, borderDash: [5, 4],
        drawTime: 'beforeDatasetsDraw',
        label: {
          display: true, content: label,
          position: 'start', color: '#a8a29e',
          font: { size: 9, weight: '600' },
          backgroundColor: 'rgba(250,247,242,0.85)',
          yAdjust: 6,
        },
      };
    });

    // Event dots at bottom of chart — clickable
    EVENTS_RICH.forEach(ev => {
      const nearest = findNearest(displayData, ev.date);
      if (!nearest) return;
      const color = ev.impact === 'positive' ? '#15803d' : ev.impact === 'negative' ? '#b91c1c' : '#b45309';
      const evN = ev.n;
      anns['ev_dot_' + evN] = {
        type: 'point',
        xValue: nearest.d, yValue: 63,
        radius: 5,
        backgroundColor: color, borderColor: '#fff', borderWidth: 1.5,
        cursor: 'pointer',
        click({element}) {
          const idx = evSorted.findIndex(e => e.n === evN);
          if (idx >= 0) selectChip(idx);
        },
        enter({element}) {
          element.options.radius = 7;
          iepChart.update('none');
          document.getElementById('iepChart').style.cursor = 'pointer';
        },
        leave({element}) {
          element.options.radius = 5;
          iepChart.update('none');
          document.getElementById('iepChart').style.cursor = 'default';
        },
      };
      anns['ev_num_' + evN] = {
        type: 'label',
        xValue: nearest.d, yValue: 63,
        content: String(evN),
        font: { size: 7, weight: '700', family: 'Inter' },
        color: '#fff',
        backgroundColor: 'transparent',
        click() {
          const idx = evSorted.findIndex(e => e.n === evN);
          if (idx >= 0) selectChip(idx);
        },
      };
    });
  }
  return anns;
}

// ── Crosshair plugin ─────────────────────────────────────────────────────────
const crosshairPlugin = {
  id: 'crosshair',
  afterDraw(chart) {
    const active = chart.getActiveElements();
    if (!active || !active.length) return;
    const idx = active[0].index;
    const { ctx, chartArea: { top, bottom } } = chart;
    const xPos = chart.scales.x.getPixelForValue(idx);
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(xPos, top);
    ctx.lineTo(xPos, bottom);
    ctx.lineWidth = 1;
    ctx.strokeStyle = 'rgba(100,116,139,0.35)';
    ctx.setLineDash([4, 3]);
    ctx.stroke();
    ctx.setLineDash([]);
    chart.data.datasets.forEach((ds, dsIdx) => {
      if (!chart.isDatasetVisible(dsIdx)) return;
      const yVal = ds.data[idx];
      if (yVal == null) return;
      const yPos = chart.scales.y.getPixelForValue(yVal);
      ctx.beginPath();
      ctx.arc(xPos, yPos, 4.5, 0, 2 * Math.PI);
      ctx.fillStyle = ds.borderColor || '#1c1917';
      ctx.fill();
      ctx.strokeStyle = '#faf7f2';
      ctx.lineWidth = 2;
      ctx.stroke();
    });
    ctx.restore();
  },
};

// ── IEP Chart ─────────────────────────────────────────────────────────────────
function initChart() {
  const init = getDisplayData();
  const ctx  = document.getElementById('iepChart').getContext('2d');
  iepChart = new Chart(ctx, {
    type: 'line',
    plugins: [crosshairPlugin],
    data: {
      labels: init.map(d => d.d),
      datasets: [
        {
          label: 'IRPM',
          data: init.map(d => d.v),
          borderColor: '#1c1917', borderWidth: 2,
          pointRadius: 0, tension: 0.12,
          fill: false, spanGaps: false, order: 1,
        },
        {
          label: 'IRPM ajustado VIX',
          data: init.map(d => d.a),
          borderColor: '#a8a29e', borderWidth: 1.5, borderDash: [5, 4],
          pointRadius: 0, tension: 0.12,
          fill: false, spanGaps: false, order: 2, hidden: true,
        },
        {
          label: 'IRPM suavizado',
          data: init.map(d => d.s),
          borderColor: '#d6cfc4', borderWidth: 1.5, borderDash: [3, 3],
          pointRadius: 0, tension: 0.12,
          fill: false, spanGaps: false, order: 1, hidden: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },

      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#fff', titleColor: '#78716c',
          bodyColor: '#1c1917', borderColor: '#e8e0d5',
          borderWidth: 1, padding: 12,
          titleFont: { size: 11 }, bodyFont: { size: 13, weight: '700' },
          filter: item => item.parsed.y != null,
          callbacks: {
            title: items => {
              if (!items.length) return '';
              const d = items[0].label;
              const [y, m, day] = d.split('-');
              const mN = {'01':'Ene','02':'Feb','03':'Mar','04':'Abr','05':'May','06':'Jun',
                          '07':'Jul','08':'Ago','09':'Sep','10':'Oct','11':'Nov','12':'Dic'};
              return parseInt(day) + ' ' + mN[m] + ' ' + y;
            },
            label: ctx => {
              const v = ctx.parsed.y;
              if (v == null) return null;
              const prefix = ctx.dataset.label === 'IRPM ajustado VIX' ? ' +VIX adj.: ' :
                             ctx.dataset.label === 'IRPM suavizado'    ? ' Suavizado: ' : ' IRPM: ';
              return prefix + v.toFixed(1);
            },
          },
        },
        annotation: { annotations: buildAnnotations(init, showDots) },
      },
      scales: {
        x: {
          type: 'category',
          ticks: {
            color: '#a8a29e', maxRotation: 90, minRotation: 90, font: { size: 10 },
            autoSkip: false,
            callback: function(val, idx) {
              const labels = this.chart.data.labels;
              const d = labels[idx];
              if (!d) return null;
              const [y, m] = d.split('-');
              const mN = {'01':'Ene','02':'Feb','03':'Mar','04':'Abr','05':'May','06':'Jun',
                          '07':'Jul','08':'Ago','09':'Sep','10':'Oct','11':'Nov','12':'Dic'};
              if (currentGranularity === 'monthly') return m === '01' ? y : mN[m] + " '" + y.slice(2);
              if (idx > 0 && labels[idx - 1].split('-')[1] === m) return null;
              return m === '01' ? y : mN[m] + " '" + y.slice(2);
            },
          },
          grid: { display: false }, border: { color: '#e8e0d5' },
        },
        y: {
          min: 60, max: 130,
          ticks: { color: '#a8a29e', font: { size: 10 }, stepSize: 10 },
          grid: { display: false }, border: { color: '#e8e0d5' },
        },
      },
    },
  });
  initRangeSelector();
}

// ── Events navigator strip ───────────────────────────────────────────────────
let evSorted = [];
let evCurrentIdx = -1;

function buildEventsNav() {
  evSorted = [...EVENTS_RICH].sort((a, b) => a.date.localeCompare(b.date));
}

function selectChip(idx) {
  evCurrentIdx = idx;
  const ev = evSorted[idx];
  if (!ev) return;

  // Fill detail panel
  const panel = document.getElementById('events-detail-panel');
  if (panel) {
    panel.classList.add('visible');
    document.getElementById('event-card-tag').textContent   = (ev.tag ? ev.tag + ' · ' : '') + 'Lectura editorial';
    document.getElementById('event-card-title').textContent = ev.title || '';
    document.getElementById('event-card-text').textContent  = ev.body || '';
    const impactEl = document.getElementById('event-card-impact');
    if (impactEl) {
      if (ev.impact === 'positive') {
        impactEl.textContent = '↑ Movimiento positivo del índice';
        impactEl.className   = 'event-card-impact impact-pos';
      } else if (ev.impact === 'negative') {
        impactEl.textContent = '↓ Movimiento negativo del índice';
        impactEl.className   = 'event-card-impact impact-neg';
      } else {
        impactEl.textContent = '→ Período de transición';
        impactEl.className   = 'event-card-impact impact-neu';
      }
    }
  }
}

function openPopup(ev) {
  const idx = evSorted.findIndex(e => e.n === ev.n);
  if (idx >= 0) selectChip(idx);
}

function renderEventCard(idx) { selectChip(idx); }

// ── Refresh ────────────────────────────────────────────────────────────────────
function refreshAll() {
  const disp = getDisplayData();

  iepChart.data.labels           = disp.map(d => d.d);
  iepChart.data.datasets[0].data = disp.map(d => d.v);
  iepChart.data.datasets[1].data = disp.map(d => d.a);
  iepChart.data.datasets[2].data = disp.map(d => d.s);
  iepChart.options.plugins.annotation.annotations = buildAnnotations(disp, true);

  iepChart.setDatasetVisibility(1, showAdj);
  iepChart.setDatasetVisibility(2, showSmooth);

  iepChart.update('none');
}

// ── Range selector ────────────────────────────────────────────────────────────
// Range selector state: 0–1 fractions into ALL_DATA
let rangeLeft  = 0.0;  // start = beginning of data
let rangeRight = 1.0;  // end   = most recent

function initRangeSelector() {
  const track   = document.getElementById('range-track');
  const fill    = document.getElementById('range-fill');
  const hLeft   = document.getElementById('range-handle-left');
  const hRight  = document.getElementById('range-handle-right');
  const labels  = document.getElementById('range-labels');
  if (!track || !fill || !hLeft || !hRight) return;

  function updateVisuals() {
    hLeft.style.left  = (rangeLeft  * 100) + '%';
    hRight.style.left = (rangeRight * 100) + '%';
    fill.style.left   = (rangeLeft  * 100) + '%';
    fill.style.width  = ((rangeRight - rangeLeft) * 100) + '%';
  }

  function applyRange() {
    if (!iepChart) return;
    const n    = ALL_DATA.length;
    const from = Math.floor(rangeLeft  * n);
    const to   = Math.ceil(rangeRight  * n);
    const slice = ALL_DATA.slice(from, to);
    // Update chart x-axis min/max by label
    iepChart.options.scales['x'].min = slice[0]?.d;
    iepChart.options.scales['x'].max = slice[slice.length - 1]?.d;
    iepChart.update('none');
    updateVisuals();
    updateRangeLabels(from, to);
  }

  function updateRangeLabels(from, to) {
    if (!labels) return;
    const a = ALL_DATA[from];
    const b = ALL_DATA[Math.min(to - 1, ALL_DATA.length - 1)];
    if (a && b) labels.innerHTML = '<span>' + a.d + '</span><span>' + b.d + '</span>';
  }

  let dragging = null;

  function onMove(e) {
    if (!dragging) return;
    const rect  = track.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    let pct = (clientX - rect.left) / rect.width;
    pct = Math.max(0, Math.min(1, pct));

    if (dragging === 'left') {
      rangeLeft = Math.min(pct, rangeRight - 0.05);
    } else {
      rangeRight = Math.max(pct, rangeLeft + 0.05);
    }
    applyRange();
  }

  function onUp() {
    if (dragging) {
      document.getElementById('range-handle-' + dragging)?.classList.remove('dragging');
      dragging = null;
    }
  }

  hLeft.addEventListener('mousedown',  (e) => { e.preventDefault(); dragging = 'left';  hLeft.classList.add('dragging'); });
  hRight.addEventListener('mousedown', (e) => { e.preventDefault(); dragging = 'right'; hRight.classList.add('dragging'); });
  hLeft.addEventListener('touchstart',  () => { dragging = 'left';  }, { passive: true });
  hRight.addEventListener('touchstart', () => { dragging = 'right'; }, { passive: true });

  document.addEventListener('mousemove', onMove);
  document.addEventListener('touchmove', onMove, { passive: true });
  document.addEventListener('mouseup',   onUp);
  document.addEventListener('touchend',  onUp);

  // Initial labels
  updateRangeLabels(0, ALL_DATA.length);
  updateVisuals();
}

// ── Period / zoom helpers ──────────────────────────────────────────────────────
function setDivZoom(btn, months) {
  document.querySelectorAll('.div-pill').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentDivZoom = months;
  if (divChart) refreshDivChart();
}

function toggleGuide(header) {
  const body = document.getElementById('read-guide-body');
  if (!body) return;
  const open = body.classList.toggle('open');
  const span = header.querySelector('span');
  if (span) span.textContent = open ? '¿Cómo leer este gráfico? ▴' : '¿Cómo leer este gráfico? ▾';
}

// ── Divergence chart ──────────────────────────────────────────────────────────
const currentDivBaseline = '2023-12-11';

function applyUtdtBaseline(utdtData, baseDate) {
  const tgt = new Date(baseDate).getTime();
  let icgBase = null, iccBase = null;
  let icgBest = Infinity, iccBest = Infinity;
  utdtData.forEach(u => {
    const diff = Math.abs(new Date(u.d).getTime() - tgt);
    if (u.icg !== null && diff < icgBest) { icgBest = diff; icgBase = u.icg; }
    if (u.icc !== null && diff < iccBest) { iccBest = diff; iccBase = u.icc; }
  });
  return utdtData.map(u => ({
    d:   u.d,
    icg: (u.icg !== null && icgBase) ? +(u.icg / icgBase * 100).toFixed(2) : null,
    icc: (u.icc !== null && iccBase) ? +(u.icc / iccBase * 100).toFixed(2) : null,
  }));
}

function buildDivDatasets(iepMonthly, utdtNorm) {
  const iepByMonth = {};
  iepMonthly.forEach(d => { iepByMonth[d.d] = d.v; });
  const utdtByMonth = {};
  utdtNorm.forEach(u => {
    const ym = u.d.slice(0, 7);
    utdtByMonth[ym] = { icg: u.icg, icc: u.icc };
  });
  const labels = [...new Set([...Object.keys(iepByMonth), ...Object.keys(utdtByMonth)])].sort();
  return {
    labels,
    iepArr: labels.map(ym => iepByMonth[ym]  ?? null),
    icgArr: labels.map(ym => utdtByMonth[ym]?.icg ?? null),
    iccArr: labels.map(ym => utdtByMonth[ym]?.icc ?? null),
  };
}

function getDivMonthlyIEP() {
  const adj    = applyBaseline(ALL_DATA, currentDivBaseline);
  const zoomed = applyZoom(adj, currentDivZoom);
  const months = {};
  zoomed.forEach(d => {
    const ym = d.d.slice(0, 7);
    if (!months[ym]) months[ym] = [];
    months[ym].push(d.v);
  });
  const result = Object.entries(months)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([ym, vals]) => ({
      d: ym,
      v: +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(2),
    }));
  const baseYM = currentDivBaseline.slice(0, 7);
  const basePt = result.find(d => d.d === baseYM);
  if (basePt) {
    const shift = basePt.v - 100;
    result.forEach(d => { d.v = +(d.v - shift).toFixed(2); });
  }
  return result;
}

function getDivUtdtNorm() {
  return applyZoom(applyUtdtBaseline(UTDT_DATA, currentDivBaseline), currentDivZoom);
}

function updateDivStrip() {
  // Show most recent divergence state in the compact bar below chart
  const norm = getDivUtdtNorm();
  const iepM = getDivMonthlyIEP();
  const bar = document.getElementById('div-strip-bar');
  if (!bar) return;

  const iepByMonth = {};
  iepM.forEach(d => { iepByMonth[d.d] = d.v; });

  const mN = {'01':'Ene','02':'Feb','03':'Mar','04':'Abr','05':'May','06':'Jun',
              '07':'Jul','08':'Ago','09':'Sep','10':'Oct','11':'Nov','12':'Dic'};

  const periods = [];
  norm.forEach(u => {
    if (u.icg === null) return;
    const ym   = u.d.slice(0, 7);
    const irpm = iepByMonth[ym] ?? null;
    if (irpm === null) return;
    const [y, m] = ym.split('-');
    periods.push({ date: ym, tag: mN[m] + ' ' + y, irpm, icg: u.icg });
  });

  if (!periods.length) return;
  const latest = periods.reduce((a, b) => a.date > b.date ? a : b);
  const gap = latest.irpm - latest.icg;
  const gapColor = gap > 0 ? '#15803d' : '#b91c1c';
  const label = gap > 0 ? 'Mercado más optimista que la ciudadanía' : 'OP más optimista que el mercado';
  const gapSign = gap > 0 ? '+' : '';

  document.getElementById('div-bar-dot').style.background  = gapColor;
  document.getElementById('div-bar-label').textContent     = label;
  document.getElementById('div-bar-period').textContent    = 'Último dato: ' + latest.tag;
  document.getElementById('div-bar-vals').textContent      = 'IRPM ' + latest.irpm.toFixed(1) + ' · ICG ' + latest.icg.toFixed(1);
  document.getElementById('div-bar-gap').textContent       = gapSign + gap.toFixed(1) + ' pts';
  document.getElementById('div-bar-gap').style.color       = gapColor;
  bar.classList.add('visible');
}

function refreshDivChart() {
  if (!divChart) return;
  const { labels, iepArr, icgArr } = buildDivDatasets(getDivMonthlyIEP(), getDivUtdtNorm());
  divChart.data.labels           = labels;
  divChart.data.datasets[0].data = iepArr;
  divChart.data.datasets[1].data = icgArr;
  divChart.update('none');
  updateDivStrip();
}

function divBaseAnnotations() {
  return {
    zonePos:      { type: 'box', drawTime: 'beforeDatasetsDraw', yMin: 110, yMax: 130, backgroundColor: 'rgba(21,128,61,0.06)',  borderWidth: 0 },
    zoneBaseline: { type: 'box', drawTime: 'beforeDatasetsDraw', yMin: 100, yMax: 110, backgroundColor: 'rgba(180,83,9,0.05)',   borderWidth: 0 },
    zoneSub:      { type: 'box', drawTime: 'beforeDatasetsDraw', yMin: 90,  yMax: 100, backgroundColor: 'rgba(217,119,6,0.06)',  borderWidth: 0 },
    zoneNeg:      { type: 'box', drawTime: 'beforeDatasetsDraw', yMin: 60,  yMax: 90,  backgroundColor: 'rgba(220,38,38,0.06)', borderWidth: 0 },
    baseline: {
      type: 'line', yMin: 100, yMax: 100,
      borderColor: '#b45309', borderWidth: 1.5, borderDash: [4, 3],
      label: { display: true, content: '100', position: 'end', color: '#b45309',
               font: { size: 9, weight: '600' }, backgroundColor: 'transparent', yAdjust: -8 },
    },
  };
}

const CORR_CONTENT = [
  { xMin: '2024-02', xMax: '2024-06', type: 'div',
    title: 'Divergencia entre condiciones de mercado y confianza',
    body: 'El IRPM sube mientras el ICG cae. La coincidencia temporal admite explicaciones alternativas y no establece anticipación.' },
  { xMin: '2024-07', xMax: '2024-07', type: 'sinc',
    title: 'Convergencia: el honeymoon se agota en ambos registros',
    body: 'IRPM e ICG corrigen juntos en julio: el ciclo de euforia inicial llega a su fin.' },
  { xMin: '2024-08', xMax: '2024-10', type: 'div',
    title: 'Divergencia posterior al shock global de agosto',
    body: 'El IRPM rebota mientras el ICG alcanza un mínimo local. Es una diferencia descriptiva; no demuestra anticipación del acuerdo con el FMI.' },
  { xMin: '2024-11', xMax: '2025-12', type: 'sinc',
    title: 'Convergencia histórica: 14 meses leyendo el mismo ciclo político',
    body: 'El período de mayor sincronía de la serie. Mercado y ciudadanía comparten el optimismo del primer aniversario y la incertidumbre legislativa.' },
  { xMin: '2026-01', xMax: '2026-12', type: 'div',
    title: 'Divergencia entre series durante 2026',
    body: 'El IRPM se estabiliza alrededor del baseline mientras el ICG cae respecto de su pico. La causa de la brecha no está identificada.' },
];

function lookupCorrContent(xMin, type) {
  const match = CORR_CONTENT.find(c => c.type === type && xMin >= c.xMin && xMin <= c.xMax);
  return match || {
    title: type === 'sinc' ? 'Convergencia' : 'Divergencia',
    body:  type === 'sinc' ? 'IRPM e ICG se mueven en la misma dirección.' : 'IRPM e ICG se mueven en sentidos contrarios.',
  };
}

function buildCorrAnnotations(labels, iepArr, icgArr) {
  const anns = {};
  let bandStart = null, bandType = null, bandIdx = 0;
  const addBand = (from, to, type) => {
    anns['corr_' + bandIdx++] = {
      type: 'box', drawTime: 'beforeDatasetsDraw',
      xMin: labels[from], xMax: labels[to],
      yMin: 60, yMax: 130,
      backgroundColor: type === 'sinc' ? 'rgba(21,128,61,0.10)' : 'rgba(220,38,38,0.10)',
      borderWidth: 0, _xMin: labels[from], _type: type,
    };
  };
  for (let i = 2; i < labels.length; i++) {
    if (iepArr[i] == null || icgArr[i] == null || iepArr[i-2] == null || icgArr[i-2] == null) continue;
    const dIcg = icgArr[i] - icgArr[i-2];
    if (Math.abs(dIcg) < 0.5) continue;
    const dIep = iepArr[i] - iepArr[i-2];
    const type = (Math.abs(dIep) < 1.0) ? 'div' : (dIep * dIcg > 0 ? 'sinc' : 'div');
    if (type !== bandType) {
      if (bandStart !== null) addBand(bandStart, i - 1, bandType);
      bandStart = i; bandType = type;
    }
  }
  if (bandStart !== null && bandType) addBand(bandStart, labels.length - 1, bandType);
  return anns;
}

let showCorr = false;

function handleCorrHover(event, chart) {
  const tip = document.getElementById('corr-tooltip');
  if (!showCorr) { tip.style.display = 'none'; return; }
  const idx = Math.round(chart.scales.x.getValueForPixel(event.x));
  if (idx < 0 || idx >= chart.data.labels.length) { tip.style.display = 'none'; return; }
  const label   = chart.data.labels[idx];
  const annsObj = chart.options.plugins.annotation.annotations;
  let found = null;
  for (const ann of Object.values(annsObj)) {
    if (ann._xMin && label >= ann.xMin && label <= ann.xMax) { found = ann; break; }
  }
  if (!found) { tip.style.display = 'none'; return; }
  const content = lookupCorrContent(found._xMin, found._type);
  const color   = found._type === 'sinc' ? '#15803d' : '#dc2626';
  tip.innerHTML = '<div class="corr-tip-title" style="color:' + color + '">' + content.title + '</div><div class="corr-tip-body">' + content.body + '</div>';
  const ca = chart.chartArea;
  let left = event.x - 110;
  let top  = event.y - 144;
  if (left < ca.left) left = ca.left;
  if (left + 220 > ca.right) left = ca.right - 220;
  if (top < ca.top) top = event.y + 14;
  tip.style.left = left + 'px';
  tip.style.top  = top  + 'px';
  tip.style.display = 'block';
}

function initDivChart() {
  const { labels, iepArr, icgArr } = buildDivDatasets(getDivMonthlyIEP(), getDivUtdtNorm());
  const ctx = document.getElementById('divChart').getContext('2d');
  divChart = new Chart(ctx, {
    type: 'line',
    plugins: [crosshairPlugin],
    data: {
      labels,
      datasets: [
        {
          label: 'IRPM (mercado)',
          data: iepArr,
          borderColor: '#1c1917', borderWidth: 2,
          pointRadius: 0, tension: 0.12,
          fill: false, spanGaps: false, order: 2,
        },
        {
          label: 'ICG UTDT',
          data: icgArr,
          borderColor: '#b45309', borderWidth: 1.5, borderDash: [5, 4],
          pointRadius: 0, tension: 0.15,
          fill: false, spanGaps: true, order: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      onHover: (event, _el, chart) => handleCorrHover(event, chart),
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#fff', titleColor: '#78716c',
          bodyColor: '#1c1917', borderColor: '#e8e0d5',
          borderWidth: 1, padding: 12,
          titleFont: { size: 11 }, bodyFont: { size: 13, weight: '700' },
          filter: item => item.parsed.y !== null,
          callbacks: {
            title: items => {
              if (!items.length) return '';
              const [y, m] = items[0].label.split('-');
              const mN = {'01':'Ene','02':'Feb','03':'Mar','04':'Abr','05':'May','06':'Jun',
                          '07':'Jul','08':'Ago','09':'Sep','10':'Oct','11':'Nov','12':'Dic'};
              return mN[m] + ' ' + y;
            },
            label: ctx => {
              const v = ctx.parsed.y;
              if (v === null) return null;
              return ' ' + ['IRPM', 'ICG UTDT'][ctx.datasetIndex] + ': ' + v.toFixed(1);
            },
          },
        },
        annotation: { annotations: divBaseAnnotations() },
      },
      scales: {
        x: {
          type: 'category',
          ticks: {
            color: '#a8a29e', maxRotation: 90, minRotation: 90, font: { size: 10 },
            autoSkip: false,
            callback: function(val, idx) {
              const lbl = this.chart.data.labels[idx];
              if (!lbl) return null;
              const [y, m] = lbl.split('-');
              const mN = {'01':'Ene','02':'Feb','03':'Mar','04':'Abr','05':'May','06':'Jun',
                          '07':'Jul','08':'Ago','09':'Sep','10':'Oct','11':'Nov','12':'Dic'};
              return m === '01' ? y : mN[m] + " '" + y.slice(2);
            },
          },
          grid: { display: false }, border: { color: '#e8e0d5' },
        },
        y: {
          min: 60, max: 130,
          ticks: { color: '#a8a29e', font: { size: 10 }, stepSize: 10 },
          grid: { display: false }, border: { color: '#e8e0d5' },
        },
      },
    },
  });
  updateDivStrip();
}

// ── Comparativa entre gestiones ───────────────────────────────────────────────
const COMP_DATA = __COMP_DATA__;

function initCompChart() {
  const ctx = document.getElementById('compChart');
  if (!ctx) return;

  // x-axis: months 0..N (max across all terms)
  const maxM = Math.max(...Object.values(COMP_DATA).map(arr => arr[arr.length - 1].m));
  const labels = Array.from({length: maxM + 1}, (_, i) => 'M' + i);

  function toMonthArray(arr) {
    const out = new Array(maxM + 1).fill(null);
    arr.forEach(({m, v}) => { out[m] = v; });
    return out;
  }

  const datasets = [
    {
      label: 'Macri (dic 2015)',
      data: toMonthArray(COMP_DATA.macri || []),
      borderColor: '#6366f1', borderWidth: 2,
      backgroundColor: 'transparent', pointRadius: 0, tension: 0.3,
      spanGaps: false,
    },
    {
      label: 'Alberto (dic 2019)',
      data: toMonthArray(COMP_DATA.alberto || []),
      borderColor: '#f97316', borderWidth: 2,
      backgroundColor: 'transparent', pointRadius: 0, tension: 0.3,
      spanGaps: false,
    },
    {
      label: 'Milei (dic 2023)',
      data: toMonthArray(COMP_DATA.milei || []),
      borderColor: '#1c1917', borderWidth: 2.5,
      backgroundColor: 'transparent', pointRadius: 0, tension: 0.3,
      spanGaps: false,
    },
  ];

  // Midterm elections: month from start of each term
  // Macri: oct 2017 ≈ M22 | Alberto: nov 2021 ≈ M23 | Milei: oct 2025 ≈ M22
  // Macri+Milei share M22 → one line, two-line label
  const electAnns = {
    baseline: {
      type: 'line', scaleID: 'y', value: 100,
      borderColor: '#b45309', borderWidth: 1, borderDash: [4, 4],
    },
    elec_m22: {
      type: 'line', scaleID: 'x', value: 22,
      borderColor: '#78716c', borderWidth: 1, borderDash: [3, 4],
      label: {
        display: true,
        content: ['Legislativas', 'Macri · Milei (M22)'],
        position: 'start',
        font: {size: 9}, color: '#57534e', backgroundColor: 'rgba(255,255,255,0.8)',
        padding: 3,
      },
    },
    elec_alberto: {
      type: 'line', scaleID: 'x', value: 23,
      borderColor: '#f97316', borderWidth: 1, borderDash: [3, 4],
      label: {
        display: true,
        content: ['Legislativas', 'Alberto (M23)'],
        position: '30%',
        font: {size: 9}, color: '#f97316', backgroundColor: 'rgba(255,255,255,0.8)',
        padding: 3,
      },
    },
    end_terms: {
      type: 'line', scaleID: 'x', value: 48,
      borderColor: '#d6cfc4', borderWidth: 1,
      label: {
        display: true, content: 'Fin mandato (M48)',
        position: 'start', font: {size: 9}, color: '#a8a29e',
        backgroundColor: 'rgba(255,255,255,0.8)', padding: 3,
      },
    },
  };

  new Chart(ctx.getContext('2d'), {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false, animation: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: items => 'Mes ' + items[0].label.replace('M', ''),
            label: item => item.dataset.label + ': ' + (item.raw !== null ? item.raw.toFixed(1) : '—'),
          }
        },
        annotation: { annotations: electAnns },
      },
      scales: {
        x: {
          ticks: {
            color: '#a8a29e', font: { size: 9 },
            callback: (v, i) => i % 6 === 0 ? 'M' + i : '',
            maxRotation: 0,
          },
          grid: { color: '#f0ebe3' }, border: { color: '#e8e0d5' },
        },
        y: {
          min: 40,
          ticks: { color: '#a8a29e', font: { size: 10 }, stepSize: 20 },
          grid: { color: '#f0ebe3' }, border: { color: '#e8e0d5' },
        },
      },
    },
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  updateHero();
  initChart();
  initDivChart();
  initCompChart();
  buildEventsNav();
  // initRangeSelector is called inside initChart() after chart is created

  document.getElementById('smooth-toggle')?.addEventListener('click', function() {
    showSmooth = !showSmooth;
    this.classList.toggle('active', showSmooth);
    if (iepChart) refreshAll();
  });
  document.getElementById('adj-toggle')?.addEventListener('click', function() {
    showAdj = !showAdj;
    this.classList.toggle('active', showAdj);
    if (iepChart) refreshAll();
  });
  // No popup-close listener needed
});
"""


# ── Main ───────────────────────────────────────────────────────────────────────

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
