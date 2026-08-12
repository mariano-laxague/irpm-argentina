"""
generate_dashboard.py — Genera outputs/dashboard.html con la serie histórica del IEP.

Uso:
    python src/dashboard/generate_dashboard.py
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
        "body": "Primer pico del período de honeymoon (~111 pts). El mercado celebra el primer trimestre del programa: superávit primario confirmado, inflación mensual bajando de 25% a un dígito en pocos meses, brecha cambiaria comprimida y EMBI que colapsa de ~1800 a ~700 bps desde el inicio de la gestión. Es la primera vez que el índice supera holgadamente la zona de alta convicción. El mercado pricea que el programa tiene viabilidad y continuidad.",
    },
    {
        "n": 2, "date": "2024-12-09", "tag": "Dic 2024",
        "title": "Máximo histórico",
        "impact": "positive",
        "body": "El IRPM alcanza su nivel más alto de toda la serie (~115 pts). Cierre del primer año de gestión con los mejores indicadores del programa: superávit fiscal primario anual confirmado, inflación en torno al 2-3% mensual sostenido, reservas en acumulación y negociaciones con el FMI en tramo final. La macro doméstica y las condiciones globales (VIX bajo, apetito por emergentes alto) convergen en el punto de máxima convicción del mercado sobre la continuidad del programa.",
    },
    {
        "n": 3, "date": "2025-09-12", "tag": "Sep 2025",
        "title": "Mínimo histórico",
        "impact": "negative",
        "body": "El IRPM toca su mínimo histórico (~70 pts), 30 puntos por debajo del baseline. La prima de riesgo electoral alcanza su punto máximo semanas antes de las legislativas. El mercado no está seguro de que el programa sobreviva una derrota legislativa significativa: el EMBI se dispara, la brecha MEP se amplía y los bonos soberanos ceden. Es el peor momento del índice bajo la gestión Milei.",
    },
    {
        "n": 4, "date": "2025-11-03", "tag": "Oct–Nov 2025",
        "title": "Legislativas 2025",
        "impact": "positive",
        "body": "El oficialismo consolida posiciones en las legislativas del 26 de octubre: más bancas, más gobernabilidad, más tiempo para el programa. El mercado procesa el resultado en días: el EMBI comprime, el MEP se estabiliza, los bonos recuperan. El IRPM recupera terreno (~97 pts), levemente por debajo del nivel de inicio de la gestión pero con momentum positivo claro.",
    },
    {
        "n": 5, "date": "2024-08-06", "tag": "Ago 2024",
        "title": "Corrección post-honeymoon",
        "impact": "negative",
        "body": "Primer valle significativo desde el inicio de la gestión (~95 pts). Confluyen dos factores: globalmente, el 'Black Monday' del 5 de agosto — colapso del Nikkei por el deshacimiento masivo del carry trade en yenes — golpea todos los activos de riesgo emergentes. Localmente, el mercado empieza a cuestionar la sostenibilidad del segundo semestre: la acumulación de reservas se desacelera, el crawling peg muestra sus primeras tensiones y la economía real no termina de salir de la recesión del ajuste.",
    },
    {
        "n": 6, "date": "2025-04-08", "tag": "Abr 2025",
        "title": "Doble shock: tarifas Trump + tensión cambiaria",
        "impact": "negative",
        "body": "El IRPM cae a su segundo piso histórico (~91 pts) bajo presión simultánea de dos frentes. Global: el 'Liberation Day' de Trump (2 de abril) anuncia aranceles masivos y desata una venta generalizada de activos emergentes. Local: Argentina atraviesa la transición hacia un esquema de flotación administrada con bandas cambiarias, generando incertidumbre transitoria sobre el ancla nominal del programa. El mercado pricea ambas fuentes de riesgo con rezago de días.",
    },
    {
        "n": 7, "date": "2025-06-04", "tag": "Jun 2025",
        "title": "Recuperación: acuerdo FMI + convergencia electoral",
        "impact": "positive",
        "body": "El IRPM sube a ~107 pts, recuperando terreno antes del período de mayor tensión pre-electoral. El driver principal es el nuevo acuerdo con el FMI (firmado en abril, ~20.000 millones de dólares en nuevo financiamiento), que despeja la restricción externa y reancla las expectativas. La coalición oficialista muestra cohesión en la conformación de listas y el programa consolida resultados: reservas en recuperación, inflación estabilizada. El mercado ve el escenario electoral con más optimismo.",
    },
    {
        "n": 8, "date": "2026-04-17", "tag": "Abr 2026",
        "title": "Pax política: el riesgo alternativo comprime",
        "impact": "positive",
        "body": "Nuevo pico local (~105 pts) en un contexto de baja tensión política. El diferencial respecto al mínimo pre-electoral de sep-2025 (+35 pts) refleja un cambio en la estructura del riesgo: el mercado no solo cree que Milei puede ganar en 2027, sino que percibe que el escenario alternativo ya no es disruptivo para el programa. Sin candidato opositor consolidado, con el peronismo fragmentado y con Kicillof señalando un giro pragmático hacia el centro, la distribución de outcomes post-2027 se estrecha. Menos cola izquierda = menos prima de riesgo político.",
    },
]

BASELINE_PRESETS = [
    {"value": "2023-12-11", "label": "Inicio de gestión Milei · Dic 2023"},
    {"value": "2024-04-08", "label": "Peak honeymoon · Abr 2024"},
    {"value": "2024-12-09", "label": "Máximo histórico · Dic 2024"},
    {"value": "2025-10-27", "label": "Legislativas 2025"},
]


# ── UTDT loader ───────────────────────────────────────────────────────────────

def load_utdt_data():
    """ICG e ICC UTDT — valores crudos desde dic-2023. La normalización al baseline activo se hace en JS."""
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
    """REM raw — solo tc_12m e ipc_12m para el strip informativo."""
    if not REM_CSV_PATH.exists():
        return []
    df = pd.read_csv(REM_CSV_PATH).query("fecha >= '2023-12'")
    if df.empty:
        return []
    result = []
    for _, row in df.iterrows():
        result.append({
            "d":      row["fecha"],
            "tc_12m": round(float(row["tc_12m"]), 0)   if pd.notna(row["tc_12m"])  else None,
            "ipc_12m":round(float(row["ipc_12m"]), 1)  if pd.notna(row["ipc_12m"]) else None,
            "pib":    round(float(row["pib_anio"]), 1)  if pd.notna(row["pib_anio"])else None,
        })
    return result


def load_rem_icm():
    """ICM-REM — indice compuesto mensual de consenso de analistas."""
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
        return {"tag": "> 110", "label": "Mercado pricea continuidad con alta convicción",
                "color": "#16a34a", "id": "gt110"}
    elif v >= 90:
        return {"tag": "90-110", "label": "Zona baseline — continuidad del programa creíble",
                "color": "#2563eb", "id": "b90_110"}
    elif v >= 70:
        return {"tag": "70-89",  "label": "Optimismo moderado con ruido",
                "color": "#ca8a04", "id": "b70_89"}
    elif v >= 40:
        return {"tag": "40-69",  "label": "Incertidumbre activa",
                "color": "#ea580c", "id": "b40_69"}
    else:
        return {"tag": "< 40",   "label": "Stress político severo",
                "color": "#dc2626", "id": "lt40"}


def build_scale_rows_html(iep_now):
    rows_def = [
        ("> 110", "#16a34a", "pos", "+10 pts vs. baseline — el mercado pricea continuidad con convicción superior al nivel de referencia", iep_now > 110),
        ("90–110","#64748b", "neu", "±10 pts vs. baseline — zona de referencia, continuidad del programa creíble",                        90 <= iep_now <= 110),
        ("< 90",  "#dc2626", "neg", "-10 pts vs. baseline — señal de debilitamiento respecto al nivel de referencia",                     iep_now < 90),
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

def build_html(data, utdt_data):
    iep_now  = data[-1]["v"]
    date_now = data[-1]["d"]
    diff     = iep_now - 100.0
    diff_str = (f"+{diff:.1f}" if diff >= 0 else f"{diff:.1f}") + " pts vs baseline"
    zone     = get_zone(iep_now)

    data_json   = json.dumps(data)
    events_json = json.dumps(EVENTS_RICH, ensure_ascii=False)
    utdt_json   = json.dumps(utdt_data)

    page = (
        "<!DOCTYPE html>\n<html lang='es'>\n<head>\n"
        "<meta charset='UTF-8'>\n"
        "<meta name='viewport' content='width=device-width,initial-scale=1.0'>\n"
        "<title>IRPM — Indice de Riesgo Politico de Mercado</title>\n"
        "<script src='https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js'></script>\n"
        "<script src='https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js'></script>\n"
        "<style>\n" + _css() + "\n</style>\n"
        "</head>\n<body>\n"
        + _html_body() + "\n"
        "<script>\n" + _js() + "\n</script>\n"
        "</body>\n</html>"
    )

    page = (page
        .replace("__DATA__",         data_json)
        .replace("__UTDT_DATA__",    utdt_json)
        .replace("__EVENTS__",       events_json)
        .replace("__IEP_NOW__",      f"{iep_now:.1f}")
        .replace("__DATE_NOW__",     date_now)
        .replace("__DIFF_STR__",     diff_str)
        .replace("__ZONE_TAG__",     zone["tag"])
        .replace("__ZONE_LABEL__",   zone["label"])
        .replace("__ZONE_COLOR__",   zone["color"])
        .replace("__ZONE_BG__",      zone["color"] + "18")
        .replace("__ZONE_BORDER__",  zone["color"] + "40")
        .replace("__DIFF_COLOR__",   "#16a34a" if diff >= 0 else "#dc2626")
        .replace("__SCALE_ROWS__",   build_scale_rows_html(iep_now))
    )
    return page



# ── CSS ────────────────────────────────────────────────────────────────────────

def _css():
    return """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f1f5f9;
  color: #1e293b;
  min-height: 100vh;
  padding: 28px 20px;
}
.container { max-width: 1100px; margin: 0 auto; }

