# IRPM — Índice de Riesgo Político de Mercado
**Índice experimental que sintetiza condiciones de mercado a partir de señales financieras sensibles al escenario político y económico argentino · Diario**
Versión documental: v0.8 · Reevaluación metodológica y de producto: 13/08/2026

> **Estado oficial:** el IRPM es un índice experimental que sintetiza condiciones de mercado a partir de señales financieras sensibles al escenario político y económico argentino. Usa un baseline convencional; no es una probabilidad electoral calibrada, no identifica causalidad política y no constituye una recomendación de inversión.
>
> **Docs vigentes:** `CONTEXTO.md` (arquitectura y decisiones) · `PLAN_ACCION.md` (única hoja de ruta operativa) · `docs/MARCO_VALIDACION_Y_GOBERNANZA.md` (claims, protocolos y releases).
>
> `PLAN.md`, `docs/IEP_Plan_Completo.md` y las secciones de log conservan historia del proyecto; no son fuente del estado actual.
> **Dashboard público:** https://marianolaxague-crypto.github.io/irpm-argentina/ · **Repo:** https://github.com/marianolaxague-crypto/irpm-argentina
> **Newsletter:** https://elindice.substack.com (El Índice — lanzado Ses. 18)

---

## 1. Identidad del Proyecto

El **IRPM** es un índice experimental que sintetiza condiciones de mercado a partir de señales financieras sensibles al escenario político y económico argentino. Se actualiza con frecuencia diaria cuando los inputs requeridos están completos.

**Constructo operativo vigente:** condiciones de mercado asociadas a la credibilidad y continuidad del programa económico. La cadena causal defendible llega hasta `precios y coberturas → evaluación de riesgo y capacidad de pago por participantes del mercado`. El salto desde esos precios hacia un resultado electoral o una causa política específica es una interpretación editorial, no un output del estadístico.

**Horizonte:** la lectura editorial presta especial atención a octubre de 2027, pero los instrumentos también reaccionan a macroeconomía corriente, factores globales, liquidez y riesgo crediticio. El índice no puede separar esas contribuciones con la metodología actual.

**Unidad:** puntos de índice alrededor de un baseline convencional igual a 100 el 11/12/2023. Los puntos no son porcentajes ni probabilidades.

**Audiencia representada:** participantes del mercado de capitales observados, no la sociedad argentina.

**Diferencial frente a instrumentos existentes:**

| Instrumento | Frecuencia | Mide | Limitación |
|---|---|---|---|
| Encuestas de opinión | Mensual / bimestral | Preferencia declarada | Rezago 3-6 semanas |
| Índice Dintella / UTDT | Mensual | Confianza del consumidor | Sin granularidad política |
| EMBI+ Argentina | Diario | Riesgo soberano agregado | No separa política, macro local y factores globales |
| **IRPM (este proyecto)** | **Diario** | **Condiciones estandarizadas de activos sensibles al escenario argentino** | No separa política, macro local y factores globales |

**Hipótesis de diferenciación:** frecuencia diaria + integración de señales + interpretación transparente. Es una propuesta a validar comercialmente, no un moat demostrado.

---

## 2. Estructura del Proyecto

