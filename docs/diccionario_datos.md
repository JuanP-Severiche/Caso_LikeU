# Diccionario de datos procesados

| Campo | Descripción |
|---|---|
| `id` | Identificador normalizado del mensaje. |
| `conversation_id` | Identificador normalizado de conversación. |
| `message_type` | `incoming`, `outgoing` o `activity`. |
| `created_at` | Fecha/hora del evento. |
| `status` | Estado transaccional (`sent`, `read`, `delivered`, `failed`). |
| `content` | Contenido textual original normalizado en bordes. |
| `content_attributes` | JSON escapado de atributos del mensaje. |
| `additional_attributes` | JSON escapado con datos adicionales. |
| `external_error` | Error externo extraído para mensajes fallidos. |
| `template_name` | Nombre de plantilla extraído principalmente de `additional_attributes.template_params.name`. |
| `json_parse_status` | `OK`, `EMPTY` o `INVALID`. |
| `incoming_category` | Clasificación ligera: `Queja`, `Pedido`, `Soporte`, `Otros`. |
| `matched_keyword` | Palabra o frase que justificó la clasificación. |
| `content_is_empty` | Indicador de contenido vacío. |

Los identificadores del archivo fuente aparecen con puntos usados como separadores de miles. El ETL los normaliza a enteros (`31.888` → `31888`).
