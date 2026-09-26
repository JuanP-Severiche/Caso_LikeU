from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
import time
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dashboard.etl_trace import PROCESSED_FILE, RAW_FILE, get_etl_trace
from dashboard.queries import (
    VALID_STATUSES,
    get_categories,
    get_dataset_summary,
    get_delivery_funnel,
    get_errors,
    get_hourly,
    get_kpis,
    get_query_support,
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
BASE_DIR = Path(__file__).resolve().parent
JS_FILE = BASE_DIR / "static" / "dashboard.js"
ETL_LOCK = threading.Lock()
ALLOW_ETL_RUN = os.getenv("DASHBOARD_ALLOW_ETL_RUN", "true").lower() == "true"


def valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False


def normalize_filters(params: dict[str, list[str]]) -> tuple[str, str, str]:
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

    return date_from, date_to, status


def execute_metric(name: str, date_from: str, date_to: str, status: str):
    """Ejecuta una métrica del dashboard y retorna datos + SQL de trazabilidad."""
    started = time.perf_counter()

    if name == "kpis":
        data = get_kpis(date_from, date_to, status or None)
    elif name == "funnel":
        data = get_delivery_funnel(date_from, date_to, status or None)
    elif name == "sla":
        data = get_kpis(date_from, date_to, status or None)
    elif name == "hourly":
        data = get_hourly(date_from, date_to)
    elif name == "errors":
        data = get_errors(date_from, date_to)
    elif name == "templates":
        data = get_templates(date_from, date_to)
    elif name == "categories":
        data = get_categories(date_from, date_to)
    else:
        raise ValueError("Métrica no permitida")

    support = get_query_support(date_from, date_to, status or None).get(name, {})
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

    return {
        "metric": name,
        "filters": {
            "date_from": date_from,
            "date_to": date_to,
            "status": status or None,
        },
        "elapsed_ms": elapsed_ms,
        "data": data,
        "query": support,
    }


def run_etl_process() -> dict:
    """Ejecuta el mismo ETL de la CLI con un comando fijo y retorna sus logs."""
    if not ETL_LOCK.acquire(blocking=False):
        return {
            "ok": False,
            "busy": True,
            "returncode": None,
            "elapsed_ms": 0,
            "log": "Ya existe una ejecución ETL en curso.",
        }

    started = time.perf_counter()
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "src.main"],
            cwd="/app",
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        output = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part).strip()
        return {
            "ok": completed.returncode == 0,
            "busy": False,
            "returncode": completed.returncode,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "log": output,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "busy": False,
            "returncode": None,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "log": f"El ETL superó el tiempo máximo de ejecución.\n{exc}",
        }
    finally:
        ETL_LOCK.release()


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "LikeUDashboard/3.0"

    def log_message(self, fmt: str, *args) -> None:
        logger.info("%s - %s", self.client_address[0], fmt % args)

    def _send_bytes(
        self,
        body: bytes,
        content_type: str,
        status_code: int = 200,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status_code: int = 200) -> None:
        self._send_bytes(html.encode("utf-8"), "text/html; charset=utf-8", status_code)

    def _send_json(self, payload: dict, status_code: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self._send_bytes(body, "application/json; charset=utf-8", status_code)

    def _send_download(self, path: Path, content_type: str) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(404, "Archivo no encontrado")
            return
        self._send_bytes(
            path.read_bytes(),
            content_type,
            extra_headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
        )

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json({"status": "ok"})
            return

        if parsed.path == "/static/dashboard.js":
            if not JS_FILE.exists():
                self.send_error(404, "Script no encontrado")
                return
            self._send_bytes(JS_FILE.read_bytes(), "text/javascript; charset=utf-8")
            return

        if parsed.path == "/api/etl/trace":
            try:
                payload = get_etl_trace()
                payload["database"] = get_dataset_summary()
                self._send_json(payload)
            except Exception:
                logger.exception("Error leyendo trazabilidad ETL")
                self._send_json({"error": "No fue posible cargar la evidencia del ETL."}, 500)
            return

        if parsed.path == "/files/raw/prueba.txt":
            self._send_download(RAW_FILE, "text/plain; charset=utf-8")
            return

        if parsed.path == "/files/processed/messages_clean.csv":
            self._send_download(PROCESSED_FILE, "text/csv; charset=utf-8")
            return

        params = parse_qs(parsed.query)
        date_from, date_to, status = normalize_filters(params)

        if parsed.path == "/api/query":
            name = params.get("name", [""])[0].strip().lower()
            try:
                payload = execute_metric(name, date_from, date_to, status)
                self._send_json(payload)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, 400)
            except Exception:
                logger.exception("Error ejecutando consulta interactiva")
                self._send_json({"error": "No fue posible ejecutar la consulta."}, 500)
            return

        if parsed.path not in {"/", "/dashboard"}:
            self.send_error(404, "Recurso no encontrado")
            return

        try:
            html = render_dashboard(
                kpis=get_kpis(date_from, date_to, status or None),
                funnel=get_delivery_funnel(date_from, date_to, status or None),
                hourly=get_hourly(date_from, date_to),
                errors=get_errors(date_from, date_to),
                templates=get_templates(date_from, date_to),
                categories=get_categories(date_from, date_to),
                summary=get_dataset_summary(),
                query_support=get_query_support(date_from, date_to, status or None),
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

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/etl/run":
            self.send_error(404, "Recurso no encontrado")
            return

        if not ALLOW_ETL_RUN:
            self._send_json({"ok": False, "error": "La ejecución ETL desde el dashboard está deshabilitada."}, 403)
            return

        try:
            result = run_etl_process()
            if result.get("busy"):
                self._send_json(result, 409)
                return
            result["trace"] = get_etl_trace()
            result["database"] = get_dataset_summary() if result.get("ok") else {}
            self._send_json(result, 200 if result.get("ok") else 500)
        except Exception:
            logger.exception("Error ejecutando ETL desde el dashboard")
            self._send_json({"ok": False, "error": "No fue posible ejecutar el ETL."}, 500)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)
    logger.info("Caso_LikeU dashboard interactivo disponible en http://localhost:%s", PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Servidor detenido por el usuario")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
