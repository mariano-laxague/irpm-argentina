# IRPM — Índice de Riesgo Político de Mercado Argentina

**Dashboard:** https://marianolaxague-crypto.github.io/irpm-argentina/

**Newsletter:** [El Índice en Substack](https://substack.com/@elindice)

---

## Qué mide

El IRPM extrae del mercado de bonos y divisas la **probabilidad implícita de continuidad del programa económico** de Argentina post-2027. Es un índice cuantitativo diario construido sobre posicionamiento real — dinero puesto en juego — no sobre opiniones.

Un IRPM de 100 representa la lectura del mercado el 11 de diciembre de 2023 (inicio de la gestión Milei). Valores superiores a 100 indican que el mercado cree más en la continuidad del programa que ese día; valores inferiores, menos.

## Componentes

| Capa | Señal | Peso |
|------|-------|------|
| Capa 1 — Señales cambiarias | MEP + ROFEX 1M equivalente | 35% |
| Capa 2 — Bonos soberanos USD | GD30/AL30/GD35 + law spread + EMBI | 40% |
| Capa 3 — Volatilidad accionaria | Semi-vol YPFD/GGAL/PAMP/TECO2 | 25% |

El índice también publica una versión ajustada por VIX (riesgo global) siguiendo la metodología de Bekaert et al. (2014).

## Qué NO es

- No es una encuesta. Captura posicionamiento de mercado, no preferencias declaradas.
- No es una predicción electoral. Es una lectura de lo que el mercado pricea hoy.
- No separa señal política de señal macro global — esa limitación está documentada en `CONTEXTO.md`.

## Fuentes de datos

- **Bonos soberanos:** PPI API (GD30D, AL30D, GD35D)
- **EMBI:** dolarito.ar API
- **Futuros ROFEX:** PPI API (DLR contratos activos) + SSPM datos.gob.ar (histórico) + BCR Boletines PDF
- **VIX:** Yahoo Finance (yfinance)
- **ICG/ICC UTDT:** scraping directo del sitio UTDT

## Actualización

El dashboard se actualiza automáticamente cada día hábil a las 18:30 (hora Argentina) via Windows Task Scheduler.

## Metodología completa

Ver `CONTEXTO.md` para la descripción técnica completa del índice, decisiones de diseño, limitaciones y log de sesiones de desarrollo.

---

*Desarrollado por Mariano Laxague. Publicación personal — no representa la opinión de ninguna institución.*
