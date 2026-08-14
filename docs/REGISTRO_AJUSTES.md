# Registro de ajustes extraordinarios

Cada ajuste que puede cambiar la serie histórica se registra en SQLite antes de cualquier cálculo. La tabla `iep_ajustes_extraordinarios` contiene el identificador, tipo, activos, fecha efectiva, fecha de implementación, regla, razón, fuente y prueba de regresión asociada. `iep_ajustes_aplicados` conserva cada aplicación concreta de los pagos de bonos sin modificar `raw_prices`.

| ID | Tipo | Fecha efectiva | Regla | Prueba asociada |
|---|---|---:|---|---|
| `bonos_pagos_v1` | Pago/amortización | 2022-01-01 | Forward-fill en ventana pre-pago si caída supera 2,5% | Pago mecánico no muta el input |
| `ypfd_split_20260803` | Split accionario | 2026-08-03 | Divide precios YPFD pre-split por 10 | Split mantiene retornos continuos |
| `backfill_ppi_20260724_20260804` | Backfill de datos | 2026-07-24 | Ocho ruedas PPI repuestas hasta 2026-08-04 | Metadata de composición por fecha |

Para incorporar un ajuste nuevo se deben cumplir tres condiciones antes de recalcular y publicar:

1. Añadir un registro en `AJUSTES_REGISTRADOS` de `src/pipeline/ajustes.py` con razón, fuente y prueba asociada.
2. Implementar una prueba determinista que falle sin el ajuste.
3. Ejecutar el recálculo y revisar el impacto en la serie antes de generar el dashboard.

Los datos crudos siguen siendo inmutables: el registro describe transformaciones de cálculo, no sobrescribe precios descargados.
