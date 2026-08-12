# IRPM — Índice de Riesgo Político de Mercado
**Probabilidad implícita de continuidad del programa económico post-2027 · Diario · Alta frecuencia**
Versión del stack: v0.7 · Actualizado: Sesión 12 — Nombre IRPM + dashboard con tabs, granularidad y comparativa vs. UTDT (14/05/2026)

> **Docs clave:** `CONTEXTO.md` (referencia técnica — pegar al inicio de cada sesión) · `PLAN.md` (hoja de ruta operativa)

---

## 1. Identidad del Proyecto

El **IEP** es un índice cuantitativo diario que mide la **probabilidad implícita de mercado de que el programa económico de Milei continúe después de las elecciones de 2027**, operacionalizada a través del posicionamiento en activos de deuda soberana y señales cambiarias.

**Constructo central:** el IEP responde a la pregunta "¿qué cree el mercado hoy sobre quién va a ganar la elección de 2027 y qué programa va a gobernar?" La cadena causal es `precio_alto → alguien_va_a_pagar_esta_deuda_bajo_el_esquema_actual`, no `precio_alto → Milei_gana`. Milei es relevante en tanto su continuidad es el vehículo del programa vigente, pero el constructo apunta al PROGRAMA que gobernará post-2027, no a la persona.

**Diferencia vs. versión original (v0.4):** el constructo anterior planteaba un horizonte de 3-6 meses. La evidencia empírica de mayo 2026 (spread CDS 1Y=238bps vs 2Y=509bps, diferencial yield Oct-2027 vs Oct-2028 ≈ 350bps) muestra que el mercado está priceando explícitamente el riesgo electoral 2027 en los instrumentos que el IEP ya monitorea. El índice no es una señal de estabilidad macro corriente — es un termómetro de la expectativa electoral de mediano plazo.

**Horizonte:** 18 meses hacia las elecciones de octubre 2027. A medida que se acorte el horizonte, la señal electoral se intensifica. Hoy (mayo 2026) el IEP en 106 dice: "el mercado cree que el programa llega a 2027" — coherente con lo que los analistas de mercado describen públicamente.

**No es una encuesta.** Captura posicionamiento real — dinero puesto en juego — y lo procesa como probabilidad electoral implícita.

> "El IEP extrae del mercado de bonos y divisas la probabilidad implícita de continuidad del programa post-2027."

**Diferencial frente a instrumentos existentes:**

| Instrumento | Frecuencia | Mide | Limitación |
|---|---|---|---|
| Encuestas de opinión | Mensual / bimestral | Preferencia declarada | Rezago 3-6 semanas |
| Índice Dintella / UTDT | Mensual | Confianza del consumidor | Sin granularidad política |
| EMBI+ Argentina | Diario | Default soberano | No capta señal de continuidad del programa |
| **IEP (este proyecto)** | **Diario** | **Probabilidad implícita de continuidad del programa post-2027** | No separa señal política de señal macro global |

**Ventaja competitiva:** combina comprensión del sistema político argentino + expertise en mercados locales (ROFEX, BYMA, bonos soberanos) + capacidad de comunicación. El diferencial específico es la frecuencia diaria y el formato de índice numérico, que ningún actor produce sistemáticamente.

---

## 2. Estructura del Proyecto

```
IEP/
├── CONTEXTO.md              # Referencia técnica (pegar al inicio de cada sesión)
├── PLAN.md                  # Hoja de ruta operativa (sesión por sesión)
│
├── docs/
│   └── IEP_Plan_Completo.md # Documento fundacional — versión 1.0 (mayo 2025)
│
├── data/
│   ├── raw/                 # Datos crudos de fuentes (no modificar)
│   └── processed/           # Series normalizadas y calculadas
│
├── src/
│   ├── scrapers/            # Scripts de recolección de datos
│   ├── pipeline/            # Cálculo del índice y sub-índices
│   └── dashboard/           # Visualización
│
├── outputs/                 # Dashboard HTML, reportes, exports
│
└── tasks/
    └── lessons.md           # Lecciones aprendidas por sesión
```

> **Regla:** los datos crudos en `data/raw/` son inmutables. Los procesados en `data/processed/` son siempre recalculables.

---

## 2b. Stack Técnico — Decisiones Tomadas (Ses. 2)

| Componente | Decisión | Motivo |
|---|---|---|
| Almacenamiento | **SQLite** — archivo único `data/iep.db` | Pandas-compatible, single file, migrable a Supabase en Fase 2 |
| Normalización | **Z-score rolling 252 días hábiles** | Ventana fija 2020-2025 mezclaría regímenes Fernández/Milei |
| Pesos fase 0-1 | **50% Capa 2 / 50% Capa 1** (provisorios) | Capa 3 no tiene historia; documentar explícitamente como "provisorios" |
| Activación Capa 3 | Mínimo 90 días de historia propia | Las opciones argentinas son poco líquidas |
| Pesos fase 2+ | 35/40/25 (Capa1/2/3) | Según documento fundacional — revisar con datos reales |
| Dashboard | HTML estático / Next.js | Sin decidir |
| Newsletter | Substack / Ghost | Sin decidir |

**Tablas SQLite:**
```sql
raw_prices (activo TEXT, fecha DATE, valor REAL, fuente TEXT, timestamp_carga DATETIME)
iep_diario (fecha DATE, capa1 REAL, capa2 REAL, capa3 REAL, iep_total REAL, pesos_version TEXT)
```

**Dependencias Python:**
```
pandas, sqlite3 (stdlib), requests, beautifulsoup4, lxml
```

---

## 3. Arquitectura del Índice

### Pesos provisorios (Fase 0-1)

| Capa | Activos | Peso provisional | Peso definitivo |
|---|---|---|---|
| **1 — Señales cambiarias y futuros** | Brecha MEP/CCL + ROFEX | 50% | 35% |
| **2 — Bonos soberanos USD** | GD30/AL30/GD35 + EMBI + law spread | 50% | 40% |
| **3 — Opciones BYMA** | YPF, Edenor, Telecom, Pampa | 0% hasta 90 días de historia | 25% |

> Los pesos definitivos son los del documento fundacional. Los provisorios se documentan como tales en todo output publicado.

> **Principio de pesos dinámicos (implementar Fase 1):** el spread post-2027 tiene peso creciente a medida que se acerca diciembre 2027. Hoy ≈ 0% dentro de Capa 2, sube hasta dominar la capa en plena campaña 2027. La revisión semestral de pesos debe contemplar este ajuste temporal.

---

