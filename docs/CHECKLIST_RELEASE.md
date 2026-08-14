# Checklist de release

Una release del IRPM debe ser reproducible, verificable y explícita sobre su
nivel de evidencia. Marcar cada punto con evidencia enlazable; no usar este
checklist para convertir el estado experimental en validación metodológica.

## Antes de etiquetar

- [ ] Árbol de trabajo limpio y commit de release identificado.
- [ ] `requirements.lock` instala y `python -m pip check` pasa.
- [ ] Suite determinista completa pasa en local y CI.
- [ ] Snapshot versionado con manifest y hashes verificados.
- [ ] Restauración del snapshot genera una DB y dashboard válidos.
- [ ] `docs/index.html` y `docs/deploy_manifest.json` se generaron en el mismo build.
- [ ] El probe público confirma el hash del manifest tras la propagación de Pages.
- [ ] `logs/deploy_status.json` registra `OK` para la publicación.
- [ ] Watchdog separado registrado y webhook de alerta probado.
- [ ] Capturas desktop y móvil revisadas, con hallazgos de accesibilidad resueltos o documentados.
- [ ] Metodología, límites y estado experimental revisados frente al dashboard.

## Publicación

1. Crear el tag anotado `vX.Y.Z` sobre el commit validado.
2. Añadir una entrada fechada a `CHANGELOG.md` con datos, cambios, riesgos y
   evidencia de los checks anteriores.
3. Publicar y ejecutar el probe hasta obtener `OK`; no cerrar una release con
   `FAILED`, `WARNING` o un manifest ausente.

## Recuperación y reversión

- Conservar el tag y el directorio de snapshot de cada release.
- Ante una regresión pública, restaurar el snapshot en una DB temporal,
  regenerar el dashboard y comparar el manifest antes de republicar.
- Registrar la causa y la acción correctiva en el changelog; no reescribir el
  snapshot ni su manifest.
