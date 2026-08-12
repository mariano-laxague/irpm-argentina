# Lessons Learned — IEP Argentina

*(Registrar errores, decisiones no obvias y patrones que vale la pena recordar)*

---

## 2026-08-12 — OPT-7: forward-fill en fechas de pago de bonos (calcular_capa2.py)

**REGLA:** `calcular_capa2.py` aplica forward-fill sobre GD30D, AL30D y GD35D en una ventana de 2 días calendario antes de cada fecha de pago (9 de enero y 9 de julio). Solo actúa si la caída supera el 2.5% Y la fecha está en la ventana. El precio de referencia para la comparación es el último precio ANTES del inicio de la ventana completa (no el día anterior al día detectado), para evitar efecto en cadena cuando la caída se reparte en dos días consecutivos.

**PORQUÉ:** en las fechas ex-pago, la paridad de los bonos cae mecánicamente en proporción al cupón + amortización pagados (ej: -13.1% el 8-jul-2026, -12.8% el 8-ene-2026). El z-score rolling lo interpreta como deterioro político cuando es un cash flow programado. Sin el fix, el IRPM caía ~6 pts en esa fecha. Con el fix, Jul-8-2026 permaneció en 107.5 (no cayó).

**COMPORTAMIENTO POST-VENTANA:** el primer día hábil después de la ventana (ej: Jul-10 para la ventana Jul-7/8/9) muestra el precio ex-div real, generando una pequeña caída en Capa2 (~0.4-0.8 z-score units). Esto es aceptable porque: (a) el impacto en IRPM es ~1-3 pts vs ~6 pts sin el fix, y (b) ese día puede tener también señal real de Capa1/Capa3.

**LIMITACIÓN CONOCIDA:** la solución ideal es usar precios ajustados por pagos (dividend-adjusted prices) o TIR en lugar de paridades. Pero eso requiere los flujos futuros de cada bono. El forward-fill es una solución pragmática suficiente para el propósito del índice.

---

## 2026-08-12 — Split accionario YPFD 10:1 (3-ago-2026) rompe Capa3

**ERROR:** YPFD hizo un split 10:1 el 3-ago-2026. El precio cayó de 82,900 a 8,105 ARS (-90.2%). `calcular_capa3.py` computó ese movimiento como un retorno real del -90%, dominó la ventana de 20 días de semi-vol, y colapsó el IRPM de 105 a 71.7.

**REGLA:** `calcular_capa3.py` mantiene un calendario `STOCK_SPLITS` con fecha y ratio. Para cada split, los precios históricos PRE-split se dividen por el ratio antes de calcular retornos logarítmicos. Esto mantiene los retornos continuos sin modificar raw_prices (que conserva los precios originales de PPI).

**PORQUÉ:** el retorno logarítmico usa P_t / P_{t-1}. Si P_t está en base post-split y P_{t-1} en base pre-split, el retorno calculado incluye el efecto mecánico del split (ej: -90% para un split 10:1). Ajustar los precios pre-split al ratio los lleva a la misma base que los post-split. El retorno de la fecha del split pasa de -90% a ~-2% (movimiento de mercado puro).

**CÓMO IDENTIFICAR FUTUROS SPLITS:** en el log de calcular_capa3.py aparece Capa3 con z-scores < -5 o vol > 100% → revisar si alguna acción del basket tuvo un cambio de precio > 50% en un día.

---

## 2026-08-12 — Gap de datos Jul-24 → Aug-4 infla artificialmente Capa3

**ERROR (potencial):** el Task Scheduler no corrió los scrapers de acciones (YPFD/GGAL/PAMP/TECO2) durante ~8 ruedas (Jul-24 → Aug-4). El Aug-5 fue el siguiente punto de datos de Capa3. El return "diario" del Aug-5 abarca en realidad ~8 ruedas reales de mercado, inflando la semi-vol a 229% (z=-12.27) y colapsando el IRPM a 71.7.

