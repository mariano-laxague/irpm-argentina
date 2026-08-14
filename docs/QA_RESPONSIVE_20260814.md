# QA responsive inicial — 14/08/2026

## Evidencia inspeccionada

| Ancho CSS | Superficie inspeccionada | Resultado |
|---:|---|---|
| 360 px | J1 portada y J2 comparativo | Se corrigió navegación cortada; lectura y gráfico sin desborde horizontal visible. |
| 390 px | J1 portada y footer | Se corrigió el recorte de enlaces del footer. |
| 768 px | J1 portada | Navegación completa y dos columnas sin recorte. |
| 1280 px | J1 portada | Jerarquía y contenedor estable. |
| 1440 px | J1 portada | Contenedor máximo y navegación estables. |

Las capturas originales se tomaron con Chrome DevTools sobre el dashboard local
generado el 14/08. El único error de consola observado fue `favicon.ico` 404;
no afecta la ejecución ni la interfaz.

## Correcciones realizadas

- Bajo 700 px, se ocultan enlaces de navegación redundantes y se conservan
  Metodología y Newsletter sin desborde.
- El footer móvil permite envolver los enlaces y reduce su densidad tipográfica.

## Límite de esta verificación

Es una comprobación inicial de breakpoints, no QA visual completo. P6.6 debe
recorrer J1, J2 y J3 en sus estados interactivos, y confirmar controles,
gráficos, foco de teclado y metodología en desktop y móvil.
