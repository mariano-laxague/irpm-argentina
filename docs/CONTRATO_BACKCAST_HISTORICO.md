# Contrato de backcast histórico del IRPM

**Estado:** diseño previo a la adquisición de datos. No producir ni publicar una serie histórica hasta completar este contrato.

## Objetivo

Construir una serie `IRPM-backcast-v1` comparable desde el 1 de diciembre de 2015 hasta hoy. Debe recalcular en cada fecha las tres capas vigentes con reglas previamente fijadas; no debe empalmar índices parciales ni reiniciar cada gestión en 100.

La serie actual se mantiene sin cambios como `IRPM-v0.1`, con cobertura completa observada desde el 20 de abril de 2022.

## Regla de comparabilidad

Un valor histórico solo se publica cuando las tres capas tienen los inputs obligatorios de la misma rueda y se calculan con la especificación versionada. Si falta una capa, el valor es `NULL` y la fecha se marca como no publicable.

Cada z-score usa 252 ruedas de historia previa y al menos 63 observaciones. Por eso, para publicar desde diciembre de 2015 hay que obtener datos desde, como mínimo, diciembre de 2014.

## Cobertura actual

| Input | Cobertura en la base actual | Estado para 2015–2022 |
|---|---|---|
| EMBI | 1998–hoy | Disponible; se conserva como una señal, no como sustituto del índice. |
| ROFEX 1M equivalente | 2009–hoy | Requiere auditoría de continuidad entre fuentes y contratos. |
| MEP calculado con AL30/AL30D | 2022–hoy | Faltante; AL30 no existía antes de la reestructuración. |
| GD30D, AL30D, GD35D y law spread | 2022–hoy | Faltante; se necesitan equivalentes históricos explícitos. |
| YPFD, GGAL, PAMP, TECO2 | 2022–hoy | Faltan cierres ajustados y revisión de acciones corporativas. |
| VIX | 2021–hoy | Faltante si se mantiene el ajuste global auxiliar. |

## Contratos por capa

### 1. Mercado cambiario

- Definir una única serie de dólar financiero para todo el período. No se admite empalmar MEP, contado con liquidación y dólar blue sin una regla documentada.
- Construir el forward equivalente a un mes a partir del contrato DLR más cercano y la cantidad exacta de meses al vencimiento.
- Guardar por rueda: instrumento original, vencimiento, fuente, precio, regla de conversión y versión.
- Si no existe simultáneamente el spot financiero y el forward, la capa no se publica para esa rueda.

### 2. Deuda soberana

- Mantener EMBI como señal independiente y conservar su unidad en puntos básicos.
- Definir una canasta de bonos por período y una regla de transición previa a cada canje, default o nueva emisión. La regla debe fijarse antes de calcular resultados.
- Los instrumentos anteriores a 2020 no se tratan como si fueran GD30 o AL30: se documenta el instrumento equivalente, jurisdicción, moneda, precio limpio/sucio y evento de canje.
- El *law spread* se calcula solo cuando existan dos bonos comparables del mismo soberano y vencimiento aproximado bajo leyes distintas. Si no existe, la fecha queda no publicable; no se rellena con otro spread.
- Registrar cupones, amortizaciones, defaults y canjes en el registro de ajustes extraordinarios.

### 3. Volatilidad accionaria

- Usar cierres ajustados por splits y dividendos según una misma política de proveedor para YPFD, GGAL, PAMP y TECO2.
- Registrar cambios de ticker, ADR/local y acciones corporativas. Un activo que no cotice en una rueda no se reemplaza silenciosamente por otro.
- La semi-volatilidad se recalcula con la ventana vigente de 20 ruedas y luego se estandariza con 252 ruedas.

### 4. Ajuste global auxiliar

- El IRPM público usa la serie principal sin alternar modos visuales. Si se conserva el ajuste VIX para diagnóstico interno, completar VIX desde diciembre de 2014 y etiquetarlo siempre como auxiliar.
- Nunca sustituye la serie principal ni se mezcla con ella en un gráfico de comparación de gestiones.

## Fuente y trazabilidad mínima

Cada fila histórica debe conservar: `activo`, `fecha`, `valor`, `fuente`, identificador del instrumento, moneda, tipo de precio, versión de transformación y hash del archivo de origen cuando aplique.

Antes de incorporar una fuente se debe registrar en una tabla de procedencia: URL o archivo original, licencia/condición de uso, fecha de descarga, zona horaria de cierre, frecuencia, faltantes y responsable de revisión.

## Validaciones de aceptación

1. Cobertura diaria de los inputs obligatorios superior al 95% en cada año publicado; el resto se reporta por fecha, no se oculta.
2. Pruebas deterministas para al menos un canje de deuda, un pago de cupón, un split accionario y un rollover de futuro.
3. Comparación de solapamiento 2022–hoy: `IRPM-backcast-v1` debe reproducir la serie vigente, salvo diferencias previamente explicadas y cuantificadas.
4. Sensibilidad: recalcular con ventanas de 126, 252 y 504 ruedas y reportar si se altera la narrativa de los extremos.
5. Revisión manual de al menos cinco episodios: salida del cepo 2015, crisis cambiaria 2018, PASO 2019, reestructuración 2020 y crisis de julio 2022.
6. Publicar una matriz de cobertura por input y un registro de transiciones instrumentales junto a la serie.

## Orden de ejecución

1. Congelar esta especificación como `backcast-v1.0`.
2. Conseguir y almacenar archivos fuente desde diciembre de 2014.
3. Implementar cargadores separados para cambiario, deuda y acciones, sin tocar `IRPM-v0.1`.
4. Ejecutar el backcast en una base nueva y producir un reporte de cobertura antes de generar gráficos.
5. Auditar el solapamiento 2022–hoy.
6. Solo si las validaciones pasan, publicar una vista `IRPM comparable desde 2015`; si no, mantener la cobertura actual.