**REGLA:** si el Task Scheduler falla por más de 3 ruedas, Capa3 acumula un gap. El primer día post-gap mostrará una caída artificial en el z-score de Capa3 proporcional al número de ruedas perdidas. Verificar `logs/` para detectar fallas del scheduler. Si se detecta el gap, considerar backfill manual del período o excluir esas fechas del cálculo.

**PORQUÉ:** la semi-volatilidad usa retornos diarios (precio_hoy/precio_ayer - 1). Si entre precio_ayer y precio_hoy hay un gap de N ruedas, el retorno calculado incluye el movimiento de N días. La std de ese único "retorno" gigante domina la ventana de 20 días y genera z-scores extremos.

---

## 2026-07-11 — z_rofex tenía signo invertido en calcular_capa1.py

**ERROR:** `calcular_capa1.py` calculaba `z_rofex = rolling_zscore(premium)` sin invertir. El comentario decía "premium alto = menos miedo = buena señal" pero es al revés: premium alto (ROFEX >> MEP) = mercado espera devaluación = señal mala. El signo correcto es `-rolling_zscore(premium)`.

**REGLA:** `z_rofex = -rolling_zscore(premium)` donde `premium = ROFEX_1M_EQUIV/MEP - 1`. Premium bajo (≈ 0, ROFEX ≈ MEP) = no hay miedo de devaluación = contribuye positivamente al IRPM.

**PORQUÉ:** en el régimen de flotación libre (desde abr-2025), el premium es ≈ 0. Con el signo incorrecto, ese premium era NEGATIVO respecto a la media histórica (que incluía el crawling peg con ~2%/mes) → z_rofex negativo → amplificaba la señal bajista del MEP en lugar de compensarla. El fix subió el IRPM de 91.6 a 101.0 (recalculado el 10-jul-2026). Rango histórico recalculado: min 75.5 (sep-2025) · max 114.9 (dic-2024).

---

