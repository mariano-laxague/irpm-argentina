# Plan de Acción Vigente — IRPM

**Versión:** 2.0
**Fecha:** 13/08/2026
**Estado:** programa de hardening metodológico, técnico y de producto
**Fuente de verdad:** este documento reemplaza a `PLAN.md` como hoja de ruta operativa.

---

## 1. Resultado buscado

Construir una release `v0.1-experimental` del IRPM que sea:

1. **Conceptualmente honesta:** un índice estandarizado de condiciones de mercado, no una probabilidad calibrada.
2. **Metodológicamente auditable:** cada afirmación pública debe corresponder a evidencia identificable.
3. **Consistente en datos:** ninguna observación puede cambiar silenciosamente de composición.
4. **Reproducible:** código, dependencias, configuración de ejemplo, metodología y snapshot de datos deben pertenecer a la misma release.
5. **Operativamente observable:** un fallo del scheduler o del deploy debe generar una alerta fuera del propio pipeline.
6. **Usable y accesible:** la experiencia debe funcionar en desktop, mobile, teclado y lectores de pantalla en sus tareas principales.

Hasta cerrar los gates de este plan, el IRPM debe presentarse como **producto experimental de research**, no como indicador validado para decisiones de inversión o como estimación probabilística electoral.

---

## 2. Estado oficial de partida

| Área | Estado al 13/08/2026 | Consecuencia |
|---|---|---|
| Pipeline y serie | Operativos; 1.054 valores diarios y 44.527 observaciones crudas en la DB revisada | Base técnica valiosa, todavía sin suite automatizada de regresión |
| Constructo | Compuesto de z-scores con baseline y escala convencionales | No puede llamarse “probabilidad implícita” |
| Eventos | 14/20 ventanas asociadas a eventos, pero con observaciones solapadas y episodios repetidos | Resultado exploratorio; se retira el estado de “validación aprobada” |
| IRPM vs. ICG | Hipótesis de leading indicator no confirmada con N=32 | Debe comunicarse como resultado negativo/inconcluso |
| Sensibilidad | Narrativa estable en 14 combinaciones de pesos externos | Prueba de robustez acotada, no validación del constructo ni elección óptima de pesos |
| Completitud diaria | Capa 2 puede renormalizarse si falta EMBI; ocurrió en 6 fechas de la serie revisada | La composición no es estrictamente fija y debe corregirse o publicarse explícitamente |
| Publicación | Web pública y rediseño local no corresponden al mismo estado; cambios centrales sin commit | No existe todavía una release trazable |
| Monitoreo | Healthcheck interno disponible; sin watchdog externo del scheduler/deploy | Una caída total del scheduler aún puede pasar inadvertida |
| UX y accesibilidad | Rediseño local sin breakpoints ni semántica suficiente; validación visual incompleta | No aprobado para mobile ni accesibilidad |

---

## 3. Principios no negociables

- **Separar dato, indicador e interpretación editorial.** Un movimiento observado no demuestra por sí solo una causa política.
- **No cambiar la hipótesis después de mirar el resultado.** Los criterios se registran antes de ejecutar cada validación.
- **No usar “DONE” sin evidencia de aceptación.** Un archivo existente no equivale a una capacidad publicada y verificada.
- **No publicar composición silenciosamente variable.** Cada valor debe declarar inputs, fecha efectiva y versión metodológica.
- **No desplegar artefactos generados por código sin versionar.** Dashboard, código y metodología deben compartir commit/release.
- **Los resultados negativos se conservan.** No se reinterpretan como confirmaciones ex post.
- **Distribución después de confianza.** Newsletter, LinkedIn, informes pagos y co-branding quedan subordinados a los gates P0–P3.

---

## 4. Frentes de trabajo

### P0 — Verdad pública y control de versión

**Objetivo:** detener la divergencia entre lo que el proyecto hace y lo que dice.

