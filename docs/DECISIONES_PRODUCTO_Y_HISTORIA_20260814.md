# Decisiones de producto e historia — 14 de agosto de 2026

Este registro conserva decisiones de alcance del dashboard y de comparabilidad histórica. Su objetivo es impedir que una simplificación visual se interprete como un cambio silencioso de cálculo.

## 1. Serie pública única

**Decisión:** el gráfico principal, la tabla accesible y el CSV público muestran solo el **IRPM diario publicado**.

**Motivo:** la serie suavizada deja observaciones recientes sin valor por su ventana centrada; por eso no puede reemplazar al dato vigente sin que el gráfico y el indicador principal diverjan. El ajuste VIX se conserva, si corresponde, como diagnóstico interno y no como modo alternativo de lectura pública.

**Consecuencia:** no hay controles para alternar serie cruda, suavizada o ajuste VIX. El cálculo, sus capas y la fecha del último valor siguen siendo los de `IRPM-v0.1`.

## 2. Comparación entre gobiernos retirada

**Decisión:** se retira del dashboard la visualización que comparaba Macri, Alberto y Milei con un índice inverso del EMBI rebased a 100 al inicio de cada gestión.

**Por qué no era IRPM:**

- Usaba un único proxy (EMBI), mientras que el IRPM combina tres capas.
- Reiniciaba cada gestión en 100; por tanto, un valor 400 significaba que el EMBI se había reducido a una cuarta parte del nivel inicial de esa gestión, no que el IRPM hubiera llegado a 400 ni que hubiera mejorado 300%.
- La etiqueta “confianza por gestión” exageraba la interpretación: no identificaba causalidad ni era comparable con el IRPM actual de 105,1.

**Regla:** no se vuelve a publicar una comparación entre gobiernos con proxies rebased. Una comparación solo puede usar un IRPM recalculado con la misma especificación, sin reinicios por gestión y con la misma escala en todo el período.

## 3. Cobertura comparable actual

El primer IRPM completo disponible es el **20 de abril de 2022**. Con datos al 11 de agosto de 2026, la cobertura comparable observada es:

| Segmento | Fechas | Observaciones | Promedio | Rango |
|---|---|---:|---:|---:|
| Final de Alberto | 20-abr-2022 a 7-dic-2023 | 397 | 100,8 | 90,8 a 112,1 |
| Milei | 11-dic-2023 a 11-ago-2026 | 641 | 105,8 | 75,7 a 115,1 |

**Decisión de interpretación:** tampoco se muestra esa comparación parcial. El tramo final de Alberto ya incorporaba expectativas sobre el cambio de gobierno y no representa limpiamente el desempeño de una gestión completa.

## 4. Cómo leer el nivel vigente

- El baseline 100 se fija el 11 de diciembre de 2023.
- Un IRPM de 105,1 significa que el compuesto de señales está 5,1 puntos por encima de esa referencia convencional.
- No significa 5,1%, 105,1% ni una probabilidad.
- Un movimiento diario o mensual describe un cambio en las señales financieras incluidas; atribuirlo a un hecho político requiere evidencia externa y se presenta como lectura editorial.

## 5. Scroll y navegación

**Decisión:** el dashboard usa scroll nativo de la ventana. Se retiró el esquema de secciones con altura fija, scroll interno y *scroll snap* obligatorio.

**Motivo:** un contenedor interno puede capturar la rueda o el gesto táctil y dejar al usuario sin una forma clara de avanzar. Los enlaces de navegación continúan llevando a secciones mediante anclas.

## 6. Próximo umbral para historia por gestiones

La única vía aceptable para esa comparación es `IRPM-backcast-v1`, especificado en [`CONTRATO_BACKCAST_HISTORICO.md`](CONTRATO_BACKCAST_HISTORICO.md):

1. datos desde diciembre de 2014 para alimentar las ventanas de 252 ruedas;
2. equivalencias explícitas para dólar financiero, futuros, bonos previos a 2020 y acciones;
3. tratamiento versionado de canjes, pagos, splits y cambios de ticker;
4. reproducción del solapamiento 2022–hoy antes de cualquier publicación;
5. cobertura y transiciones visibles junto al gráfico.

Hasta completar esas condiciones, el producto comunica `IRPM-v0.1` como serie observada desde abril de 2022 y no compara gobiernos completos.