## 2026-06-11 — Ruta credenciales PPI hardcodeada a Desktop (laptop vieja)
**ERROR:** `scraper_bonos.py`, `scraper_acciones.py` y `scraper_rofex.py` tenían `CRED_PATH` apuntando a `C:/Users/Mlaxague/Desktop/MARIANO/INVERSIONES/ENGINE/API KEY PPI.txt` — ruta de la laptop anterior.
**REGLA:** la ruta correcta en la nueva laptop es `C:/Users/Mlaxague/Projects/INVERSIONES/ENGINE/API KEY PPI.txt`.
**PORQUÉ:** cambio de laptop en junio 2026. La carpeta MARIANO del Desktop no se copió; los proyectos se migraron a `C:\Users\Mlaxague\Projects\`.

---

## 2026-05-20 — Kink electoral: DLR_ENE27 disponible, DLR_DIC27 no listado hasta ~dic-2026

**ERROR (estimación):** la activación del kink electoral estaba estimada en agosto-2026, asumiendo que ambos contratos (DLR_ENE27 y DLR_DIC27) estarían disponibles para entonces.
**HALLAZGO:** DLR_ENE27 ya tiene 69 filas (umbral MIN_PERIODS=63 superado). Pero DLR_DIC27 (dic-2027) no está listado en PPI — ROFEX lista contratos solo hasta ~12 meses adelante, y dic-2027 está a 19 meses.
**REGLA:** La activación del kink depende de DLR_DIC27 exclusivamente. Verificar en dic-2026. Activación estimada corregida: mar-2027 (63 días hábiles tras aparecer DIC27).
**PORQUÉ:** No alcanza con que un contrato supere el umbral — ambos son necesarios para la señal diferencial. `scraper_rofex.py` ampliado a `n_months=14` para capturar contratos hasta ABR27.

---

## 2026-05-19 — calcular_rofex_signal.py dependía de MEP que aún no existía al momento de correr

**ERROR:** en el pipeline, `calcular_rofex_signal.py` (paso 7) leía el activo `MEP` de `raw_prices` para normalizar los contratos PPI a equivalente 1-mes. Pero `MEP` lo guarda `calcular_capa1.py` (paso 8). Entonces los últimos días hábiles no tenían MEP disponible al momento del cálculo y quedaban fuera de la serie.

**REGLA:** `calcular_rofex_signal.py` ahora computa MEP directamente desde AL30_ARS/AL30D_USD (disponibles desde el paso 1 de scrapers), sin depender de calcular_capa1.py. Función: `load_mep()`.

**PORQUÉ:** dependencia circular de facto en el pipeline — si A necesita output de B y B corre después de A, siempre va a usar datos del día anterior. El fix es que A compute su dependencia directamente desde las fuentes primarias.

---

## 2026-05-13 — Transición BCR→PPI crea spike de 6pp en premium (limitación documentada)

**ERROR:** ninguno de datos — es una limitación estructural del pipeline.

**REGLA:** el período Oct 8 - Oct 26 de 2025 tiene un artefacto en ROFEX_1M_EQUIV. BCR medía el contrato 1M real (DLR_NOV25 ≈ 1469 ARS). PPI sólo tiene contratos activos desde MAY26. La normalización a 1M de DLR_MAY26 (a 7 meses de distancia con curva en contango pronunciado pre-electoral) sobreestima el 1M real en ~90 ARS (6%). El gap se cierra post-elecciones cuando la curva se aplana.

**PORQUÉ:** el mercado en Oct-2025 tenía una prima de incertidumbre electoral concentrada en los tramos de 2-7 meses, mientras el tramo 1M ("espera y verá") estaba casi flat. La normalización de expectations theory asume curva plana — no captura el kink electoral.

**IMPACTO:** ~19 días de z-score de ROFEX ligeramente inflacionado, parcialmente absorbido por el blend 50/50 MEP+ROFEX. No afecta materialmente el IEP histórico. Resoluble únicamente con datos del contrato 1M de ese período (DLR_NOV25), que no están disponibles en fuentes públicas.

---

## 2026-05-13 — Parsing BCR confirmado exacto al céntimo (spot-check 13/15 PDFs)

**REGLA:** confiar en los datos BCR. Los 13 PDFs verificables coinciden 0.0 diferencia. Los 2 "NO_FOUND" son boletines no publicados ese día, no errores de extracción.

**PORQUÉ:** el regex de `scraper_rofex_bcr.py` extrae el precio de ajuste (columna 9) correctamente para todos los formatos de PDF encontrados en el período abr-2024 → oct-2025.

---

## 2026-05-08 — Normalización: no mezclar regímenes políticos en la ventana histórica

**ERROR:** el plan original usaba z-score con ventana fija 2020-2025 para normalizar los activos.

**REGLA:** usar z-score rolling de 252 días hábiles (1 año).

**PORQUÉ:** el período 2020-2025 mezcla el gobierno de Fernández/CFK con el de Milei. Los niveles de riesgo soberano, brecha cambiaria y paridad de bonos son incomparables entre regímenes. Un z-score calculado sobre esa ventana genera falsos "extremos" porque el piso de riesgo cambió estructuralmente. El rolling 252d se adapta al régimen vigente.

---

## 2026-05-08 — No arrancar por la fuente más difícil técnicamente

**ERROR:** el plan original empezaba Capa 1 con ROFEX (API con autenticación, lógica de pendiente electoral, contratos múltiples).

**REGLA:** la señal de riesgo político de la brecha MEP/CCL es igual de relevante, más accesible (scraping público) y con historia desde 2019. Empezar ahí.

**PORQUÉ:** el riesgo de atascarse en infraestructura técnica antes de tener un solo dato es real. Validar primero que el pipeline funciona end-to-end con la fuente más simple; luego incorporar complejidad.

---

## 2026-05-08 — El spread pre/post-mandato es la señal electoral más pura en curva de bonos

**NOTA: pendiente de revisión — ver lección del 13/05/2026 más abajo.**

**REGLA (intención original):** incluir el diferencial de yields entre bonos que vencen después del cambio de gobierno (GD35+) y los que vencen durante el mandato vigente (GD30) como componente explícito en Capa 2.

**PORQUÉ:** ese spread cuantifica directamente cuánto le cobra el mercado a Argentina por la incertidumbre sobre quién va a gobernar cuando venzan esos bonos. En mayo 2026 ≈ 300 bps en CDS. Es la "prima de riesgo electoral" pura.

---

## 2026-05-13 — El spread GD30D-GD35D NO es una señal electoral limpia

**ERROR (del documento fundacional):** se asumió que el spread GD30D-GD35D capturaba riesgo post-electoral, sin validar contra los datos.

**REGLA:** NO agregar GD30D-GD35D como componente del IEP. Evaluar siempre el comportamiento histórico de cualquier señal antes de integrarla.

**PORQUÉ:** los datos muestran una tendencia secular fuerte: +1.86 (2022) → +9.18 (2024) → -10.86 (oct-2025-hoy). Esta tendencia refleja la amortización de GD30 (que reduce su precio per unit) y el cambio en la estructura de flujos del bono, no riesgo electoral. La correlación con el IEP es r=0.114 — prácticamente nula. El spread correcto (CDS 1Y vs 2Y, bond maturity kink) existe en el mercado pero no es capturable con los instrumentos disponibles en la DB porque GD30 y GD35 AMBOS vencen post-2027.

**La señal electoral disponible más directa es el law spread (GD30D-AL30D)**, ya en Capa 2, con r=0.349 con IEP y perfectamente alineada con todos los hitos históricos. Es la señal kirchnerismo: cuando sube → mercado teme reestructuración bajo ley argentina.

---

## 2026-05-09 — El constructo del IEP es "continuidad del programa", no "reelección de Milei"

**REGLA:** el IEP mide expectativa de continuidad del programa político-económico vigente. La pregunta central es: "¿qué tan creíble es que Argentina siga pagando su deuda bajo el esquema de política económica actual?"

**PORQUÉ:** los bonos pricean probabilidad de *pago de deuda*, no identidad del próximo presidente. La cadena causal real es `precio_alto → alguien_paga_la_deuda`, no `precio_alto → Milei_gana`. Definir el constructo como "reelección de Milei" crea inconsistencias: ¿qué pasa si el programa continúa bajo otro candidato? ¿Si Milei gana pero pivota el programa? La definición basada en el programa es más robusta y más defensible ante audiencias institucionales.

---

## 2026-05-09 — EMBI es componente O validador externo, no ambos

**REGLA:** el EMBI entra a Capa 2 como componente del índice. Por lo tanto, no puede ser benchmark de validación externa. Los validadores válidos son: ICG-UTDT, IG-RadarPolitico.ai, y análisis de eventos políticos con fecha conocida.

**PORQUÉ:** validar el IEP contra el EMBI cuando el EMBI es uno de sus componentes es circular — la correlación está parcialmente garantizada por diseño, no por validez del constructo. Una validación real requiere variables construidas con metodologías y datos completamente independientes. El ICG-UTDT (encuesta mensual de confianza) y las encuestas de aprobación cumplen ese requisito hoy. RadarPolitico se suma como validador cuando exista como producto.

---

## 2026-05-08 — No asignar peso a una capa sin historia propia

**ERROR:** el plan original asignaba 25% del índice a Capa 3 (opciones BYMA) desde el inicio.

**REGLA:** la Capa 3 arranca en 0% y se activa cuando haya mínimo 90 días de historia propia.

**PORQUÉ:** el mercado de opciones en Argentina es ilíquido. Los datos históricos son escasos y poco confiables. Asignarle 25% del índice sin historia es irresponsable metodológicamente y no publicable.
