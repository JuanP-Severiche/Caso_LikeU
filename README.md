# Caso_LikeU — Caso Técnico Analista de Datos

Solución reproducible para procesar el extracto `prueba.txt`, estructurar JSON embebido, clasificar mensajes entrantes con NLP ligero, cargar PostgreSQL, calcular indicadores SQL y presentar un dashboard web construido **sin framework de visualización**: Python estándar + HTML/CSS + JavaScript nativo.

## Arquitectura

```text
prueba.txt
   │
   ▼
ETL Python / Pandas
   │
   ▼
PostgreSQL 16
   │
   ├── SQL: Funnel
   ├── SQL: SLA con Window Functions
   ├── SQL: Curva horaria
   └── Vistas analíticas
   │
   ▼
Dashboard Python estándar
   │
   └── HTML + CSS
```

## Requisitos

- Docker Desktop
- Docker Compose v2
- Git (si el repositorio se clona)

No es necesario instalar PostgreSQL ni Python localmente.

## Ejecución rápida en Windows CMD

Desde la raíz de `Caso_LikeU`:

```cmd
copy .env.example .env

docker compose down -v
docker compose up -d postgres

docker compose --profile tools build etl
docker compose --profile tools run --rm etl python -m src.main

docker compose --profile tools run --rm etl pytest -v

docker compose up -d dashboard

start http://localhost:8000
```

> `docker compose down -v` reinicia los volúmenes. Úselo al preparar una ejecución limpia. Si ya existen datos que desea conservar, omita ese comando.

## Validaciones esperadas

El ETL debe reportar aproximadamente:

```text
Registros útiles: 3687
Outgoing: 2507
Incoming: 430
Failed: 1396
```

Las pruebas deben finalizar con:

```text
14 passed
```

Verificación de PostgreSQL:

```cmd
docker compose exec postgres psql -U likeu_user -d likeu_analytics -c "SELECT COUNT(*) FROM messages;"
```

Resultado esperado:

```text
3687
```


## Trazabilidad ETL visible en el dashboard

La sección **00 · Trazabilidad ETL** permite demostrar el proceso completo sin salir del navegador:

- Vista previa del archivo fuente `data/raw/prueba.txt`.
- Metadatos del archivo: nombre, tamaño, fecha de modificación y filas físicas.
- Botón **Ejecutar ETL en vivo**, que ejecuta el mismo `python -m src.main` usado desde CMD.
- Log real de la ejecución ETL.
- Vista previa de `data/processed/messages_clean.csv` después del procesamiento.
- Descarga del TXT original y del CSV limpio.
- Código Python real de lectura, limpieza, parsing JSON, NLP y carga a PostgreSQL.
- Flujo visual TXT → limpieza → JSON → NLP → CSV → PostgreSQL → dashboard.

El servicio `dashboard` monta `./data:/app/data`, por lo que el archivo limpio generado desde el navegador o desde el contenedor ETL queda persistido también en la carpeta local `data\processed`.

Para verificarlo desde Windows CMD:

```cmd
dir data\processed
```

Debe aparecer:

```text
messages_clean.csv
```

## Calidad y normalización del mensaje

El ETL conserva la columna `content` como dato fuente y genera `clean_message` como versión preparada para análisis. Esta columna normaliza Unicode en NFC, corrige de forma conservadora mojibake recuperable (por ejemplo `conversaciÃ³n` → `conversación`), conserva tildes, `ñ`, emojis y signos, y reemplaza el marcador `¶` por espacios. El CSV se exporta como `utf-8-sig` para compatibilidad con Excel/Windows.

Además se agregan `encoding_repaired` y `text_quality_status`. Si la fuente ya contiene pérdida irreversible como `Nu?Ez`, el proceso no inventa caracteres: conserva el texto y lo marca como `SOURCE_CHARACTER_LOSS`.

## Dashboard

Abrir:

```text
http://localhost:8000
```

El tablero presenta una interfaz ejecutiva organizada por requisitos y **cada visualización incluye un bloque desplegable con la consulta SQL real que la alimenta y los parámetros activos**. Además, cada gráfica dispone de un botón **Ejecutar consulta**: el navegador llama al endpoint `/api/query`, Python ejecuta nuevamente la consulta en PostgreSQL y la gráfica se actualiza en la misma pantalla con animación y tiempo de ejecución. Esto permite demostrar en vivo la trazabilidad entre SQL, dato y visualización.

El tablero incluye:

- Filtros por fecha inicio, fecha fin y estado.
- Mensajes salientes.
- Tasas de failed, read y delivered.
- SLA promedio, mediana y P90.
- Cobertura y mensajes sin acción posterior.
- Funnel de entrega.
- Volumen incoming por hora.
- Principales errores de entrega.
- Plantillas con mayor concentración de fallos.
- Clasificación NLP de incoming.
- Hallazgo ejecutivo generado con las métricas filtradas.
- Consulta SQL de apoyo visible para KPIs, SLA, funnel, curva horaria, errores, plantillas y categorías.
- Ejecución interactiva de cada consulta sin recargar la página.
- Actualización animada de barras y KPIs con JavaScript nativo.
- Indicador de tiempo de ejecución de cada consulta.
- Modo presentación que recorre y ejecuta las visualizaciones principales.

El servidor web usa `http.server.ThreadingHTTPServer` de la librería estándar de Python. La interacción del navegador usa JavaScript nativo (`fetch`, DOM y CSS transitions). No utiliza Django, Flask, Streamlit, Metabase, Bootstrap, React, Vue ni frameworks JavaScript.

## Trazabilidad de requisitos

La correspondencia entre el enunciado, el código y la evidencia se documenta en `docs/matriz_requisitos.md`.

## Consultas del caso

Desde Windows CMD:

```cmd
type sql\02_funnel_entrega.sql | docker compose exec -T postgres psql -U likeu_user -d likeu_analytics

type sql\03_sla_respuesta.sql | docker compose exec -T postgres psql -U likeu_user -d likeu_analytics

type sql\04_curva_horaria.sql | docker compose exec -T postgres psql -U likeu_user -d likeu_analytics
```

Resultados de referencia para el dataset completo:

- Outgoing: 2.507
- Failed: 1.396 (55,68%)
- Read: 708 (28,24%)
- Sent: 320 (12,76%)
- Delivered: 83 (3,31%)
- Incoming: 430
- Con acción posterior: 369
- Sin acción posterior: 61
- SLA promedio: ~127,24 min
- SLA mediana: ~0,68 min
- P90: ~81,33 min

## Seguridad y buenas prácticas

- Credenciales en `.env`, nunca embebidas en el código.
- `.env` excluido de Git.
- SQL parametrizado para filtros recibidos desde el navegador.
- Lista cerrada de estados permitidos.
- Validación ISO de fechas.
- Cabeceras HTTP básicas de seguridad (`nosniff`, `DENY`, `no-referrer`).
- Contenedores separados por responsabilidad.
- ETL desacoplado de la visualización.
- Pruebas automáticas para limpieza, parser JSON, clasificación e integración del dataset.

## Estructura

```text
Caso_LikeU/
├── dashboard/
│   ├── server.py
│   ├── queries.py
│   ├── render.py
│   ├── templates/dashboard.html
│   ├── static/dashboard.css
│   └── static/dashboard.js
├── data/
│   ├── raw/prueba.txt
│   └── processed/
├── docs/
├── sql/
├── src/
├── tests/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Detener el proyecto

```cmd
docker compose down
```

Para borrar también los datos de PostgreSQL:

```cmd
docker compose down -v
```
