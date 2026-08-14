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

### Producto y comparabilidad

- Scroll nativo de página; se retiró el contenedor de slides que podía bloquear la rueda o el gesto táctil.
- Una única serie pública: IRPM diario publicado. Se retiraron modos visuales de suavizado y ajuste VIX.
- Retirada la comparación por gestiones basada en un proxy EMBI rebased; no era IRPM ni comparable con su escala.
- Documentada la cobertura observada desde abril de 2022 y el contrato para un backcast comparable desde 2015.

### Pendiente antes de etiquetar

- Registrar y probar la tarea externa y el webhook.
- Publicar un build con `deploy_manifest.json` y confirmar el probe público.
- Completar evidencia de UX, responsive y accesibilidad.
