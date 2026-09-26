# Arquitectura — Caso_LikeU

## Objetivo

Procesar el extracto transaccional `prueba.txt` con herramientas Open Source, almacenar el resultado estructurado en PostgreSQL y presentar los indicadores de la campaña en un dashboard web liviano construido con Python estándar y HTML/CSS.

## Flujo

```text
prueba.txt
    │
    ▼
Python / Pandas
    │
    ├─ limpieza estructural
    ├─ parsing JSON
    ├─ clasificación NLP ligera
    └─ validaciones
    │
    ▼
PostgreSQL 16
    │
    ├─ tabla messages
    ├─ índices
    ├─ vistas analíticas
    └─ consultas SQL con CTEs y Window Functions
    │
    ▼
Servidor HTTP Python estándar
    │
    ▼
HTML + CSS
```

## Separación de responsabilidades

- **ETL (`src/`)**: carga, limpia, transforma y persiste los datos.
- **PostgreSQL (`sql/`)**: conserva la fuente analítica y resuelve métricas de negocio.
- **Dashboard (`dashboard/`)**: consulta datos ya procesados y genera HTML; no modifica la fuente.
- **Tests (`tests/`)**: valida limpieza, JSON, clasificación, dataset y render del dashboard.

## Decisiones

- PostgreSQL se mantiene como fuente única para los indicadores.
- El dashboard no usa Django, Flask, Streamlit ni una plataforma BI.
- El servidor usa `ThreadingHTTPServer` de la librería estándar de Python.
- Los filtros se parametrizan en `psycopg`; los valores recibidos del navegador nunca se concatenan directamente en SQL.
- El estado se valida contra una lista cerrada antes de consultar la base.
- Las fechas deben cumplir formato ISO `YYYY-MM-DD`.

## Rendimiento / FinOps

Para varios usuarios concurrentes, la estrategia de menor costo es medir primero y reducir trabajo repetido: índices sobre los campos filtrados, vistas/materialized views para agregaciones costosas si el volumen aumenta, pool/proxy de conexiones si se vuelve necesario y medición con `EXPLAIN (ANALYZE, BUFFERS)`. Para este caso técnico, las consultas operan sobre un conjunto pequeño y el servidor HTTP es deliberadamente simple.
