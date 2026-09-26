# Demo interactiva del dashboard

## Objetivo

La visualización mantiene la arquitectura del caso técnico, pero permite ejecutar las consultas SQL durante la presentación sin recargar toda la página.

## Flujo en tiempo real

```text
Usuario pulsa "Ejecutar consulta"
        ↓
JavaScript nativo llama GET /api/query
        ↓
Python valida fecha y estado
        ↓
psycopg ejecuta SQL parametrizado en PostgreSQL
        ↓
Servidor retorna JSON + SQL + parámetros + elapsed_ms
        ↓
JavaScript actualiza y anima la gráfica
```

No existe una copia independiente del cálculo en JavaScript. PostgreSQL sigue siendo la fuente de verdad; el navegador únicamente representa el resultado retornado por el backend.

## Controles

- **Ejecutar análisis**: ejecuta todas las métricas con los filtros seleccionados.
- **Ejecutar consulta**: ejecuta solamente la visualización seleccionada.
- **Restablecer**: vuelve al periodo completo y estado Todos, y ejecuta nuevamente el análisis.
- **Modo presentación**: recorre funnel, SLA, curva horaria, errores, plantillas y NLP; ejecuta cada consulta antes de avanzar.
- **Consulta de apoyo**: muestra el SQL real y sus parámetros activos.

## Seguridad

- Sólo se permiten nombres de métricas definidos en el backend.
- Fechas en formato ISO son validadas por Python.
- Estado se valida contra una lista cerrada.
- Los valores siguen enviándose como parámetros `psycopg`; no se concatenan directamente en SQL.
- La API devuelve JSON y no ejecuta SQL enviado por el navegador.

## Presentación

Para demostrar trazabilidad técnica:

1. Seleccionar filtros.
2. Pulsar **Ejecutar consulta** en Funnel.
3. Observar la animación y el tiempo de ejecución.
4. Abrir **Consulta de apoyo** y explicar CTE, parámetros y resultado.
5. Repetir en SLA y curva horaria.
6. Usar **Modo presentación** para recorrer el diagnóstico complementario.
