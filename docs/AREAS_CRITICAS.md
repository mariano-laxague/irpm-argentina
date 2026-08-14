# Áreas Críticas — IEP Índice de Expectativa Política
**Revisión conceptual externa · Mayo 2026**

Este documento registra los gaps conceptuales del proyecto antes de avanzar en la implementación. No evalúa el estado de desarrollo sino la solidez de los supuestos que sostienen el índice. Su propósito es forzar alineamiento antes de construir sobre bases que podrían ser incorrectas.

---

## Reevaluación vigente — 13/08/2026

La revisión del repositorio, la base de datos y el producto publicado encontró consecuencias nuevas. Varias resoluciones de mayo se basaban en documentar la limitación, pero la comunicación pública continuó elevando el claim. Por eso se reabren los puntos que afectan una release trazable.

| # | Área | Estado vigente | Decisión operativa |
|---|---|---|---|
| 1 | Identificación política vs. macro/global | 🔴 Abierto | Reencuadrar como condiciones de mercado y evaluar identificación/ablaciones (P1/P3) |
| 2 | Constructo | 🟡 Redefinido | Retirar “probabilidad implícita”; unidad = índice estandarizado, baseline convencional |
| 3 | Validación | 🔴 Reabierto | Eventos v1 pasa a exploratorio; leading ICG no confirmado; aplicar protocolo preregistrado |
| 4 | Baseline | 🟡 Documentado, no calibrado | Mantener 11/12/2023 como convención y revisar umbrales heurísticos |
| 5 | Representatividad del mercado | 🟡 Limitación permanente | No extrapolar a sociedad ni consenso económico general |
| 6 | Feedback loop | 🟡 Riesgo futuro | Metodología, T+1, provenance y monitoreo; no declarar “irrelevante” por etapa |
| 7 | Escala accionable | 🔴 Abierto | Definir utilidad descriptiva; retirar zonas causales/probabilísticas no calibradas |
| 8 | Ventaja competitiva | 🟡 Hipótesis comercial | Validar distribución después de gates técnicos/metodológicos |
| 9 | Horizonte 2027 | 🔴 Abierto | Tratar contenido electoral como indirecto; kink futuro sujeto a historia y validación |

**Fuentes vigentes:** `../PLAN_ACCION.md` y `MARCO_VALIDACION_Y_GOBERNANZA.md`.

---

## Tabla de resolución histórica — Sesión 6 (09/05/2026)

> Esta tabla explica decisiones de mayo de 2026. Sus estados “cerrado” o “documentado” no reemplazan la reevaluación vigente anterior.

| # | Gap | Clasificación | Estado | Decisión / Acción |
|---|-----|--------------|--------|-------------------|
| 1 | Problema de identificación | Limitación documentable | ✅ Documentado | Sección 8b CONTEXTO.md: el IEP sintetiza riesgo soberano con interpretación editorial; no puede aislar señal política de macro. Limitación compartida con el EMBI. |
| 2 | Confusión de constructos | **Bloqueador** | ✅ Cerrado | Constructo = expectativa de continuidad del programa económico (no reelección de Milei). Cadena causal: `precio_alto → alguien_paga_la_deuda`. Horizonte: 3-6 meses. Ver sección 1 CONTEXTO.md. |
| 3 | Circularidad en validación | **Bloqueador** | ✅ Cerrado | EMBI sale del esquema de validación. Benchmarks válidos hoy: ICG-UTDT + encuestas de aprobación + análisis de eventos. RadarPolitico se incorpora cuando exista como producto. Ver sección 8 CONTEXTO.md y sección 0.5 PLAN.md. |
| 4 | Baseline no exógeno | Limitación documentable | ✅ Documentado | Sección 8b CONTEXTO.md: baseline = convención narrativa anclada en fecha políticamente significativa (27-oct-2025). No es valor fundamental — análogo al año base de un IPC. |
| 5 | Supuesto de eficiencia en mercado ilíquido | Limitación documentable | ✅ Documentado | Sección 8b CONTEXTO.md: el IEP representa consenso de participantes del mercado de capitales argentino, no de la sociedad. Limitación no removible; relevante para qué audiencias usa el índice. |
| 6 | Causalidad inversa / feedback loop | Limitación documentable | ✅ Documentado | Sección 8b CONTEXTO.md: riesgo escala con adopción. Mitigación: publicación T+1 + metodología pública. Irrelevante en Fase 0. |
| 7 | Escala no accionable | No-problema (feature) | ✅ Sin acción | El IEP es instrumento descriptivo de contexto, no señal de trading. La newsletter interpreta. La escala relativa es suficiente para ese uso. |
| 8 | Ventaja competitiva no verificada | No-problema (estratégico) | ✅ Sin acción | Gap estratégico-comercial, no metodológico. El moat real es ejecución (frecuencia diaria + índice numérico). No requiere cambio en metodología. |
| 9 | Horizonte temporal débil a 18+ meses | Limitación documentable | ✅ Documentado | Sección 8b CONTEXTO.md: horizonte declarado = 3-6 meses. Señal electoral adquiere peso creciente al acercarse 2027, estimativamente desde H1 2027. |