## 3a. Capa 2 — Bonos Soberanos USD (50% provisional / 40% definitivo)

*Primera capa en implementar — mayor liquidez, datos más accesibles.*

| Componente | Señal política | Fuente | Estado |
|---|---|---|---|
| **GD30 paridad** | Precio del bono NY como % del valor nominal. Sube = el mercado cree que Argentina paga. | IOL / Rava | Pendiente scraper |
| **AL30 paridad** | Mismo, pero bajo ley argentina. Spread vs. GD30 = riesgo de restructuración unilateral. | IOL / Rava | Pendiente scraper |
| **GD35 paridad** | Bono más largo — captura expectativa de largo plazo. | IOL / Rava | Pendiente scraper |
| **Law spread (GD30 − AL30)** | Cuando se amplía: el mercado teme una restructuración bajo ley local. Señal directa de riesgo político interno. | Calculado de los anteriores | Pendiente cálculo |
| **EMBI+ Argentina** | Spread de riesgo soberano vs. treasuries (en bps). Indicador global más citado. | API BCRA (`api.bcra.gob.ar/estadisticas/v2.0/`) — sin autenticación | Pendiente scraper |
| **Law spread (GD30−AL30)** ← **SEÑAL ELECTORAL PRINCIPAL** | Diferencial entre bono NY y bono ley argentina. Cuando sube: mercado teme reestructuración bajo ley local = gobierno kirchnerista. Validación empírica (Ses. 10): z=-2.11 en mínimo IEP sep-2025, z=+1.37 en máximo dic-2024 — correlación perfecta con todos los hitos históricos. r=0.349 con IEP. | Calculado: GD30D − AL30D | **ACTIVO** — Componente más directo de señal electoral |
| ~~Spread post-2027 (GD30D − GD35D)~~ | DESCARTADO en Ses. 10 tras validación. Tendencia secular (+1.86 en 2022 → +9.18 en 2024 → -10.86 en oct-2025-hoy) confundida con amortización de GD30 y cambio de estructura. Correlación con IEP: r=0.114 (no significativo). No es señal electoral limpia. | — | **RECHAZADO** |

**Rangos históricos de referencia:**
- EMBI Fernández peak: ~2.800 bps (2022) | EMBI Milei post-acuerdo FMI: ~700 bps (2025)
- Law spread: explotó en 2020 (restructuración), se comprimió en 2025
- Spread post-2027: ~300 bps en mayo 2026 (calibrado por Gemini Deep Research, mayo 2026)

**Benchmarks EMBI para calibración de escala IEP:**
- Escenario reelección consolidada: EMBI < 400 bps
- Escenario cambio de gobierno priceado: EMBI > 1.500 bps

---

## 3b. Capa 1 — Señales Cambiarias y Futuros (35% definitivo)

*Blend 50/50 de MEP y ROFEX_1M_EQUIV. Script: `calcular_capa1.py` (lee ROFEX de raw_prices).*

| Componente | Señal política | Fuente | Estado |
|---|---|---|---|
| **MEP (AL30_ARS/AL30D_USD)** | Gap entre dólar financiero y oficial. Alto relativo = fuga a dólares = señal mala. z-score rolling 252d sobre log(MEP), invertido. | PPI API — ratio AL30/AL30D | **ACTIVO** — 1065 ruedas 2022-hoy |
| **ROFEX_1M_EQUIV** | Precio forward implícito a 1 mes (equiv.). Premium alto sobre MEP = devaluación esperada = señal mala. z-score rolling 252d sobre premium, sin invertir. | SSPM (2022-2024-04) + BCR PDF (2024-04-2025-10) + PPI normalizado (2025-10-hoy) | **ACTIVO** — 6009 filas desde 2009. Script: `calcular_rofex_signal.py` |
| **ROFEX electoral kink** (futuro) | DLR_DIC27/DLR_ENE27−1. Prima de devaluación post-electoral vs. pre-electoral. | PPI FUTUROS (acumulando desde oct-2025) | **PENDIENTE** — activar ~agosto 2026 cuando haya ≥63 días de DLR_ENE27 y DLR_DIC27 |

**Blend actual:** `capa1 = 0.5 × z_mep + 0.5 × z_rofex_premium`

**Limitación documentada (Ses. 11):** oct-2025, los primeros ~19 días del período PPI (Oct 8 - Oct 26) tienen un artefacto de ~6pp en el premium porque PPI no capturó los contratos 1M que ya habían expirado (DLR_NOV25, etc.) — solo tiene contratos 7M+ en ese momento. La curva tenía contango pronunciado pre-electoral. El artefacto se absorbe en el z-score rolling. **Spot-check BCR confirmado:** 13/15 fechas verificadas contra PDFs originales con diferencia = 0.0 exacto.

---

## 3c. Capa 3 — Opciones BYMA (0% hasta 90 días de historia)

*Diferida. Arrancar a recolectar datos desde implementación; activar en el índice cuando haya historia suficiente.*

| Componente | Señal política | Activos monitoreados |
|---|---|---|
| IV sectorial | IV empresas reguladas (político) vs. exportadoras (macro) | YPF, Edenor, Telecom, Pampa |
| Put/Call ratio | Aumento de puts = cobertura ante reversión política | YPF, Edenor, Telecom, Pampa |
| Skew electoral | Asimetría de distribución implícita cerca de elecciones | YPF, Edenor, Telecom, Pampa |

---

## 3e. Capa Analítica Secundaria — Volatilidad del Índice

*No es un componente del IEP. Es una señal de segundo orden para el dashboard y el newsletter.*

| Señal | Definición | Cuándo activar |
|---|---|---|
| **Volatilidad GARCH(1,1) del IEP** | Modela la volatilidad condicional del índice compuesto. Alta volatilidad = incertidumbre electoral creciente, señal de alerta para carteras conservadoras. | Fase 1 — cuando haya mínimo 60 días de IEP diario |

---

## 3d. Normalización y Construcción del Índice Compuesto

**Z-score rolling 252 días hábiles:**
```python
# Para cada serie de precios:
z_score = (valor_hoy - media_rolling_252d) / std_rolling_252d
# Mapeado a escala IEP con baseline=100 al 27-oct-2025
```

**Ventana de suavizado:** media móvil de 5 ruedas (semana bursátil) sobre el IEP compuesto diario.

**Baseline = 100** → 11 de diciembre de 2023 (inicio de la gestión Milei). El índice mide cuánto se aleja el mercado, hacia arriba o hacia abajo, de la lectura que tenía cuando el programa empezó.

