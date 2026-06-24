from __future__ import annotations

import glob
import json
import os
import re


class Storage:
    def __init__(self, base_dir: str) -> None:
        self._dir = base_dir
        self._cache_dir = os.path.join(base_dir, "cache")
        os.makedirs(self._dir, exist_ok=True)
        os.makedirs(self._cache_dir, exist_ok=True)

    # ── documents ──────────────────────────────────────────────────────────────

    def find_document(self, doc_id: str) -> dict | None:
        matches = glob.glob(os.path.join(self._dir, f"{doc_id}_*.json"))
        if matches:
            with open(matches[0], encoding="utf-8") as f:
                return json.load(f)
        cache_path = os.path.join(self._cache_dir, f"{doc_id}.json")
        if os.path.exists(cache_path):
            with open(cache_path, encoding="utf-8") as f:
                return json.load(f)
        return None

    def save_document(self, doc_id: str, user_declarant_id: int, data: dict) -> None:
        path = os.path.join(self._dir, f"{doc_id}_{user_declarant_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    # ── doc-id lists ───────────────────────────────────────────────────────────

    def find_list_cache(self, user_declarant_id: int) -> list[str] | None:
        """Список doc_id з cache/{user_declarant_id}.json (відповідь URI-2)."""
        cache_path = os.path.join(self._cache_dir, f"{user_declarant_id}.json")
        if os.path.exists(cache_path):
            with open(cache_path, encoding="utf-8") as f:
                raw = json.load(f)
            return [item["id"] for item in raw.get("data", [])]
        return None

    def find_doc_ids_in_storage(self, user_declarant_id: int) -> list[str]:
        """doc_id усіх вже збережених декларацій за маскою *_{uid}.json."""
        pattern = os.path.join(self._dir, f"*_{user_declarant_id}.json")
        suffix = f"_{user_declarant_id}.json"
        return [
            os.path.basename(p)[: -len(suffix)]
            for p in glob.glob(pattern)
        ]

    # ── cache ──────────────────────────────────────────────────────────────────

    def save_cache_document(self, doc_id: str, data: dict) -> None:
        path = os.path.join(self._cache_dir, f"{doc_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def save_cache_list(self, user_declarant_id: int, data: dict) -> None:
        path = os.path.join(self._cache_dir, f"{user_declarant_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    # ── html ───────────────────────────────────────────────────────────────────

    def find_html(self, user_declarant_id: int) -> str | None:
        matches = glob.glob(os.path.join(self._dir, f"{user_declarant_id}_*.html"))
        return matches[0] if matches else None

    def save_html(self, user_declarant_id: int, fullname: str, html: str) -> str:
        safe = re.sub(r"[^\wЀ-ӿ]", "_", fullname)
        path = os.path.join(self._dir, f"{user_declarant_id}_{safe}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return path
