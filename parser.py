from __future__ import annotations


def extract_meta(raw: dict) -> dict:
    s1_data = raw.get("data", {}).get("step_1", {}).get("data", {})
    parts = [
        s1_data.get("lastname", ""),
        s1_data.get("firstname", ""),
        s1_data.get("middlename", ""),
    ]
    fullname = " ".join(p.strip() for p in parts if p.strip())
    return {
        "doc_id": raw.get("id", ""),
        "user_declarant_id": raw.get("user_declarant_id", 0),
        "year": raw.get("declaration_year", 0),
        "fullname": fullname,
    }