**Revisión de pesos:** semestral, o ante cambios estructurales de mercado.

---

## 4. Fuentes de Datos — Estado y Acceso

| Fuente | Qué provee | Acceso | Estado | Prioridad |
|---|---|---|---|---|
| **PPI API** | GD30D / AL30D / GD35D (paridad USD) + MEP via ratio AL30/AL30D | ppi-client — credenciales en `INVERSIONES/ENGINE/API KEY PPI.txt` | **ACTIVA** — 1062 ruedas 2022-hoy | 1 |
| **API BCRA** | EMBI+ Argentina (serie histórica) | v2.0 y v3.0 deprecadas — sin endpoint funcional | **INACTIVA** | 1 |
| **Rava Bursatil** | EMBI/Riesgo Pais (bps reales, OHLC diario, ultimos ~366 dias) | Scraping `_chartData` de `/perfil/RIESGO%20PAIS` — sin auth | **ACTIVA** — 366 dias desde 2025-05-08 | 1 |
| **GD30D via PPI (proxy EMBI)** | Precio bono como proxy EMBI para 2022-2025 | PPI API — ya disponible en DB | **ACTIVA** — backfill completo | 1 |
| **dolarapi.com** | Dólar MEP / cotizaciones actuales | REST sin auth | Activa (solo tiempo real, sin historia) | 2 |
| **Primary/Matba-Rofex** | Curva de futuros ROFEX | API REST con autenticación | Pendiente registrar | 2 |
| **BYMA** | Opciones sobre acciones | API / scraping | Pendiente evaluar | 3 |

**Criterio de selección:** preferir API sobre scraping. Si hay scraping, verificar TOS. Priorizar fuentes con historia 2020-presente.

---

## 5. Escala de Interpretación

| Rango IEP | Interpretación | Equivalente histórico |
|---|---|---|
| **> 110** | Mercado pricea reelección con mayor convicción que post-legislativas 2025 | — (zona nueva) |
| **90 – 110** | Zona baseline — continuidad del programa creíble | Post-legislativas oct-2025 |
| **70 – 89** | Optimismo moderado con ruido | H1 2025 (pre-acuerdo FMI) |
| **40 – 69** | Incertidumbre activa | 2024 pre-estabilización |
| **< 40** | Stress político severo | Período Massa/Guzmán (2022) |

---

## 6. El Problema que Resuelve

Argentina enfrenta un ciclo electoral de alta intensidad 2025-2027. Existe demanda concreta no satisfecha:

- **Inversores financieros:** necesitan señales políticas procesadas, no ruido mediático
- **Consultoras políticas:** carecen de métricas de mercado integradas en sus modelos de riesgo
- **Medios:** compiten por narrativas con datos propios y diferenciados
- **Organismos internacionales:** monitorean el riesgo político argentino de forma sistemática
- **Partidos y campañas:** necesitan termómetros de credibilidad distintos a encuestas internas

---

## 7. Audiencias Objetivo

| Segmento | Job-to-be-done | Disposición a pagar |
|---|---|---|
| Traders / analistas de renta fija | "Quiero una señal política procesada, no leer diarios" | Alta (newsletter individual) |
| Consultoras de riesgo político | "Necesito métricas de mercado para mis informes de clientes" | Alta (institucional) |
| Research de brokers / bancos | "Quiero un índice citeable para mis reportes" | Alta (institucional) |
| Periodistas financieros | "Necesito datos propios, no depender de Bloomberg" | Media (newsletter) |
| Equipos de campaña (2027) | "¿Cómo está el mercado leyendo nuestra viabilidad?" | Alta (consultoría) |
| Organismos multilaterales (FMI, BID) | Monitoreo sistemático del riesgo político | Media–Alta |

---

## 8. Validación del Constructo

**Principio:** los benchmarks de validación deben ser independientes de los componentes del índice. El EMBI es componente de Capa 2 y por lo tanto **no puede ser validador externo** (circularidad: validar un promedio contra uno de sus términos es metodológicamente inválido). El EMBI puede aparecer en análisis comparativo como contexto, no como criterio de validez.

| Validación | Hipótesis | Criterio de éxito | Criterio de falla |
|---|---|---|---|
| **vs. encuestas de aprobación** | IEP es leading indicator con lag k = 2-4 semanas respecto a encuestas de aprobación | Caída del IEP precede caída de aprobación | IEP no tiene valor predictivo sobre encuestas |
| **Análisis de eventos** | Shocks en la serie del IEP deben corresponder con eventos políticos documentados | ≥ 70% de los 10 eventos más grandes tienen causa política identificable | Los shocks más grandes no tienen correlato político |

> **Nota sobre ICG/ICC-UTDT:** el IEP mide expectativas del mercado financiero; el ICG/ICC mide opiniones de la sociedad. Son constructos distintos por diseño. La baja correlación entre ellos no es un fallo metodológico del IEP — es justamente el espacio analítico interesante: los períodos en que mercado y sociedad leen la situación de forma divergente. Esta comparación se desarrolla como análisis propio en la **Idea A** del dashboard (panel de convergencia/divergencia).

**Falsabilidad:** el IEP fallaría como constructo si (a) los shocks en la serie no se corresponden con eventos políticos documentados, o (b) el IEP no tiene poder predictivo sobre encuestas de aprobación con ningún rezago entre 0 y 8 semanas.

> **Integración futura (Fase 3):** cuando RadarPolitico.ai esté operativo como producto, el IG (Índice de Gobierno) puede sumarse como validador externo adicional. Por ahora no existe como fuente disponible.

---

## 8b. Limitaciones y Alcance Declarado

Estas limitaciones no invalidan el índice, pero deben estar explícitas en toda comunicación pública y en la metodología.

**Señal política no separable de señal macro.** El IRPM no puede aislar movimientos de origen político de movimientos de origen macroeconómico o global. Las tasas de la Fed, el sentimiento de emergentes y la liquidez internacional mueven los mismos activos. La interpretación política de los z-scores es editorial: está informada por el contexto, no producida por el estadístico. Esta limitación es compartida con el EMBI y con todos los índices de riesgo soberano.

> **Cuantificación empírica (Bekaert et al. 2014):** en promedio, menos de un tercio del spread soberano de mercados emergentes refleja riesgo político puro. Los otros dos tercios corresponden a fundamentales macro locales y factores globales. Esto implica que el IRPM captura *riesgo soberano total con énfasis político*, no riesgo político puro. La excepción es el **law spread (GD30−AL30)**: al ser un diferencial relativo entre dos bonos del mismo emisor bajo distinta jurisdicción, cancela automáticamente los factores globales (β_global) y gran parte de los fundamentales locales. Es el componente teóricamente más limpio del índice. Para toda comunicación pública, la formulación correcta es: "el IRPM extrae del mercado la probabilidad de continuidad del programa" — no "el IRPM mide el riesgo político".

