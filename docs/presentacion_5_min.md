# Guion sugerido - presentación de 5 minutos

## 0:00 - 0:40 | Problema y solución

El objetivo fue convertir un extracto transaccional crudo de WhatsApp en información accionable usando herramientas Open Source. La solución usa Python para limpieza y enriquecimiento, PostgreSQL para análisis y dashboard web en Python puro para visualización. Docker Compose permite reproducir todo el entorno.

## 0:40 - 1:30 | Calidad y transformación

El TXT viene delimitado por `|`, contiene una fila separadora y JSON escapado. El ETL normaliza 3.687 registros útiles, estructura identificadores y fechas, extrae `external_error` y `template_name`, y clasifica mensajes entrantes en Pedido, Queja, Soporte u Otros mediante reglas transparentes.

## 1:30 - 2:40 | Hallazgo principal

Existen 2.507 mensajes salientes. De ellos, 1.396 terminaron en `failed`, equivalente a 55,68 %. El hallazgo más importante es la concentración: 1.374 de los 1.396 fallos (98,42 %) corresponden al error `#132000`, asociado con una diferencia entre los parámetros enviados y los esperados. Además, 1.352 fallos están asociados con la plantilla `lanzamiento_`.

Esto sugiere priorizar la corrección de la parametrización de esa plantilla antes de aumentar infraestructura o capacidad operativa.

## 2:40 - 3:35 | SLA y operación

Para el SLA se mide cada incoming hasta la siguiente actividad o salida de la misma conversación, usando una Window Function. El promedio debe interpretarse junto con mediana y P90 porque existen valores extremos. También se deja una vista complementaria para medir hasta el siguiente outgoing y separar actividades automáticas de respuestas efectivas.

La curva horaria muestra el volumen de incoming por hora para apoyar decisiones de Workforce Management.

## 3:35 - 4:20 | Dashboard

El tablero incluye KPIs, funnel de estados, SLA, volumen horario, errores principales, plantillas con fallos y clasificación de contactos. Los filtros mínimos son fecha y estado; se pueden agregar plantilla y categoría.

## 4:20 - 5:00 | Escalabilidad

Antes de escalar hardware se optimizan consultas e índices, se usa caché, se reduce el auto-refresh y se materializan agregados costosos si el volumen lo requiere. La prioridad FinOps es medir primero y pagar capacidad adicional solo cuando la evidencia lo justifique.
