**INDICE DE EXPECTATIVA POLITICA**

**IEP Argentina**

*Midiendo la expectativa electoral a traves de los mercados financieros*

| METODOLOGIA, ARQUITECTURA Y PLAN DE NEGOCIO Version 1.0 \- Mayo 2025 |
| :---: |

Documento preparado por:

**Mariano \- Consultor en Inteligencia Politica y Datos**

RadarPolitico.ai  |  LegiscopeAR

# **1\. Resumen Ejecutivo**

El Indice de Expectativa Politica (IEP) es un indicador cuantitativo de alta frecuencia que sintetiza la informacion implicita en los mercados financieros argentinos para medir, en tiempo real, la expectativa del mercado sobre la continuidad o reversion del programa politico-economico vigente.

A diferencia de las encuestas de opinion —que miden preferencias declaradas con rezago de semanas— el IEP captura posicionamiento real: dinero puesto en juego. Los agentes de mercado procesan informacion, anticipan escenarios y se cubren con horas o dias de antelacion respecto al ciclo noticioso. El IEP convierte esas senales en un numero interpretable para audiencias politicas, periodisticas y financieras.

| COMPONENTE | SENAL QUE CAPTURA | PESO |
| ----- | :---- | :---: |
| Futuros de dolar (ROFEX/MAE) | Expectativa cambiaria y credibilidad del ancla | **35%** |
| Bonos soberanos USD (AL30/GD30) | Riesgo soberano y probabilidad de continuidad fiscal | **40%** |
| Opciones BYMA - volatilidad implicita | Incertidumbre sectorial y sesgo electoral | **25%** |

El IEP se ancla en el resultado de las elecciones legislativas del 27 de octubre de 2025, momento en que el mercado consolido su lectura de continuidad del programa. Ese punto es el baseline = 100. Valores superiores reflejan mayor conviccion de reeleccion; valores inferiores senalan aumento del riesgo politico percibido.

| RANGO IEP | INTERPRETACION |
| :---: | :---- |
| **> 110** | Mercado pricea reeleccion con mayor conviccion que post-legislativas 2025 |
| **90 - 110** | Zona baseline - continuidad del programa creible |
| **70 - 89** | Optimismo moderado con ruido - comparable a H1 2025 |
| **40 - 69** | Incertidumbre activa - comparable a 2024 pre-estabilizacion |
| **< 40** | Stress politico severo - comparable a periodo Massa/Guzman |

# **2\. El Problema que Resuelve**

## **2.1 El vacio de informacion en tiempo real**

El ecosistema de informacion politico-electoral en Argentina tiene una brecha estructural: los instrumentos que miden expectativas operan en frecuencias incompatibles con la velocidad de los eventos.

| INSTRUMENTO | FRECUENCIA | MIDE | LIMITACION |
| :---- | :---: | :---- | ----- |
| Encuestas de opinion | Mensual / bimestral | Preferencia declarada | Rezago de 3-6 semanas |
| Indice Dintella / UTDT | Mensual | Confianza del consumidor | Sin granularidad politica |
| Riesgo pais (EMBI) | Diario | Default soberano | No capta senal electoral |
| **IEP (este proyecto)** | **Diario** | **Expectativa electoral de mercado** | -- |

## **2.2 La oportunidad de mercado**

Argentina enfrenta un ciclo electoral de alta intensidad entre 2025 y 2027: legislativas de medio termino (octubre 2025) y presidenciales (2027). En ese contexto existe demanda concreta no satisfecha:

* Los inversores financieros necesitan senales politicas procesadas, no ruido mediatico.
* Las consultoras politicas carecen de metricas de mercado integradas en sus modelos de riesgo.
* Los medios compiten por narrativas con datos propios y diferenciados.
* Los organismos internacionales monitorean el riesgo politico argentino de forma sistematica.
* Los partidos y campanas necesitan termometros de credibilidad distintos a las encuestas internas.

# **3\. Metodologia del Indice**

## **3.1 Arquitectura de tres capas**

### **CAPA 1 - Futuros de Dolar ROFEX/MAE (Peso: 35%)**

| METRICA | DEFINICION Y SENAL POLITICA |
| :---- | :---- |
| Pendiente de la curva de futuros | Diferencial entre contratos cortos y largos. Pendiente moderada = credibilidad del ancla. Empinamiento pronunciado = el mercado anticipa salto cambiario. |
| Prima de riesgo electoral implicita | Diferencial entre el contrato previo y posterior a la fecha electoral clave, ajustado por tasa de interes. Cuantifica cuanto del tipo de cambio futuro es puro evento electoral. |
| Volatilidad de la curva de futuros | Dispersion de los contratos respecto a la tendencia de crawling peg esperada. Mayor dispersion = mayor incertidumbre sobre la continuidad del esquema cambiario. |

