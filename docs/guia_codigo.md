# Guía del código

Esta guía explica dónde se resuelve cada parte del caso técnico.

## 1. Procesamiento del archivo

### `src/extract.py`
Lee `prueba.txt` con separador `|`. Se usa `csv.QUOTE_NONE` porque el archivo contiene JSON con comillas escapadas y no debe interpretarse como un CSV convencional.

### `src/transform.py`
Realiza la limpieza principal:

- elimina la fila separadora y columnas vacías;
- limpia espacios residuales;
- convierte identificadores, fechas y valores booleanos;
- conserva `content` como dato fuente;
- genera `clean_message` para análisis;
- extrae `external_error` y `template_name` desde los campos JSON;
- agrega la categoría NLP para mensajes `incoming`.

La normalización de texto corrige únicamente problemas de codificación recuperables. Si el carácter ya se perdió en la fuente, el proceso conserva el valor y lo marca en `text_quality_status`.

### `src/classifier.py`
Clasifica mensajes entrantes en `Queja`, `Pedido`, `Soporte` u `Otros` mediante palabras clave. Es una solución deliberadamente simple porque el caso solicita NLP ligero.

### `src/load.py`
Carga el DataFrame procesado en PostgreSQL por lotes y ejecuta `ANALYZE` al finalizar.

### `src/main.py`
Coordina el ETL completo: lectura, transformación, exportación del CSV y carga en PostgreSQL.

## 2. Consultas SQL solicitadas

Las tres consultas del punto 2 están consolidadas en `sql/consultas_punto_2.sql` y también se mantienen separadas para facilitar su revisión:

- `sql/02_funnel_entrega.sql`
- `sql/03_sla_respuesta.sql`
- `sql/04_curva_horaria.sql`

El SLA usa una Window Function para localizar la siguiente acción `activity` u `outgoing` dentro de la misma `conversation_id`.

## 3. Dashboard

### `dashboard/queries.py`
Contiene las consultas parametrizadas usadas por la interfaz. Los filtros de fecha y estado se envían como parámetros y no se concatenan directamente al SQL.

### `dashboard/server.py`
Sirve la interfaz, valida filtros y expone únicamente las métricas permitidas. No existe un endpoint para ejecutar SQL arbitrario.

### `dashboard/render.py`
Convierte los resultados de PostgreSQL en los bloques HTML del dashboard.

### `dashboard/etl_trace.py`
Muestra la trazabilidad del ETL: archivo fuente, archivo limpio, etapas del proceso y código real utilizado.

## 4. Seguridad y configuración

- Las credenciales se toman de variables de entorno.
- `.env` no se versiona.
- Los estados válidos se controlan con una lista cerrada.
- Las fechas se validan antes de consultar PostgreSQL.
- El ETL ejecutado desde el dashboard usa un comando fijo.
- Los contenedores separan base de datos, ETL y dashboard.

## 5. Pruebas

La carpeta `tests/` valida las reglas principales del caso: lectura y limpieza, parsing de JSON, clasificación NLP, integración del dataset y render del dashboard.