| ID | Acción | Entregable | Criterio de aceptación | Estado |
|---|---|---|---|---|
| P0.1 | Sustituir “probabilidad implícita” por el framing experimental acordado | README, metodología, contexto y dashboard alineados | Búsqueda global sin usos no históricos de la formulación retirada | ✅ Local completado 13/08; deploy en P5.2 |
| P0.2 | Designar fuentes documentales | `PLAN_ACCION.md`, `CONTEXTO.md`, `docs/MARCO_VALIDACION_Y_GOBERNANZA.md` | Cada documento declara su función y los históricos tienen banner | ✅ Completado 13/08 |
| P0.3 | Congelar el estado actual antes de nuevos cambios | Commit de baseline técnico + tag interno | Worktree limpio y tag identificable | ✅ Completado 14/08 — tag `baseline-20260814` |
| P0.4 | Publicar versión y commit de metodología en el dashboard | Metadatos visibles o descargables | El usuario puede identificar fórmula, fecha y commit que generaron el valor | ⬜ Pendiente |

### P1 — Constructo, escala y lenguaje

**Objetivo:** hacer que cada etiqueta describa lo que realmente calcula el código.

| ID | Acción | Entregable | Criterio de aceptación | Estado |
|---|---|---|---|---|
| P1.1 | Adoptar definición oficial | “Índice experimental que sintetiza condiciones de mercado a partir de señales financieras sensibles al escenario político y económico argentino” | Definición idéntica en superficies vigentes | ✅ Completado 13/08 |
| P1.2 | Revisar nombre y dirección del índice | Memo de decisión: “riesgo” vs. valores altos positivos | No existe ambigüedad sobre si subir significa más o menos riesgo | ⬜ Pendiente |
| P1.3 | Corregir etiquetas de capas | Dashboard | Los z-scores rolling se describen contra su media móvil, no contra dic-2023 | ✅ Completado 13/08 |
| P1.4 | Revisar umbrales 90/110 | Especificación o retiro de zonas | Cada umbral tiene justificación empírica o se declara heurístico | ✅ Declarados heurísticos 13/08 |
| P1.5 | Etiquetar inferencias editoriales | Hitos con fuentes y grado de certeza | Se diferencia “dato”, “lectura editorial” e “hipótesis” | 🟡 Etiqueta y copy listos; fuentes pendientes |

### P2 — Integridad de datos y composición

**Objetivo:** garantizar que dos valores del IRPM sean comparables y trazables.

| ID | Acción | Entregable | Criterio de aceptación | Estado |
|---|---|---|---|---|
| P2.1 | Definir política de fecha efectiva | Decisión implementada y documentada | El IRPM no usa componentes de fechas distintas sin indicarlo | ✅ Completado 14/08 — misma rueda o estado degradado |
| P2.2 | Eliminar renormalización silenciosa | Gate de completitud o estado degradado explícito | Test que demuestra que falta de EMBI no cambia pesos sin flag | ✅ Completado 14/08 — 5 señales obligatorias en Capa 2 |
| P2.3 | Registrar composición por observación | Campos/tabla de metadata | Cada fecha expone versión, componentes disponibles, fechas y pesos efectivos | ✅ Completado 14/08 — tabla `iep_composicion` |
| P2.4 | Auditar seis fechas sin EMBI | Informe de impacto | Serie corregida o excepción documentada con delta cuantificado | ✅ Completado 14/08 — `docs/AUDITORIA_COMPLETITUD_20260814.md` |
| P2.5 | Versionar ajustes extraordinarios | Registro de splits, pagos y backfills | Toda corrección histórica tiene razón, fecha y test de regresión | ⬜ Pendiente |

### P3 — Validación metodológica

**Objetivo:** reemplazar validaciones narrativas por protocolos falsables y reproducibles.

