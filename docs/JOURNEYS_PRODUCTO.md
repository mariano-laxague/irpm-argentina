# Journeys prioritarios del dashboard

Este mapa define qué debe poder hacer una persona antes de evaluar responsive o
accesibilidad. No sustituye el QA visual: P6.6 debe capturar estos recorridos
en desktop y móvil sobre el dashboard servido.

## J1 — Lectura rápida

**Necesidad:** entender en menos de un minuto qué mide el IRPM, cuál es su
último valor y qué tan reciente es el dato, sin tomarlo como predicción.

1. Abrir la portada y reconocer IRPM como indicador experimental de riesgo de
   mercado.
2. Leer valor, fecha efectiva, distancia respecto del baseline y una frase de
   interpretación limitada.
3. Encontrar la advertencia metodológica y llegar a la explicación completa.

**Éxito:** valor, fecha y límite interpretativo son visibles sin interactuar.
**Riesgos a verificar:** fecha desactualizada, lenguaje probabilístico retirado,
contraste de la zona y comprensión sin depender del color.

## J2 — Explicación de un movimiento

**Necesidad:** investigar un cambio del indicador sin inferir causalidad que
los datos no sostienen.

1. Elegir un período y leer la curva del IRPM.
2. Activar o desactivar el ajuste VIX y distinguirlo del IRPM principal.
3. Abrir un hito o comparar capas para ver contexto, fecha y advertencia de no
   causalidad.
4. Volver al valor actual sin perder la orientación.

**Éxito:** controles, estado activo y series se entienden con teclado y no
ocultan la serie principal.
**Riesgos a verificar:** canvas inaccesible, controles sin labels/foco, hito
que sólo dependa de hover o una leyenda que confunda contexto con explicación.

## J3 — Auditoría metodológica

**Necesidad:** evaluar cómo se compone el indicador, su evidencia y qué parte
del resultado no debe usarse para decisiones concluyentes.

1. Navegar a metodología desde la cabecera o el final de la lectura rápida.
2. Identificar las tres capas, pesos, baseline y política de completitud.
3. Acceder a metodología pública, snapshot, ajustes y límites de validación.
4. Consultar datos o resumen equivalente sin depender del gráfico.

**Éxito:** una persona puede verificar el framing experimental y navegar hacia
evidencia reproducible sin leer código.
**Riesgos a verificar:** enlaces no visibles, contenido crítico sólo en canvas,
jerarquía de encabezados insuficiente y ausencia de alternativa tabular.

## Secuencia de implementación P6

1. P6.2 preserva los controles que necesita J2.
2. P6.3 hace que los tres journeys funcionen en 360, 390, 768, 1280 y 1440 px.
3. P6.4 y P6.5 eliminan dependencias de mouse/canvas para J2 y J3.
4. P6.6 captura y revisa cada journey con estados iniciales e interactivos.