> **Implicación operativa:** cuando el VIX supera 20 o los spreads EM se amplían globalmente, los movimientos del IRPM deben interpretarse con mayor cautela. El dashboard incluirá (OPT-2) una nota de contexto automática según umbral de VIX.

**Baseline convencional, no técnico.** La elección de IRPM=100 el 11-dic-2023 (inicio de la gestión Milei) es una convención narrativa, no una estimación de valor fundamental. Es análoga al año base de un IPC: metodológicamente válida si se declara como tal. El baseline determina si la serie histórica aparece "sobre" o "bajo" 100 — lo que define la narrativa del índice: un IRPM por encima de 100 significa que el mercado cree más en la continuidad del programa que el primer día de gestión; por debajo, menos. Esta convención está documentada y no debe presentarse como resultado técnico.

**Consenso de participantes del mercado, no de la sociedad.** El mercado de capitales argentino es ilíquido, con cepo cambiario, intervención activa del BCRA y flujos concentrados en pocos operadores institucionales. El IEP representa "lo que el mercado de bonos y dólares financieros pricea hoy", no "lo que piensa la sociedad argentina". Es un instrumento útil para inversores, analistas y gestores de riesgo precisamente porque ese es su foco; pero no debe extenderse a representaciones sobre la sociedad en general.

**Riesgo de feedback loop (escala con adopción).** Si el IEP es citado en medios financieros y usado para operar, puede retroalimentar los precios que construye. Este riesgo es irrelevante en Fase 0 (uso interno), empieza a ser relevante en Fase 2 (co-branding con broker). Mitigación: publicar con rezago T+1 respecto a los precios usados en el cálculo; mantener metodología pública para que los participantes puedan descontar el sesgo.

**Instrumentos de deuda en pesos fuera del alcance.** El IRPM no captura bonos duales (CER/TAMAR), Lecaps ni otros instrumentos en moneda local. La demanda por duration post-2027 en pesos es una señal complementaria de continuidad del programa — la oversubscription 16x del AO28 en junio 2026 es un ejemplo concreto — pero no es incorporable al índice sin contaminar la señal con expectativas de inflación y tasas locales, que son factores no políticos empaquetados en el mismo precio. Los instrumentos en USD que usa el IRPM eliminan esa contaminación por construcción. Adicionalmente, la demanda de instrumentos en pesos puede reflejar captivos regulatorios (AFIP, FGS) más que convicción privada, reduciendo su valor como señal de mercado libre.

**Señal electoral parcialmente capturada — falta estructura de plazos.** El IEP captura la probabilidad electoral a través del law spread (señal más directa disponible) y los niveles de bonos. Lo que NO captura es el diferencial de plazos entre instrumentos que vencen antes vs. después de 2027. Este "kink electoral" existe en el mercado (evidencia mayo 2026: CDS 1Y=238bps vs 2Y=509bps; yield Oct-2027 ~5% vs Oct-2028 ~8.5%) pero no es capturable con los instrumentos actuales porque todos los bonos del IEP (GD30, AL30, GD35) vencen post-2027. **El ROFEX electoral kink** (diferencial de contratos DLR antes y después de oct-2027) resolverá este gap cuando esté disponible (~agosto 2026, cuando haya 63 días de historia en PPI). La señal `spread GD30D−GD35D` fue evaluada y DESCARTADA (Ses. 10) por tendencia secular no electoral (r=0.114 con IEP).

---

## 9. Integración con el Ecosistema

| Proyecto | Qué aporta al IEP | Qué recibe del IEP |
|---|---|---|
| **RadarPolitico.ai** | Contexto narrativo mediático (IG semanal) — para validar convergencia señal mercado/medios | Capa de mercado para enriquecer análisis del IG |
| **LegiscopeAR** | Señal de alineamiento legislativo — si los aliados rompen, el mercado debería responder | Lectura del mercado sobre las alianzas políticas |

**Hipótesis de convergencia:** cuando el IG (RadarPolitico) cae Y el IEP baja en los días siguientes = señal política fuerte. Cuando divergen = tensión a resolver con análisis editorial.

---

## 10. Modelo de Negocio

| Vertical | Audiencia | Precio | Meta Año 1 |
|---|---|---|---|
| **Newsletter individual** | Periodistas, analistas, traders | USD 20/mes | 100 suscriptores = USD 2.400/mes |
| **Newsletter institucional** | Brokers, consultoras, medios | USD 100/mes | 15 orgs = USD 1.800/mes |
| **Informes por evento** | Fondos, consultoras de riesgo | USD 200-500 | 6 inf × 12 clientes = USD 18.000 anuales |
| **Consultoría experta** | Embajadas, fondos PE, campañas | USD 800-2.000/sesión | 8 sesiones = USD 9.600 |
| **Dashboard SaaS** (Año 2) | Institucional multi-usuario | USD 300-600/mes/org | — |
| **API de datos** (Año 2) | Fintech, hedge funds | USD 500-1.500/mes | — |

**Proyección conservadora Año 1:** ~USD 69.600

**Break-even operativo:** 1 cliente institucional (USD 200/mes) cubre toda la infraestructura técnica.

---

## 11. Riesgos y Mitigaciones

| Riesgo | Mitigación |
|---|---|
| Acceso a datos de opciones BYMA (escasos históricamente) | Arrancar con Capas 1 y 2. Capa 3 al 0% hasta tener historia. |
| Correlación baja con encuestas | Diseñar la validación como investigación pública. Los resultados intermedios también son publicables. |
| Contagio financiero externo (beta EM) | Incorporar filtro de componente beta de mercados emergentes como variable de control. |
| Competencia de medios financieros | La ventaja es la interpretación política experta y la velocidad de llegada. Ser primero importa. |
| Baja volatilidad política | En escenarios estables, el índice valida el consenso y sigue siendo útil como confirmación. |
| Mezcla de regímenes en normalización | Z-score rolling 252d en lugar de ventana fija 2020-2025. ✅ Resuelto Ses. 2. |

---

## 12. Decisiones Técnicas — Log