| ID | Acción | Entregable | Criterio de aceptación | Estado |
|---|---|---|---|---|
| P3.1 | Rediseñar análisis de eventos | Protocolo + script v2 | Episodios no solapados, eventos ex ante, signos fijos, benchmark nulo y resultado reproducible | ⬜ Pendiente |
| P3.2 | Registrar formalmente el resultado ICG | Nota metodológica | Dice “leading no confirmado”, N, potencia y fecha de próximo test | ✅ Completado 13/08 |
| P3.3 | Ampliar sensibilidad | Matriz de especificaciones | Incluye ventanas, baseline, escala, componentes, missingness y ajuste VIX; no sólo pesos externos | ⬜ Pendiente |
| P3.4 | Evaluar redundancia informativa | IRPM vs. EMBI/bonos/MEP con ablaciones | Se cuantifica qué información incremental aporta cada capa | ⬜ Pendiente |
| P3.5 | Evaluar identificación | Modelo explícito o límite definitivo | Se demuestra control parcial de factores macro/globales o se limita el claim a condiciones de mercado | ⬜ Pendiente |
| P3.6 | Crear holdout temporal | Protocolo out-of-sample | Decisiones congeladas antes del período de evaluación | ⬜ Pendiente |

**Regla:** sensibilidad, face validity y correlación contemporánea son evidencia útil, pero ninguna se rotula como “validación del constructo”.

### P4 — Reproducibilidad e ingeniería

**Objetivo:** que otra persona pueda auditar el cálculo sin reconstruir el entorno por intuición.

| ID | Acción | Entregable | Criterio de aceptación | Estado |
|---|---|---|---|---|
| P4.1 | Completar y fijar dependencias | requirements/lock | Incluye scipy y statsmodels; instalación limpia verificada | ⬜ Pendiente |
| P4.2 | Crear configuración de ejemplo | `config.ini.example` | Clone nuevo puede entender todas las claves sin exponer secretos | ✅ Completado 14/08 |
| P4.3 | Añadir tests | Suite de cálculo, datos y regresión | Fórmulas, signos, missingness, splits, pagos y baseline cubiertos | ✅ Completado 14/08 — 10 pruebas deterministas sin DB ni APIs |
| P4.4 | Añadir CI | Workflow read-only | Tests y generación del dashboard pasan en cada commit | ⬜ Pendiente |
| P4.5 | Modularizar dashboard | Templates/CSS/JS separados o arquitectura equivalente | Se reduce el generador monolítico sin cambiar output | ⬜ Pendiente |
| P4.6 | Crear snapshot reproducible | CSV + manifest + hashes | Una release puede recalcularse sin depender del DB vivo | ⬜ Pendiente |

### P5 — Operación y releases

**Objetivo:** detectar fallos incluso cuando el pipeline no llega a ejecutarse.

| ID | Acción | Entregable | Criterio de aceptación | Estado |
|---|---|---|---|---|
| P5.1 | Crear watchdog externo | Monitor independiente | Alerta si no hay run o publicación antes de la hora límite | ⬜ Pendiente |
| P5.2 | Verificar deploy público | Probe posterior al push | Fecha/commit visible en web coincide con build local | ⬜ Pendiente |
| P5.3 | No silenciar fallos de deploy | Estado separado pipeline/deploy | El cálculo puede quedar OK, pero publicación figura FAILED y alerta | ⬜ Pendiente |
| P5.4 | Formalizar release | Checklist y changelog | Release incluye código, docs, datos, tests y evidencia UX | ⬜ Pendiente |
| P5.5 | Ensayar recuperación | Restore desde backup | Simulación documentada recupera DB y dashboard | ⬜ Pendiente |

### P6 — Producto, responsive y accesibilidad

**Objetivo:** conservar la utilidad analítica en una experiencia comprensible y robusta.