---

---

## 1. El problema de identificación

**Supuesto no demostrado:** los precios de los activos elegidos contienen una señal política extraíble y distinguible del ruido macroeconómico.

Los bonos soberanos, el tipo de cambio y las opciones sobre acciones se mueven por razones simultáneas y entrelazadas: tasas de la Fed, sentimiento global de emergentes, flujos de fondos internacionales, datos fiscales locales, renegociaciones con el FMI, inflación de EEUU, eventos de liquidez puntual. El proyecto asume que un z-score sobre estas series produce una "señal política". No es así: produce un z-score. La interpretación política es editorial, no estadística.

**Pregunta sin responder:** ¿qué mecanismo técnico justifica que los movimientos seleccionados son señal política y no señal crediticia o macroeconómica? Sin un modelo de identificación explícito, el IEP es una reinterpretación narrativa de instrumentos de renta fija estándar.

**Riesgo concreto:** si el IEP correlaciona >0.85 con el EMBI (probable, dado que EMBI es componente de Capa 2), el índice no agrega información nueva respecto a lo que ya es público y gratuito.

---

## 2. Confusión entre dos constructos distintos

El proyecto define el IEP como medida de dos cosas simultáneamente:

1. La probabilidad de reelección de Milei en 2027
2. La expectativa de continuidad del programa político-económico

Estos no son equivalentes y el mercado tampoco los trata como equivalentes:

- Un sucesor puede continuar el programa (ej. un candidato de LLA o PRO)
- Milei puede ganar y pivotar el programa antes de 2027
- El programa puede fracasar independientemente del resultado electoral
- La oposición puede ganar y mantener disciplina fiscal

Los bonos pricean probabilidad de *pago de deuda*, no identidad del próximo presidente. La cadena causal que el proyecto asume es `precio_alto → Milei_gana`. La cadena real es `precio_alto → alguien_va_a_pagar_esta_deuda`. La brecha entre ambas es conceptualmente grande y empíricamente no está cerrada.

**Decisión requerida:** ¿qué mide el IEP? Debe ser una sola cosa, definida con precisión suficiente para que la validación empírica sea posible.

---

## 3. Circularidad en la validación

El EMBI figura como componente de Capa 2 (parte de la construcción del índice) y como benchmark de validación externa (sección 8 de CONTEXTO.md). Esto es circular: si el EMBI entra en la construcción, la correlación con el EMBI está parcialmente garantizada por diseño, no por validez del constructo.

Para que la validación sea válida metodológicamente, el EMBI debe elegirse en uno de dos roles mutuamente excluyentes:

- **Rol constructivo:** entra al índice como señal, y se usa otra variable externa para validar
- **Rol validador:** no entra al índice, y se usa solo como contrastador externo

En el diseño actual cumple ambos roles al mismo tiempo, lo que hace inválida la validación propuesta.

---

## 4. El baseline no es exógeno

El baseline IEP=100 en octubre 27, 2025 se justifica con el argumento de que "el mercado consolidó su lectura de continuidad del programa" tras las legislativas. Pero:

- Los mercados pudieron haber priceado ese resultado semanas antes del 27/10
- El día siguiente a una elección puede ser un spike de alivio transitorio, no un equilibrio estable
- Otros eventos son candidatos igualmente válidos como anchor: el acuerdo con el FMI, el primer superávit fiscal anunciado, la salida del cepo parcial

La elección del baseline es una decisión editorial, no técnica. Y tiene consecuencias grandes: determina si toda la serie histórica aparece "por debajo" o "por encima" de 100, lo cual define la narrativa completa del índice. Una decisión con tanto peso sobre la interpretación necesita justificación técnica explícita, o debe reconocerse abiertamente como convencional.

---

## 5. El supuesto de eficiencia de mercado en un mercado ilíquido e intervenido

La premisa operativa del IEP — "los mercados procesan información política antes que las encuestas" — es una aplicación de la hipótesis de mercados eficientes. Su validez requiere mercados razonablemente líquidos, con participantes diversos y sin intervención sistemática.

El mercado financiero argentino relevante (BYMA, ROFEX, bonos soberanos) tiene características opuestas:

