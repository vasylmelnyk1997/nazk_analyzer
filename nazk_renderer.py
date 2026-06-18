from __future__ import annotations

import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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

_CSS = """\
<style>
*{box-sizing:border-box}
body{font-family:Arial,sans-serif;font-size:14px;color:#222;max-width:1000px;margin:0 auto;padding:16px}
h2{font-size:15px;font-weight:bold;border-bottom:1px solid #ccc;padding-bottom:4px;margin-top:24px}
h3{font-size:13px;font-weight:bold;margin:12px 0 4px}
p{margin:4px 0}
table{border-collapse:collapse;width:100%}
th,td{border:1px solid #ccc;padding:5px 10px;text-align:left}
th{background:#f0f0f0}
.tabs{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:-1px}
.tab-btn{padding:5px 12px;border:1px solid #ccc;background:#f5f5f5;cursor:pointer;
         border-radius:4px 4px 0 0;border-bottom:none;font-size:13px}
.tab-btn.active{background:#fff;font-weight:bold}
.tab-panel{display:none;border:1px solid #ccc;padding:12px}
.tab-panel.active{display:block}
details{margin:8px 0}
summary{cursor:pointer;user-select:none}
summary.asset-summary{display:flex;align-items:center;justify-content:space-between;gap:12px}
details ol{margin:6px 0 6px 18px;padding:0}
details li{margin:3px 0}
.stub{color:#999;font-style:italic;margin:6px 0}
</style>"""

_JS = """\
<script>
function showTab(id){
  var g=document.querySelectorAll('.tab-panel'),b=document.querySelectorAll('.tab-btn');
  for(var i=0;i<g.length;i++){g[i].classList.remove('active');b[i].classList.remove('active')}
  document.getElementById(id).classList.add('active');
  document.querySelector('[data-tab="'+id+'"]').classList.add('active');
}
</script>"""


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
    return f"{value:,.0f}".replace(",", " ")


def _proper_name(raw: str) -> str:
    parts = [part.strip() for part in raw.split() if part.strip()]
    return " ".join(part.capitalize() for part in parts)


def _owner_name(person_id: str, owners: dict[str, str]) -> str:
    return owners.get(person_id, person_id)


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
        return "загальна площа", f"{val:g} м²"
    ha = val / 10_000
    return "площа", f"{ha:g} га"


# ── section renderers ──────────────────────────────────────────────────────────

def _realty_html(items: list, owner_id: str) -> str:
    rows = []
    n = 1
    for item in items:
        owners_list = _rights_owners(item)
        if owner_id not in owners_list:
            continue
        label, area = _area_str(item)
        region = item.get("region", "")
        district = item.get("district", "")
        city = item.get("city", "")
        prefix = _CITY_TYPE_PREFIX.get(item.get("cityType", ""), "")
        date = item.get("owningDate", "")
        otype = item.get("objectType", "")
        share = f", частка 1/{len(owners_list)}" if len(owners_list) > 1 else ""
        rows.append(
            f"<li>{n}. {otype}, {label}: {area}, "
            f"за адресою {region} обл., {district} р-н, "
            f"{prefix} {city}, у власності з {date}{share}</li>"
        )
        n += 1
    if not rows:
        return ""
    return "<h3>Об'єкти нерухомості</h3><ol>" + "".join(rows) + "</ol>"


def _vehicles_html(items: list, owner_id: str) -> str:
    rows = []
    n = 1
    for item in items:
        if owner_id not in _rights_owners(item):
            continue
        otype = item.get("objectType", "")
        brand = item.get("brand", "")
        model = item.get("model", "")
        year = item.get("graduationYear", "")
        date = item.get("owningDate", "")
        rows.append(f"<li>{n}. {otype} {brand} {model} {year} р.в., у власності з {date}</li>")
        n += 1
    if not rows:
        return ""
    return "<h3>Транспортні засоби</h3><ol>" + "".join(rows) + "</ol>"


def _income_html(items: list, owner_id: str) -> str:
    own = [i for i in items if owner_id in _care_owners(i)]
    if not own:
        return ""
    total = sum(float(i.get("sizeIncome", 0)) for i in own)
    detail = "".join(
        f"<li>{n}. {i.get('objectType','')}: {_fmt(float(i.get('sizeIncome',0)))} грн</li>"
        for n, i in enumerate(own, 1)
    )
    return (
        f"<details><summary class=\"asset-summary\"><span>Доходи:</span>"
        f"<strong>{_fmt(total)} грн</strong></summary><ol>{detail}</ol></details>"
    )


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
    total_str = (_fmt(total_uah) + " грн") if all_converted else "сума н/д"
    detail = "".join(
        f"<li>{n}. {_CASH_TYPE_LABEL.get(i.get('objectType',''), i.get('objectType',''))}: "
        f"{_fmt(float(i.get('sizeAssets',0)))} {_currency_code(i.get('assetsCurrency','UAH'))}</li>"
        for n, i in enumerate(own, 1)
    )
    return (
        f"<details><summary class=\"asset-summary\"><span>Грошові активи:</span>"
        f"<strong>{total_str}</strong></summary><ol>{detail}</ol></details>"
    )


def _corporate_html(items: list, owner_id: str) -> str:
    own = [i for i in items if owner_id in _rights_owners(i)]
    if not own:
        return ""
    total = sum(float(i.get("cost", 0)) for i in own)
    detail = "".join(
        f"<li>{n}. {i.get('name','')}"
        f" ({i.get('cost_percent','')}%): {_fmt(float(i.get('cost',0)))} грн</li>"
        for n, i in enumerate(own, 1)
    )
    return (
        f"<details><summary class=\"asset-summary\"><span>Корпоративні права:</span>"
        f"<strong>{_fmt(total)} грн</strong></summary><ol>{detail}</ol></details>"
    )