| Decisión | Opción elegida | Alternativa descartada | Motivo | Sesión |
|---|---|---|---|---|
| Stack almacenamiento | SQLite | CSV flat files | CSV es frágil para series temporales con backfill y correcciones | Ses. 2 |
| Normalización | Z-score rolling 252d | Z-score fijo 2020-2025 | El período 2020-2025 mezcla regímenes Fernández/Milei con niveles de riesgo incomparables | Ses. 2 |
| Capa 1 inicio | Brecha MEP/CCL | ROFEX API | Misma señal de riesgo político, cero fricción técnica para conseguir datos con historia | Ses. 2 |
| Capa 3 timing | Diferir, 0% hasta 90 días historia | Incluir desde el inicio | Opciones argentinas son poco líquidas; asignarles 25% sin historia es irresponsable metodológicamente | Ses. 2 |
| Añadir EMBI a Capa 2 | Sí, como componente | No incluir | Es el indicador global más citado; API BCRA pública; sirve además como benchmark de validación | Ses. 2 |
| Law spread AL/GD | Sí, como componente separado | Tratar como variante del mismo instrumento | Señal única: diferencia entre riesgo de restructuración bajo ley local vs. internacional | Ses. 2 |
| EMBI histórico 2022-2025 | dolarito.ar API (`api/frontend/indices/riesgoPais`) | GD30D proxy temporal | Header auth-client necesario; 7072 registros desde 1998 en un solo GET | Ses. 8 |
| Capa 3 señal | Semi-volatilidad a la baja del basket YPFD/GGAL/PAMP/TECO2 | IV opciones BYMA (sin historia) | Proxy del put-side con datos disponibles hoy; vol completa confunde euforia con miedo | Ses. 9 |
| Pesos definitivos | 35/40/25 activados | Esperar Capa 3 con IV real | Las 3 capas convergen en −3.2 en sep-2025; coherencia empírica validada | Ses. 9 |
| ROFEX histórico gap | BCR Boletines PDF (scraping pdfplumber) | Modelar crawling peg extrapolado | BCR publica precio de ajuste DLR diariamente — fuente oficial, spot-check 13/13 OK | Ses. 10-11 |
| Blend ROFEX en Capa 1 | 50/50 MEP + ROFEX_1M_EQUIV | Solo MEP | ROFEX agrega información de las expectativas de devaluación de corto plazo independiente del nivel del MEP | Ses. 11 |
| Signo z_rofex | `rolling_zscore(premium)` sin inversión | `−rolling_zscore(premium)` | Premium alto (ROFEX cerca de MEP) = menos miedo devaluatorio = señal positiva para IEP | Ses. 11 |

---

## 13. Log de Sesiones

### Sesión 21 — 12/08/2026 · OPT-7 + split YPFD + OPT-4 (análisis de eventos)

**IRPM al cierre:** bruto=103.6 / ajustado=105.1 (VIX=14.9, MEP=1524.8, EMBI=466).

**OPT-7 — Forward-fill en fechas de pago de bonos (`calcular_capa2.py`):**
Los bonos GD30, AL30, GD35 pagan cupón + amortización el 9 de enero y 9 de julio. La paridad cae mecánicamente ~13% en la fecha ex-pago y el z-score lo interpretaba como señal política negativa. Fix: forward-fill con el precio pre-ventana como referencia fija (±2 días calendario antes de cada fecha de pago, umbral >2.5%). 22 caídas mecánicas detectadas y corregidas. Jul-8-2026: IRPM se mantuvo en 107.5 (antes caía a 101.2). Limitación documentada: primer día post-ventana muestra el precio real ex-div, causando una caída menor (~1-3 pts). Solución definitiva diferida: precios ajustados / TIR.

**Split YPFD 10:1 (3-ago-2026) + backfill gap Jul-24 → Aug-4:**
YPF hizo un split 10:1 el 3-ago. El precio pasó de 82,900 a 8,105 ARS. `calcular_capa3.py` calculaba ese -90% como retorno real, colapsando Capa3 a z=-12.27 e IRPM a 71.7 (desde 105.5). Fix: calendario `STOCK_SPLITS` en `calcular_capa3.py` — divide precios pre-split por el ratio antes de calcular log returns. 1108 precios YPFD ajustados (raw_prices conserva valores originales de PPI). Simultáneamente se backfillaron las 8 ruedas de gap (scraper_acciones y scraper_bonos --desde 2026-07-23). IRPM post-fix: 103.6.

**OPT-4 — Análisis de eventos políticos:**
`data/eventos_politicos.json` — 15 eventos Argentina 2022-2026 con tipo, severidad esperada, dirección y delta observado.
`src/analysis/analisis_eventos.py` — cruza el JSON con la serie IRPM (ventana ±5 ruedas), verifica dirección/magnitud, y valida el criterio de ≥70% de los top shocks explicados. Correr con `--guardar` para actualizar `irpm_delta_observado` en el JSON.
Resultado validación: **14/20 = 70% ✓ APROBADO**.
Hallazgos sorpresivos documentados en PLAN.md §OPT-4: renuncia Guzmán (+3.2, mercado lo leyó positivo), ballotage (+8.4, ya priceado), Black Monday (+5.8, Argentina no correlacionó), legislativas 2025 (+5.9, ya anticipadas).

**Archivos nuevos/modificados:**
- `src/pipeline/calcular_capa2.py` — OPT-7: `_PAYMENT_WINDOW`, `ffill_payment_dates()`
- `src/pipeline/calcular_capa3.py` — `STOCK_SPLITS`, `apply_splits()`
- `data/eventos_politicos.json` — nuevo
- `src/analysis/analisis_eventos.py` — nuevo
- `tasks/lessons.md` — 3 lecciones nuevas (OPT-7, split YPFD, gap Task Scheduler)

---

### Sesión 16 — 19/05/2026 · Bug fix pipeline ROFEX + update de datos

**Bug corregido — dependencia circular calcular_rofex_signal.py:**
`calcular_rofex_signal.py` (paso 7 del pipeline) leía el activo `MEP` de raw_prices, pero `MEP` lo guarda `calcular_capa1.py` (paso 8). En consecuencia, los últimos días hábiles sin MEP previo quedaban fuera de la serie ROFEX_UNIFIED. Fix: nueva función `load_mep()` que computa MEP on-the-fly desde AL30_ARS/AL30D_USD (disponibles desde el paso 1 de scrapers).

**Impacto del fix:** ROFEX_UNIFIED ahora llega a la fecha más reciente en cada corrida. IRPM 19/05 con datos correctos: bruto=103.0 / ajustado=104.4 (vs. 102.2/103.7 en el run buggy).

**Pipeline actualizado:** `calcular_rofex_signal.py` — función `load_mep()` reemplaza `load_series("MEP")`.

