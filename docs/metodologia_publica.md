# IRPM — Metodología pública

**Versión 1.2-experimental · Agosto 2026**
**Dashboard:** https://marianolaxague-crypto.github.io/irpm-argentina/

> El IRPM es un índice experimental que sintetiza condiciones de mercado a partir de señales financieras sensibles al escenario político y económico argentino. No es una probabilidad electoral calibrada ni una recomendación de inversión.

---

## Qué mide

El **Índice de Riesgo Político de Mercado (IRPM)** sintetiza diariamente señales de activos argentinos sensibles a cambios en riesgo soberano, expectativas cambiarias, credibilidad del programa económico y volatilidad local.

El índice observa posicionamiento de mercado, no preferencias declaradas. Esto lo vuelve complementario de encuestas e indicadores de opinión pública, pero no implica que anticipe sus movimientos ni que represente a la sociedad argentina.

El IRPM está anclado en 100 el 11 de diciembre de 2023. Valores superiores indican que el compuesto de señales se encuentra en condiciones más favorables que en esa fecha; valores inferiores indican condiciones menos favorables. El 100 es una convención de lectura. Los puntos del índice no son porcentajes ni probabilidades.

## Cómo se construye

### Capa 1 — Señal cambiaria (35%)

Combina el tipo de cambio MEP calculado mediante AL30/AL30D y una serie equivalente a un mes de futuros ROFEX. Un MEP o premium de futuros elevado respecto de su historia reciente se interpreta como mayor demanda de cobertura cambiaria.

### Capa 2 — Deuda soberana (40%)

Combina precios de GD30D, AL30D y GD35D, EMBI Argentina y el diferencial GD30D−AL30D o *law spread*. El law spread compara títulos del mismo soberano bajo jurisdicciones diferentes y puede reducir parte de la exposición común, pero no aísla exclusivamente riesgo político.

### Capa 3 — Volatilidad accionaria (25%)

Utiliza la semi-volatilidad realizada a la baja de YPFD, GGAL, PAMP y TECO2. Esta señal resume estrés bajista del basket; es un proxy de nerviosismo accionario, no volatilidad implícita de opciones ni una medida política pura.

### Normalización

Cada señal se transforma mediante z-score rolling de 252 ruedas, con un mínimo de 63 observaciones. Las capas se combinan y se reescalan:

> IRPM(t) = 100 + (0,35 × z₁ + 0,40 × z₂ + 0,25 × z₃ − valor del compuesto en el baseline) × 10

El factor 10 facilita la lectura. No surge de una calibración probabilística.

## Completitud de datos y fecha efectiva

La fecha efectiva de una observación es la rueda de sus inputs. El IRPM sólo publica un valor cuando Capa 1, Capa 2 y Capa 3 están disponibles para esa misma fecha; no usa el último dato conocido de otra rueda ni renormaliza pesos si falta una señal.

Capa 2 requiere sus cinco señales (GD30D, AL30D, GD35D, *law spread* y EMBI). Capa 3 requiere las cuatro acciones del basket. Si falta una señal necesaria, la observación queda en estado **degradado**, su IRPM es `NULL` y el pipeline no la trata como actualización publicable.

La tabla local `iep_composicion` registra por fecha la versión metodológica, estado, fecha efectiva, señales disponibles, pesos de cada capa y motivo de degradación. La auditoría de las seis fechas históricas afectadas está en [`AUDITORIA_COMPLETITUD_20260814.md`](AUDITORIA_COMPLETITUD_20260814.md).

## Qué evidencia existe

### Sensibilidad de pesos

Se evaluaron 14 combinaciones de pesos externos. La fecha del máximo histórico se mantuvo en todas y la fecha del mínimo en 13 de 14; la magnitud del mínimo varió hasta aproximadamente 5,5 puntos.

Esto demuestra **robustez narrativa dentro de esa grilla**. No demuestra que los pesos 35/40/25 sean óptimos ni valida el significado político del índice.

### IRPM e ICG-UTDT

Con 32 meses de superposición, la correlación contemporánea fue `r=0,367`. La mayor correlación observada fue con el ICG adelantando un mes al IRPM (`r=0,384`); IRPM adelantando un mes obtuvo `r=0,324`. Los tests de Granger no encontraron evidencia de que el IRPM agregue poder predictivo sobre el ICG en lags de uno a tres meses.

La hipótesis original de que el mercado adelantaba sistemáticamente a la opinión pública **no fue confirmada**. La muestra es corta y el análisis deberá repetirse con un protocolo congelado y más observaciones.

### Análisis de eventos

El análisis inicial asoció 14 de las 20 mayores ventanas de movimiento con eventos políticos cercanos. Sin embargo, varias observaciones pertenecen al mismo episodio y las ventanas son amplias y solapadas. Por ese motivo, el resultado se considera **exploratorio**, no una validación aprobada.

La próxima versión utilizará episodios no solapados, eventos definidos ex ante, benchmark nulo, intervalos de confianza y evaluación fuera de muestra.

## Limitaciones principales

- **Política, macro local y contexto global no están identificados por separado.** Los mismos activos reaccionan a tasas internacionales, liquidez, inflación, reservas, política fiscal y eventos electorales.
- **El baseline y la escala son convencionales.** Cambian la narrativa visual, no el orden relativo de los movimientos.
- **Los z-scores son relativos a una ventana móvil.** Un valor de capa positivo significa estar por encima de su media reciente orientada, no necesariamente por encima del 11/12/2023.
- **El mercado observado es parcial.** Refleja participantes del mercado de capitales, no a la sociedad argentina.
- **La Capa 3 usa volatilidad realizada.** No sustituye a datos de opciones ni elimina shocks sectoriales o globales.
- **Las explicaciones de hitos son editoriales.** La proximidad temporal no prueba causalidad.
- **La estructura de plazos electoral directa aún es limitada.** El ROFEX post-elección se incorporará sólo después de acumular historia suficiente y superar validaciones.

## Fuentes

| Señal | Fuente | Frecuencia objetivo |
|---|---|---|
| MEP y bonos GD30/AL30/GD35 | PPI API | Diaria |
| Futuros de dólar | PPI, SSPM y boletines BCR | Diaria |
| EMBI Argentina | dolarito.ar | Diaria |
| Acciones YPFD/GGAL/PAMP/TECO2 | PPI API | Diaria |
| VIX | Yahoo Finance | Diaria |
| ICG/ICC | UTDT | Mensual |

## Gobernanza

Los niveles de evidencia, protocolos de validación, política de completitud y gates de release se definen en [`MARCO_VALIDACION_Y_GOBERNANZA.md`](MARCO_VALIDACION_Y_GOBERNANZA.md).

Toda modificación que cambie la serie histórica requiere una nueva versión metodológica, tests antes/después y changelog. Los resultados negativos se conservan y publican.

---

*Metodología sujeta a revisión. Para consultas: Mariano Laxague · mariano.laxague@gmail.com · https://elindice.substack.com*