| ID | Acción | Entregable | Criterio de aceptación | Estado |
|---|---|---|---|---|
| P6.1 | Definir journeys prioritarios | Mapa de tareas | Lectura rápida, explicación del movimiento y auditoría metodológica cubiertas | ⬜ Pendiente |
| P6.2 | Recuperar controles analíticos necesarios | Dashboard | Período, series y contexto VIX accesibles sin saturar la portada | ⬜ Pendiente |
| P6.3 | Implementar responsive | CSS y pruebas | 360, 390, 768, 1280 y 1440 px sin recortes ni scroll bloqueado | ⬜ Pendiente |
| P6.4 | Implementar semántica y teclado | HTML/JS | `h1`, `main`, labels, ARIA, foco y range operable por teclado | ⬜ Pendiente |
| P6.5 | Añadir alternativa a canvas | Tabla/resumen descargable | Datos y conclusiones principales accesibles sin percepción visual del gráfico | ⬜ Pendiente |
| P6.6 | Ejecutar QA visual | Capturas desktop/mobile | Todos los journeys y estados clave inspeccionados antes de publicar | ⬜ Pendiente |

### P7 — Distribución responsable

**Objetivo:** reactivar crecimiento sólo cuando el producto pueda sostener escrutinio público.

| ID | Acción | Gate previo | Estado |
|---|---|---|---|
| P7.1 | Newsletter de relanzamiento metodológico | P0–P5 cerrados | ⏸ Bloqueado |
| P7.2 | Posts de metodología | P3 cerrado y copy auditado | ⏸ Bloqueado |
| P7.3 | Informe inaugural pago | Release estable + disclaimer de uso | ⏸ Bloqueado |
| P7.4 | Conversación con broker | Trazabilidad, watchdog y release estable | ⏸ Bloqueado |

---

## 5. Secuencia de ejecución

### Fase A — Cierre documental y freeze

1. Alinear todos los documentos vigentes.
2. Marcar históricos y contradicciones conocidas.
3. Inventariar cambios sin commit.
4. Crear commit de baseline y tag interno.

### Fase B — Integridad antes de nueva metodología

1. Política de completitud y fecha efectiva.
2. Metadata por observación.
3. Tests de regresión del cálculo actual.
4. Recalcular y comparar la serie.

### Fase C — Validación v2

1. Preregistrar eventos y criterios.
2. Implementar de-clustering y benchmark nulo.
3. Ejecutar ablaciones y sensibilidad ampliada.
4. Publicar resultados, incluidos los negativos.

### Fase D — Release candidate de producto

1. Corregir lenguaje y labels del dashboard.
2. Implementar responsive y accesibilidad.
3. Conectar versión metodológica y manifest.
4. Ejecutar QA visual y operativo.

### Fase E — Publicación y distribución

1. Tag `v0.1-experimental`.
2. Deploy verificado.
3. Monitoreo externo activo.
4. Comunicación pública con alcance y límites explícitos.

---

## 6. Gates de release

Una release pública nueva sólo puede salir si todos estos checks están en verde:

- [ ] Terminología alineada y sin claims probabilísticos no calibrados.
- [ ] Composición diaria completa o degradación explícita.
- [ ] Suite automatizada pasa en entorno limpio.
- [ ] Dependencias y configuración de ejemplo disponibles.
- [ ] Código, metodología, dashboard y snapshot comparten versión.
- [ ] Resultados de validación reproducibles y correctamente rotulados.
- [ ] Watchdog del scheduler y verificación de deploy operativos.
- [ ] QA desktop/mobile completado con capturas inspeccionadas.
- [ ] Navegación por teclado y alternativa textual a gráficos verificadas.
- [ ] Changelog y limitaciones de la release publicados.

---

## 7. Protocolo de sesión

Cada sesión debe:

1. Elegir un único ID de este plan.
2. Registrar antes de trabajar el criterio de aceptación.
3. Implementar y verificar con evidencia proporcional al riesgo.
4. Actualizar el estado del ID y `tasks/lessons.md` si aparece una regla durable.
5. No abrir tareas de distribución mientras exista un gate bloqueante.

**Próximo trabajo recomendado:** P2.5 — versionar ajustes extraordinarios de splits, pagos y backfills con registro durable y pruebas de regresión.