```
IEP/
├── CONTEXTO.md              # Arquitectura, decisiones y log técnico
├── PLAN_ACCION.md           # Única hoja de ruta operativa vigente
├── PLAN.md                  # Plan histórico; no usar para prioridades actuales
│
├── docs/
│   ├── metodologia_publica.md
│   ├── MARCO_VALIDACION_Y_GOBERNANZA.md
│   ├── AREAS_CRITICAS.md
│   └── IEP_Plan_Completo.md # Documento fundacional histórico
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
| Normalización | **Z-score rolling 252 ruedas, min 63** | Comparación con historia reciente; requiere sensibilidad adicional |
| Pesos externos actuales | **35/40/25 (Capa1/2/3)** | Activos desde 2022; robustez parcial, no optimalidad demostrada |
| Capa 3 | Semi-volatilidad realizada a la baja, no opciones | Proxy pragmático; debe rotularse como tal |
| Dashboard | HTML estático + Chart.js | Decidido; generador monolítico pendiente de modularización |
| Newsletter | Substack | Lanzada; nueva distribución bloqueada por gates de hardening |
| Estado metodológico | Experimental | No probabilidad, no causalidad, no asesoramiento financiero |

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

### Pesos externos actuales

| Capa | Activos/señales | Peso |
|---|---|---:|
| **1 — Señales cambiarias y futuros** | MEP + ROFEX_1M_EQUIV | 35% |
| **2 — Bonos soberanos USD** | GD30D/AL30D/GD35D + EMBI + law spread | 40% |
| **3 — Volatilidad accionaria** | Semi-vol YPFD/GGAL/PAMP/TECO2 | 25% |

> Los pesos son una especificación experimental. La sensibilidad realizada muestra estabilidad de extremos dentro de una grilla acotada, pero no demuestra optimalidad ni validez del constructo.
>
> Los pesos dinámicos y el kink electoral permanecen como hipótesis de diseño. No se implementarán antes de cerrar integridad, tests y protocolo de validación.

---

## 3a. Capa 2 — Bonos Soberanos USD (40%)

*Compuesto experimental de precios, spread jurisdiccional y EMBI.*

| Componente | Señal política | Fuente | Estado |
|---|---|---|---|
| **GD30D** | Precio de bono global 2030; sensible a riesgo soberano, liquidez y tasas | PPI API | **ACTIVO** |
| **AL30D** | Precio de bono ley argentina 2030; sensible a los mismos factores y a jurisdicción | PPI API | **ACTIVO** |
| **GD35D** | Precio de bono global 2035; mayor exposición a duration y estructura de flujos | PPI API | **ACTIVO** |
| **Law spread GD30D−AL30D** | Diferencial jurisdiccional que reduce parte de la exposición común, sin aislar riesgo político puro | Calculado | **ACTIVO** — hipótesis de mayor contenido doméstico pendiente de validación v2 |
| **EMBI Argentina** | Riesgo soberano agregado; alta contaminación macro/global | dolarito.ar | **ACTIVO** — no puede usarse como validador externo |
| ~~Spread post-2027 (GD30D − GD35D)~~ | DESCARTADO en Ses. 10 tras validación. Tendencia secular (+1.86 en 2022 → +9.18 en 2024 → -10.86 en oct-2025-hoy) confundida con amortización de GD30 y cambio de estructura. Correlación con IEP: r=0.114 (no significativo). No es señal electoral limpia. | — | **RECHAZADO** |

**Rangos históricos de referencia:**
- EMBI Fernández peak: ~2.800 bps (2022) | EMBI Milei post-acuerdo FMI: ~700 bps (2025)
- Law spread: explotó en 2020 (restructuración), se comprimió en 2025
- Spread post-2027: ~300 bps en mayo 2026 (calibrado por Gemini Deep Research, mayo 2026)

Los umbrales históricos de EMBI pueden usarse como contexto editorial, no como calibración de probabilidad electoral ni de la escala IRPM.

---

## 3b. Capa 1 — Señales Cambiarias y Futuros (35% vigente)

*Blend 50/50 de MEP y ROFEX_1M_EQUIV. Script: `calcular_capa1.py` (lee ROFEX de raw_prices).*

| Componente | Señal política | Fuente | Estado |
|---|---|---|---|
| **MEP (AL30_ARS/AL30D_USD)** | Gap entre dólar financiero y oficial. Alto relativo = fuga a dólares = señal mala. z-score rolling 252d sobre log(MEP), invertido. | PPI API — ratio AL30/AL30D | **ACTIVO** — 1065 ruedas 2022-hoy |
| **ROFEX_1M_EQUIV** | Precio forward equivalente a 1 mes. Premium alto sobre MEP = mayor devaluación esperada; z-score invertido. | SSPM (2022-2024-04) + BCR PDF (2024-04-2025-10) + PPI normalizado (2025-10-hoy) | **ACTIVO** — script `calcular_rofex_signal.py` |
| **ROFEX electoral kink** (futuro) | DLR_DIC27/DLR_ENE27−1. Hipótesis de prima cambiaria alrededor del horizonte electoral. | PPI FUTUROS | **PENDIENTE** — revisar desde dic-2026; activar sólo con historia suficiente y protocolo validado |

**Blend actual:** `capa1 = 0.5 × z_mep + 0.5 × z_rofex_premium`

**Limitación documentada (Ses. 11):** oct-2025, los primeros ~19 días del período PPI (Oct 8 - Oct 26) tienen un artefacto de ~6pp en el premium porque PPI no capturó los contratos 1M que ya habían expirado (DLR_NOV25, etc.) — solo tiene contratos 7M+ en ese momento. La curva tenía contango pronunciado pre-electoral. El artefacto se absorbe en el z-score rolling. **Spot-check BCR confirmado:** 13/15 fechas verificadas contra PDFs originales con diferencia = 0.0 exacto.

---

## 3c. Capa 3 — Volatilidad accionaria realizada (25%)

*Proxy activo de estrés bajista; no utiliza opciones BYMA.*

| Componente | Transformación | Activos |
|---|---|---|
| Semi-volatilidad a la baja | Desvío de retornos negativos rolling 20 ruedas, anualizado; z-score 252 e invertido | YPFD, GGAL, PAMP, TECO2 |

La capa puede reaccionar a commodities, noticias corporativas, riesgo global y factores regulatorios. No debe describirse como volatilidad política pura ni como put-side observado.

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
# Mapeado a escala IRPM con baseline=100 al 11-dic-2023
```

