from __future__ import annotations

import logging
import sys

from src.config import settings
from src.extract import read_raw_messages
from src.load import load_messages
from src.transform import clean_messages


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def run() -> int:
    configure_logging()
    logger = logging.getLogger("likeu-etl")

    try:
        logger.info("Iniciando ETL de Caso_LikeU")
        logger.info("Leyendo archivo: %s", settings.raw_file)

        raw = read_raw_messages(settings.raw_file)
        logger.info("Filas leídas (incluyendo separador): %s", len(raw))

        clean = clean_messages(raw)
        logger.info("Registros útiles después de limpieza: %s", len(clean))
        logger.info("Columnas finales: %s", len(clean.columns))

        settings.processed_file.parent.mkdir(parents=True, exist_ok=True)
        clean.to_csv(settings.processed_file, index=False, encoding="utf-8")
        logger.info("CSV procesado guardado en: %s", settings.processed_file)

        load_messages(clean, settings.database_url)
        logger.info("Carga a PostgreSQL completada")

        outgoing = clean.loc[clean["message_type"].eq("outgoing")]
        incoming = clean.loc[clean["message_type"].eq("incoming")]
        logger.info("Mensajes outgoing: %s", len(outgoing))
        logger.info("Mensajes incoming: %s", len(incoming))
        logger.info("Mensajes failed: %s", int(outgoing["status"].eq("failed").sum()))
        logger.info("ETL finalizado correctamente")
        return 0

    except Exception:
        logger.exception("El ETL terminó con error")
        return 1


if __name__ == "__main__":
    sys.exit(run())
