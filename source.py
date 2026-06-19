from __future__ import annotations

import json
import os
from typing import Protocol

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_BASE_DIR, "data")

_DOC_MAP: dict[str, str] = {
    "31f44ed5-9d90-465d-858f-7e182f27c745": os.path.join(_DATA_DIR, "Лаврик_Микола_Анатолійович-2025.json"),
    "e9d07eea-3483-4578-aa6a-f297e23f04ed": os.path.join(_DATA_DIR, "М'ялик_Віктор_Ничипорович-2019-повна.json"),
    "7c6b0e7e-69fb-404d-8650-fd91f056fcff": os.path.join(_DATA_DIR, "Ніколаєв_Ярослав_Олегович-2019-повна-перед_звільненням.json"),
    "24852186-8989-464a-b74b-9bf6649866e6": os.path.join(_DATA_DIR, "Ніколаєв_Ярослав_Олегович-2019-повна-після_звільнення.json"),
    "4eb0256f-0b3a-4533-9231-878167be421e": os.path.join(_DATA_DIR, "Підкапка_Костянтин_Васильович-2019-повна-кандидат.json"),
    "767bf293-a574-4ede-ace7-c0e3f33bbd54": os.path.join(_DATA_DIR, "Підкапка_Костянтин_Васильович-2020-повна.json"),
    "c28ec29a-31ea-4d83-9d15-589270f20931": os.path.join(_DATA_DIR, "Підкапка_Костянтин_Васильович-2025-повна.json"),
    "7b267b2a-8866-4a3d-8d91-a11f3c7f2321": os.path.join(_DATA_DIR, "Явтушенко_Олександр_Миколайович-2016-повна.json"),
}

_USER_MAP: dict[int, str] = {
    1432475: os.path.join(_DATA_DIR, "М'ялик_Віктор_Ничипорович-список.json"),
    1525473: os.path.join(_DATA_DIR, "Підкапка_Костянтин_Васильович-список.json"),
    101763:  os.path.join(_DATA_DIR, "Явтушенко_Олександр_Миколайович-список.json"),
}


class DeclarationSource(Protocol):
    def get_document(self, doc_id: str) -> dict: ...
    def get_document_list(self, user_declarant_id: int) -> list[str]: ...


class FileSource:
    def __init__(
        self,
        doc_map: dict[str, str] = _DOC_MAP,
        user_map: dict[int, str] = _USER_MAP,
    ) -> None:
        self._doc_map = doc_map
        self._user_map = user_map

    def get_document(self, doc_id: str) -> dict:
        path = self._doc_map.get(doc_id)
        if path is None:
            raise KeyError(f"Document not found: {doc_id}")
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)

    def get_document_list(self, user_declarant_id: int) -> list[str]:
        path = self._user_map.get(user_declarant_id)
        if path is None:
            raise KeyError(f"Declarant not found: {user_declarant_id}")
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
        return [item["id"] for item in data.get("data", [])]
