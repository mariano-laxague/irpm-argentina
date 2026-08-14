# Marco de Validación y Gobernanza — IRPM

**Versión:** 1.0
**Fecha:** 13/08/2026
**Aplicación:** obligatorio para metodología, dashboard, newsletter, informes y releases.

---

## 1. Estado metodológico

El IRPM es, en su estado actual, un **índice experimental que sintetiza condiciones de mercado a partir de señales financieras sensibles al escenario político y económico argentino**.

Combina señales cambiarias, de deuda soberana y de volatilidad accionaria. Su construcción permite comparar el estado relativo de esas señales a través del tiempo. No produce una probabilidad calibrada, no identifica causalidad política y no predice por sí solo un resultado electoral.

### Formulaciones permitidas

- “El IRPM sintetiza diariamente señales de activos sensibles al escenario político y económico argentino.”
- “Un valor superior a 100 indica condiciones más favorables que en el baseline convencional del 11/12/2023.”
- “La interpretación política es una lectura editorial apoyada en datos de mercado.”
- “El resultado es experimental y está sujeto a revisión metodológica.”

### Formulaciones no permitidas sin nueva evidencia

- “El IRPM calcula la probabilidad de continuidad o reelección.”
- “El mercado anticipa a las encuestas.”
- “Un movimiento fue causado por un evento” cuando sólo existe proximidad temporal.
- “Validado” sin especificar qué hipótesis, muestra, protocolo y criterio fueron superados.
- “El law spread aísla exclusivamente riesgo político.”

---

## 2. Niveles de evidencia

| Nivel | Qué demuestra | Ejemplo | Estado actual |
|---|---|---|---|
| E0 — Implementación | El cálculo corre y produce datos | Pipeline y dashboard | Alcanzado |
| E1 — Validez técnica | Fórmulas, signos, fechas y datos cumplen invariantes | Tests y controles de calidad | Parcial |
| E2 — Robustez interna | El resultado no depende excesivamente de una decisión acotada | Sensibilidad 14 combinaciones | Parcial |
| E3 — Validez descriptiva | El índice covaría de forma consistente con fenómenos externos definidos ex ante | Estudio de eventos v2 | No alcanzado |
| E4 — Validez incremental | Aporta información no contenida en sus inputs o benchmarks simples | Ablaciones/out-of-sample | No evaluado |
| E5 — Calibración predictiva | Se traduce en probabilidades o predicciones con error medible | Brier score/calibración | No aplicable hoy |

La existencia de E0–E2 no autoriza claims de E3–E5.

---

## 3. Separación de capas de verdad

Toda superficie debe diferenciar:

1. **Dato observado:** precio, spread, volatilidad, fecha y fuente.
2. **Transformación:** z-score, ponderación, baseline y ajuste.
3. **Resultado del índice:** valor y variación del IRPM.
4. **Interpretación editorial:** hipótesis sobre qué factores pueden explicar el movimiento.

Las interpretaciones deben incluir fuente cuando incorporen hechos externos y usar lenguaje de incertidumbre: “coincide con”, “es consistente con”, “hipótesis”, “puede reflejar”.

---

## 4. Protocolo de completitud de datos

Cada observación publicable debe registrar:

- fecha del IRPM;
- versión de metodología;
- commit o release;
- fecha máxima de cada input;
- componentes presentes y ausentes;
- pesos nominales y efectivos;
- flags de ajustes extraordinarios;
- estado `COMPLETO`, `DEGRADADO` o `NO_PUBLICABLE`.

### Regla propuesta para `v0.1-experimental`

- `COMPLETO`: todos los componentes obligatorios tienen fecha compatible y pasan sanity checks.
- `DEGRADADO`: sólo se permite para análisis interno; nunca se publica como valor ordinario.
- `NO_PUBLICABLE`: falta un componente, existe una anomalía o no puede verificarse el deploy.

La renormalización automática por ausencia de un input queda prohibida para publicación salvo que se defina una metodología alternativa versionada y visible.

---

## 5. Protocolo de análisis de eventos v2

### Antes de ejecutar

1. Definir la lista de eventos sin mirar las variaciones del IRPM del período evaluado.
2. Registrar fecha, ventana, dirección esperada, mecanismo y fuente primaria/secundaria.
3. Definir el conjunto de exclusión: shocks globales, pagos, splits y días con datos degradados.
4. Congelar métricas y criterio de éxito.

