# Decisiones técnicas y supuestos

## 1. Formato del TXT

El archivo está representado como una tabla delimitada por `|` y contiene una fila separadora de guiones. Además, los campos JSON incluyen comillas escapadas. Por esto el extractor usa `csv.QUOTE_NONE`; un parser CSV convencional interpreta incorrectamente algunas comillas.

## 2. Ubicación real de los datos JSON

El caso solicita extraer errores y plantilla. En el archivo entregado se observó que:

- `external_error` se encuentra principalmente en `content_attributes`.
- `template_params.name` se encuentra principalmente en `additional_attributes`.

El parser utiliza ambas fuentes y aplica fallbacks para tolerar variaciones.

## 3. NLP ligero

Se implementa una clasificación por reglas y palabras clave porque el alcance pide NLP básico. La solución es transparente, barata, reproducible y fácil de explicar. Se normalizan mayúsculas, acentos y espacios. `Queja` tiene prioridad sobre otras categorías cuando un mensaje contiene términos que podrían pertenecer simultáneamente a `Pedido`.

## 4. SLA

La métrica oficial sigue literalmente el caso: `incoming` → siguiente `activity` u `outgoing` de la misma conversación. Se usa una Window Function con un frame hacia adelante para encontrar el siguiente evento calificable sin ejecutar una subconsulta correlacionada por cada fila.

Como complemento se crea `vw_incoming_human_sla_detail`, que mide `incoming` → siguiente `outgoing`. Esta vista no reemplaza la métrica pedida; ayuda a separar actividades del sistema de una respuesta saliente real.

## 5. Seguridad

- `.env` no se versiona.
- `.env.example` contiene solo valores de desarrollo.
- No hay secretos incrustados en Python/SQL.
- La base usa un usuario específico del proyecto.
- El proyecto no expone una API pública.

## 6. Calidad

Se incluyen pruebas unitarias para limpieza, parser JSON y clasificación, además de una prueba de integración contra el archivo entregado.


## 7. Trazabilidad visual → SQL

Cada gráfica expone un bloque desplegable "Consulta de apoyo". El SQL mostrado no es una copia independiente: se obtiene de los mismos constructores de consulta que usa el backend para ejecutar la visualización. Así se evita que la documentación y la lógica real diverjan.

Los valores de filtro siguen enviándose por parámetros de `psycopg`, por lo que el tablero muestra los placeholders y la lista de parámetros activos sin concatenar entradas del navegador dentro de SQL.

## 8. Diseño del dashboard

La interfaz se organiza en tres niveles: indicadores ejecutivos, insights exigidos por el caso y análisis complementario. Los elementos "Requerido" diferencian lo solicitado en el enunciado de métricas adicionales como mediana, P90, errores por plantilla y NLP. Esto mantiene el alcance defendible para un perfil junior sin perder calidad de presentación.
