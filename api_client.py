from __future__ import annotations

import json
import urllib.error
import urllib.request


class ApiSource:
    def __init__(self, base_url: str) -> None:
        self._base = base_url.rstrip("/")

    def get_document(self, doc_id: str) -> dict:
        return self._get(f"{self._base}/v2/documents/{doc_id}")

    def get_document_list(self, user_declarant_id: int) -> list[str]:
        raw = self.fetch_list_raw(user_declarant_id)
        return [item["id"] for item in raw.get("data", [])]

    def fetch_list_raw(self, user_declarant_id: int) -> dict:
        return self._get(f"{self._base}/v2/documents/list?user_declarant_id={user_declarant_id}")

    def _get(self, url: str) -> dict:
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            exc = RuntimeError(
                f"HTTP {e.code} {e.reason} — {url}. Спробуйте пізніше."
            )
            exc.http_code = e.code
            raise exc from e
        except Exception as e:
            raise RuntimeError(
                f"Помилка з'єднання ({url}): {e}. Спробуйте пізніше."
            ) from e
