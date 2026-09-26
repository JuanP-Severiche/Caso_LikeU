# Matriz de trazabilidad del caso técnico

Esta matriz vincula cada requerimiento del caso técnico con su implementación y evidencia dentro del repositorio.

| Requerimiento | Implementación | Evidencia |
|---|---|---|
| Limpieza estructural de `prueba.txt` | Lectura del delimitador `|`, eliminación de fila separadora, espacios y columnas vacías | `src/extract.py`, `src/transform.py`, `tests/test_cleaning.py` |
| Parsing de JSON para mensajes `failed` | Extracción segura de `external_error` y `template_name` con tolerancia a JSON escapado | `src/transform.py`, `tests/test_json_parser.py` |
| NLP ligero para `incoming` | Clasificación determinística por palabras clave y prioridad de reglas | `src/classifier.py`, `tests/test_classifier.py` |
| Base relacional gratuita | PostgreSQL 16 en Docker | `docker-compose.yml`, `sql/01_schema.sql` |
| Funnel de entrega | CTE + agregación por estado outgoing | `sql/02_funnel_entrega.sql`, dashboard sección Funnel |
| SLA de respuesta | Window Function por `conversation_id` hasta siguiente `activity` u `outgoing` | `sql/03_sla_respuesta.sql`, `sql/05_dashboard_views.sql`, dashboard sección SLA |
| Curva horaria | Agrupación de incoming por hora con las 24 franjas | `sql/04_curva_horaria.sql`, dashboard sección Workforce |
| Filtros por fecha y estado | Parámetros GET validados + SQL parametrizado | `dashboard/server.py`, `dashboard/queries.py` |
| Dashboard | Python estándar + HTML/CSS, sin framework de visualización | `dashboard/` |
| Consulta visible por gráfica | Cada visualización muestra el SQL real ejecutado y sus parámetros activos | `dashboard/queries.py`, `dashboard/render.py`, `dashboard/templates/dashboard.html` |
| Visión de negocio | Hallazgo ejecutivo sobre concentración de errores y plantilla | Dashboard + `docs/presentacion_5_min.md` |
| Escalabilidad / FinOps | Índices, separación ETL/dashboard, vistas, conexión corta, estrategia de caché documentada | `sql/06_indexes.sql`, `docs/arquitectura.md`, `docs/decisiones_tecnicas.md` |
| Código Python documentado | Módulos separados por responsabilidad y docstrings | `src/`, `dashboard/` |
| Archivo SQL con consultas | Consultas requeridas versionadas | `sql/02_funnel_entrega.sql`, `sql/03_sla_respuesta.sql`, `sql/04_curva_horaria.sql` |
| Video de máximo 5 minutos | Guion estructurado de exposición | `docs/presentacion_5_min.md` |

## Principios de ingeniería aplicados

- Separación de responsabilidades entre extracción, transformación, carga, consulta y presentación.
- Configuración y credenciales fuera del código mediante `.env`.
- SQL parametrizado para entradas del navegador.
- Validación de fechas y lista cerrada de estados permitidos.
- Pruebas automáticas para reglas críticas y dataset.
- Contenedores separados por responsabilidad.
- Documentación reproducible y trazabilidad requisito → código → evidencia.
