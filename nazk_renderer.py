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

def _safe_float(value: str) -> float:
    return float(value) if value != "None" else 0.0

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


def _format_member_name(lastname: str, firstname: str, middlename: str, previous_lastname: str = "") -> str:
    last = _proper_name(lastname)
    prev = previous_lastname.strip()
    if prev and not prev.startswith("["):
        last = f"{last} ({_proper_name(prev)})"
    return " ".join(p for p in [last, _proper_name(firstname), _proper_name(middlename)] if p)


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


def _family_ids(s1: dict, s2_items: list) -> set[str]:
    ids = {"1"}
    for m in s2_items:
        mid = str(m.get("id", ""))
        if mid:
            ids.add(mid)
    return ids


def _has_pct(r: dict) -> bool:
    pct = r.get("percentOwnership")
    return pct is not None and pct != "None"


def _family_share(rights: list[dict], fids: set[str]) -> float:
    """Частка сумарної власності родини в активі (0.0–1.0)."""
    family = [r for r in rights if str(r.get("rightBelongs", "")) in fids]
    if not family:
        return 0.0
    if any(_has_pct(r) for r in family):
        return sum(_safe_float(r["percentOwnership"]) for r in family if _has_pct(r)) / 100.0
    return len(family) / len(rights) if rights else 1.0


def _member_share(rights: list[dict], member_id: str) -> float:
    """Частка конкретного члена родини в активі (0.0–1.0)."""
    for r in rights:
        if str(r.get("rightBelongs", "")) == member_id:
            if _has_pct(r):
                return _safe_float(r["percentOwnership"]) / 100.0
            family_count = sum(1 for x in rights if str(x.get("rightBelongs", "")) != "j")
            return 1.0 / family_count if family_count else 0.0
    return 0.0


def _total_cash_uah(items: list, year: int, fids: set[str]) -> float:
    """Загальна сума грошових активів родини в UAH з урахуванням частки."""
    total = 0.0
    for item in items:
        rights = item.get("rights", [])
        share = _family_share(rights, fids)
        if share == 0.0:
            continue
        rate = _nbu_rate(item.get("assetsCurrency", "UAH"), year)
        if rate is None:
            rate = 1.0
        total += float(item.get("sizeAssets", 0)) * rate * share
    return total


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
    inner = '<ol class="cl cl-box-blinking" onclick="copyText(this, getListText)">' + "".join(rows) + "</ol>"
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
    own = [i for i in items if owner_id in _rights_owners(i)]
    if not own:
        return ""
    rows = []
    total = 0.0
    for i in own:
        raw = i.get("sizeIncome", 0)
        try:
            val = float(raw)
        except (TypeError, ValueError):
            val = 0.0
        total += val
        rows.append((i.get("objectType", ""), f"{_fmt(val)} грн"))
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


def _obligations_html(items: list, owner_id: str, year: int = 0) -> str:
    own = [i for i in items if owner_id in _rights_owners(i)]
    if not own:
        return ""
    total_uah = 0.0
    all_converted = True
    for item in own:
        raw_cur = item.get("currency", "UAH")
        rate = _nbu_rate(raw_cur, year)
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


def _normalize_income_item(item: dict) -> dict:
    """Для stored файлів до v.2.5: заповнити rights з person_who_care якщо поле відсутнє або порожнє."""
    if not item.get("rights") and item.get("person_who_care"):
        return {**item, "rights": [
            {"rightBelongs": str(p.get("person", "")), "percentOwnership": None}
            for p in item["person_who_care"] if p.get("person")
        ]}
    return item


def _realty_address_key(item: dict) -> str:
    region = _addr_field(item.get("region", ""), item.get("region_txt", ""), " область")
    district = _addr_field(item.get("district", ""), item.get("district_txt", ""), " район")
    city = _addr_field(item.get("city", ""), item.get("city_txt", ""))
    if not city:
        city = district
        district = ""
    return "|".join([region, district, city])