### **CAPA 2 - Bonos Soberanos USD: AL30 / GD30 / GD35 (Peso: 40%)**

| METRICA | DEFINICION Y SENAL POLITICA |
| :---- | :---- |
| Paridad promedio ponderada AL30/GD30/GD35 | Precio del bono como porcentaje del valor nominal. Sube = el mercado cree que Argentina cumple con los pagos. Baja = incremento de riesgo de reestructuracion. |
| Spread AL vs GD (ley local vs. NY) | Cuando el diferencial se amplia, el mercado distingue entre riesgo de reestructuracion unilateral domestica vs. internacional. Es una senal directa de riesgo politico interno. |
| Curva de probabilidad de pago implicita | Strip de cupones escalonados para extraer probabilidad de continuidad de pago anio a anio. |
| Z-score historico normalizado | Posicion de la paridad actual en percentiles historicos 2020-2025. Traduce el precio de mercado a la escala 0-100 del IEP. |

### **CAPA 3 - Opciones sobre Acciones BYMA (Peso: 25%)**

| METRICA | DEFINICION Y SENAL POLITICA |
| :---- | :---- |
| Volatilidad implicita sectorial (IV) | IV de opciones sobre empresas reguladas (YPF, Edenor, Telecom) vs. commodities exportadores (ALUA, TXAR). |
| Put/Call ratio por activo | Aumento de puts sobre empresas sensibles a regulacion = el mercado compra cobertura ante escenario de reversion politica. |
| Skew electoral (distribucion implicita) | Asimetria de la distribucion de probabilidad implicita en opciones. Skew negativo cerca de fechas electorales = tail risk bajista. |

## **3.2 Normalizacion y construccion del indice compuesto**

| PARAMETRO | VALOR |
| :---- | :---: |
| Periodo de calibracion historica | Enero 2020 - Octubre 2025 |
| Baseline (IEP = 100) | 27 de octubre de 2025 (resultado legislativo) |
| Frecuencia de actualizacion | Diaria (dia habil bursatil) |
| Ventana de suavizado | Media movil de 5 ruedas (semana bursatil) |
| Revision de ponderaciones | Semestral, o ante cambios estructurales de mercado |

## **3.3 Validacion del constructo**

1. Correlacion con rezago vs. encuestas de aprobacion presidencial (Zuban Cordoba, Analogias, CB Consultora). Lag optimo estimado: k = 2-4 semanas.
2. Correlacion con Indice Dintella (UTDT) - frecuencia mensual. Se espera r > 0.65 en la serie 2024-2025.
3. Analisis de eventos: verificar que los shocks en la serie del IEP corresponden con eventos politicos documentados.

# **4\. Arquitectura del Producto**

| CAPA | COMPONENTES | TECNOLOGIA |
| ----- | :---- | :---- |
| **Pipeline de datos** | Scrapers ROFEX, Investing.com, IOL/PPI. Almacenamiento historico. Calculo diario del indice. | Python (pandas, requests), PostgreSQL / Supabase, cron jobs |
| **Dashboard** | Visualizacion del IEP compuesto, sub-indices, serie historica con eventos anotados, comparacion vs. encuestas. | Next.js, D3.js / Recharts, Vercel |
| **Distribucion** | Newsletter semanal. API para terceros. Informes PDF automatizados. Widget para medios. | Resend / Ghost, FastAPI, WeasyPrint |

# **5\. Modelo de Negocio**

## **Vertical 1 - Newsletter de pago (Lanzamiento inmediato)**

- Audiencia: periodistas financieros, analistas politicos, traders, consultores
- Precio: USD 15-25/mes (individual) | USD 80-120/mes (institucional)
- Meta anio 1: 150 suscriptores pagos = USD 2.250-3.750/mes

## **Vertical 2 - Informes puntuales por evento (Lanzamiento inmediato)**

- Audiencia: fondos de inversion, consultoras de riesgo politico, organismos multilaterales
- Precio: USD 200-500 por informe | Packs de 4 anuales: USD 1.200-1.800
- Meta anio 1: 6-8 informes x 15-20 clientes = USD 18.000-40.000 anuales

## **Vertical 3 - Dashboard institucional SaaS (Anio 2)**

- Audiencia: consultoras politicas, camaras empresariales, research de bancos/brokers
- Precio: USD 300-600/mes por organizacion

