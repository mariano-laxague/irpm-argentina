# Auditoría de completitud — 14/08/2026

## Alcance

Se auditó la serie calculada antes de la política de composición fija `v0.1-experimental-full-components`. La regla anterior renormalizaba Capa 2 a cuatro señales cuando faltaba EMBI; la regla nueva exige cinco señales y deja la fecha degradada.

## Resultado

Se identificaron seis fechas con Capa 1 y Capa 3 presentes, pero sin EMBI en la misma rueda. Antes contenían un IRPM calculado con pesos alterados; desde la corrección tienen `iep_total = NULL`, estado `degradado` y metadata de componentes por fecha.

| Fecha | IRPM anterior | Componente faltante | Tratamiento actual |
|---|---:|---|---|
| 2022-09-20 | 101,76 | EMBI | Retirado; degradado |
| 2022-09-21 | 101,02 | EMBI | Retirado; degradado |
| 2022-11-18 | 100,53 | EMBI | Retirado; degradado |
| 2023-07-03 | 102,67 | EMBI | Retirado; degradado |
| 2023-07-04 | 102,67 | EMBI | Retirado; degradado |
| 2026-08-12 | 103,64 | EMBI | Retirado; degradado |

La diferencia no se expresa como un nuevo nivel comparable: no existe un valor corregido sin imputar o cambiar los pesos. La corrección consiste precisamente en retirar las seis observaciones ordinarias. La última fecha publicable tras el recálculo es 2026-08-11, con IRPM 105,1.

## Evidencia reproducible

- `src/pipeline/calcular_capa2.py` bloquea Capa 2 con menos de cinco señales.
- `src/pipeline/calcular_iep.py` requiere las tres capas, baseline exacto y registra `iep_composicion`.
- `tests/test_calculations.py` verifica el caso de EMBI faltante y la metadata de degradación.