def _realty_key(item: dict) -> tuple:
    """Ключ порівняння об'єкта нерухомості (v.2.11): тип + площа + адреса + дата набуття права."""
    return (
        item.get("objectType", ""),
        str(item.get("totalArea", "")).strip(),
        _realty_address_key(item),
        item.get("owningDate", ""),
    )


def _vehicle_key(item: dict) -> tuple:
    """Ключ порівняння транспортного засобу (v.2.11): марка + модель + рік виробництва + дата набуття права."""
    return (
        item.get("brand", ""),
        item.get("model", ""),
        item.get("graduationYear", ""),
        item.get("owningDate", ""),
    )


def _realty_keys_for_family(items: list, fids: set[str]) -> set[tuple]:
    return {_realty_key(i) for i in items if _family_share(i.get("rights", []), fids) > 0}


def _vehicle_keys_for_family(items: list, fids: set[str]) -> set[tuple]:
    return {_vehicle_key(i) for i in items if _family_share(i.get("rights", []), fids) > 0}


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
        any(owner_id in _rights_owners(item) for item in s11),
        any(owner_id in _rights_owners(item) for item in s12),
        any(owner_id in _rights_owners(item) for item in s8),
        any(owner_id in _rights_owners(item) for item in s13),
    ])


# ── "Загальна" вкладка ────────────────────────────────────────────────────────

_DOC_TYPE_LABELS: dict[int, str] = {
    1: "Декларація",
    2: "Повідомлення про суттєві зміни в майновому стані",
    3: "Виправлена декларація",
}


def _doc_kind_label(doc: dict) -> str:
    """Текстовий лейбл виду декларації: 'data.step_0.data.declaration_type' + doc_type."""
    s0_data = doc.get("data", {}).get("step_0", {}).get("data", {})
    kind = s0_data.get("declaration_type", "")
    doc_type = _DOC_TYPE_LABELS.get(doc.get("type"), "")
    if kind and doc_type:
        return f"{kind} — {doc_type}"
    return kind or doc_type


def _summary_row(label: str, value_str: str, cls: str = "") -> str:
    cls_attr = f' class="{cls}"' if cls else ""
    return (
        f'<div{cls_attr} style="display:flex;justify-content:space-between;'
        f'border-bottom:1px solid #eee">'
        f'<span>{label}</span><strong>{value_str}</strong></div>'
    )


def _general_numeric_html(
    title: str,
    items: list,
    fids: set[str],
    owners: dict[str, str],
    year: int,
    amount_fn,          # (item, member_id) -> float
    fmt_fn,             # (member_total) -> str
    currency_fn=None,   # (item) -> str | None, для деталі без конвертації
) -> str:
    """Агрегат числового активу: загальна сума + деталізація по члену родини."""
    member_totals: dict[str, float] = {mid: 0.0 for mid in owners}
    has_data = False
    for item in items:
        rights = item.get("rights", [])
        for mid in owners:
            share = _member_share(rights, mid)
            if share > 0:
                val = amount_fn(item, mid, share)
                member_totals[mid] += val
                has_data = True
    if not has_data:
        return ""
    total = sum(member_totals.values())
    rows = [
        (owners[mid], fmt_fn(member_totals[mid]))
        for mid in owners
        if member_totals[mid] > 0
    ]
    return _expandable(title, fmt_fn(total), rows)


def _general_income_html(items: list, fids: set[str], owners: dict[str, str]) -> str:
    def amount(item, mid, share):
        raw = item.get("sizeIncome", 0)
        try:
            return float(raw) * share
        except (TypeError, ValueError):
            return 0.0

    return _general_numeric_html(
        "Доходи:", items, fids, owners, 0,
        amount_fn=amount,
        fmt_fn=lambda v: f"{_fmt(v)} грн",
    )


def _general_cash_html(items: list, fids: set[str], owners: dict[str, str], year: int) -> str:
    def amount(item, mid, share):
        rate = _nbu_rate(item.get("assetsCurrency", "UAH"), year)
        if rate is None:
            rate = 1.0
        try:
            return float(item.get("sizeAssets", 0)) * rate * share
        except (TypeError, ValueError):
            return 0.0

    return _general_numeric_html(
        "Грошові активи:", items, fids, owners, year,
        amount_fn=amount,
        fmt_fn=lambda v: f"{_fmt(v)} грн",
    )


