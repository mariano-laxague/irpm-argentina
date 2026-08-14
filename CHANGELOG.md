# Changelog

## Próxima release experimental

### Trazabilidad y operación

- Snapshot reproducible `2026-08-14-v0.1-experimental` con CSV, insumos,
  manifest y hashes.
- Restaurador de snapshot y pruebas de integridad.
- Watchdog de heartbeat y estado separado de deploy, ambos preparados para
  notificar por webhook.
- Manifest de GitHub Pages y probe de igualdad por SHA-256.

### Calidad de cálculo

- Composición estricta: no se publica un IRPM con capas faltantes o pesos
  renormalizados silenciosamente.
- Registro persistente de ajustes extraordinarios.
- Lock de dependencias, CI y suite determinista.

### Pendiente antes de etiquetar

- Registrar y probar la tarea externa y el webhook.
- Publicar un build con `deploy_manifest.json` y confirmar el probe público.
- Completar evidencia de UX, responsive y accesibilidad.
