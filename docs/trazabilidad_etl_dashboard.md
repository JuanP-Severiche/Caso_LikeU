# Trazabilidad ETL en el dashboard

## Objetivo

La sección `00 · Trazabilidad ETL` demuestra de forma visual y reproducible cómo el archivo `prueba.txt` se convierte en el dataset analítico.

## Flujo

```text
prueba.txt
   ↓
Python / Pandas
   ↓
Limpieza estructural
   ↓
Parsing JSON
   ↓
NLP ligero
   ↓
messages_clean.csv
   ↓
PostgreSQL
   ↓
Consultas SQL / Dashboard
```

## Archivo de salida

El ETL guarda explícitamente el CSV en la ruta definida por `PROCESSED_FILE`, cuyo valor por defecto es:

```text
data/processed/messages_clean.csv
```

Tanto el servicio `etl` como el servicio `dashboard` usan el volumen `./data:/app/data`. Por tanto, el CSV queda visible en la carpeta local del repositorio y no se pierde al eliminar el contenedor temporal creado por `docker compose run --rm`.

## Ejecución desde el navegador

El botón **Ejecutar ETL en vivo** llama un endpoint interno que ejecuta un comando fijo:

```text
python -m src.main
```

No recibe comandos del usuario ni ejecuta SQL arbitrario. Al finalizar actualiza la evidencia del archivo procesado y vuelve a consultar los indicadores del dashboard.

## Código visible

El panel lee con `inspect.getsource` las funciones reales del proyecto para mostrar exactamente el código utilizado en:

1. Lectura del TXT.
2. Limpieza y transformación.
3. Parsing del JSON embebido.
4. Clasificación NLP ligera.
5. Carga a PostgreSQL.

Así, la demostración mantiene trazabilidad entre entrada, código, salida y visualización.
