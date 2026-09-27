# Caso LikeU - Analista de Datos

Solución del caso técnico para analizar una campaña de WhatsApp a partir de `prueba.txt` usando herramientas Open Source.

El proyecto cubre el flujo completo solicitado: limpieza con Python, parsing de JSON, NLP ligero, carga en PostgreSQL, consultas SQL, dashboard con filtros y propuesta de escalabilidad.

## Flujo de la solución

```text
prueba.txt
   |
   v
Python + Pandas
   |
   +-- limpieza estructural
   +-- normalización de texto
   +-- parsing de JSON
   +-- NLP ligero
   |
   v
messages_clean.csv
   |
   v
PostgreSQL 16
   |
   +-- Funnel de entrega
   +-- SLA de respuesta
   +-- Curva horaria
   |
   v
Dashboard web
```

## Tecnologías

- Python 3.12
- Pandas
- PostgreSQL 16
- SQLAlchemy / psycopg
- HTML, CSS y JavaScript nativo
- Docker y Docker Compose
- Pytest

## Requisitos del caso cubiertos

### Punto 1 - Procesamiento

- Lectura del archivo con delimitador `|`.
- Eliminación de espacios, fila separadora y columnas vacías.
- Extracción de `external_error` y `template_name` desde JSON.
- Clasificación de mensajes `incoming` en `Pedido`, `Queja`, `Soporte` u `Otros`.
- Exportación del resultado a `data/processed/messages_clean.csv`.

### Punto 2 - SQL

Las tres consultas solicitadas están en:

```text
sql/02_funnel_entrega.sql
sql/03_sla_respuesta.sql
sql/04_curva_horaria.sql
```

También se entregan juntas en:

```text
sql/consultas_punto_2.sql
```

### Punto 3 - Dashboard y negocio

El dashboard incluye:

- filtros por fecha y estado;
- KPIs de entrega;
- funnel de estados outgoing;
- SLA promedio, mediana, P90 y cobertura;
- volumen incoming por hora;
- errores de entrega;
- fallos por plantilla;
- clasificación NLP de mensajes incoming;
- trazabilidad del ETL y consultas SQL visibles.

## Ejecución en Windows CMD

Desde la raíz del proyecto:

```cmd
copy .env.example .env

docker compose up -d postgres

docker compose --profile tools build etl
docker compose --profile tools run --rm etl python -m src.main

docker compose --profile tools run --rm etl pytest -v

docker compose build dashboard
docker compose up -d dashboard

start http://localhost:8000
```

Para detener los servicios:

```cmd
docker compose down
```

No uses `docker compose down -v` si quieres conservar los datos de PostgreSQL.

## Resultados de referencia

Con el dataset suministrado:

- Registros útiles: 3.687
- Mensajes outgoing: 2.507
- Mensajes incoming: 430
- Failed: 1.396
- Read: 708
- Sent: 320
- Delivered: 83
- SLA promedio: 127,24 min
- SLA mediana: 0,68 min
- P90: 81,33 min
- Cobertura SLA: 85,81%

## Hallazgo principal

La mayor parte de los mensajes fallidos está asociada al error de cantidad de parámetros de plantilla. La plantilla `lanzamiento_` concentra la mayoría de esos fallos. Por eso, antes de aumentar infraestructura, la primera revisión debe enfocarse en la parametrización del envío.

La curva horaria también permite identificar los periodos de mayor demanda para apoyar decisiones de Workforce Management.

## Escalabilidad

Para un escenario de 50 usuarios actualizando el dashboard cada cinco minutos, la estrategia propuesta es optimizar antes de aumentar infraestructura:

- índices en campos consultados con frecuencia;
- caché de resultados repetidos;
- vistas materializadas para agregaciones costosas;
- pooling de conexiones;
- revisión de consultas con `EXPLAIN ANALYZE`.

## Documentación

- `docs/caso_uso.md`: objetivo y flujo funcional.
- `docs/guia_codigo.md`: explicación breve de los módulos.
- `docs/matriz_requisitos.md`: relación entre requisito y evidencia.
- `docs/decisiones_tecnicas.md`: decisiones de implementación y FinOps.

## Seguridad

- Credenciales por variables de entorno.
- `.env` fuera del repositorio.
- SQL parametrizado para filtros.
- Validación de fechas y estados.
- Endpoint de consultas limitado a métricas conocidas.
- Separación de responsabilidades entre ETL, base de datos y dashboard.