**Ventana de suavizado:** media móvil de 5 ruedas (semana bursátil) sobre el IEP compuesto diario.

**Baseline = 100** → 11 de diciembre de 2023. Es una convención narrativa. El índice mide la distancia del compuesto respecto de ese punto, no una diferencia de probabilidad.

**Revisión de pesos:** semestral, o ante cambios estructurales de mercado.

---

## 4. Fuentes de Datos — Estado y Acceso

| Fuente | Qué provee | Acceso | Estado | Prioridad |
|---|---|---|---|---|
| **PPI API** | GD30D/AL30D/GD35D/AL30, acciones y contratos DLR | `ppi-client` + credenciales locales | **ACTIVA** — fuente diaria principal | 1 |
| **dolarito.ar** | EMBI Argentina histórico | API pública usada por `scraper_embi_historico.py` | **ACTIVA** — historia desde 1998; puede cerrar un día después que PPI | 1 |
| **SSPM datos.gob.ar** | ROFEX 1M/2M/3M histórico | Dataset público | **ACTIVA para historia** | 2 |
| **BCR boletines** | ROFEX 1M/2M/3M abr-2024 a oct-2025 | Extracción de PDF validada por spot-check | **ACTIVA para cubrir gap histórico** | 2 |
| **Yahoo Finance** | VIX | `yfinance` | **ACTIVA** — control global experimental | 2 |
| **UTDT** | ICG e ICC mensuales | PDF/web pública | **ACTIVA** — comparación externa | 2 |
| **BCRA REM** | Expectativas mensuales de analistas | Archivo público | **ACTIVA** — capa analítica separada | 3 |
| **BYMA opciones** | IV, skew y put/call | Sin acceso productivo actual | **NO ACTIVA** — no confundir con Capa 3 realizada | 3 |

**Criterio de selección:** preferir fuentes primarias/API, registrar fecha efectiva y mantener provenance. Si una fuente cierra después que otra, el valor compuesto no puede renormalizarse silenciosamente.

---

## 5. Escala de Interpretación

| Rango IRPM | Lectura descriptiva vigente |
|---|---|
| **> 110** | Compuesto más de 10 puntos por encima del baseline |
| **90–110** | Entorno cercano al baseline convencional |
| **< 90** | Compuesto más de 10 puntos por debajo del baseline |

Los cortes ±10 son heurísticos de presentación. Las categorías anteriores de “reelección”, “optimismo” y “stress político” quedan retiradas hasta disponer de calibración empírica.

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

**Estado general:** la validación del constructo no está cerrada. Hay evidencia de implementación y robustez interna parcial; la validez descriptiva, incremental y predictiva permanece abierta. Los niveles y protocolos oficiales están en `docs/MARCO_VALIDACION_Y_GOBERNANZA.md`.

**Principio:** los benchmarks deben ser independientes. El EMBI es componente de Capa 2 y no puede utilizarse como validación externa; sí debe analizarse en ablaciones para medir redundancia.

| Ejercicio | Qué permite afirmar | Qué no permite afirmar | Estado vigente |
|---|---|---|---|
| Sensibilidad de pesos | Los extremos son relativamente estables dentro de 14 combinaciones externas | Pesos óptimos o constructo válido | **Robustez parcial** |
| IRPM vs. ICG | Existe covariación contemporánea débil/moderada en N=32 | Que el IRPM anticipe encuestas o que la complementariedad esté “confirmada” | **Hipótesis leading no confirmada** |
| Análisis de eventos v1 | Hay correspondencias temporales exploratorias | 20 shocks independientes, causalidad o 70% de accuracy | **Resultado retirado como validación** |

