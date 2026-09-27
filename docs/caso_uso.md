# Caso de uso

## Objetivo

Analizar una campaña de WhatsApp a partir del archivo `prueba.txt` para dar visibilidad sobre entrega de mensajes, tiempos de respuesta y comportamiento de los clientes, usando herramientas de bajo costo y Open Source.

## Flujo implementado

1. Leer el archivo transaccional con Python y Pandas.
2. Limpiar la estructura y normalizar los campos necesarios para análisis.
3. Extraer desde JSON el error de entrega y el nombre de la plantilla en mensajes `failed`.
4. Clasificar mensajes `incoming` con reglas simples de palabras clave.
5. Guardar el resultado en PostgreSQL.
6. Ejecutar las tres consultas SQL solicitadas: funnel, SLA y curva horaria.
7. Mostrar los resultados en un dashboard con filtros por fecha y estado.
8. Complementar el análisis con errores, plantillas y categorías de mensajes.

## Preguntas que responde la solución

- ¿Qué porcentaje de mensajes salientes quedó en `read`, `delivered` o `failed`?
- ¿Cuánto tarda el equipo en realizar la siguiente acción después de un mensaje `incoming`?
- ¿En qué horas se concentra la demanda entrante?
- ¿Qué errores explican la mayor parte de los mensajes fallidos?
- ¿Qué plantillas concentran esos fallos?
- ¿Qué tipo de mensajes envían los clientes?

## Resultado esperado

La solución convierte un archivo transaccional crudo en información útil para operación. El análisis permite separar problemas técnicos de problemas de capacidad y priorizar acciones con evidencia.
