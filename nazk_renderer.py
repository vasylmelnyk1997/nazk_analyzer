from __future__ import annotations

from typing import Any

from currency_rate_archive import RATES_ARCHIVE

_CITY_TYPE_PREFIX: dict[str, str] = {
    "Місто": "м.",
    "Селище міського типу": "с-ще",
    "Селище": "с-ще",
    "Село": "с.",
}

_AREA_M2_TYPES: frozenset[str] = frozenset({
    "Квартира",
    "Житловий будинок",
    "Садовий (дачний) будинок",
    "Садибний (приватний) будинок",
    "Гараж",
    "Офіс",
    "Інше нерухоме майно",
})

_CASH_TYPE_LABEL: dict[str, str] = {
    "Готівкові кошти": "готівка",
    "Кошти, розміщені на банківських рахунках": "кошти на рахунку",
}


def _step_data(step: Any) -> list:
    if isinstance(step, dict):
        return step.get("data") or []
    return []


def _currency_code(raw: str) -> str:
    return raw.strip().split()[0].upper()


def _nbu_rate(currency_raw: str, year: int) -> float | None:
    code = _currency_code(currency_raw)
    if code == "UAH":
        return 1.0
    return RATES_ARCHIVE.get(year, {}).get(code, {}).get("nbu")


def _fmt(value: float) -> str:
    return f"{value:,.0f}".replace(",", " ")


def _proper_name(raw: str) -> str:
    parts = [part.strip() for part in raw.split() if part.strip()]
    return " ".join(part.capitalize() for part in parts)


def _build_owners(s1: dict, s2_items: list) -> dict[str, str]:
    d = s1.get("data", {})
    name = _proper_name(
        f"{d.get('lastname','')} {d.get('firstname','')} {d.get('middlename','')}"
    )
    result: dict[str, str] = {"1": name}
    for m in s2_items:
        mid = str(m.get("id", ""))
        mname = _proper_name(
            f"{m.get('lastname','')} {m.get('firstname','')} {m.get('middlename','')}"
        )
        if mid:
            result[mid] = mname
    return result


def _rights_owners(item: dict) -> list[str]:
    return [str(r.get("rightBelongs", "")) for r in item.get("rights", [])]


def _care_owners(item: dict) -> list[str]:
    return [str(p.get("person", "")) for p in item.get("person_who_care", [])]


def _area_str(item: dict) -> tuple[str, str]:
    obj_type = item.get("objectType", "")
    raw = str(item.get("totalArea", "")).replace(",", ".")
    try:
        val = float(raw)
    except ValueError:
        return "площа", raw
    if obj_type in _AREA_M2_TYPES:
        return "загальна площа", f"{val:g} м²"
    ha = val / 10_000
    return "площа", f"{ha:g} га"


def _detail_table(rows: list[tuple[str, str]]) -> str:
    trs = "".join(
        f'<tr><td class="dl">{n}.&nbsp;{label}</td>'
        f'<td class="ds"></td>'
        f'<td class="da">{amount}</td></tr>'
        for n, (label, amount) in enumerate(rows, 1)
    )
    return f'<table class="dt">{trs}</table>'


def _expandable(title: str, total_str: str, rows: list[tuple[str, str]]) -> str:
    table = _detail_table(rows)
    return (
        f'<details>'
        f'<summary class="summary-toggle"><span class="asum">'
        f'<span class="asum-arrow">&#9658;</span>'
        f'<span>{title}</span>'
        f'<strong>{total_str}</strong>'
        f'</span></summary>'
        f'{table}</details>'
    )


def _addr_field(primary: str, txt: str, strip: str = "") -> str:
    val = primary
    if not val or val[0] in "1[":
        t = txt.strip()
        if t and not t.startswith("["):
            val = t
        else:
            val = ""
    if strip:
        val = val.replace(strip, "").strip()
    return val


def _details_html(title: str, rows: list[str]) -> str:
    inner = '<ol class="cl cl-box-blinking" onclick="copyList(this)">' + "".join(rows) + "</ol>"
    return (
        f'<details>'
        f'<summary class="summary-toggle"><span class="asum">'
        f'<span class="asum-arrow">&#9658;</span>'
        f"<span>{title} <strong>[&nbsp;{len(rows)}&nbsp;]</strong></span>"
        f'</span></summary>'
        f'{inner}</details>'
    )