**Falsabilidad vigente:** cada nueva hipótesis debe declarar ex ante qué resultado la refutaría. El proyecto fallaría como indicador político incremental si, tras controlar inputs simples y factores macro/globales, no aporta información adicional reproducible o si sus asociaciones con eventos no superan benchmarks nulos fuera de muestra.

### Resultado H2.2 — Sensibilidad de pesos (exploratoria)

**Script:** `src/analysis/analisis_sensibilidad_pesos.py` | Datos: 1044 ruedas (abr-2022 → ago-2026)

**Grid:** Capa1 ∈ {25-45%}, Capa2 ∈ {35-50%}, Capa3 ∈ {15-30%}, suma=100% → 14 combinaciones.

| Métrica | Resultado |
|---|---|
| Correlación vs. base (35/40/25) | r = 0.977 – 1.000 |
| Δ mínimo histórico | −5.5 a +3.7 pts |
| Δ máximo histórico | −1.7 a +0.9 pts |
| Fecha del máximo (dic-2024) | **100% de combinaciones** — estable |
| Fecha del mínimo (sep-2025) | **93%** — 1 escenario lo mueve 3 días (sep-12 vs sep-15) |

Escenario más extremo: 25%/50%/25% → mínimo 70.1 (vs. 75.6 base, Δ=−5.5 pts). Requiere +10pp en Capa2 y −10pp en Capa1 simultáneamente.

**Conclusión permitida:** las fechas extremas son estables dentro de la grilla analizada y la magnitud puede variar aproximadamente ±6 puntos. No se evaluaron todavía ventanas, pesos internos, componentes, missingness, baseline, escala ni ajuste VIX.

Tabla completa: `data/sensibilidad_pesos.csv`

---

### Resultado H2.3 — IRPM vs. ICG-UTDT

**Datos:** N=32 meses (dic-2023 → jul-2026). IRPM mensualizado promedio vs. ICG mensual UTDT. Script: `src/analysis/validacion_leading_indicator.py`.

**Cross-lag correlations (Pearson):**

| Lag | Descripción | r | p-valor |
|---|---|---|---|
| k=-1 | ICG adelanta 1m al IRPM | **+0.384** | 0.033 ✓ |
| k=0 | Contemporáneo | +0.367 | 0.039 ✓ |
| k=+1 | IRPM adelanta 1m al ICG | +0.324 | 0.075 ~ |
| k=+2 a +4 | IRPM adelanta 2-4m | <0.28 | >0.12 |

**Granger causality (IRPM → ICG):** F ≈ 0.2-0.5, p = 0.65-0.67 para lags 1-3. Sin evidencia estadística.

**Directional accuracy:** 40% a lag+1 (esencialmente aleatorio).

**Veredicto vigente: hipótesis de leading indicator no confirmada.**

La hipótesis original era que el IRPM adelantaría al ICG. La mayor correlación observada está en la dirección contraria (`k=-1`) y Granger no encuentra poder predictivo IRPM→ICG. Con N=32 la potencia es baja, por lo que el resultado es negativo/inconcluso, no una confirmación de independencia o complementariedad.

El panel de divergencias puede conservarse como herramienta descriptiva. No debe afirmar que “uno vio algo que el otro todavía no” sin evidencia adicional.

**Próximo test:** congelar protocolo, evaluar estacionariedad y múltiples lags, repetir con N≥50 y mantener un holdout posterior.

> **Integración futura (Fase 3):** cuando RadarPolitico.ai esté operativo como producto, el IG (Índice de Gobierno) puede sumarse como validador externo adicional. Por ahora no existe como fuente disponible.

---

## 8b. Limitaciones y Alcance Declarado

Estas limitaciones determinan el alcance de los claims permitidos y deben estar visibles en toda comunicación pública.

**Señal política no separable de señal macro.** El IRPM no puede aislar movimientos de origen político de movimientos de origen macroeconómico o global. Las tasas de la Fed, el sentimiento de emergentes y la liquidez internacional mueven los mismos activos. La interpretación política de los z-scores es editorial: está informada por el contexto, no producida por el estadístico. Esta limitación es compartida con el EMBI y con todos los índices de riesgo soberano.

> El law spread reduce parte de la exposición compartida entre bonos del mismo soberano, pero conserva diferencias de liquidez, jurisdicción, estructura y demanda. Se lo trata como componente con hipótesis de mayor contenido doméstico, no como aislador de riesgo político puro.

> **Implicación operativa:** cuando el VIX supera 20 o los spreads EM se amplían globalmente, los movimientos del IRPM deben interpretarse con mayor cautela. El dashboard incluirá (OPT-2) una nota de contexto automática según umbral de VIX.

