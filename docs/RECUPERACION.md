# Ensayo de recuperación

La restauración nunca apunta a `data/iep.db`. Copiar primero un backup a un
destino nuevo, validar SQLite y recién entonces generar y revisar el dashboard.

```powershell
python src/pipeline/restore_backup.py `
  --backup data/backups/iep_AAAAMMDD.db `
  --target data/iep_recuperada.db

$env:IRPM_DB_PATH = (Resolve-Path data/iep_recuperada.db)
python src/dashboard/generate_dashboard.py
```

El comando rechaza un destino existente y elimina una copia incompleta si la
validación `PRAGMA integrity_check` falla. La DB activa no se sobrescribe.

Para una release, registrar en el changelog el backup elegido, el resultado de
integridad y el hash del dashboard regenerado. El snapshot versionado es la
alternativa preferida para reproducibilidad de datos; el backup sirve para
recuperación operativa rápida.