### Diseño mínimo

- Una observación por episodio; no contar días consecutivos como shocks independientes.
- Ventanas no solapadas o reglas explícitas de asignación.
- Retorno/variación anormal comparado contra un benchmark o distribución nula.
- Intervalos de confianza obtenidos con un método compatible con dependencia temporal, como block bootstrap.
- Reporte separado de positivos, negativos, falsos positivos y eventos sin reacción.
- Holdout temporal para evitar calibrar y evaluar en la misma muestra.

### Criterio de interpretación

La proximidad evento-movimiento aporta evidencia de correspondencia temporal; no demuestra causalidad. El resultado 14/20 de la versión anterior se conserva como análisis exploratorio, pero no como validación aprobada.

---

## 6. Protocolo IRPM vs. ICG y otras series

### Resultado vigente

- Muestra: 32 meses, diciembre de 2023 a julio de 2026.
- Correlación contemporánea: `r=0,367`.
- Mayor correlación observada: ICG adelantando un mes al IRPM, `r=0,384`.
- IRPM adelantando un mes: `r=0,324`.
- Granger IRPM→ICG: sin evidencia estadística en lags 1–3.
- Accuracy direccional a un mes: 40%.

**Conclusión permitida:** la hipótesis de que el IRPM adelanta sistemáticamente al ICG no fue confirmada en la muestra disponible. La baja potencia obliga a reexaminarla con más datos, pero no autoriza a declarar el resultado esperado o confirmado.

### Próxima evaluación

- Congelar el protocolo antes del rerun.
- Evaluar estacionariedad y especificación antes de correlaciones/Granger.
- Corregir por múltiples lags examinados.
- Repetir cuando `N≥50` y nuevamente con un holdout posterior.
- No redefinir “éxito” después de observar el resultado.

---

## 7. Sensibilidad y ablaciones

La sensibilidad actual prueba sólo combinaciones de pesos externos dentro de una grilla. La próxima versión debe cubrir:

- ventanas rolling y mínimos de historia;
- baseline y factor de escala;
- pesos externos e internos;
- exclusión individual de componentes;
- tratamiento de faltantes;
- fechas de pago y splits;
- uso o no del ajuste VIX;
- período de muestra;
- media móvil de presentación.

Cada resultado debe separar:

- estabilidad de fechas extremas;
- estabilidad de magnitud;
- estabilidad del ranking de episodios;
- información incremental respecto de EMBI, MEP y bonos individuales.

Robustez no equivale a optimalidad ni a validez del constructo.

---

## 8. Gobernanza de cambios

### Cambio metodológico

Todo cambio que afecte valores históricos requiere:

1. issue o entrada de plan con hipótesis y motivo;
2. test antes/después;
3. comparación completa de series;
4. actualización de versión metodológica;
5. changelog;
6. decisión explícita sobre recalcular historia;
7. revisión del dashboard y de la documentación pública.

### Release

Una release debe contener o referenciar:

- tag y commit;
- metodología pública;
- código del cálculo;
- dependencias;
- configuración de ejemplo;
- snapshot de datos y hashes;
- resultados de tests;
- manifest de componentes;
- changelog;
- QA desktop/mobile;
- límites de uso.

El dashboard debe mostrar la fecha efectiva del dato y la versión metodológica. La actualización de datos no puede versionar solamente el HTML si el código generador o la metodología cambiaron.

---

## 9. Gobernanza editorial

Cada hito público debe incluir:

- fecha o período;
- valor y variación observada;
- fuentes del hecho externo;
- explicación marcada como hipótesis o lectura editorial;
- factores alternativos relevantes;
- indicación de shock global o dato degradado;
- autor/fecha de la interpretación.

Las piezas comerciales no pueden elevar el nivel de evidencia respecto del documento metodológico vigente.

---

## 10. Criterio de salida de fase experimental

El proyecto puede retirar la etiqueta “experimental” cuando:

- complete E1 de manera automatizada;
- publique al menos una evaluación E3 preregistrada y no solapada;
- demuestre información incremental E4 o acote formalmente su propuesta a síntesis descriptiva;
- opere releases trazables y monitoreo externo durante un período sostenido;
- complete QA accesible y responsive;
- mantenga lenguaje público consistente con la evidencia alcanzada.