**Baseline convencional, no técnico.** La elección de IRPM=100 el 11-dic-2023 (inicio de la gestión Milei) es una convención narrativa, no una estimación de valor fundamental. Es análoga al año base de un índice: determina si el compuesto aparece sobre o bajo 100. Un valor superior sólo significa que las señales incluidas son relativamente más favorables que en el baseline; no cuantifica creencias sobre continuidad, reelección ni resultados políticos.

**Participantes del mercado, no sociedad.** El IRPM resume precios de mercados con liquidez y participación desiguales. No representa preferencias sociales ni un consenso amplio de actores económicos.

**Riesgo de feedback loop.** Si el índice gana adopción, puede influir en narrativas sobre los propios activos que utiliza. T+1 y metodología pública reducen opacidad, pero no eliminan el riesgo.

**Instrumentos de deuda en pesos fuera del alcance.** El IRPM no captura bonos duales (CER/TAMAR), Lecaps ni otros instrumentos en moneda local. Esos precios agregan expectativas de inflación, tasas, regulación y liquidez difíciles de separar. Los instrumentos en dólares reducen algunas de esas exposiciones, pero conservan riesgo crediticio, macroeconómico, global y de liquidez; tampoco son una señal política pura.

**Contenido electoral indirecto.** La metodología actual no aísla una prima electoral 2027. El law spread y los niveles de bonos contienen riesgo soberano amplio. El ROFEX electoral kink permanece como hipótesis futura y sólo podrá activarse con historia suficiente, tests y versión metodológica nueva.

**Completitud y fecha efectiva.** Desde el 14/08/2026, Capa 2 exige sus cinco señales, Capa 3 exige el basket completo y el compuesto sólo publica cuando las tres capas pertenecen a la misma rueda. Las seis fechas sin EMBI se retiraron como observaciones ordinarias; `iep_composicion` expone versión, señales, fecha efectiva, pesos y motivo de degradación. Ver `docs/AUDITORIA_COMPLETITUD_20260814.md`.

**Escala no calibrada.** Baseline, factor 10 y umbrales visuales son decisiones de presentación. No deben interpretarse como probabilidades, niveles fundamentales ni fronteras de decisión.

---

## 9. Integración con el Ecosistema

| Proyecto | Qué aporta al IEP | Qué recibe del IEP |
|---|---|---|
| **RadarPolitico.ai** | Contexto narrativo mediático (IG semanal) — para validar convergencia señal mercado/medios | Capa de mercado para enriquecer análisis del IG |
| **LegiscopeAR** | Señal de alineamiento legislativo — si los aliados rompen, el mercado debería responder | Lectura del mercado sobre las alianzas políticas |

**Hipótesis de convergencia:** la coincidencia o divergencia futura entre IG e IRPM puede definir casos para análisis editorial. No se tratará como “señal política fuerte” hasta contar con protocolo, muestra y benchmark registrados.

---

## 10. Modelo de Negocio

Estas cifras son hipótesis comerciales históricas, no forecast validado. Toda distribución o monetización permanece bloqueada por los gates P0–P5 de `PLAN_ACCION.md`.

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
| Claim probabilístico sin calibración | Retirar el lenguaje de probabilidad; reabrirlo sólo con protocolo E5 |
| Confusión entre política y macro/global | Acotar definición, mostrar VIX/contexto y evaluar identificación/ablaciones |
| Faltantes y ajustes de componentes | Gate estricto, estado degradado, metadata y registro durable de splits/pagos/backfills implementados |
| Validación post hoc | Preregistro, episodios no solapados, benchmark nulo y holdout |
| Dependencia de un scheduler local | Watchdog externo y probe posterior al deploy |
| Divergencia código/dashboard/metodología | Release única con commit, manifest, snapshot y changelog |
| Reproducibilidad insuficiente | Config de ejemplo, tests y lock Python 3.12 implementados; CI pendiente (P4.4) |
| UX mobile/accesibilidad no verificada | Breakpoints, semántica, teclado, alternativa textual y QA visual |

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
| Pesos vigentes | 35/40/25 activados | Esperar Capa 3 con IV real | La convergencia observada en sep-2025 aportó face validity, no demuestra optimalidad ni valida el constructo | Ses. 9 |
| ROFEX histórico gap | BCR Boletines PDF (scraping pdfplumber) | Modelar crawling peg extrapolado | BCR publica precio de ajuste DLR diariamente — fuente oficial, spot-check 13/13 OK | Ses. 10-11 |
| Blend ROFEX en Capa 1 | 50/50 MEP + ROFEX_1M_EQUIV | Solo MEP | ROFEX agrega información de las expectativas de devaluación de corto plazo independiente del nivel del MEP | Ses. 11 |
| Signo z_rofex | `rolling_zscore(premium)` sin inversión | `−rolling_zscore(premium)` | Premium alto (ROFEX cerca de MEP) = menos miedo devaluatorio = señal positiva para IEP | Ses. 11 |