**Estado al cierre:** pipeline de 13 pasos operativo. IRPM bruto=103.0 / ajustado=104.4 (19/05/2026). Dashboard v3 regenerado. Lección registrada en `tasks/lessons.md`.

---

### Sesión 15 — 19/05/2026 · OPT-1 + Dashboard overhaul completo

**OPT-1 — Reponderación interna de Capa 2:**
Pesos explícitos en `calcular_capa2.py` (v3): law_spread=35%, GD30=20%, AL30=20%, GD35=10%, EMBI=15%. Media ponderada normalizada por componentes disponibles (cuando EMBI no hay, se renormalizan los 4 restantes ÷0.85). Rango histórico: 70.5–115.3. Versión DB: `35-20-20-10-15-v3`.

**Dashboard Tab 1 — renovación completa:**
- Gradiente → 3 bandas planas de color (box annotations: verde >110, gris 90-110, rojo <90)
- Dots de hitos: sobre la línea (d.v), verde para positivos / rojo para negativos, click abre popup
- `resolveEventDates`: prioridad exacta → mes → semana → nearest (resuelve timezone)
- **8 hitos**: + corrección Ago 2024 (Black Monday) + shock Trump Abr 2025 + recuperación Jun 2025 + pax política Abr 2026. Contenido editorial revisado con valores post-OPT-1.
- **Líneas de aniversario** punteadas: Año 1 (dic-2024), Año 2 (dic-2025)
- **Toggle "Hitos"**: controla dots + líneas de aniversario juntos
- **Toggle "+VIX adj."**: independiente, muestra IRPM ajustado (línea punteada gris)
- **Controles**: Vista/Período/Baseline como `<select>` desplegables (antes botones)

**Dashboard Tab 2 — renovación completa:**
- ICC eliminado — solo ICG (Índice de Confianza en el Gobierno)
- Zonas de color idénticas a Tab 1, escala unificada 60–130
- Estructura igual: chart-panel + scale-panel + footnote (explicativo fuera del gráfico)
- **Toggle "Sinc."**: bandas de co-movimiento IRPM/ICG, verde = misma dirección, rojo = sentidos contrarios
- **Hover editorial**: tooltip sigue el mouse, contenido específico por período (5 períodos con narrativa propia):
  - Feb-Jun 2024 (rojo): "el ajuste que el mercado celebra, la sociedad siente"
  - Jul 2024 (verde): "corrección compartida, honeymoon se agota"
  - Ago-Oct 2024 (rojo): "el mercado anticipa el FMI, la ciudadanía todavía no"
  - Nov 2024–Dic 2025 (verde): "14 meses leyendo el mismo ciclo"
  - Ene 2026+ (rojo): "el mercado mira 2027, la sociedad evalúa el presente"

**Archivos modificados:** `calcular_capa2.py`, `calcular_iep.py` (recalculado), `calcular_ajuste_global.py` (recalculado), `generate_dashboard.py`.

---

### Sesión 14 — 15/05/2026 · Evaluación bibliográfica + IRPM ajustado por VIX

**Objetivo:** evaluar el IRPM contra 10 fichas bibliográficas e implementar la Oportunidad A (descomposición macro explícita).

**Fichas analizadas:** Bekaert et al. (2014), Nogués-Grandes (2001), Kim (2018), Arce-Morgan-Werquin (2025), Brooks-Cunha-Mosley (2026), Ichev-Spruk (2026), Reinhart-Rogoff, Sonenshine, KPMG Economic Compass (mayo 2026), FMI GFSR 2025.

**5 gaps críticos identificados:**
1. Sin control macro explícito — z-scores capturan señal global + local indistinguiblemente (Bekaert, Nogués-Grandes)
2. Sin señal de conflicto social — protestas preceden al mercado como leading indicator (Arce-Morgan-Werquin)
3. Z-scores adaptan lento post-shock estructural (Ichev-Spruk)
4. Sin calendario de rollover — $23B en vencimientos 2027 no modula la interpretación (Reinhart-Rogoff)
5. Feedback loop no gestionado — si el IRPM alcanza visibilidad mediática puede influir lo que mide (Brooks-Cunha-Mosley)

**Validaciones que confirma la bibliografía:**
- Law spread como señal más limpia: beta-neutral por construcción ✅ (Bekaert)
- ROFEX electoral kink: prima de Kim directamente operacionalizada ✅
- Tab 2 mercado vs. sociedad: mecanismo documentado en Brasil 2022 ✅ (Brooks)

**Implementado — Oportunidad A (Bekaert / Nogués-Grandes):**
- `src/scrapers/scraper_vix.py` — VIX diario via yfinance. 1348 filas 2021-hoy.
- `src/pipeline/calcular_ajuste_global.py` — regresión rolling OLS 252d de cada capa contra z_vix. Residuos = señal argentina pura. Misma escala/baseline que iep_total.
- Nuevas columnas en `iep_diario`: `capa1_adj`, `capa2_adj`, `capa3_adj`, `iep_ajustado`
- Dashboard: toggle "+VIX adj." en Tab 1 — línea punteada gris superpuesta
- `update_daily.py`: 13 pasos (antes 11)
- Bug fix: `resolveEventDates()` en `onClick` del dashboard corregido (se llamaba sin args)

**Resultados empíricos:**

| Capa | r(VIX) | R² | Interpretación |
|---|---|---|---|
| Capa 1 (MEP/ROFEX) | +0.073 | 0.5% | Casi nula — MEP es local por construcción |
| Capa 2 (bonos) | −0.192 | 3.7% | Moderada — GD30 se mueve con el apetito global |
| Capa 3 (semi-vol) | −0.041 | 0.2% | Mínima |

El IRPM ya era bastante inmune al VIX por diseño. La corrección es pequeña en promedio pero puede ser 4-6 pts en momentos de VIX extremo.

**Gap hoy (15/05/2026):** bruto=100.7 / ajustado=102.0 / gap=+1.3 (VIX=18.1 comprime levemente el bruto).

**Interpretación del gap:** positivo = VIX comprime el bruto → ajustado mejor que titular. Negativo = VIX inflaba el bruto → la señal argentina pura era peor.

---

### Sesión 13 — 14/05/2026 · Validación teórica del constructo

**Objetivo:** validar la arquitectura del IRPM contra literatura académica sobre riesgo político en mercados emergentes.

