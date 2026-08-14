# IRPM — Índice de Riesgo Político de Mercado Argentina

> **Estado: experimental.** El IRPM es un índice experimental que sintetiza condiciones de mercado a partir de señales financieras sensibles al escenario político y económico argentino. No es una probabilidad electoral calibrada ni una recomendación de inversión.

**Dashboard:** https://marianolaxague-crypto.github.io/irpm-argentina/

**Newsletter:** [El Índice en Substack](https://elindice.substack.com)

---

## Qué mide

El IRPM sintetiza diariamente el comportamiento relativo de activos argentinos sensibles a cambios en credibilidad fiscal, expectativas cambiarias, riesgo soberano y volatilidad local.

El valor 100 corresponde a un baseline convencional fijado el 11 de diciembre de 2023. Un valor superior indica condiciones de mercado más favorables que en esa fecha; uno inferior, condiciones menos favorables. La escala expresa distancia estandarizada respecto del baseline: **no representa un porcentaje ni una probabilidad**.

La lectura de esas variaciones en clave política es editorial y debe considerar simultáneamente factores macroeconómicos locales y globales.

## Componentes actuales

| Capa | Señales | Peso externo |
|---|---|---:|
| Capa 1 — Cambiaria | MEP + ROFEX 1M equivalente | 35% |
| Capa 2 — Deuda soberana | GD30/AL30/GD35 + law spread + EMBI | 40% |
| Capa 3 — Volatilidad accionaria | Semi-vol YPFD/GGAL/PAMP/TECO2 | 25% |

El proyecto también calcula una variante ajustada por VIX. Esa serie es un control analítico experimental, no una separación completa entre riesgo global y riesgo argentino.

## Qué no puede afirmarse todavía

- No estima la probabilidad de continuidad, reelección o default.
- No identifica causalmente qué parte de un movimiento es política.
- No demostró anticipar encuestas: la hipótesis de leading indicator del ICG-UTDT no fue confirmada con la muestra disponible.
- El análisis de eventos existente es exploratorio; sus ventanas solapadas impiden tratar el resultado 14/20 como veinte pruebas independientes.
- La sensibilidad de pesos muestra estabilidad narrativa dentro de una grilla acotada, pero no valida el constructo ni demuestra que los pesos sean óptimos.

## Estado de desarrollo

El pipeline local incluye recolección, cálculo, backups, sanity checks, generación del dashboard y healthcheck. Permanecen abiertos los siguientes gates antes de una release trazable:

- política estricta de completitud por componente;
- metadata de composición y versión por observación;
- tests automatizados y CI;
- dependencias reproducibles y configuración de ejemplo;
- watchdog externo del scheduler y verificación del deploy;
- validación metodológica v2;
- responsive, accesibilidad y QA visual.

La automatización está diseñada para ejecutarse en días hábiles mediante Windows Task Scheduler. La fecha visible en el dashboard debe interpretarse como la última publicación exitosa, no como garantía de que el scheduler esté operativo.

## Fuentes

- **Bonos y acciones:** PPI API.
- **EMBI Argentina:** dolarito.ar API.
- **Futuros ROFEX:** PPI API + SSPM datos.gob.ar + boletines BCR.
- **VIX:** Yahoo Finance mediante `yfinance`.
- **ICG/ICC UTDT:** Universidad Torcuato Di Tella.

## Documentación

- [`docs/metodologia_publica.md`](docs/metodologia_publica.md): explicación pública vigente.
- [`docs/MARCO_VALIDACION_Y_GOBERNANZA.md`](docs/MARCO_VALIDACION_Y_GOBERNANZA.md): niveles de evidencia, protocolos y releases.
- [`docs/SNAPSHOT_REPRODUCIBLE.md`](docs/SNAPSHOT_REPRODUCIBLE.md): corte de datos, hashes y restauración independiente de una release.
- [`docs/WATCHDOG_OPERATIVO.md`](docs/WATCHDOG_OPERATIVO.md): monitor independiente del scheduler y configuración de alertas.
- [`docs/VERIFICACION_DEPLOY.md`](docs/VERIFICACION_DEPLOY.md): manifest y probe del artefacto servido por GitHub Pages.
- [`docs/CHECKLIST_RELEASE.md`](docs/CHECKLIST_RELEASE.md): condiciones mínimas para etiquetar y publicar una release.
- [`docs/RECUPERACION.md`](docs/RECUPERACION.md): restauración segura y ensayo desde un backup SQLite.
- [`docs/JOURNEYS_PRODUCTO.md`](docs/JOURNEYS_PRODUCTO.md): recorridos prioritarios para lectura, análisis y auditoría.
- [`docs/QA_RESPONSIVE_20260814.md`](docs/QA_RESPONSIVE_20260814.md): evidencia y límites de la revisión inicial de breakpoints.
- [`docs/QA_VISUAL_20260814.md`](docs/QA_VISUAL_20260814.md): recorridos inspeccionados y límites del QA visual local.
- [`CONTEXTO.md`](CONTEXTO.md): arquitectura técnica, decisiones y log de desarrollo.
- [`PLAN_ACCION.md`](PLAN_ACCION.md): hoja de ruta operativa vigente.

`PLAN.md` se conserva localmente como registro histórico y no es fuente de prioridades actuales.

## Configuración local

1. Copiá `config.ini.example` como `config.ini`.
2. Configurá `paths.cred_ppi` con la ruta absoluta al archivo de credenciales de PPI. Ese archivo y `config.ini` están excluidos de Git.
3. Usá Python 3.12 (ver `.python-version`) e instalá el entorno bloqueado: `python -m pip install -r requirements.lock`.
4. Ejecutá `python -m pip check` y luego `python src/pipeline/update_daily.py`.

Las rutas de base de datos y backups son relativas a la raíz del repositorio. El pipeline requiere una base existente para una corrida diaria. Cada release trazable debe incluir un snapshot versionado; ver [`docs/SNAPSHOT_REPRODUCIBLE.md`](docs/SNAPSHOT_REPRODUCIBLE.md).

## Pruebas

La suite determinista no toca la DB ni requiere credenciales. Desde la raíz del repositorio:

```powershell
python -m unittest discover -s tests -v
```

Cubre pesos, orientación de señales, baseline, faltantes, splits y pagos mecánicos. La política de faltantes exige composición completa o estado degradado explícito.

El workflow de GitHub Actions ejecuta el lock, `pip check`, la suite y una generación del dashboard con datos fixture en cada push y pull request.

El generador conserva datos y composición en `src/dashboard/generate_dashboard.py`; las plantillas estáticas de HTML, CSS y JavaScript viven en `src/dashboard/templates.py`. La refactorización se verificó regenerando un HTML con el mismo SHA-256.

---

*Desarrollado por Mariano Laxague. Publicación personal; no representa la opinión de ninguna institución y no constituye asesoramiento financiero.*
