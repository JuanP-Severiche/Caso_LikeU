# Calidad de texto y mensaje limpio

## Principio

El dato fuente no se sobrescribe. `content` se conserva para trazabilidad y `clean_message` se usa para consumo analítico.

## Normalización

1. Unicode NFC.
2. Reparación conservadora de mojibake solo cuando reduce patrones sospechosos.
3. Reemplazo del marcador `¶` por espacio.
4. Compactación de espacios y saltos.
5. Conservación de tildes, ñ, signos y emojis.
6. Detección de pérdida ya presente en la fuente (`letra?letra`) sin inventar el carácter.

## Columnas

- `content`: texto fuente.
- `clean_message`: texto normalizado.
- `encoding_repaired`: indica si se reparó mojibake.
- `text_quality_status`: `OK`, `ENCODING_REPAIRED` o `SOURCE_CHARACTER_LOSS`.

## Exportación

`messages_clean.csv` se escribe como UTF-8 con BOM (`utf-8-sig`) para que Excel/Windows detecte correctamente caracteres como `á`, `é`, `í`, `ó`, `ú` y `ñ`.