---

## 13. Log de Sesiones

### Sesión 24 — 12/08/2026 · H2.2 + H2.3 — Sensibilidad de pesos + Relación IRPM/ICG

**H2.2 — Sensibilidad de pesos:** extremos estables dentro de la grilla externa ensayada (min sep-2025, max dic-2024); la magnitud varía ±5.5 pts en el escenario extremo. Es robustez parcial. Ver §8 para detalle.

**H2.3 — Relación IRPM/ICG:** r contemporánea=+0.367, p<0.05. La hipótesis original de anticipación no fue confirmada; no se redefine ese resultado como “esperado”. Ver §8 para detalle.

**Script ejecutado:** `src/analysis/validacion_leading_indicator.py`
- Fuentes: `data/irpm_export.csv` (IRPM diario mensualizado) + `data/utdt_icg.csv` (ICG mensual UTDT)
- Cross-lag correlations k=-4 a +4. Granger causality (statsmodels). Directional analysis.
- N=32 meses (dic-2023 → jul-2026).

**Hallazgos clave:**
- Contemporánea significativa: r=+0.367, p=0.039 ✓
- k=-1 (ICG lidera IRPM): r=+0.384, p=0.033 — la dirección es inversa a la hipótesis
- k=+1 (IRPM lidera ICG): r=+0.324, p=0.075 — por debajo del umbral
- Granger IRPM→ICG: p=0.65-0.67 (sin evidencia)

**Implicación operativa:** eliminado el claim "el mercado adelanta a las encuestas". El valor del IRPM es la señal del dinero puesto en juego y los períodos de divergencia vs. ICG, no su poder predictivo.

**Archivos nuevos/modificados:**
- `src/analysis/validacion_leading_indicator.py` — nuevo (con interpretación actualizada)
- `data/irpm_export.csv` — nuevo (workaround SQLite I/O error en sandbox Linux)
- `CONTEXTO.md` §8 — resultado H2.3 documentado

---

### Sesión 23 — 12/08/2026 · H1.4 — Sanity checks por capa

**IRPM al cierre:** 103.6 bruto / 105.1 ajustado (12/08/2026).

**H1.4 — Tests de sanity post-cálculo:**
- `src/pipeline/sanity.py` — módulo compartido con `assert_capa_sanity(capa)`. Tres checks: z-score último día en ±5, delta diario < 3 z-units, freshness ≤ 5 días hábiles. Umbrales configurables en `config.ini [pipeline]`. Escribe alertas en `logs/health_alerts.log`, sale con exit code 1 si falla.
- `calcular_capa1.py`, `calcular_capa2.py`, `calcular_capa3.py`: cada uno llama `assert_capa_sanity()` al final. Pipeline se detiene en el paso que falla.
- Resultado hoy: capa1 z=-0.46 ✓ | capa2 z=-0.28 ✓ | capa3 z=+0.28 ✓

**Archivos nuevos/modificados:**
- `src/pipeline/sanity.py` — nuevo
- `src/pipeline/calcular_capa1/2/3.py` — llamada a `assert_capa_sanity()` al final

---

### Sesión 22 — 12/08/2026 · H1.1 + H1.2 + H1.3 — Infraestructura de robustez

**IRPM al cierre:** 103.6 bruto / 105.1 ajustado (12/08/2026).

- `config.ini` + `src/config.py`: configuración centralizada. CRED_PATH eliminada de los 3 scrapers PPI — leer siempre `CFG.cred_ppi`.
- `check_pipeline_health.py` (paso 15): valida IRPM en rango, delta diario, freshness, z-scores por capa. Escribe `logs/last_run.txt`.
- `data/backups/`: backup automático de `iep.db` antes de cada corrida, rotación 7 días.

**Archivos nuevos/modificados:**
- `config.ini` — nuevo
- `src/config.py` — nuevo
- `src/pipeline/check_pipeline_health.py` — nuevo
- `src/pipeline/update_daily.py` — paso 0 (backup) + paso 15 (healthcheck) + import CFG
- `src/scrapers/scraper_bonos/acciones/rofex.py` — CRED_PATH → CFG