**Research analizado:** "Arquitectura del Riesgo Político: Reacción de los Mercados Financieros y Sostenibilidad de la Deuda en Argentina y Economías Emergentes" — marco teórico de Bekaert et al. 2014 (NPRSS), Pástor & Veronesi 2012-2013 (shocks políticos), evidencia Argentina/México/Brasil.

**Confirmaciones:**
- Constructo central (willingness to pay) alineado con la teoría dominante ✅
- Law spread: teóricamente el componente más limpio — beta-neutral ✅
- ROFEX electoral kink: directamente justificado por teoría de prima electoral en estructura de plazos ✅
- Capa 3 basket (YPF/Edenor/Pampa/Telecom): validado por "Efecto Milei" sectorial ✅
- Tab 2 (divergencia mercado-sociedad): base en mecanismo "voting cues" Brasil 2022 ✅
- Hitos como "desastres raros" persistentes: morfología de serie histórica coherente con la teoría ✅

**Hallazgo clave para comunicación:** <1/3 del spread soberano es riesgo político puro (Bekaert et al.). Formulación correcta del IRPM: "riesgo soberano con énfasis político", no "riesgo político puro". Actualizado en §8b.

**Optimizaciones generadas:** 6 acciones concretas en §0.7 del PLAN.md (OPT-1 a OPT-6).

---

### Sesión 12 — 14/05/2026 · Dashboard v2 + nombre IRPM

**Nombre:** IEP → **IRPM** (Índice de Riesgo Político de Mercado). Alias informal: "Riesgo Kuka".

**Dashboard (`outputs/dashboard.html`):**
- 2 tabs: IRPM (principal) + Mercado vs. Opinión Pública
- Tab 1: granularidad D/S/M, timeframe 1M/3M/6M/YTD/Total, baseline selector. Datos solo desde dic-2023.
- Tab 2: IRPM mensualizado vs. ICG/ICC UTDT, todos indexados al baseline activo. Toggles de leyenda. Lazy init.
- Sin dots en líneas. Dots de hitos en eje X (y=62, clickeables).

**Scraper UTDT:** `src/scrapers/scraper_utdt.py` — ICG desde texto HTML + ICC desde PDF. Paso 5 del pipeline. CSVs propios en `data/`. Datos a abril 2026.

**Fix metodológico:** ICG/ICC-UTDT removidos de la validación. La divergencia mercado↔sociedad es el hallazgo analítico del Tab 2, no un criterio de éxito/fracaso del índice.

---

### Sesión 11 — 13/05/2026 · Señal ROFEX integrada en Capa 1 + validación de fuentes

**Entregables:**
- `src/pipeline/calcular_rofex_signal.py` — construye `ROFEX_1M_EQUIV` unificando SSPM+BCR+PPI. Para contratos PPI: `equiv = MEP × (DLR_front/MEP)^(1/meses)`. Excluye contratos con <20 días al vencimiento (evita amplificación exponencial).
- `calcular_capa1.py` actualizado: `capa1 = 0.5 × z_mep + 0.5 × rolling_zscore(ROFEX/MEP−1)`
- `update_daily.py` actualizado: 10 pasos (agrega `calcular_rofex_signal.py` entre scrapers y Capa 1)
- Pipeline completo re-corrido. IEP hoy = 102.2 (antes: 106.2 sin blend ROFEX)

**Resultados con blend:** min=68.8 (sep-2025) / max=114.7 (dic-2024) / hoy=102.2. Narrativa coherente: Guzmán=86.5, Honeymoon peak=111.1, pre-electoral=72.2, baseline=100.0.

**Validación de fuentes (3 checks):**
1. Spot-check BCR: 13/15 PDFs verificados, diferencia = 0.0 exacto en todos ✅
2. Transición SSPM→BCR (18-abr-2024): 1.5 ARS de diferencia (0.17%) ✅
3. Período PPI: artefacto de 6pp en Oct 8-26 por cambio de instrumento (BCR 1M → PPI 7M normalizado). Estructural, irresolvible sin datos DLR_NOV25. Documentado en lessons.md.

---

### Sesión 10 — 13/05/2026 · Reencuadre conceptual + ROFEX gap cerrado con BCR Boletines
- **Reencuadre del constructo:** de "expectativa de continuidad 3-6m" a "probabilidad implícita de continuidad del programa post-2027" (CDS spread evidencia)
- **Señal rechazada:** GD30D−GD35D — tendencia secular, r=0.114, no capturable con instrumentos disponibles
- **Señal electoral disponible:** law spread GD30D−AL30D, r=0.349, ya activa en Capa 2
- **ROFEX gap cerrado:** BCR Boletines PDF (`boletin-mercado-granos-{id}.pdf`, IDs 18541-18910) → 284 filas cubren abr-2024→oct-2025 con pdfplumber+regex

### Sesión 9 — 12/05/2026 · Capa 3 activa + pesos definitivos 35/40/25
- Capa 3: semi-volatilidad a la baja (std retornos negativos, 20d) del basket YPFD/GGAL/PAMP/TECO2
- Scrapers: `scraper_acciones.py` + `calcular_capa3.py`
- Pesos definitivos activados: 35/40/25. Las 3 capas convergen en −3.2 en sep-2025 ✅
- ROFEX: PPI FUTUROS activo desde oct-2025 (DLR_MAY26…DLR_DIC26). Gap histórico: SSPM + pendiente BCR (Ses. 10)

### Sesión 8 — 12/05/2026 · EMBI histórico completo + pipeline automatizado
- EMBI desde 1998: `api.dolarito.ar/api/frontend/indices/riesgoPais` (header auth-client: f7d471ab…)
- `scraper_embi_historico.py` reemplaza a scraper_embi.py para backfill. 7071 registros.
- Pipeline automatizado: `update_daily.py` (orquestador) + `run_update.bat` (Task Scheduler Lun-Vie 18:30)
- Bug fix calcular_capa2.py: INSERT OR REPLACE → ON CONFLICT DO UPDATE (preserva capa1)

### Sesión 7 — 09/05/2026 · Dashboard HTML v1
- `outputs/dashboard.html` — Chart.js 4.4, gradiente, 7 hitos, zoom temporal, selector de baseline
- Decisiones técnicas: dots como datasets nativos (no annotations); baseline ancla en daily `v` no smooth `s`; autoSkip:false + detección de inicio de mes para eje X

### Sesión 6 — 09/05/2026 · Resolución de gaps conceptuales
- Triaje de 9 gaps de AREAS_CRITICAS.md: constructo = continuidad del programa (no reelección de Milei)
- EMBI sale del esquema de validación externa (circularidad). Benchmarks válidos: ICG-UTDT + encuestas
- CONTEXTO.md actualizado a v0.4

