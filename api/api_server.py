from __future__ import annotations

import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")

DOC_MAP = {
    "31f44ed5-9d90-465d-858f-7e182f27c745": os.path.join(
        DATA_DIR, "Лаврик_Микола_Анатолійович-2025.json"
    ),
    "e9d07eea-3483-4578-aa6a-f297e23f04ed": os.path.join(
        DATA_DIR, "М'ялик_Віктор_Ничипорович-2019-повна.json"
    ),
    "7c6b0e7e-69fb-404d-8650-fd91f056fcff": os.path.join(
        DATA_DIR, "Ніколаєв_Ярослав_Олегович-2019-повна-перед_звільненням.json"
    ),
    "24852186-8989-464a-b74b-9bf6649866e6": os.path.join(
        DATA_DIR, "Ніколаєв_Ярослав_Олегович-2019-повна-після_звільненням.json"
    ),
    "4eb0256f-0b3a-4533-9231-878167be421e": os.path.join(
        DATA_DIR, "Підкапка_Костянтин_Васильович-2019-повна-кандидат.json"
    ),
    "767bf293-a574-4ede-ace7-c0e3f33bbd54": os.path.join(
        DATA_DIR, "Підкапка_Костянтин_Васильович-2020-повна.json"
    ),
    "c28ec29a-31ea-4d83-9d15-589270f20931": os.path.join(
        DATA_DIR, "Підкапка_Костянтин_Васильович-2025-повна.json"
    ),
    "7b267b2a-8866-4a3d-8d91-a11f3c7f2321": os.path.join(
        DATA_DIR, "Явтушенко_Олександр_Миколайович-2016-повна.json"
    ),
}

USER_DOC_MAP = {
    1432475: os.path.join(DATA_DIR, "М'ялик_Віктор_Ничипорович-список.json"),
    1525473: os.path.join(DATA_DIR, "Підкапка_Костянтин_Васильович-список.json"),
    101763: os.path.join(DATA_DIR, "Явтушенко_Олександр_Миколайович-список.json"),
}

UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def resolve_document_path(doc_id: str) -> str | None:
    return DOC_MAP.get(doc_id)


def resolve_list_path(user_declarant_id: int) -> str | None:
    return USER_DOC_MAP.get(user_declarant_id)


def read_json_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8-sig") as file:
        return json.load(file)


class MockApiHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/v2/documents/list":
            self._handle_list(query)
            return

        if path.startswith("/v2/documents/"):
            doc_id = path.split("/")[-1]
            if UUID_PATTERN.fullmatch(doc_id):
                self._handle_document(doc_id)
                return

        self._send_json(
            {
                "error": "Not Found",
                "message": f"Unsupported endpoint: {path}",
            },
            status=404,
        )

    def _handle_document(self, doc_id: str) -> None:
        file_path = resolve_document_path(doc_id)
        if file_path is None:
            self._send_json(
                {
                    "error": "Not Found",
                    "message": f"Document {doc_id} is not mapped",
                },
                status=404,
            )
            return

        self._send_json(read_json_file(file_path))

    def _handle_list(self, query: dict[str, list[str]]) -> None:
        values = query.get("user_declarant_id")
        if not values or len(values) != 1:
            self._send_json(
                {
                    "error": "Bad Request",
                    "message": "Query parameter user_declarant_id is required",
                },
                status=400,
            )
            return

        try:
            user_declarant_id = int(values[0])
        except (TypeError, ValueError):
            self._send_json(
                {
                    "error": "Bad Request",
                    "message": "Query parameter user_declarant_id must be an integer",
                },
                status=400,
            )
            return

        file_path = resolve_list_path(user_declarant_id)
        if file_path is None:
            self._send_json(
                {
                    "error": "Not Found",
                    "message": f"User declarant {user_declarant_id} is not mapped",
                },
                status=404,
            )
            return

        self._send_json(read_json_file(file_path))

    def _send_json(self, payload: Any, status: int = 200) -> None:
        response = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format: str, *args: Any) -> None:
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), MockApiHandler)
    print("Mock API server is running at http://127.0.0.1:8000")
    server.serve_forever()
