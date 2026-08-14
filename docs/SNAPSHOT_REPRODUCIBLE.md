# Snapshot reproducible

Un snapshot inmoviliza los datos necesarios para auditar una release del IRPM
sin consultar la base de datos viva. Cada archivo se registra en
`manifest.json` con su hash SHA-256 y, para las tablas, su cantidad de filas.

## Release inicial

`data/snapshots/2026-08-14-v0.1-experimental/` corresponde al corte
`v0.1-experimental-20260814`. Contiene:

- `raw_prices.csv`: series crudas disponibles al corte;
- `iep_diario.csv` y `iep_composicion.csv`: índice, señales, pesos y estado de
  completitud por fecha;
- los dos registros de ajustes extraordinarios;
- los insumos locales de UTDT y REM en `inputs/`;
- `manifest.json`: versión, referencia de código, fecha de creación, filas y
  hashes.

No convierte el snapshot en validación metodológica ni en una publicación
oficial: conserva el estado experimental y las restricciones de completitud
que tuviera el corte.

## Crear un nuevo snapshot

Desde la raíz del repositorio, con la DB ya actualizada:

```powershell
python src/pipeline/create_snapshot.py `
  --output data/snapshots/AAAA-MM-DD-etiqueta `
  --code-ref etiqueta-o-commit
```

El destino no puede existir; así se evita sobrescribir una release. Antes de
versionarlo, revisar el manifest y ejecutar la suite de pruebas.

## Verificar y restaurar

```powershell
python src/pipeline/restore_snapshot.py `
  --snapshot data/snapshots/AAAA-MM-DD-etiqueta `
  --db data/iep_restaurada.db
```

El restaurador verifica primero todos los hashes y aborta si alguno difiere.
Luego recrea una DB SQLite independiente con las tablas del snapshot. Para una
verificación de presentación se puede apuntar el dashboard a esa DB:

```powershell
$env:IRPM_DB_PATH = (Resolve-Path data/iep_restaurada.db)
python src/dashboard/generate_dashboard.py
```

Los CSV de `inputs/` se preservan para reconstruir el contexto de las señales;
no se copian de vuelta al directorio activo automáticamente.