---

### Sesión 21b — 12/08/2026 · TIR diferida (H2.1) + limpieza

**H2.1 — TIR diferida:** `estimate_bonds` PPI no funciona para bonos hard-dollar (GD30D/AL30D/GD35D) — retorna `"Quantity Type not found"` para todos los `quantityType`. `marketdata.search` tampoco incluye TIR. La columna `raw_prices.tir` queda en la DB. OPT-7 resuelve el problema operativo. Opción futura: YTM desde flujos via `scipy.optimize` con prospecto 2020.

**Limpieza:** `scraper_tir_bonos.py` eliminado · step removido de `update_daily.py` · `calcular_capa2.py` revertido a paridad+OPT-7 simple · `PLAN_ACCION.md` H2.1 = DIFERIDO.

---

### Sesión 21 — 12/08/2026 · OPT-7 + split YPFD + OPT-4 + Deploy GitHub Pages

**IRPM al cierre:** bruto=103.6 / ajustado=105.1 (VIX=14.9, MEP=1524.8, EMBI=466).

**OPT-7 — Forward-fill en fechas de pago de bonos (`calcular_capa2.py`):**
Los bonos GD30, AL30, GD35 pagan cupón + amortización el 9 de enero y 9 de julio. La paridad cae mecánicamente ~13% en la fecha ex-pago y el z-score lo interpretaba como señal política negativa. Fix: forward-fill con el precio pre-ventana como referencia fija (±2 días calendario antes de cada fecha de pago, umbral >2.5%). 22 caídas mecánicas detectadas y corregidas. Jul-8-2026: IRPM se mantuvo en 107.5 (antes caía a 101.2). Limitación documentada: primer día post-ventana muestra el precio real ex-div, causando una caída menor (~1-3 pts). Solución definitiva diferida: precios ajustados / TIR.

**Split YPFD 10:1 (3-ago-2026) + backfill gap Jul-24 → Aug-4:**
YPF hizo un split 10:1 el 3-ago. El precio pasó de 82,900 a 8,105 ARS. `calcular_capa3.py` calculaba ese -90% como retorno real, colapsando Capa3 a z=-12.27 e IRPM a 71.7 (desde 105.5). Fix: calendario `STOCK_SPLITS` en `calcular_capa3.py` — divide precios pre-split por el ratio antes de calcular log returns. 1108 precios YPFD ajustados (raw_prices conserva valores originales de PPI). Simultáneamente se backfillaron las 8 ruedas de gap (scraper_acciones y scraper_bonos --desde 2026-07-23). IRPM post-fix: 103.6.

**OPT-4 — Análisis de eventos políticos:**
`data/eventos_politicos.json` — 15 eventos Argentina 2022-2026 con tipo, severidad esperada, dirección y delta observado.
`src/analysis/analisis_eventos.py` — cruza el JSON con la serie IRPM (ventana ±5 ruedas), verifica dirección/magnitud, y valida el criterio de ≥70% de los top shocks explicados. Correr con `--guardar` para actualizar `irpm_delta_observado` en el JSON.
Resultado reportado en esa sesión: **14/20 = 70%** y rotulado entonces como “aprobado”. La revisión del 13/08/2026 retiró ese estado porque las ventanas se solapan y varios movimientos pertenecen al mismo episodio; se conserva sólo como resultado exploratorio histórico.
Los hallazgos narrativos de aquella corrida (renuncia de Guzmán, ballotage, Black Monday y legislativas 2025) son asociaciones ex post y no evidencia causal ni predictiva.

**Deploy a GitHub Pages — DASHBOARD PÚBLICO LIVE:**
- Repo público: `https://github.com/marianolaxague-crypto/irpm-argentina`
- Dashboard en vivo: `https://marianolaxague-crypto.github.io/irpm-argentina/`
- `generate_dashboard.py` escribe a `docs/index.html` además de `outputs/dashboard.html`
- `update_daily.py` llama `deploy_github()` al final del pipeline (git commit + push automático)
- `.gitignore` excluye: `data/*.db`, `outputs/`, `PLAN.md`, `config.ini`, archivos temporales
- Archivos nuevos en repo: `.gitignore`, `requirements.txt`, `README.md`