def _obligations_html(items: list, owner_id: str) -> str:
    own = [i for i in items if owner_id in _care_owners(i)]
    if not own:
        return ""
    total_uah = 0.0
    all_converted = True
    for item in own:
        raw_cur = item.get("currency", "UAH")
        rate = _nbu_rate(raw_cur, 0)  # obligations use nominal year-end rate
        if rate is None:
            # fallback: try to parse year from context or just treat as UAH
            rate = 1.0 if _currency_code(raw_cur) == "UAH" else None
        if rate is None:
            all_converted = False
        else:
            total_uah += float(item.get("credit_rest", 0)) * rate
    total_str = (_fmt(total_uah) + " грн") if all_converted else "сума н/д"
    detail = "".join(
        f"<li>{n}. {i.get('objectType','')}: "
        f"{_fmt(float(i.get('credit_rest',0)))} {_currency_code(i.get('currency','UAH'))}</li>"
        for n, i in enumerate(own, 1)
    )
    return (
        f"<details><summary class=\"asset-summary\"><span>Фінансові зобов'язання:</span>"
        f"<strong>{total_str}</strong></summary><ol>{detail}</ol></details>"
    )


def _has_any_owner_assets(
    owner_id: str,
    s3: list,
    s6: list,
    s11: list,
    s12: list,
    s8: list,
    s13: list,
) -> bool:
    return any(
        [
            any(owner_id in _rights_owners(item) for item in s3),
            any(owner_id in _rights_owners(item) for item in s6),
            any(owner_id in _care_owners(item) for item in s11),
            any(owner_id in _rights_owners(item) for item in s12),
            any(owner_id in _rights_owners(item) for item in s8),
            any(owner_id in _care_owners(item) for item in s13),
        ]
    )


# ── main renderer ──────────────────────────────────────────────────────────────

def render_declaration(data: dict) -> str:
    steps = data.get("data", {})

    s0 = steps.get("step_0", {})
    s1 = steps.get("step_1", {})
    s2 = _step_data(steps.get("step_2"))
    s3 = _step_data(steps.get("step_3"))
    s6 = _step_data(steps.get("step_6"))
    s8 = _step_data(steps.get("step_8"))
    s11 = _step_data(steps.get("step_11"))
    s12 = _step_data(steps.get("step_12"))
    s13 = _step_data(steps.get("step_13"))

    year: int = s0.get("data", {}).get("declaration_year", 2024)
    owners = _build_owners(s1, s2)
    d1 = s1.get("data", {})

    # ── block 1: declarant ────────────────────────────────────────────────────
    full_name = _proper_name(
        f"{d1.get('lastname','')} {d1.get('firstname','')} {d1.get('middlename','')}"
    )
    b1 = (
        "<section>"
        "<h2>Інформація про декларанта</h2>"
        f"<p><b>ПІБ:</b> {full_name}</p>"
        f"<p><b>Місце роботи:</b> {d1.get('workPlace','')}</p>"
        f"<p><b>Посада:</b> {d1.get('workPost','')}</p>"
        "</section>"
    )

    # ── block 2: family ───────────────────────────────────────────────────────
    family_rows = []
    for m in s2:
        family_name = _proper_name(
            f"{m.get('lastname', '')} {m.get('firstname', '')} {m.get('middlename', '')}"
        )
        family_rows.append(
            f"<tr><td>{m.get('subjectRelation', '')}</td><td>{family_name}</td></tr>"
        )
    rows = "".join(family_rows)
    family_body = (
        f"<table><thead><tr><th>Родинний зв'язок</th><th>ПІБ</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        if rows else "<p>Немає відомостей</p>"
    )
    b2 = f"<section><h2>Склад сім'ї</h2>{family_body}</section>"

    # ── block 3: assets per owner (tabs) ─────────────────────────────────────
    buttons: list[str] = []
    panels: list[str] = []

    filtered_owners = {
        oid: oname
        for oid, oname in owners.items()
        if _has_any_owner_assets(oid, s3, s6, s11, s12, s8, s13)
    }

    for i, (oid, oname) in enumerate(filtered_owners.items()):
        tid = f"tab-{oid}"
        active = " active" if i == 0 else ""
        buttons.append(
            f'<button class="tab-btn{active}" data-tab="{tid}" onclick="showTab(\'{tid}\')">{oname}</button>'
        )
        parts = [
            _realty_html(s3, oid),
            _vehicles_html(s6, oid),
            _income_html(s11, oid),
            _cash_html(s12, oid, year),
            _corporate_html(s8, oid),
            _obligations_html(s13, oid),
            '<p class="stub">Цінні папери: не застосовується</p>',
            '<p class="stub">Видатки: не застосовується</p>',
        ]
        content = "".join(p for p in parts if p)
        panels.append(f'<div id="{tid}" class="tab-panel{active}">{content or "<p>Немає активів</p>"}</div>')

    b3 = (
        "<section>"
        "<h2>Активи</h2>"
        f'<div class="tabs">{"".join(buttons)}</div>'
        + "".join(panels)
        + "</section>"
    )

    return (
        "<!DOCTYPE html>"
        "<html lang='uk'>"
        f"<head><meta charset='utf-8'><title>Декларація — {full_name}</title>{_CSS}</head>"
        f"<body>{b1}{b2}{b3}{_JS}</body>"
        "</html>"
    )


if __name__ == "__main__":
    data_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        "Підкапка_Костянтин_Васильович-2025-повна.json",
    )
    with open(data_path, encoding="utf-8-sig") as f:
        declaration = json.load(f)

    html = render_declaration(declaration)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Saved: {out_path}")
