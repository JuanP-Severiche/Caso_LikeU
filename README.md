# Caso_LikeU — Caso Técnico Analista de Datos

Solución reproducible para procesar el extracto `prueba.txt`, estructurar JSON embebido, clasificar mensajes entrantes con NLP ligero, cargar PostgreSQL, calcular indicadores SQL y presentar un dashboard web construido **sin framework de visualización**: Python estándar + HTML/CSS.

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
11 passed
```

Verificación de PostgreSQL:

```cmd
docker compose exec postgres psql -U likeu_user -d likeu_analytics -c "SELECT COUNT(*) FROM messages;"
```

Resultado esperado:

```text
3687
```

## Dashboard

Abrir:

```text
http://localhost:8000
```

El tablero presenta una interfaz ejecutiva organizada por requisitos y **cada visualización incluye un bloque desplegable con la consulta SQL real que la alimenta y los parámetros activos**. Esto permite demostrar trazabilidad entre el gráfico y el cálculo ejecutado en PostgreSQL.

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

El servidor web usa `http.server.ThreadingHTTPServer` de la librería estándar de Python. No utiliza Django, Flask, Streamlit, Metabase, Bootstrap ni frameworks JavaScript.

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
│   └── static/dashboard.css
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