.header { margin-bottom: 20px; }
.header h1 {
  font-size: 0.7rem; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: #64748b; margin-bottom: 2px;
}
.header p { font-size: 0.76rem; color: #94a3b8; }

/* Hero */
.hero {
  display: flex; align-items: flex-end; gap: 24px;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 22px 26px; margin-bottom: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.hero-value {
  font-size: 4rem; font-weight: 700; line-height: 1;
  letter-spacing: -0.03em; color: #0f172a;
}
.hero-meta { flex: 1; }
.hero-date { font-size: 0.73rem; color: #94a3b8; margin-bottom: 6px; }
.hero-zone {
  display: inline-block; font-size: 0.68rem; font-weight: 700;
  letter-spacing: 0.07em; text-transform: uppercase;
  padding: 2px 9px; border-radius: 20px; margin-bottom: 6px; border: 1px solid;
}
.hero-desc { font-size: 0.83rem; color: #475569; }
.hero-diff { font-size: 0.76rem; margin-top: 4px; font-weight: 500; }

/* Chart panel */
.chart-panel {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 18px 20px 16px; margin-bottom: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.chart-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px; flex-wrap: wrap; gap: 10px;
}
.panel-title {
  font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em;
  text-transform: uppercase; color: #94a3b8;
}
.controls { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }

.zoom-group { display: flex; gap: 3px; }
.zoom-btn {
  font-size: 0.7rem; padding: 3px 9px; border-radius: 4px;
  border: 1px solid #e2e8f0; background: #fff; color: #94a3b8;
  cursor: pointer; transition: all 0.12s;
}
.zoom-btn:hover { border-color: #94a3b8; color: #475569; }
.zoom-btn.active { background: #f1f5f9; color: #1e293b; border-color: #94a3b8; font-weight: 700; }

.baseline-group { display: flex; align-items: center; gap: 6px; }
.baseline-label { font-size: 0.7rem; color: #94a3b8; white-space: nowrap; }
.baseline-select {
  font-size: 0.7rem; padding: 3px 7px; border-radius: 4px;
  border: 1px solid #e2e8f0; background: #fff; color: #475569; cursor: pointer;
}

/* Chart wrap — must be position:relative for the popup */
.chart-wrap { position: relative; height: 400px; }

/* Floating event popup */
.event-popup {
  position: absolute;
  width: 300px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 9px;
  padding: 14px 16px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.14);
  z-index: 200;
}
.popup-head {
  display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px;
}
.popup-num {
  width: 24px; height: 24px; border-radius: 50%; flex-shrink: 0;
  background: #1e293b; color: #fff;
  font-size: 0.72rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  margin-top: 1px;
}
.popup-title-wrap { flex: 1; }
.popup-title { font-size: 0.88rem; font-weight: 700; color: #0f172a; line-height: 1.3; }
.popup-date-tag { font-size: 0.68rem; color: #94a3b8; margin-top: 2px; }
.popup-close {
  margin-left: auto; flex-shrink: 0; background: none; border: none;
  cursor: pointer; color: #cbd5e1; font-size: 1.1rem; line-height: 1;
  padding: 0 2px; transition: color 0.1s;
}
.popup-close:hover { color: #64748b; }
.popup-badges {
  display: flex; gap: 6px; margin-bottom: 10px; flex-wrap: wrap;
  align-items: center;
}
.popup-iep-badge {
  font-size: 0.7rem; font-weight: 700; padding: 2px 8px;
  border-radius: 4px;
}
.popup-zone-badge {
  font-size: 0.68rem; font-weight: 600; padding: 2px 7px;
  border-radius: 4px; background: #f1f5f9; color: #64748b;
}
.popup-body {
  font-size: 0.78rem; color: #475569; line-height: 1.65; margin-bottom: 9px;
}
.popup-impact { font-size: 0.72rem; font-weight: 600; }

/* Scale panel */
.scale-panel {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  padding: 18px 22px; margin-bottom: 14px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.scale-title {
  font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em;
  text-transform: uppercase; color: #94a3b8; margin-bottom: 4px;
}
.scale-note { font-size: 0.67rem; color: #cbd5e1; margin-bottom: 12px; }
.scale-rows { display: flex; flex-direction: column; gap: 5px; }
.scale-row {
  display: flex; align-items: center; gap: 10px;
  padding: 7px 10px; border-radius: 6px; border: 1px solid transparent;
}
.scale-row.current { background: #f0f9ff; border-color: #bae6fd; }
.scale-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.scale-range { font-size: 0.76rem; font-weight: 700; width: 48px; flex-shrink: 0; }
.scale-label { font-size: 0.8rem; color: #64748b; flex: 1; }
.scale-now {
  font-size: 0.62rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
  color: #2563eb; border: 1px solid #bae6fd; background: #eff6ff;
  border-radius: 3px; padding: 1px 6px;
}

.corr-tooltip {
  position: absolute; pointer-events: none; z-index: 200;
  width: 230px; background: #fff;
  border: 1px solid #e2e8f0; border-radius: 8px;
  padding: 11px 13px; box-shadow: 0 6px 24px rgba(0,0,0,0.11);
}
.corr-tip-title {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em;
  text-transform: uppercase; margin-bottom: 5px;
}
.corr-tip-body { font-size: 0.75rem; color: #475569; line-height: 1.55; }

.footnote {
  font-size: 0.68rem; color: #94a3b8; text-align: center; line-height: 1.7;
}

/* Control divider */
.ctrl-divider {
  width: 1px; background: #e2e8f0; height: 18px; align-self: center; flex-shrink: 0;
}

/* Tabs */
.tab-nav {
  display: flex; gap: 2px; margin-bottom: 14px;
  border-bottom: 2px solid #e2e8f0;
}
.tab-btn {
  font-size: 0.75rem; font-weight: 600; padding: 8px 16px;
  border: none; background: none; cursor: pointer;
  color: #94a3b8; border-bottom: 2px solid transparent;
  margin-bottom: -2px; transition: color 0.12s, border-color 0.12s;
  letter-spacing: 0.02em;
}
.tab-btn:hover { color: #475569; }
.tab-btn.active { color: #0f172a; border-bottom-color: #0f172a; }
.tab-pane { display: none; }
.tab-pane.active { display: block; }

/* Divergence panel */
.div-legend {
  display: flex; gap: 18px; flex-wrap: wrap;
  margin-bottom: 14px; align-items: center;
}
.div-legend-item {
  display: flex; align-items: center; gap: 5px;
  font-size: 0.72rem; color: #64748b;
}
.div-legend-line {
  width: 20px; height: 2px; background: #0f172a; border-radius: 2px;
}
.div-legend-dot {
  width: 10px; height: 10px; border-radius: 50%;
}
.div-legend-item {
  cursor: pointer; user-select: none; transition: opacity 0.15s;
}
.div-legend-item.hidden { opacity: 0.35; }
.div-note {
  font-size: 0.67rem; color: #cbd5e1; margin-top: 10px; line-height: 1.5;
}
/* Divergence strip */
.div-strip {
  margin-top: 14px; display: flex; flex-direction: column; gap: 6px;
}
.div-row {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 6px 10px; border-radius: 6px; background: #f8fafc;
  border: 1px solid #e2e8f0;
}
.div-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.div-label { font-size: 0.78rem; color: #475569; flex: 1; min-width: 180px; }
.div-period { color: #94a3b8; font-size: 0.7rem; }
.div-vals { font-size: 0.73rem; color: #94a3b8; white-space: nowrap; }
.div-gap { font-size: 0.76rem; white-space: nowrap; }
.div-dir { color: #94a3b8; font-weight: 400; font-size: 0.7rem; }
"""


# ── HTML body ──────────────────────────────────────────────────────────────────

def _html_body():
    return """
<div class="container">

  <div class="header">
    <h1>IRPM &middot; Indice de Riesgo Politico de Mercado</h1>
    <p>Probabilidad implícita de continuidad del programa economico post-2027, extraída de bonos soberanos, señales cambiarias y volatilidad accionaria &mdash; puntos clickeables en el grafico abren el analisis del hito</p>
  </div>

  <div class="hero">
    <div class="hero-value" id="hero-value">__IEP_NOW__</div>
    <div class="hero-meta">
      <div class="hero-date">Ultima actualizacion: __DATE_NOW__</div>
      <div class="hero-zone" id="hero-zone"
           style="color:__ZONE_COLOR__;background:__ZONE_BG__;border-color:__ZONE_BORDER__">__ZONE_TAG__</div>
      <div class="hero-desc" id="hero-desc">__ZONE_LABEL__</div>
      <div class="hero-diff" id="hero-diff" style="color:__DIFF_COLOR__">__DIFF_STR__</div>
    </div>
  </div>

  <!-- Tab nav -->
  <nav class="tab-nav">
    <button class="tab-btn active" data-tab="tab-iep">IRPM</button>
    <button class="tab-btn" data-tab="tab-div">Mercado vs. Opinión Pública</button>
  </nav>

  <!-- Tab 1: IEP principal -->
  <div class="tab-pane active" id="tab-iep">

    <div class="chart-panel">
      <div class="chart-header">
        <div class="panel-title">IRPM</div>
        <div class="controls">
          <div class="baseline-group">
            <label class="baseline-label">Vista:</label>
            <select class="baseline-select" id="gran-select">
              <option value="daily" selected>Diario</option>
              <option value="weekly">Semanal</option>
              <option value="monthly">Mensual</option>
            </select>
          </div>
          <div class="ctrl-divider"></div>
          <div class="baseline-group">
            <label class="baseline-label">Período:</label>
            <select class="baseline-select" id="zoom-select">
              <option value="1">1M</option>
              <option value="3">3M</option>
              <option value="6">6M</option>
              <option value="0">YTD</option>
              <option value="null" selected>Total</option>
            </select>
          </div>
          <div class="ctrl-divider"></div>
          <button class="zoom-btn active" id="dots-toggle" title="Mostrar/ocultar hitos históricos">Hitos</button>
          <div class="ctrl-divider"></div>
          <button class="zoom-btn" id="adj-toggle" title="IRPM ajustado por VIX — componente global sustraído">+VIX adj.</button>
        </div>
      </div>

      <div class="chart-wrap">
        <canvas id="iepChart"></canvas>

        <!-- Popup flotante de hitos -->
        <div id="event-popup" class="event-popup" style="display:none">
          <div class="popup-head">
            <div class="popup-num" id="popup-n">1</div>
            <div class="popup-title-wrap">
              <div class="popup-title" id="popup-title"></div>
              <div class="popup-date-tag" id="popup-date"></div>
            </div>
            <button class="popup-close" id="popup-close">&#x2715;</button>
          </div>
          <div class="popup-badges">
            <span class="popup-iep-badge" id="popup-iep"></span>
            <span class="popup-zone-badge" id="popup-zone"></span>
          </div>
          <p class="popup-body" id="popup-body"></p>
          <div class="popup-impact" id="popup-impact"></div>
        </div>
      </div>
    </div>

    <div class="scale-panel">
      <div class="scale-title">Escala de interpretacion</div>
      <div class="scale-note" id="scale-note">Baseline activo = 100. La curva se desplaza para que esa fecha valga 100; los umbrales son siempre ±10 y ±30 pts respecto al baseline.</div>
      <div class="scale-rows">__SCALE_ROWS__</div>
    </div>

    <div class="footnote">
      Pesos: 35% Capa 1 (MEP/CCL) &nbsp;&middot;&nbsp; 40% Capa 2 (bonos soberanos USD + EMBI) &nbsp;&middot;&nbsp; 25% Capa 3 (semi-volatilidad accionaria AR — proxy put-side opciones).<br>
      El IRPM mide la probabilidad implícita de continuidad del programa económico post-2027. No es predicción electoral. Baseline = 100 al 11-dic-2023 (inicio gestión Milei).
    </div>

  </div><!-- /tab-iep -->

  <!-- Tab 2: Mercado vs. Opinión Pública -->
  <div class="tab-pane" id="tab-div">

    <div class="chart-panel">
      <div class="chart-header">
        <div class="panel-title">Mercado vs. Opinión Pública — Convergencia y Divergencia</div>
        <div class="controls">
          <div class="baseline-group">
            <label class="baseline-label">Período:</label>
            <select class="baseline-select" id="div-zoom-select">
              <option value="1">1M</option>
              <option value="3">3M</option>
              <option value="6">6M</option>
              <option value="0">YTD</option>
              <option value="null" selected>Total</option>
            </select>
          </div>
          <div class="ctrl-divider"></div>
          <button class="zoom-btn" id="toggle-corr" title="Sombrear períodos de sincronía/divergencia — verde: IRPM e ICG se mueven en la misma dirección · rojo: sentidos contrarios">Sinc.</button>
        </div>
      </div>
      <div class="chart-wrap">
        <canvas id="divChart"></canvas>
        <div id="corr-tooltip" class="corr-tooltip" style="display:none"></div>
      </div>
    </div>

    <div class="scale-panel">
      <div class="scale-title">Divergencia mercado vs. opinión pública</div>
      <div class="scale-note">Series indexadas a 100 en el baseline activo. IRPM: promedio mensual. ICG: Confianza en el Gobierno (UTDT). Signo positivo = mercado más optimista que la sociedad.</div>
      <div id="div-strip" class="div-strip" style="margin-top:10px"></div>
    </div>

    <div class="footnote">
      La divergencia es el hallazgo analítico — mercado y sociedad miden cosas distintas y no tienen por qué coincidir. Las zonas de color reflejan la escala del IRPM; ICG e ICC tienen dinámicas propias.
    </div>

  </div><!-- /tab-div -->

</div>
"""


# ── JavaScript ─────────────────────────────────────────────────────────────────

def _js():
    return r"""
const ALL_DATA    = __DATA__;
const EVENTS_DATA = __EVENTS__;
const UTDT_DATA   = __UTDT_DATA__;

const currentBaseline  = '2023-12-11';
let currentZoom        = null;
let currentGranularity = 'daily';

let selectedEvent   = null;

// ── Data helpers ──────────────────────────────────────────────────────────────
function findNearest(arr, dateStr) {
  // Usar T12:00:00 para evitar problemas de timezone con fechas ISO en UTC midnight
  const t = new Date(dateStr + 'T12:00:00').getTime();
  let best = arr[0], bestD = Infinity;
  for (const pt of arr) {
    const d = Math.abs(new Date(pt.d + 'T12:00:00').getTime() - t);
    if (d < bestD) { bestD = d; best = pt; }
  }
  return best;
}

function getBaseVal(arr, dateStr) {
  const pt = arr.find(d => d.d === dateStr) || findNearest(arr, dateStr);
  return pt.v;
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
    if (!groups[key])  groups[key]  = [];
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
      d: key,
      v: avg(vals),
      s: null,
      a: aGroups[key] ? avg(aGroups[key]) : null,
    }));
}

function applyZoom(data, months) {
  if (months === null) return data;
  let cutoff;
  if (months === 'milei') {
    cutoff = '2023-12-11';  // primer dia habil del gobierno Milei
  } else if (months === 0) {
    cutoff = new Date().getFullYear() + '-01-01';
  } else {
    const dt = new Date();
    dt.setMonth(dt.getMonth() - months);
    cutoff = dt.toISOString().slice(0, 10);
  }
  return data.filter(d => d.d >= cutoff);
}

// Re-anclar después de agregar: el período que contiene el baseline debe valer 100.
// Necesario porque applyBaseline ancla un día exacto pero applyGranularity promedia
// varios días, desplazando el primer período (especialmente en vistas mensual/semanal).
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
  const data = applyGranularity(applyZoom(applyBaseline(ALL_DATA, currentBaseline), currentZoom), gran);
  return reanchorToBaseline(data, currentBaseline, gran);
}

function getZone(v) {
  if (v > 110) return { tag: 'Positivo', label: 'Por encima del baseline',   color: '#16a34a', id: 'pos' };
  if (v >= 90) return { tag: 'Neutro',   label: 'Zona baseline',             color: '#64748b', id: 'neu' };
  return            { tag: 'Negativo', label: 'Por debajo del baseline',   color: '#dc2626', id: 'neg' };
}

function getIEPAtDate(dateStr) {
  const adj = applyBaseline(ALL_DATA, currentBaseline);
  const pt  = findNearest(adj, dateStr);
  return pt.v;
}

// (gradientBgPlugin removido — reemplazado por box annotations en buildAnnotations)

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
      backgroundColor: 'rgba(22,163,74,0.07)', borderWidth: 0,
    },
    zoneNeu: {
      type: 'box', drawTime: 'beforeDatasetsDraw',
      yMin: 90, yMax: 110,
      backgroundColor: 'rgba(148,163,184,0.05)', borderWidth: 0,
    },
    zoneNeg: {
      type: 'box', drawTime: 'beforeDatasetsDraw',
      yMin: 60, yMax: 90,
      backgroundColor: 'rgba(220,38,38,0.07)', borderWidth: 0,
    },
    baseline: {
      type: 'line', yMin: 100, yMax: 100,
      borderColor: 'rgba(100,116,139,0.45)', borderWidth: 1.5,
      label: {
        display: true, content: '100',
        position: 'end', color: '#94a3b8',
        font: { size: 9, weight: '600' },
        backgroundColor: 'transparent', yAdjust: -8,
      },
    },
  };

  if (withHitos && displayData.length) {
    ANIO_MARKS.forEach(({ date, label }) => {
      const nearest = findNearest(displayData, date);
      // Solo mostrar si el label más cercano está dentro de 60 días (evita anclarse al último punto si la fecha es futura)
      const daysDiff = Math.abs(new Date(nearest.d + 'T12:00:00') - new Date(date + 'T12:00:00')) / 86400000;
      if (daysDiff > 60) return;
      anns['anio_' + label] = {
        type: 'line', scaleID: 'x', value: nearest.d,
        borderColor: 'rgba(100,116,139,0.45)',
        borderWidth: 1.5, borderDash: [5, 4],
        drawTime: 'beforeDatasetsDraw',
        label: {
          display: true, content: label,
          position: 'start', color: '#94a3b8',
          font: { size: 9, weight: '600' },
          backgroundColor: 'rgba(255,255,255,0.85)',
          yAdjust: 6,
        },
      };
    });
  }

  return anns;
}

// ── Event dot datasets ────────────────────────────────────────────────────────
// Resuelve cada evento al período que LO CONTIENE (no al más cercano en tiempo).
// Prioridad: (1) match exacto de fecha, (2) match de mes (YYYY-MM-01),
// (3) match del lunes de la semana que contiene la fecha, (4) nearest como fallback.
function resolveEventDates(displayData) {
  const resolved = new Map();
  if (!displayData || !displayData.length) return resolved;

  EVENTS_DATA.forEach(ev => {
    let pt = null;

    // 1. Match exacto (vista diaria)
    pt = displayData.find(d => d.d === ev.date);

    // 2. Match por mes (vista mensual: labels son "YYYY-MM-01")
    if (!pt) {
      const monthKey = ev.date.slice(0, 7) + '-01';
      pt = displayData.find(d => d.d === monthKey);
    }

    // 3. Match por semana que contiene la fecha (vista semanal: labels son lunes)
    if (!pt) {
      const evDt = new Date(ev.date + 'T12:00:00');
      const day  = evDt.getDay() || 7;   // 1=Lun…7=Dom
      const mon  = new Date(evDt);
      mon.setDate(evDt.getDate() - day + 1);
      const weekKey = mon.toISOString().slice(0, 10);
      pt = displayData.find(d => d.d === weekKey);
    }

    // 4. Fallback: más cercano en tiempo
    if (!pt) pt = findNearest(displayData, ev.date);

    if (pt) resolved.set(ev.n, { date: pt.d, iep: pt.v });
  });
  return resolved;
}

function buildEventDatasets(displayData) {
  const resolved = resolveEventDates(displayData);
  const dateToEvN = new Map();
  resolved.forEach((v, n) => dateToEvN.set(v.date, n));

  const posData = [], negData = [], posR = [], negR = [];
  displayData.forEach(d => {
    const evN = dateToEvN.get(d.d);
    const ev  = evN != null ? EVENTS_DATA.find(e => e.n === evN) : null;
    if (ev && ev.impact === 'positive') {
      posData.push(d.v); posR.push(8);
      negData.push(null); negR.push(0);
    } else if (ev && ev.impact === 'negative') {
      posData.push(null); posR.push(0);
      negData.push(d.v); negR.push(8);
    } else {
      posData.push(null); posR.push(0);
      negData.push(null); negR.push(0);
    }
  });

  return [
    {
      label: '_ev_pos',
      data: posData, pointRadius: posR, pointHoverRadius: 14,
      backgroundColor: '#16a34a', borderColor: '#fff',
      pointBorderColor: '#fff', pointBorderWidth: 2,
      showLine: false, fill: false, spanGaps: false, order: 0,
    },
    {
      label: '_ev_neg',
      data: negData, pointRadius: negR, pointHoverRadius: 14,
      backgroundColor: '#dc2626', borderColor: '#fff',
      pointBorderColor: '#fff', pointBorderWidth: 2,
      showLine: false, fill: false, spanGaps: false, order: 0,
    },
  ];
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
      if (ds.label === '_ev_pos' || ds.label === '_ev_neg') return;
      if (!chart.isDatasetVisible(dsIdx)) return;
      const yVal = ds.data[idx];
      if (yVal == null) return;
      const yPos = chart.scales.y.getPixelForValue(yVal);
      ctx.beginPath();
      ctx.arc(xPos, yPos, 4.5, 0, 2 * Math.PI);
      ctx.fillStyle = ds.borderColor || '#0f172a';
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();
    });
    ctx.restore();
  },
};

// ── Chart ─────────────────────────────────────────────────────────────────────
let chart;
let showAdj = false;
let popupCloseTimer = null;

function initChart() {
  const init = getDisplayData();
  const ctx  = document.getElementById('iepChart').getContext('2d');

  chart = new Chart(ctx, {
    type: 'line',
    plugins: [crosshairPlugin],
    data: {
      labels: init.map(d => d.d),
      datasets: [
        {
          label: 'IRPM',
          data: init.map(d => d.v),
          borderColor: '#0f172a', borderWidth: 2,
          pointRadius: 0, tension: 0.12,
          fill: false, spanGaps: false, order: 1,
        },
        ...buildEventDatasets(init),
        {
          label: 'IRPM ajustado VIX',
          data: init.map(d => d.a),
          borderColor: '#64748b', borderWidth: 1.5,
          borderDash: [5, 4],
          pointRadius: 0, tension: 0.12,
          fill: false, spanGaps: false, order: 2,
          hidden: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      onClick: (event, elements) => {
        for (const el of elements) {
          const ds = chart.data.datasets[el.datasetIndex];
          if ((ds.label === '_ev_pos' || ds.label === '_ev_neg') && ds.data[el.index] != null) {
            const dateStr = chart.data.labels[el.index];
            const resolved = resolveEventDates(getDisplayData());
            for (const ev of EVENTS_DATA) {
              if (resolved.get(ev.n)?.date === dateStr) {
                if (selectedEvent === ev.n) { closePopup(); return; }  // segundo click cierra
                openPopup(ev.n, event); return;
              }
            }
          }
        }
        closePopup();
      },
      onHover: (event, elements) => {
        const onDot = elements.some(el => {
          const ds = chart.data.datasets[el.datasetIndex];
          return (ds.label === '_ev_pos' || ds.label === '_ev_neg') && ds.data[el.index] != null;
        });
        chart.canvas.style.cursor = onDot ? 'pointer' : 'default';
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#fff', titleColor: '#64748b',
          bodyColor: '#1e293b', borderColor: '#e2e8f0',
          borderWidth: 1, padding: 12,
          titleFont: { size: 11 },
          bodyFont: { size: 13, weight: '700' },
          filter: item => {
            const lbl = item.dataset.label;
            if (lbl === '_ev_pos' || lbl === '_ev_neg') return false;
            return item.parsed.y != null;
          },
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
              const prefix = ctx.dataset.label === 'IRPM ajustado VIX' ? ' +VIX adj.: ' : ' IRPM: ';
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
            color: '#94a3b8', maxRotation: 90, minRotation: 90, font: { size: 10 },
            autoSkip: false,
            callback: function(val, idx) {
              const labels = this.chart.data.labels;
              const d = labels[idx];
              if (!d) return null;
              const parts = d.split('-');
              const [y, m] = parts;
              const mN = {'01':'Ene','02':'Feb','03':'Mar','04':'Abr','05':'May','06':'Jun',
                          '07':'Jul','08':'Ago','09':'Sep','10':'Oct','11':'Nov','12':'Dic'};
              // Mensual: un label por punto (siempre)
              if (currentGranularity === 'monthly') return m === '01' ? y : mN[m] + " '" + y.slice(2);
              // Diario/Semanal: solo el primer label de cada mes
              if (idx > 0 && labels[idx - 1].split('-')[1] === m) return null;
              return m === '01' ? y : mN[m] + " '" + y.slice(2);
            },
          },
          grid: { display: false }, border: { color: '#e2e8f0' },
        },
        y: {
          min: 60, max: 130,
          ticks: { color: '#94a3b8', font: { size: 10 }, stepSize: 10 },
          grid: { display: false }, border: { color: '#e2e8f0' },
        },
      },
    },
  });
}

// ── Popup ─────────────────────────────────────────────────────────────────────
function openPopup(n, chartEvent) {
  selectedEvent = n;
  const popup  = document.getElementById('event-popup');
  const canvas = document.getElementById('iepChart');
  const wrap   = canvas.parentElement;

  // canvas-relative position → wrap-relative position
  const cRect = canvas.getBoundingClientRect();
  const wRect = wrap.getBoundingClientRect();
  const relX  = chartEvent.x + (cRect.left - wRect.left);
  const relY  = chartEvent.y + (cRect.top  - wRect.top);

  const popupW = 300;
  const left   = (relX + 20 + popupW > wRect.width) ? relX - popupW - 10 : relX + 20;
  const top    = Math.max(8, relY - 70);

  popup.style.left    = left + 'px';
  popup.style.top     = top  + 'px';

  const ev  = EVENTS_DATA.find(e => e.n === n);
  const iep = getIEPAtDate(ev.date);
  const z   = getZone(iep);

  document.getElementById('popup-n').textContent      = ev.n;
  document.getElementById('popup-title').textContent  = ev.title;
  document.getElementById('popup-date').textContent   = ev.date + '  ·  ' + ev.tag;
  document.getElementById('popup-body').textContent   = ev.body;

  const iepEl = document.getElementById('popup-iep');
  iepEl.textContent   = 'IEP ' + iep.toFixed(1);
  iepEl.style.color   = z.color;
  iepEl.style.background = z.color + '14';

  document.getElementById('popup-zone').textContent = z.tag;

  const impEl = document.getElementById('popup-impact');
  impEl.textContent  = ev.impact === 'positive' ? '▲ Positivo para el programa' : '▼ Negativo para el programa';
  impEl.style.color  = ev.impact === 'positive' ? '#16a34a' : '#dc2626';

  popup.style.display = 'block';
}

function closePopup() {
  document.getElementById('event-popup').style.display = 'none';
  selectedEvent = null;
}

// ── Refresh ────────────────────────────────────────────────────────────────────
function refreshAll() {
  const disp = getDisplayData();
  const evDs = buildEventDatasets(disp);

  chart.data.labels           = disp.map(d => d.d);
  chart.data.datasets[0].data = disp.map(d => d.v);
  [1, 2].forEach((i, j) => {
    chart.data.datasets[i].data        = evDs[j].data;
    chart.data.datasets[i].pointRadius = evDs[j].pointRadius;
  });
  chart.data.datasets[3].data = disp.map(d => d.a);
  chart.options.plugins.annotation.annotations = buildAnnotations(disp, showDots);
  chart.update('none');
}

function updateHero() {
  const adj  = applyBaseline(ALL_DATA, currentBaseline);
  const last = adj[adj.length - 1];
  const v    = last.v;
  const diff = v - 100;
  const z    = getZone(v);

  document.getElementById('hero-value').textContent = v.toFixed(1);
  const diffEl = document.getElementById('hero-diff');
  diffEl.textContent  = (diff >= 0 ? '+' : '') + diff.toFixed(1) + ' pts vs baseline';
  diffEl.style.color  = diff >= 0 ? '#16a34a' : '#dc2626';

  const zEl = document.getElementById('hero-zone');
  zEl.textContent       = z.tag;
  zEl.style.color       = z.color;
  zEl.style.background  = z.color + '18';
  zEl.style.borderColor = z.color + '40';
  document.getElementById('hero-desc').textContent = z.label;

  ['pos','neu','neg'].forEach(id => {
    const el = document.getElementById('scale-row-' + id);
    if (el) el.classList.remove('current');
  });
  const activeEl = document.getElementById('scale-row-' + z.id);
  if (activeEl) activeEl.classList.add('current');
}

// ── Listeners ─────────────────────────────────────────────────────────────────
document.getElementById('gran-select').addEventListener('change', e => {
  currentGranularity = e.target.value;
  refreshAll();
  closePopup();
});

document.getElementById('zoom-select').addEventListener('change', e => {
  const v = e.target.value;
  currentZoom = (v === 'null') ? null : parseInt(v);
  refreshAll();
  closePopup();
});

document.getElementById('popup-close').addEventListener('click', closePopup);


let showDots = true;

document.getElementById('dots-toggle').addEventListener('click', function() {
  showDots = !showDots;
  chart.setDatasetVisibility(1, showDots);
  chart.setDatasetVisibility(2, showDots);
  chart.options.plugins.annotation.annotations = buildAnnotations(getDisplayData(), showDots);
  this.classList.toggle('active', showDots);
  if (!showDots) closePopup();
  chart.update();
});

document.getElementById('adj-toggle').addEventListener('click', function() {
  showAdj = !showAdj;
  chart.setDatasetVisibility(3, showAdj);
  this.classList.toggle('active', showAdj);
  chart.update();
});

// ── Divergence chart ─────────────────────────────────────────────────────────
let divChart;
const currentDivBaseline = '2023-12-11';
let currentDivZoom       = null;

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
  const iepByMonth  = {};
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

function getDivDisplayData() {
  return applyZoom(applyBaseline(ALL_DATA, currentDivBaseline), currentDivZoom);
}

function getDivMonthlyIEP() {
  // IEP diario → promedio mensual, con baseline aplicado
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
  // Re-anclar: el mes que contiene el baseline debe valer exactamente 100.
  // Sin esto, el promedio del mes parcial (ej. dic-2023 desde el día 11)
  // difiere del día exacto anclado por applyBaseline.
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
  const norm    = getDivUtdtNorm();
  const lastIcg = [...norm].reverse().find(u => u.icg !== null);
  const lastIcc = [...norm].reverse().find(u => u.icc !== null);
  const iepM    = getDivMonthlyIEP();
  const lastIep = iepM[iepM.length - 1];

  const fmtGap = gap => {
    const sign  = gap >= 0 ? '+' : '';
    const color = gap >= 0 ? '#16a34a' : '#dc2626';
    const dir   = gap > 0 ? 'mercado más optimista' : gap < 0 ? 'sociedad más optimista' : 'sin diferencia';
    return `<span style="color:${color};font-weight:600">${sign}${gap.toFixed(1)} pts</span> <span class="div-dir">(${dir})</span>`;
  };

  let html = '';
  if (lastIcg && lastIep) {
    const gap = +(lastIep.v - lastIcg.icg).toFixed(1);
    html += `<div class="div-row">
      <span class="div-dot" style="background:#4f46e5"></span>
      <span class="div-label">IRPM vs. ICG UTDT <span class="div-period">(${lastIcg.d.slice(0,7)})</span></span>
      <span class="div-vals">IRPM ${lastIep.v.toFixed(1)} vs. ICG ${lastIcg.icg.toFixed(1)}</span>
      <span class="div-gap">${fmtGap(gap)}</span></div>`;
  }
  document.getElementById('div-strip').innerHTML = html;
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
    zonePos: { type: 'box', drawTime: 'beforeDatasetsDraw', yMin: 110, yMax: 130, backgroundColor: 'rgba(22,163,74,0.07)', borderWidth: 0 },
    zoneNeu: { type: 'box', drawTime: 'beforeDatasetsDraw', yMin: 90,  yMax: 110, backgroundColor: 'rgba(148,163,184,0.05)', borderWidth: 0 },
    zoneNeg: { type: 'box', drawTime: 'beforeDatasetsDraw', yMin: 60,  yMax: 90,  backgroundColor: 'rgba(220,38,38,0.07)', borderWidth: 0 },
    baseline: {
      type: 'line', yMin: 100, yMax: 100,
      borderColor: 'rgba(100,116,139,0.4)', borderWidth: 1.5,
      label: { display: true, content: '100', position: 'end', color: '#94a3b8',
               font: { size: 9, weight: '600' }, backgroundColor: 'transparent', yAdjust: -8 },
    },
  };
}

// Contenido editorial por período — calculado con datos reales de IRPM mensual e ICG UTDT
const CORR_CONTENT = [
  { xMin: '2024-02', xMax: '2024-06', type: 'div',
    title: 'Divergencia: el mercado celebra lo que la sociedad todavía padece',
    body: 'El IRPM sube anticipando la consolidación fiscal, la caída de la inflación y el colapso del EMBI de 1.800 a ~700 bps. El ICG cae casi 20 puntos: la ciudadanía está absorbiendo el costo del ajuste — recesión, caída del salario real, tarifas en suba — sin ver aún sus beneficios. El mercado pricea el programa; la sociedad vive sus costos inmediatos.' },
  { xMin: '2024-07', xMax: '2024-07', type: 'sinc',
    title: 'Convergencia: el honeymoon se agota en ambos registros',
    body: 'IRPM e ICG corrigen juntos en julio: el ciclo de euforia inicial llega a su fin. El mercado empieza a cuestionar la sostenibilidad del crawling peg y la acumulación de reservas en el segundo semestre. La ciudadanía también enfría su aprobación. Ambos registros procesan el mismo agotamiento del momentum inicial del programa.' },
  { xMin: '2024-08', xMax: '2024-10', type: 'div',
    title: 'Divergencia: el mercado anticipa el FMI; la ciudadanía todavía no',
    body: 'El IRPM rebota fuertemente post-Black Monday de agosto y anticipa el cierre del acuerdo con el FMI. El ICG tuvo su mínimo de 2024 en septiembre — posible fatiga del ajuste y tensión cambiaria de la segunda mitad del año — antes de recuperar recién en octubre. El mercado fue varios meses adelante de la opinión pública en reconocer la fortaleza estructural del programa.' },
  { xMin: '2024-11', xMax: '2025-12', type: 'sinc',
    title: 'Convergencia histórica: 14 meses leyendo el mismo ciclo político',
    body: 'El período de mayor sincronía de la serie. Nov-dic 2024: mercado y ciudadanía comparten el optimismo del primer aniversario — superávit fiscal confirmado, inflación en baja, reservas en alza. Ago-sep 2025: ambos sienten la incertidumbre legislativa en tiempo real — IRPM en mínimos históricos, ICG en caída libre. Nov-dic 2025: el resultado electoral es procesado como señal de continuidad en los dos registros. El mercado y la sociedad nunca estuvieron tan alineados en su lectura del ciclo político-económico.' },
  { xMin: '2026-01', xMax: '2026-12', type: 'div',
    title: 'Divergencia: el mercado mira 2027; la sociedad evalúa el presente',
    body: 'Desde enero de 2026 el IRPM se estabiliza en zona de continuidad mientras el ICG cae más de 20 puntos desde el pico post-electoral. El mercado pricea un escenario 2027 con oposición fragmentada y señales de un peronismo más moderado — la "amenaza alternativa" se reduce. La ciudadanía, en cambio, evalúa el costo acumulado del ajuste estructural: inflación acumulada, salarios reales en reconstrucción lenta, tarifas más altas. Dos lecturas de dos realidades temporales distintas: el mercado descuenta el futuro electoral; la sociedad vive el presente económico.' },
];

function lookupCorrContent(xMin, type) {
  const match = CORR_CONTENT.find(c => c.type === type && xMin >= c.xMin && xMin <= c.xMax);
  return match || {
    title: type === 'sinc' ? 'Convergencia' : 'Divergencia',
    body: type === 'sinc'
      ? 'IRPM e ICG se mueven en la misma dirección.'
      : 'IRPM e ICG se mueven en sentidos contrarios.',
  };
}

// Bandas de correlación — ventana 2 meses, umbral solo en ICG.
function buildCorrAnnotations(labels, iepArr, icgArr) {
  const anns = {};
  let bandStart = null, bandType = null, bandDIep = 0, bandDIcg = 0, bandIdx = 0;
  const addBand = (from, to, type) => {
    anns['corr_' + bandIdx++] = {
      type: 'box', drawTime: 'beforeDatasetsDraw',
      xMin: labels[from], xMax: labels[to],
      yMin: 60, yMax: 130,
      backgroundColor: type === 'sinc' ? 'rgba(22,163,74,0.11)' : 'rgba(220,38,38,0.11)',
      borderWidth: 0,
      _xMin: labels[from], _type: type,
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
      bandStart = i; bandType = type; bandDIep = dIep; bandDIcg = dIcg;
    } else { bandDIep = dIep; bandDIcg = dIcg; }
  }
  if (bandStart !== null && bandType) addBand(bandStart, labels.length - 1, bandType);
  return anns;
}

let showCorr = false;

// Tooltip sigue el mouse dentro de la banda activa
function handleCorrHover(event, chart) {
  const tip = document.getElementById('corr-tooltip');
  if (!showCorr) { tip.style.display = 'none'; return; }
  const idx = Math.round(chart.scales.x.getValueForPixel(event.x));
  if (idx < 0 || idx >= chart.data.labels.length) { tip.style.display = 'none'; return; }
  const label = chart.data.labels[idx];
  const annsObj = chart.options.plugins.annotation.annotations;
  let found = null;
  for (const ann of Object.values(annsObj)) {
    if (ann._xMin && label >= ann.xMin && label <= ann.xMax) { found = ann; break; }
  }
  if (!found) { tip.style.display = 'none'; return; }
  const content = lookupCorrContent(found._xMin, found._type);
  const color   = found._type === 'sinc' ? '#16a34a' : '#dc2626';
  tip.innerHTML = `<div class="corr-tip-title" style="color:${color}">${content.title}</div><div class="corr-tip-body">${content.body}</div>`;
  const ca = chart.chartArea;
  const TW = 240, TH = 130;
  let left = event.x - TW / 2;
  let top  = event.y - TH - 14;
  if (left < ca.left)         left = ca.left;
  if (left + TW > ca.right)   left = ca.right - TW;
  if (top < ca.top)           top  = event.y + 14;
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
          borderColor: '#0f172a', borderWidth: 2,
          pointRadius: 0, tension: 0.12,
          fill: false, spanGaps: false, order: 2,
        },
        {
          label: 'ICG UTDT',
          data: icgArr,
          borderColor: '#4f46e5', borderWidth: 1.5,
          pointRadius: 0,
          tension: 0.15,
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
          backgroundColor: '#fff', titleColor: '#64748b',
          bodyColor: '#1e293b', borderColor: '#e2e8f0',
          borderWidth: 1, padding: 12,
          titleFont: { size: 11 },
          bodyFont: { size: 13, weight: '700' },
          filter: item => item.parsed.y !== null,
          callbacks: {
            title: items => {
              if (!items.length) return '';
              const d = items[0].label;
              const [y, m] = d.split('-');
              const mN = {'01':'Ene','02':'Feb','03':'Mar','04':'Abr','05':'May','06':'Jun',
                          '07':'Jul','08':'Ago','09':'Sep','10':'Oct','11':'Nov','12':'Dic'};
              return mN[m] + ' ' + y;
            },
            label: ctx => {
              const v = ctx.parsed.y;
              if (v === null) return null;
              return ` ${['IRPM', 'ICG UTDT', 'ICC UTDT'][ctx.datasetIndex]}: ${v.toFixed(1)}`;
            },
          },
        },
        annotation: { annotations: divBaseAnnotations() },
      },
      scales: {
        x: {
          type: 'category',
          ticks: {
            color: '#94a3b8', maxRotation: 90, minRotation: 90, font: { size: 10 },
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
          grid: { display: false }, border: { color: '#e2e8f0' },
        },
        y: {
          min: 60, max: 130,
          ticks: { color: '#94a3b8', font: { size: 10 }, stepSize: 10 },
          grid: { display: false }, border: { color: '#e2e8f0' },
        },
      },
    },
  });

  // Toggle Sincronía: bandas de co-movimiento IRPM vs ICG
  document.getElementById('toggle-corr').addEventListener('click', function() {
    showCorr = !showCorr;
    const { labels, iepArr, icgArr } = buildDivDatasets(getDivMonthlyIEP(), getDivUtdtNorm());
    const base = divBaseAnnotations();
    divChart.options.plugins.annotation.annotations = showCorr
      ? { ...base, ...buildCorrAnnotations(labels, iepArr, icgArr) }
      : base;
    this.classList.toggle('active', showCorr);
    divChart.update();
  });

  // Zoom select Tab 2
  document.getElementById('div-zoom-select').addEventListener('change', e => {
    const v = e.target.value;
    currentDivZoom = (v === 'null') ? null : parseInt(v);
    refreshDivChart();
  });

  updateDivStrip();
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
let divChartInitialized = false;

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const pane = document.getElementById(btn.dataset.tab);
    pane.classList.add('active');
    if (btn.dataset.tab === 'tab-div' && !divChartInitialized) {
      divChartInitialized = true;
      initDivChart();
    }
  });
});


// ── Init ──────────────────────────────────────────────────────────────────────
initChart();
updateHero();
"""


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("generate_dashboard | IEP Argentina")
    data = load_data()
    print(f"  Datos IEP: {len(data)} puntos ({data[0]['d']} a {data[-1]['d']})")
    utdt_data = load_utdt_data()
    print(f"  Datos UTDT: {len(utdt_data)} meses ({utdt_data[0]['d']} a {utdt_data[-1]['d']})")
    html = build_html(data, utdt_data)
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"  Dashboard: {OUTPUT}")
    DOCS_OUTPUT.parent.mkdir(exist_ok=True)
    DOCS_OUTPUT.write_text(html, encoding="utf-8")
    print(f"  IRPM hoy: {data[-1]['v']}")


if __name__ == "__main__":
    main()