**Archivos nuevos/modificados:**
- `src/pipeline/calcular_capa2.py` — OPT-7: `_PAYMENT_WINDOW`, `ffill_payment_dates()`
- `src/pipeline/calcular_capa3.py` — `STOCK_SPLITS`, `apply_splits()`
- `src/pipeline/update_daily.py` — función `deploy_github()` como paso final
- `src/dashboard/generate_dashboard.py` — output duplicado a `docs/index.html`
- `data/eventos_politicos.json` — nuevo
- `src/analysis/analisis_eventos.py` — nuevo
- `.gitignore`, `requirements.txt`, `README.md` — nuevos
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
  - Ago-Oct 2024 (rojo): copy histórico de “anticipación del FMI”, retirado por exceder la evidencia disponible
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
- Capa 3 basket (YPF/Edenor/Pampa/Telecom): selección histórica apoyada en face validity sectorial; no constituye validación del constructo
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
- **Reencuadre histórico del constructo:** se propuso “probabilidad implícita de continuidad del programa post-2027”. La revisión del 13/08/2026 retiró esa formulación porque el compuesto no está calibrado como probabilidad.
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

## 14. Workflow Operativo

### Pipeline diario — 16 pasos + deploy (Task Scheduler Lun-Vie 18:30)

```
run_update.bat → src/pipeline/update_daily.py
  0. backup_db()
  1. scraper_bonos.py
  2. scraper_acciones.py
  3. scraper_rofex.py
  4. scraper_embi_historico.py
  5. scraper_utdt.py
  6. scraper_rem.py
  7. calcular_rem_icm.py
  8. scraper_vix.py
  9. calcular_rofex_signal.py
 10. calcular_capa1.py + sanity
 11. calcular_capa2.py + sanity
 12. calcular_capa3.py + sanity
 13. calcular_iep.py
 14. calcular_ajuste_global.py
 15. generate_dashboard.py
 16. check_pipeline_health.py
 deploy_github()
```

**Limitación operativa:** el healthcheck sólo detecta problemas si el proceso arranca. El watchdog externo y el chequeo del deploy siguen pendientes en `PLAN_ACCION.md` P5.

### Corrida manual
```
py src/pipeline/update_daily.py
```

### Protocolo de inicio de sesión
```
Retomemos el proyecto IEP.
Leer: CONTEXTO.md + PLAN_ACCION.md + docs/MARCO_VALIDACION_Y_GOBERNANZA.md
ID del plan: [P#.#] | Criterio de aceptación: [evidencia observable]
```

---

## 15. Reglas del Sistema

1. **Los datos crudos son inmutables.** Los scores son recalculables y versionados.
2. **Ningún valor público cambia de composición silenciosamente.** Faltantes implican estado degradado o no publicable.
3. **Dato, indicador e interpretación editorial se separan.**
4. **Una sola unidad de plan por sesión.** Cada sesión cierra un ID y su evidencia.
5. **Los benchmarks de validación son externos.** Los componentes sólo sirven para ablaciones y diagnóstico.
6. **Las hipótesis y criterios se congelan antes del test.** Los resultados negativos no se reencuadran como confirmación.
7. **Toda release une código, metodología, datos, tests y dashboard.**
8. **Usar siempre `PLAN_ACCION.md`; `PLAN.md` es histórico.**

---

## 16. Decisiones Abiertas

| Decisión | Opciones | Estado |
|---|---|---|
| Fuente principal bonos | IOL API vs. Rava scraping vs. PPI | **PPI API — DECIDIDO** (Ses. 3) |
| Dashboard tech | HTML estático vs. Next.js + Recharts | **HTML estático** — funcional, sin servidor |
| Newsletter plataforma | Substack vs. Ghost | **Substack — DECIDIDO** |
| Automatización pipeline | Windows Task Scheduler | **Implementado, observabilidad incompleta** — falta watchdog externo |
| Nombre público del índice | IRPM / alternativa direccional | **IRPM actual; revisión de dirección semántica abierta (P1.2)** |
| Dominio y presencia online | iep.ar / iepargentina.com | Sin decidir |
| Co-branding con broker | PPI / IOL | Pendiente Fase 2 |
| IRPM vs. ICG-UTDT | Leading indicator | **No confirmado con N=32** — repetir bajo protocolo congelado |
| Política de faltantes | Renormalizar vs. no publicar | **No publicar; misma rueda o estado degradado — DECIDIDO (14/08/2026)** |
| Umbrales 90/110 | Heurísticos vs. calibrados | **Heurísticos; revisar o retirar (P1.4)** |
