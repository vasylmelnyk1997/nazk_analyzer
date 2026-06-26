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


def map_document(raw: dict) -> dict:
    steps = raw.get("data", {})

    def _get_list(key: str) -> list:
        s = steps.get(key)
        if isinstance(s, dict):
            return s.get("data") or []
        if isinstance(s, list):
            return s
        return []

    def _rights(items: list) -> list:
        return [
            {
                "rightBelongs": str(r.get("rightBelongs", "")),
                "percentOwnership": str(r.get("percent-ownership")).replace(",", "."),
            }
            for r in items
        ]

    def _income_rights(item: dict) -> list:
        """Підтримка двох форматів: 'rights' (старіші декларації) і 'person_who_care' (реальний API)."""
        if item.get("rights"):
            return _rights(item["rights"])
        return [
            {"rightBelongs": str(p.get("person", "")), "percentOwnership": None}
            for p in item.get("person_who_care", [])
            if p.get("person")
        ]

    s1_data = steps.get("step_1", {}).get("data", {})

    step2 = [
        {
            "id": m.get("id", ""),
            "lastname": m.get("lastname", ""),
            "firstname": m.get("firstname", ""),
            "middlename": m.get("middlename", ""),
            "subjectRelation": m.get("subjectRelation", ""),
        }
        for m in _get_list("step_2")
    ]

    step3 = [
        {
            "objectType": i.get("objectType", ""),
            "totalArea": i.get("totalArea", ""),
            "region": i.get("region", ""),
            "district": i.get("district", ""),
            "city": i.get("city", ""),
            "cityType": i.get("cityType", ""),
            "region_txt": i.get("region_txt", ""),
            "district_txt": i.get("district_txt", ""),
            "city_txt": i.get("city_txt", ""),
            "owningDate": i.get("owningDate", ""),
            "rights": _rights(i.get("rights", [])),
        }
        for i in _get_list("step_3")
    ]

    step6 = [
        {
            "objectType": i.get("objectType", ""),
            "brand": i.get("brand", ""),
            "model": i.get("model", ""),
            "graduationYear": i.get("graduationYear", ""),
            "owningDate": i.get("owningDate", ""),
            "rights": _rights(i.get("rights", [])),
        }
        for i in _get_list("step_6")
    ]

    step8 = [
        {
            "name": i.get("name", ""),
            "cost": i.get("cost", 0),
            "cost_percent": i.get("cost_percent", ""),
            "rights": _rights(i.get("rights", [])),
        }
        for i in _get_list("step_8")
    ]

    step11 = [
        {
            "objectType": i.get("objectType", ""),
            "sizeIncome": i.get("sizeIncome", 0),
            "rights": _income_rights(i),
        }
        for i in _get_list("step_11")
    ]

    step12 = [
        {
            "objectType": i.get("objectType", ""),
            "sizeAssets": i.get("sizeAssets", 0),
            "assetsCurrency": i.get("assetsCurrency", "UAH"),
            "rights": _rights(i.get("rights", [])),
        }
        for i in _get_list("step_12")
    ]

    step13 = [
        {
            "objectType": i.get("objectType", ""),
            "credit_rest": i.get("credit_rest", 0),
            "currency": i.get("currency", "UAH"),
            "rights": _income_rights(i),
        }
        for i in _get_list("step_13")
    ]

    return {
        "id": raw.get("id", ""),
        "user_declarant_id": raw.get("user_declarant_id", 0),
        "declaration_year": raw.get("declaration_year", 0),
        "data": {
            "step_1": {
                "data": {
                    k: s1_data.get(k, "")
                    for k in ("lastname", "firstname", "middlename", "workPlace", "workPost")
                }
            },
            "step_2": {"data": step2},
            "step_3": {"data": step3},
            "step_6": {"data": step6},
            "step_8": {"data": step8},
            "step_11": {"data": step11},
            "step_12": {"data": step12},
            "step_13": {"data": step13},
        },
    }
