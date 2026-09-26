from __future__ import annotations

import logging
import os
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from dashboard.queries import (
    VALID_STATUSES,
    get_categories,
    get_dataset_summary,
    get_delivery_funnel,
    get_errors,
    get_hourly,
    get_kpis,
    get_templates,
)
from dashboard.render import render_dashboard


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

HOST = "0.0.0.0"
PORT = int(os.getenv("DASHBOARD_PORT", "8000"))
DEFAULT_DATE_FROM = "2023-07-25"
DEFAULT_DATE_TO = "2023-08-02"


def valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "LikeUDashboard/1.0"

    def log_message(self, fmt: str, *args) -> None:
        logger.info("%s - %s", self.client_address[0], fmt % args)

    def _send_html(self, html: str, status_code: int = 200) -> None:
        body = html.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_html("OK")
            return
        if parsed.path not in {"/", "/dashboard"}:
            self.send_error(404, "Recurso no encontrado")
            return

        params = parse_qs(parsed.query)
        date_from = params.get("date_from", [DEFAULT_DATE_FROM])[0]
        date_to = params.get("date_to", [DEFAULT_DATE_TO])[0]
        status = params.get("status", [""])[0].strip().lower()

        if not valid_date(date_from):
            date_from = DEFAULT_DATE_FROM
        if not valid_date(date_to):
            date_to = DEFAULT_DATE_TO
        if date_from > date_to:
            date_from, date_to = date_to, date_from
        if status not in VALID_STATUSES:
            status = ""

        try:
            html = render_dashboard(
                kpis=get_kpis(date_from, date_to, status or None),
                funnel=get_delivery_funnel(date_from, date_to, status or None),
                hourly=get_hourly(date_from, date_to),
                errors=get_errors(date_from, date_to),
                templates=get_templates(date_from, date_to),
                categories=get_categories(date_from, date_to),
                summary=get_dataset_summary(),
                date_from=date_from,
                date_to=date_to,
                status=status,
            )
            self._send_html(html)
        except Exception:
            logger.exception("Error generando dashboard")
            self._send_html(
                "<h1>No fue posible cargar el dashboard</h1>"
                "<p>Revise que PostgreSQL esté disponible y que el ETL se haya ejecutado.</p>",
                500,
            )


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    logger.info("Caso_LikeU dashboard disponible en http://localhost:%s", PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Servidor detenido por el usuario")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