def _general_corporate_html(items: list, fids: set[str], owners: dict[str, str]) -> str:
    def amount(item, mid, share):
        try:
            return float(item.get("cost", 0)) * share
        except (TypeError, ValueError):
            return 0.0

    return _general_numeric_html(
        "Корпоративні права:", items, fids, owners, 0,
        amount_fn=amount,
        fmt_fn=lambda v: f"{_fmt(v)} грн",
    )


def _general_obligations_html(items: list, fids: set[str], owners: dict[str, str], year: int) -> str:
    def amount(item, mid, share):
        rate = _nbu_rate(item.get("currency", "UAH"), year)
        if rate is None:
            rate = 1.0
        try:
            return float(item.get("credit_rest", 0)) * rate * share
        except (TypeError, ValueError):
            return 0.0

    return _general_numeric_html(
        "Фінансові зобов'язання:", items, fids, owners, year,
        amount_fn=amount,
        fmt_fn=lambda v: f"{_fmt(v)} грн",
    )


def general_tab_html(
    doc: dict,
    savings: float,
    owners: dict[str, str],
) -> str:
    """HTML-вміст вкладки 'Загальна'."""
    steps = doc.get("data", {})
    doc_id = doc.get("id", "")
    year: int = doc.get("declaration_year", 0)
    s1 = steps.get("step_1", {})
    s2 = _step_data(steps.get("step_2"))
    s3 = _step_data(steps.get("step_3"))
    s6 = _step_data(steps.get("step_6"))
    s8 = _step_data(steps.get("step_8"))
    s11 = _step_data(steps.get("step_11"))
    s12 = _step_data(steps.get("step_12"))
    s13 = _step_data(steps.get("step_13"))

    fids = _family_ids(s1, s2)
    s11 = [_normalize_income_item(i) for i in s11]
    s13 = [_normalize_income_item(i) for i in s13]

    total_income = sum(
        (lambda raw: float(raw) if _try_float(raw) else 0.0)(i.get("sizeIncome", 0))
        for i in s11
        if _family_share(i.get("rights", []), fids) > 0
    )
    delta = total_income - savings

    parts: list[str] = []

    # ── вид/тип декларації першим рядком ──────────────────────────────────────
    kind_label = _doc_kind_label(doc)
    if kind_label:
        parts.append(f"<div class='doc-label'><b>{kind_label}</b></div>")

    # ── метрики першими ───────────────────────────────────────────────────────
    parts.append(_summary_row("Заощадження за останній рік:", f"{_fmt(savings)} грн", "general row savings"))
    parts.append(_summary_row("Фінансова дельта:", f"{_fmt(delta)} грн", "general row delta"))
    parts.append('<div style="margin-top:10px"></div>')

    # ── нерухомість (всі об'єкти родини, дедублікація не потрібна — кожен унікальний) ──
    realty_rows = []
    for item in s3:
        rights = item.get("rights", [])
        if _family_share(rights, fids) == 0.0:
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
        region_ex = f" {region} обл.," if region else ""
        district_ex = "" if not district else f" {district} р-н,"
        city_ex = f"{'  ' if not prefix else f' {prefix}'} {city}," if city else ""
        realty_rows.append(f"<li>{otype}, {label}: {area}, за адресою{region_ex}{district_ex}{city_ex} у власності з {date}</li>")
    if realty_rows:
        parts.append(_details_html("Об'єкти нерухомості", realty_rows))

    # ── транспорт ─────────────────────────────────────────────────────────────
    vehicle_rows = []
    for item in s6:
        v_rights = item.get("rights", [])
        if _family_share(v_rights, fids) == 0.0:
            continue
        otype = item.get("objectType", "")
        brand = item.get("brand", "")
        model = item.get("model", "")
        yr = item.get("graduationYear", "")
        date = item.get("owningDate", "")
        vehicle_rows.append(f"<li>{otype} {brand} {model} {yr} р.в., у власності з {date}</li>")
    if vehicle_rows:
        parts.append(_details_html("Транспортні засоби", vehicle_rows))

    # ── числові агрегати по членам родини ─────────────────────────────────────
    income_h = _general_income_html(s11, fids, owners)
    if income_h:
        parts.append(income_h)

    cash_h = _general_cash_html(s12, fids, owners, year)
    if cash_h:
        parts.append(cash_h)

    corp_h = _general_corporate_html(s8, fids, owners)
    if corp_h:
        parts.append(corp_h)

    obl_h = _general_obligations_html(s13, fids, owners, year)
    if obl_h:
        parts.append(obl_h)

    if not any([realty_rows, vehicle_rows, income_h, cash_h, corp_h, obl_h]):
        parts.append('<p>Немає активів</p>')

    parts.append(f"<div class='doc-id'>[ doc-id: <span onclick='copyText(this)'>{doc_id}</span> ]</div>")

    return "".join(parts)


