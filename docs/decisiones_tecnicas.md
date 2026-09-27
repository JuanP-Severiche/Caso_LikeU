# Decisiones técnicas

## Formato del archivo

El TXT se procesa con separador `|` y sin interpretar las comillas internas del JSON. Esto evita romper los campos `content_attributes` y `additional_attributes`.

## Conservación del dato fuente

`content` se mantiene sin sobrescribir. La columna `clean_message` contiene la versión preparada para análisis. De esta forma se puede comparar el dato original con el transformado.

## Parsing de JSON

El error de entrega se obtiene de `content_attributes` y el nombre de la plantilla de `additional_attributes`, con validaciones para tolerar campos vacíos o JSON malformado.

## NLP ligero

La clasificación se basa en reglas y palabras clave. No se usa un modelo externo porque el alcance pide una clasificación básica, explicable y de bajo costo.

## SLA

Para cada mensaje `incoming` se busca la primera acción posterior de tipo `activity` u `outgoing` dentro de la misma conversación. La consulta usa una Window Function para evitar búsquedas repetitivas por fila.

## Dashboard

El tablero consulta PostgreSQL y permite filtrar por fecha y estado. Las consultas se parametrizan y la interfaz no recibe SQL libre desde el navegador.

## Escalabilidad y FinOps

Para un escenario de 50 usuarios actualizando cada cinco minutos, primero se reduce trabajo innecesario antes de aumentar infraestructura:

- índices sobre columnas usadas en filtros y ordenamiento;
- caché para resultados repetidos;
- vistas materializadas si las agregaciones crecen en costo;
- pooling de conexiones si aumenta la concurrencia;
- revisión con `EXPLAIN ANALYZE` antes de escalar recursos.