- Volumen de opciones muy bajo, especialmente en Edenor y Telecom
- Intervención activa del BCRA en el tipo de cambio
- Cepo cambiario que limita la libre formación de precios
- Concentración de flujos en un número reducido de operadores institucionales locales

En estas condiciones, el precio puede reflejar las apuestas de 10 fondos que comparten los mismos analistas y leen los mismos diarios. "Señal de mercado" y "consenso de un grupo pequeño" son cosas distintas. El proyecto no distingue entre ambas.

---

## 6. Causalidad inversa no considerada

El proyecto asume la dirección causal: `evento político → reacción de mercado → IEP lo captura`.

En Argentina existe evidencia documentada de la dirección inversa: operadores grandes acumulan o venden → el precio se mueve → los medios interpretan el movimiento como "señal del mercado" → esa narrativa condiciona el clima político y las decisiones de otros actores.

Si el IEP tiene audiencia y circula diariamente, puede incorporarse al propio mercado que pretende medir. Los lectores que usan el índice para operar retroalimentan los precios que construyen el índice. Este riesgo de feedback loop no está mencionado en el documento fundacional y no tiene mitigación propuesta.

---

## 7. La escala de interpretación no produce output accionable

El rango IEP 70-89 se define como "optimismo moderado con ruido — comparable a H1 2025". Esta definición tiene dos problemas:

**Problema descriptivo:** "comparable a H1 2025" no es un criterio operacional. H1 2025 duró seis meses y tuvo alta varianza interna. ¿Comparable en qué dimensión exacta?

**Problema de utilidad:** un trader, un analista de riesgo o un consultor político no puede tomar una decisión basada en un rango que describe una analogía histórica. Para ser accionable, la escala necesita o bien probabilidades (ej. "el mercado pricea X% de probabilidad de continuidad") o bien señales condicionales (ej. "si el índice cae N puntos en K días, históricamente siguió el evento Y").

Sin output accionable, el índice produce narrativa, no instrumento. La diferencia importa para la propuesta de valor y para la disposición a pagar de las audiencias objetivo.

---

## 8. Ventaja competitiva no verificada

El documento fundacional afirma: "ningún actor del mercado tiene las tres capacidades: comprensión política + expertise en mercados + capacidad de comunicación."

Esta es una hipótesis sobre el ecosistema, no un hecho relevado. Actores que operan en esa intersección existen:

- Consultoras de riesgo político con perspectiva de mercado (ACM, Analytica, EPyCA, Equilibra)
- Analistas que publican en esa intersección con audiencia consolidada (Redrado, Furiase, Bein)
- Research de brokers medianos que cruzan política y finanzas (Balanz, Portfolio Personal)

El diferencial real del IEP sería la *frecuencia diaria* y el *formato de índice numérico*, que ninguno de los actores mencionados produce sistemáticamente. Ese es un moat de ejecución, no de capacidad. Es válido, pero es más frágil: puede replicarse con recursos si el índice demuestra tracción.

---

## 9. Horizonte temporal del constructo

El índice pretende medir expectativa sobre las elecciones de 2027. En mayo de 2026 faltan 18+ meses. La pregunta de si los mercados financieros pricean riesgo electoral con ese horizonte es empírica y no está respondida en el proyecto.

Es plausible que la señal electoral sea débil o ruidosa hasta que el horizonte baje a 6-9 meses. En ese caso, el IEP podría ser principalmente un indicador de riesgo crediticio hasta mediados de 2026, y recién adquirir contenido electoral significativo en 2027. El diseño del índice no contempla esta variación temporal del constructo que pretende medir.

---

## Mapa de decisiones requeridas

Antes de continuar la implementación, estas preguntas necesitan respuesta explícita:

| # | Pregunta | Por qué no puede postergarse |
|---|----------|------------------------------|
| 1 | ¿Qué mide exactamente el IEP: riesgo crediticio, continuidad del programa, o probabilidad de reelección? | Define qué variables son relevantes y qué validación es necesaria |
| 2 | ¿Cómo se justifica que el movimiento de los activos elegidos es señal política y no señal crediticia o macro? | Sin esto, la interpretación política del índice es editorial, no metodológica |
| 3 | ¿El EMBI es componente del índice o validador externo? | No puede ser ambos |
| 4 | ¿El baseline tiene justificación técnica o es convencional? | Si es convencional, debe documentarse y comunicarse así |
| 5 | ¿Bajo qué condiciones el índice sería falsable? | Sin criterio de falsabilidad, no es un instrumento científico |

---

*Este documento es una herramienta de alineamiento conceptual, no un juicio sobre la viabilidad del proyecto. Los gaps identificados son resolubles. Su valor es forzar las respuestas antes de que el costo de cambiarlas sea alto.*