### Sesiones 4-5 — 09/05/2026 · Capa 2 + Capa 1 + IEP provisional
- Ses. 4: `calcular_capa2.py` — 5 componentes, z-score rolling 252d, 1100 filas
- Ses. 5: AL30_ARS via PPI, MEP = AL30_ARS/AL30D_USD, `calcular_capa1.py`, `calcular_iep.py` (50/50 provisional)
- IEP range inicial: min 74.1 (sep-2025) / max 121.5 (dic-2024)

### Sesión 3 — 08/05/2026 · Primera implementación: DB + bonos + EMBI
- SQLite inicializado, `scraper_bonos.py` (GD30D/AL30D/GD35D via PPI, 1062 ruedas c/u), `scraper_embi.py`
- 3552 filas en DB (4 activos)

### Sesión 2 — 08/05/2026 · Revisión conceptual y arquitectura
- 6 optimizaciones aprobadas: z-score rolling 252d, EMBI en Capa 2, MEP/CCL para Capa 1, law spread, Capa 3 diferida, SQLite

### Sesión 1 — 07/05/2026 · Fundación
- Proyecto iniciado a partir de `docs/IEP_Plan_Completo.md` (mayo 2025)
- Estructura de carpetas creada en `Desktop/MARIANO/IEP/`
- Archivos base: CONTEXTO.md (v0.1), tasks/lessons.md
- Proyecto registrado en CLAUDE.md y MEMORY.md
- Decisión inicial: arrancar con Capa 2 → Capa 1 → Capa 3 diferida

### Sesión 3 — 08/05/2026 · Primera implementación: DB + bonos + EMBI
- SQLite inicializado: `data/iep.db` (tablas `raw_prices` + `iep_diario`)
- Exploración de fuentes: BCRA API deprecada; PPI API confirmada con credenciales propias
- `src/pipeline/init_db.py` — schema SQLite, idempotente
- `src/scrapers/scraper_bonos.py` — GD30D / AL30D / GD35D via PPI, paginacion anual
- `src/scrapers/scraper_embi.py` — EMBI bps reales via Rava scraping (_chartData)
- **DB final: 3552 filas** (4 activos)
  - GD30D/AL30D/GD35D: 1062 ruedas c/u desde 2022-01-03 (PPI)
  - EMBI: 366 dias desde 2025-05-08 en bps reales (Rava)
- Limitacion EMBI: solo cubre ultimo año; 2022-2025 = GD30D proxy en pipeline
- Fuente MEP historico: PPI ratio AL30_ARS/AL30D_USD (siguiente sesion)

### Sesión 2 — 08/05/2026 · Revisión conceptual y arquitectura
- Revisión pre-implementación: 6 optimizaciones identificadas y aprobadas
- **Nuevos componentes:** EMBI+ Argentina (Capa 2), brecha MEP/CCL (Capa 1 inicio), law spread GD30−AL30 (Capa 2)
- **Stack:** SQLite, z-score rolling 252d
- **Pesos provisorios:** 50/50 Capa1/Capa2 hasta tener historia en Capa 3
- CONTEXTO.md reescrito a v0.2. PLAN.md creado.
- **Próxima sesión:** implementación SQLite schema + scrapers (EMBI → bonos → MEP/CCL)

---

## 14. Workflow Operativo (Fase 0)

### Pipeline diario — 10 pasos automatizados (Task Scheduler Lun-Vie 18:30)

```
run_update.bat → src/pipeline/update_daily.py
  1. scraper_bonos.py          → GD30D, AL30D, GD35D, AL30 (últimos 7d, PPI)
  2. scraper_acciones.py       → YPFD, GGAL, PAMP, TECO2 (últimos 7d, PPI)
  3. scraper_rofex.py          → DLR futuros PPI (acumulador electoral kink)
  4. scraper_embi_historico.py → EMBI completo desde 1998 (dolarito.ar)
  5. calcular_rofex_signal.py  → ROFEX_1M_EQUIV unificado (SSPM+BCR+PPI) → raw_prices
  6. calcular_capa1.py         → blend MEP + ROFEX → iep_diario.capa1
  7. calcular_capa2.py         → bonos soberanos + EMBI → iep_diario.capa2
  8. calcular_capa3.py         → semi-vol accionaria → iep_diario.capa3
  9. calcular_iep.py           → IEP compuesto 35/40/25 → iep_diario.iep_total
 10. generate_dashboard.py     → outputs/dashboard.html
```

### Corrida manual
```
py src/pipeline/update_daily.py
```

### Protocolo de inicio de sesión
```
Retomemos el proyecto IEP.
Pegar: CONTEXTO.md + PLAN.md
Estado: [última corrida] | Objetivo de hoy: [UNA SOLA COSA]
```

---

## 15. Reglas del Sistema

1. **Los datos crudos son inmutables.** Los scores son siempre recalculables.
2. **Los pesos provisorios (50/50) se documentan como tales en todo output publicado.** Cuando se activen los pesos definitivos, se recalcula toda la serie.
3. **Una sola cosa por sesión.** Cada sesión tiene un único entregable.
4. **Los benchmarks de validación son externos al índice.** El EMBI no puede validar el IEP porque es componente de Capa 2. Validadores válidos hoy: ICG-UTDT + encuestas de aprobación + análisis de eventos. RadarPolitico se suma cuando exista como producto.
5. **Metodología abierta.** Los errores de validación también se publican — la transparencia es parte del diferencial.
6. **Pegar siempre CONTEXTO.md + PLAN.md al inicio de cada sesión.**

---

## 16. Decisiones Abiertas

| Decisión | Opciones | Estado |
|---|---|---|
| Fuente principal bonos | IOL API vs. Rava scraping vs. PPI | **PPI API — DECIDIDO** (Ses. 3) |
| Dashboard tech | HTML estático vs. Next.js + Recharts | **HTML estático** — funcional, sin servidor |
| Newsletter plataforma | Substack vs. Ghost | Sin decidir |
| Automatización pipeline | Windows Task Scheduler | **Task Scheduler — DECIDIDO** `run_update.bat`, Lun-Vie 18:30 |
| Nombre público del índice | "IEP" / "Índice de Expectativa Política" | Confirmado |
| Dominio y presencia online | iep.ar / iepargentina.com | Sin decidir |
| Co-branding con broker | PPI / IOL | Pendiente Fase 2 |
| Validación externa IEP vs. ICG-UTDT | Correlación esperada r > 0.65 | Pendiente — próxima sesión analítica |