## **Vertical 4 - API de datos (Anio 2)**

- Audiencia: fintech, plataformas de inversion, hedge funds cuantitativos
- Precio: USD 500-1.500/mes

## **Vertical 5 - Consultoria experta**

- Audiencia: embajadas, organismos internacionales, fondos PE, campanas politicas
- Precio: USD 800-2.000 por sesion | retainer USD 1.500-3.500/mes

# **6\. Proyeccion Financiera**

## **Escenario conservador - Anio 1**

| FUENTE | VOLUMEN | TICKET | ANUAL |
| :---- | ----- | ----- | :---: |
| Newsletter individual | 100 suscriptores | USD 20/mes | USD 24.000 |
| Newsletter institucional | 15 orgs | USD 100/mes | USD 18.000 |
| Informes por evento | 6 inf x 12 clientes | USD 250 | USD 18.000 |
| Consultoria | 8 sesiones | USD 1.200 | USD 9.600 |
| **TOTAL** | | | **aprox. USD 69.600** |

## **Escenario optimista - Anio 2**

| FUENTE | VOLUMEN | TICKET | ANUAL |
| :---- | ----- | ----- | :---: |
| Newsletter (ind + inst) | 300 + 30 orgs | USD 20-100/mes | USD 108.000 |
| Dashboard SaaS | 10 clientes | USD 400/mes | USD 48.000 |
| API de datos | 5 clientes | USD 800/mes | USD 48.000 |
| Informes + consultoria | varios | varios | USD 45.000 |
| **TOTAL** | | | **aprox. USD 249.000** |

# **7\. Roadmap de Ejecucion**

| FASE | PERIODO | HITOS CLAVE | OBJETIVOS |
| :---: | :---: | :---- | :---- |
| **0 - Fundacion** | Mes 1-2 | Pipeline de datos. Serie historica 2020-2025. Validacion vs. encuestas. | MVP interno. Sin lanzamiento publico. |
| **1 - Lanzamiento** | Mes 3-4 | Publicacion del indice. Newsletter gratuita. 3 notas publicas en LinkedIn. | 50 suscriptores gratuitos. 10 pagos. Primera venta de informe. |
| **2 - Traccion** | Mes 5-8 | Dashboard beta. Co-branding con 1 broker. 2 menciones en medios. | 100 suscriptores pagos. 3 clientes institucionales. USD 5k/mes. |
| **3 - Escala** | Mes 9-12 | Integracion con RadarPolitico y LegiscopeAR. API beta. Informe electoral 2025. | MRR USD 7.500+. |
| **4 - Institucional** | Anio 2 | Dashboard SaaS. API comercial. Presentacion en organismos y fondos. | MRR USD 15.000-20.000. |

# **8\. Ventaja Competitiva**

El IEP combina tres capacidades que raramente coexisten en un mismo actor:

1. Comprension profunda del sistema politico argentino
2. Expertise en mercados de capitales locales (ROFEX, BYMA, bonos soberanos)
3. Capacidad de comunicacion y produccion de contenido

Un banco de inversion tiene la segunda pero no la primera ni la tercera. Una consultora politica tiene la primera pero no la segunda. Un medio tiene la tercera pero no las dos primeras. **El IEP ocupa la interseccion exacta de las tres.**

# **9\. Riesgos y Mitigaciones**

| RIESGO | MITIGACION |
| :---- | :---- |
| Acceso a datos de opciones BYMA (escasos) | Arrancar con capas 1 y 2. Incorporar opciones progresivamente. |
| Correlacion baja con encuestas | Disenar la validacion como investigacion publica. Los resultados intermedios tambien son publicables. |
| Contagio financiero externo | Incorporar filtro de componente beta de mercados emergentes. |
| Competencia de medios financieros | La ventaja es la interpretacion politica experta y la velocidad de llegada. Ser primero importa. |
| Baja volatilidad politica | En escenarios estables, el indice valida el consenso y sigue siendo util como confirmacion. |

# **10\. Conclusion**

El IEP es una propuesta de valor concreta, con fundamento metodologico solido, audiencia identificada y multiples vectores de monetizacion. No compite con las encuestas de opinion: las complementa desde una perspectiva radicalmente distinta, la de los agentes que ponen dinero real en funcion de sus expectativas politicas.

| El IEP convierte el ruido del mercado en senal politica. *Y la senal politica en ingresos.* |
| :---: |

*Documento preparado por Mariano  |  RadarPolitico.ai  |  LegiscopeAR  |  Mayo 2025*