def _realty_html(items: list, owner_id: str) -> str:
    rows = []
    for item in items:
        owners_list = _rights_owners(item)
        if owner_id not in owners_list:
            continue
        label, area = _area_str(item)
        region = _addr_field(item.get("region", ""), item.get("region_txt", ""), " область")
        district = _addr_field(item.get("district", ""), item.get("district_txt", ""), " район")
        city = _addr_field(item.get("city", ""), item.get("city_txt", ""))
        prefix = _CITY_TYPE_PREFIX.get(item.get("cityType", ""), "")
        if not city:
            city = district
            district = ""
        date = item.get("owningDate", "")
        otype = item.get("objectType", "")
        share = f", частка 1/{len(owners_list)}" if len(owners_list) > 1 else ""
        region_ex = f" {region} обл.,"
        district_ex = "" if district == "" else f" {district} р-н,"
        city_ex = f"{"" if prefix == "" else f" {prefix}"} {city},"
        rows.append(
            f"<li>{otype}, {label}: {area}, "
            f"за адресою{region_ex}{district_ex}"
            f"{city_ex} у власності з {date}{share}</li>"
        )
    if not rows:
        return ""
    return _details_html("Об'єкти нерухомості", rows)


def _vehicles_html(items: list, owner_id: str) -> str:
    rows = []
    for item in items:
        if owner_id not in _rights_owners(item):
            continue
        otype = item.get("objectType", "")
        brand = item.get("brand", "")
        model = item.get("model", "")
        year = item.get("graduationYear", "")
        date = item.get("owningDate", "")
        rows.append(f"<li>{otype} {brand} {model} {year} р.в., у власності з {date}</li>")
    if not rows:
        return ""
    return _details_html("Транспортні засоби", rows)


def _income_html(items: list, owner_id: str) -> str:
    own = [i for i in items if owner_id in _care_owners(i)]
    if not own:
        return ""
    total = sum(float(i.get("sizeIncome", 0)) for i in own)
    rows = [
        (i.get("objectType", ""), f"{_fmt(float(i.get('sizeIncome', 0)))} грн")
        for i in own
    ]
    return _expandable("Доходи:", f"{_fmt(total)} грн", rows)


def _cash_html(items: list, owner_id: str, year: int) -> str:
    own = [i for i in items if owner_id in _rights_owners(i)]
    if not own:
        return ""
    total_uah = 0.0
    all_converted = True
    for item in own:
        raw_cur = item.get("assetsCurrency", "UAH")
        rate = _nbu_rate(raw_cur, year)
        if rate is None:
            all_converted = False
        else:
            total_uah += float(item.get("sizeAssets", 0)) * rate
    if all_converted:
        total_str = f"{_fmt(total_uah)} грн"
    elif total_uah > 0:
        total_str = f"{_fmt(total_uah)} грн (курс недоступний)"
    else:
        total_str = "(курс недоступний)"
    rows = [
        (
            _CASH_TYPE_LABEL.get(i.get("objectType", ""), i.get("objectType", "")),
            f"{_fmt(float(i.get('sizeAssets', 0)))} {_currency_code(i.get('assetsCurrency', 'UAH'))}",
        )
        for i in own
    ]
    return _expandable("Грошові активи:", total_str, rows)


def _corporate_html(items: list, owner_id: str) -> str:
    own = [i for i in items if owner_id in _rights_owners(i)]
    if not own:
        return ""
    total = sum(float(i.get("cost", 0)) for i in own)
    rows = [
        (
            f"{i.get('name', '')} ({i.get('cost_percent', '')}%)",
            f"{_fmt(float(i.get('cost', 0)))} грн",
        )
        for i in own
    ]
    return _expandable("Корпоративні права:", f"{_fmt(total)} грн", rows)


def _obligations_html(items: list, owner_id: str) -> str:
    own = [i for i in items if owner_id in _care_owners(i)]
    if not own:
        return ""
    total_uah = 0.0
    all_converted = True
    for item in own:
        raw_cur = item.get("currency", "UAH")
        rate = _nbu_rate(raw_cur, 0)
        if rate is None:
            rate = 1.0 if _currency_code(raw_cur) == "UAH" else None
        if rate is None:
            all_converted = False
        else:
            total_uah += float(item.get("credit_rest", 0)) * rate
    if all_converted:
        total_str = f"{_fmt(total_uah)} грн"
    elif total_uah > 0:
        total_str = f"{_fmt(total_uah)} грн (курс недоступний)"
    else:
        total_str = "(курс недоступний)"
    rows = [
        (
            i.get("objectType", ""),
            f"{_fmt(float(i.get('credit_rest', 0)))} {_currency_code(i.get('currency', 'UAH'))}",
        )
        for i in own
    ]
    return _expandable("Фінансові зобов'язання:", total_str, rows)


def _has_any_owner_assets(
    owner_id: str,
    s3: list,
    s6: list,
    s11: list,
    s12: list,
    s8: list,
    s13: list,
) -> bool:
    return any([
        any(owner_id in _rights_owners(item) for item in s3),
        any(owner_id in _rights_owners(item) for item in s6),
        any(owner_id in _care_owners(item) for item in s11),
        any(owner_id in _rights_owners(item) for item in s12),
        any(owner_id in _rights_owners(item) for item in s8),
        any(owner_id in _care_owners(item) for item in s13),
    ])