def _try_float(val) -> bool:
    try:
        float(val)
        return True
    except (TypeError, ValueError):
        return False


def _years_to_ranges(years: list[int]) -> str:
    sorted_years = sorted(set(y for y in years if y))
    if not sorted_years:
        return ""
    ranges: list[str] = []
    start = sorted_years[0]
    prev = sorted_years[0]
    for y in sorted_years[1:]:
        if y == prev + 1:
            prev = y
        else:
            ranges.append(f"{start}–{prev}" if start != prev else str(start))
            start = y
            prev = y
    ranges.append(f"{start}–{prev}" if start != prev else str(start))
    return ", ".join(ranges)


def _collect_family_history(sorted_docs: list[dict]) -> list[tuple[str, str, str]]:
    """Unique family members across all years → (relation, fullname, year_range).
    sorted_docs is newest-first; order in result mirrors first-appearance (newest first)."""
    members: dict[str, dict] = {}
    for doc in sorted_docs:
        year = doc.get("declaration_year", 0)
        if not year:
            continue
        s2 = _step_data(doc.get("data", {}).get("step_2"))
        for m in s2:
            key = "|".join([
                m.get("lastname", "").lower().strip(),
                m.get("firstname", "").lower().strip(),
                m.get("middlename", "").lower().strip(),
            ])
            if not any(k for k in key.split("|")):
                continue
            if key not in members:
                members[key] = {
                    "lastname": m.get("lastname", ""),
                    "firstname": m.get("firstname", ""),
                    "middlename": m.get("middlename", ""),
                    "subjectRelation": m.get("subjectRelation", ""),
                    "previous_lastname": m.get("previous_lastname", ""),
                    "years": [],
                }
            elif not members[key]["previous_lastname"]:
                members[key]["previous_lastname"] = m.get("previous_lastname", "")
            members[key]["years"].append(year)

    return [
        (
            info["subjectRelation"],
            _format_member_name(
                info["lastname"], info["firstname"], info["middlename"],
                info["previous_lastname"],
            ),
            _years_to_ranges(info["years"]),
        )
        for info in members.values()
    ]


def _collect_career_history(sorted_docs: list[dict]) -> list[dict]:
    """Career history merged by consecutive same workplace+position; output oldest-first."""
    raw_entries = []
    for doc in reversed(sorted_docs):
        year = doc.get("declaration_year", 0)
        if not year:
            continue
        d1 = doc.get("data", {}).get("step_1", {}).get("data", {})
        wp = d1.get("workPlace", "").strip()
        wpost = d1.get("workPost", "").strip()
        if wp or wpost:
            raw_entries.append({"year": year, "workPlace": wp, "workPost": wpost})

    merged: list[dict] = []
    for entry in raw_entries:
        if (
            merged
            and merged[-1]["workPlace"] == entry["workPlace"]
            and merged[-1]["workPost"] == entry["workPost"]
            and entry["year"] == merged[-1]["end_year"] + 1
        ):
            merged[-1]["end_year"] = entry["year"]
        else:
            merged.append({
                "start_year": entry["year"],
                "end_year": entry["year"],
                "workPlace": entry["workPlace"],
                "workPost": entry["workPost"],
            })
    return merged
