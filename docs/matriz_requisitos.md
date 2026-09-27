# Matriz de requisitos

| Requisito del caso | Implementación | Evidencia principal |
| --- | --- | --- |
| Limpieza estructural de `prueba.txt` | Lectura con `|`, eliminación de separador, espacios y columnas vacías | `src/extract.py`, `src/transform.py` |
| Parsing de JSON en mensajes `failed` | Extracción de `external_error` y `template_name` | `src/transform.py` |
| NLP ligero para `incoming` | Clasificación por palabras clave | `src/classifier.py` |
| Base de datos relacional gratuita | PostgreSQL 16 | `docker-compose.yml`, `sql/01_schema.sql` |
| Funnel de entrega | Porcentaje de estados sobre mensajes outgoing | `sql/02_funnel_entrega.sql` |
| SLA operativo | Siguiente `activity` u `outgoing` por conversación | `sql/03_sla_respuesta.sql` |
| Curva horaria | Volumen `incoming` por hora | `sql/04_curva_horaria.sql` |
| Filtros por fecha y estado | Filtros parametrizados desde el dashboard | `dashboard/queries.py`, `dashboard/server.py` |
| Diagnóstico de negocio | Errores, plantillas, NLP y KPIs | Dashboard |
| Escalabilidad y FinOps | Índices, caché, vistas materializadas, pooling y medición | `docs/decisiones_tecnicas.md` |
| Código Python documentado | Comentarios y docstrings en puntos relevantes | `src/`, `dashboard/`, `docs/guia_codigo.md` |
| Archivo con las tres consultas | Consultas consolidadas | `sql/consultas_punto_2.sql` |
