from __future__ import annotations

import os

from nazk_renderer import (
    _build_owners,
    _cash_html,
    _collect_career_history,
    _collect_family_history,
    _corporate_html,
    _family_ids,
    _has_any_owner_assets,
    _income_html,
    _normalize_income_item,
    _obligations_html,
    _owner_name_keys,
    _proper_name,
    _realty_html,
    _realty_keys_for_family,
    _realty_keys_for_owner,
    _step_data,
    _total_cash_uah,
    _vehicle_keys_for_family,
    _vehicle_keys_for_owner,
    _vehicles_html,
    general_tab_html,
)

with open(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons.svg.xml"),
    encoding="utf-8",
) as _f:
    _ICONS_SVG = _f.read()

_CSS = """\
<style>
*{box-sizing:border-box}
body{font-family:Arial,sans-serif;font-size:14px;color:#222;max-width:1100px;margin:0 auto;padding:16px}
h2{font-size:15px;font-weight:bold;border-bottom:1px solid #ccc;padding-bottom:4px;margin-top:24px}
.user-declarant-id{font-size:75%;color:#777}
h3{font-size:13px;font-weight:bold;margin:12px 0 4px}
p{margin:4px 0}
table{border-collapse:collapse;width:100%}
th,td{border:1px solid #ccc;padding:5px 10px;text-align:left}
th{background:#f0f0f0}
.tab-career .col-1{width:10%}
.tab-career .col-2{width:60%}
.tab-family .col-1{width:10%}
.tab-family .col-2{width:20%}

/* year tabs (outer, vertical — left column) */
.year-tabs{display:flex;border:1px solid #ccc;min-height:200px}
.year-tab-btns{display:flex;flex-direction:column;min-width:72px;border-right:1px solid #ccc;
               background:#fafafa;flex-shrink:0}
.year-btn{padding:10px 14px;border:none;background:transparent;cursor:pointer;text-align:left;
          font-size:14px;font-weight:bold;border-left:3px solid transparent;white-space:nowrap}
.year-btn:hover{background:#f0f0f0}
.year-btn.active{background:#fff;border-left-color:#0066cc}
.year-change-marker{display:inline-flex;align-items:center;gap:1px;margin-left:4px;vertical-align:middle}
.chg-icon{width:14px;height:14px;stroke-width:2.5;vertical-align:middle}
.chg-plus{color:#1a9d43}
.chg-minus{color:#d43c3c}
.year-panel{display:none;flex:1;flex-direction:column}
.year-panel.active{display:flex}

/* owner tabs (inner, horizontal — top of panel) */
.owner-tab-btns{display:flex;flex-wrap:wrap;gap:4px;padding:8px 12px 0;border-bottom:1px solid #ccc;
                flex-shrink:0;margin-bottom:-1px}
.owner-btn{padding:5px 12px;border:1px solid #ccc;background:#f5f5f5;cursor:pointer;
           border-radius:4px 4px 0 0;border-bottom:none;font-size:13px}
.owner-btn:hover{background:#eee}
.owner-btn.active{background:#fff;font-weight:bold;border-bottom:1px solid #fff;position:relative;z-index:1;margin-bottom:-1px}
.owner-panels{flex:1;padding:12px;overflow:auto;display:grid}
.owner-panel{display:none;position:relative}
.owner-panel.active{display:block}
.doc-id{font-size:75%;color:#999;width:100%;text-align:right;position:absolute;bottom:0;right:0}
.doc-label{padding:8px}

/* assets */
details{margin:16px 0;border:1px solid #eee;padding:8px;border-radius:4px}
summary.summary-toggle{cursor:pointer;user-select:none;list-style:none}
summary.summary-toggle::-webkit-details-marker{display:none}
.asum{display:inline-flex;align-items:baseline;gap:6px}
.asum-arrow{font-size:10px;transition:transform .15s;display:inline-block}
details[open] .asum-arrow{transform:rotate(90deg)}
table.dt{border-collapse:collapse;width:auto;margin:6px 0 4px 18px}
table.dt td{border:none;padding:1px 0;vertical-align:top}
table.dt .dl{white-space:nowrap;text-align:left}
table.dt .ds{width:15px}
table.dt .da{white-space:nowrap;text-align:right}
.stub{color:#999;font-style:italic;margin:6px 0}
.cl-list{margin:6px 0 4px 18px}
.cl-list .row-item{margin:3px 0}
.cl-list.cl{cursor:pointer;position:relative}
.cl-list.cl:hover::after{content:'клікніть щоб скопіювати';position:absolute;top:-22px;left:0;
  background:#333;color:#fff;font-size:11px;padding:2px 7px;border-radius:3px;
  white-space:nowrap;pointer-events:none}
.cl-box-blinking{background-color: transparent}
.chg-removed{color:#d43c3c}
.chg-added{color:#1a9d43}
.animate-blink{animation: blink 0.5s ease-in-out}
@keyframes blink{0%{background-color: transparent}
50%{background-color: #d1dee9}
100%{background-color: transparent}}

/* "Загальна" вкладка — метрики */
.general.row{width:33%;margin:4px 0;padding:6px 8px;border-radius:4px;font-size:13px}
.general.row.savings{background:#f0f7ff}
.general.row.delta{background:#f5fff0}

</style>"""

_JS = """\
<script>
function showYearTab(yearId) {
  document.querySelectorAll('.year-panel').forEach(function(p){p.classList.remove('active')});
  document.querySelectorAll('.year-btn').forEach(function(b){b.classList.remove('active')});
  document.getElementById(yearId).classList.add('active');
  document.querySelector('[data-year="'+yearId+'"]').classList.add('active');
}
function showOwnerTab(yearId, ownerId) {
  var yp = document.getElementById(yearId);
  yp.querySelectorAll('.owner-panel').forEach(function(p){p.classList.remove('active')});
  yp.querySelectorAll('.owner-btn').forEach(function(b){b.classList.remove('active')});
  document.getElementById(ownerId).classList.add('active');
  yp.querySelector('[data-tab="'+ownerId+'"]').classList.add('active');
}
function getListText(ol){
  return Array.from(ol.querySelectorAll('.row-item:not(.chg-removed)')).map(function(li){
    return li.textContent.trim();
  }).join('\\n');
}
function getElemText(elem){
  return elem.innerText.trim();
}
function copyText(elem, fGetText){
  if(typeof fGetText !== 'function') fGetText = getElemText;
  navigator.clipboard.writeText(fGetText(elem));
  elem.addEventListener('animationend',()=>elem.classList.remove('animate-blink'),{once:true});
  elem.classList.add('animate-blink');
}
</script>"""


def _sort_owners(
    owners: dict[str, str], s2_items: list
) -> list[tuple[str, str]]:
    spouse_ids = {
        str(m.get("id"))
        for m in s2_items
        if m.get("subjectRelation", "").lower() in ("дружина", "чоловік")
    }

    def rank(item: tuple[str, str]) -> int:
        oid = item[0]
        if oid == "1":
            return 0
        if oid in spouse_ids:
            return 1
        return 2

    return sorted(owners.items(), key=rank)


def _compute_savings(sorted_docs: list[dict]) -> dict[int, float]:
    """Заощадження = грошові активи поточного року - попереднього.
    Обхід від найстарішого до найновішого; пропуск у роках → prev = 0.
    sorted_docs відсортовані від більшого до меншого."""
    result: dict[int, float] = {}
    prev_cash = 0.0
    prev_year = 0
    for doc in reversed(sorted_docs):
        year: int = doc.get("declaration_year", 0)
        steps = doc.get("data", {})
        s1 = steps.get("step_1", {})
        s2 = _step_data(steps.get("step_2"))
        s12 = _step_data(steps.get("step_12"))
        fids = _family_ids(s1, s2)
        cash = _total_cash_uah(s12, year, fids)
        if prev_year != 0 and year != prev_year + 1:
            prev_cash = 0.0
        result[year] = cash - prev_cash
        prev_cash = cash
        prev_year = year
    return result


def _asset_family_keys(doc: dict) -> tuple[set[tuple], set[tuple]]:
    steps = doc.get("data", {})
    s1 = steps.get("step_1", {})
    s2 = _step_data(steps.get("step_2"))
    fids = _family_ids(s1, s2)
    s3 = _step_data(steps.get("step_3"))
    s6 = _step_data(steps.get("step_6"))
    return _realty_keys_for_family(s3, fids), _vehicle_keys_for_family(s6, fids)


def _compute_asset_changes(sorted_docs: list[dict]) -> dict[int, dict[str, bool]]:
    """Позначки змін майнового стану (v.2.11): порівняння між сусідніми фактично поданими
    роками (сусідні елементи sorted_docs), агреговано по всій родині. Найстарший
    (і єдиний) рік порівнювати нема з чим — маркер не формується."""
    changes: dict[int, dict[str, bool]] = {}
    for i in range(len(sorted_docs) - 1):
        newer, older = sorted_docs[i], sorted_docs[i + 1]
        newer_year = newer.get("declaration_year", 0)
        newer_realty, newer_vehicle = _asset_family_keys(newer)
        older_realty, older_vehicle = _asset_family_keys(older)
        changes[newer_year] = {
            "realty_added": bool(newer_realty - older_realty),
            "realty_removed": bool(older_realty - newer_realty),
            "vehicle_added": bool(newer_vehicle - older_vehicle),
            "vehicle_removed": bool(older_vehicle - newer_vehicle),
        }
    return changes


def _compute_owner_asset_changes(
    sorted_docs: list[dict],
) -> dict[int, dict[str, dict[str, bool]]]:
    """Позначки змін майнового стану по власниках (v.2.12): так само як _compute_asset_changes,
    але окремо для кожного власника. Власники зіставляються між суміжними роками за ПІБ
    (без previous_lastname). Частка власника оцінюється як булева ознака (є/немає) —
    зміна відсотка володіння без повної появи/зникнення частки не вважається зміною.
    Власник, що вперше з'явився в родині цього року — порівнювати нема з чим."""
    changes: dict[int, dict[str, dict[str, bool]]] = {}
    for i in range(len(sorted_docs) - 1):
        newer, older = sorted_docs[i], sorted_docs[i + 1]
        newer_year = newer.get("declaration_year", 0)
        newer_name_keys = _owner_name_keys(newer)
        older_by_name = {v: k for k, v in _owner_name_keys(older).items()}

        n_s3 = _step_data(newer.get("data", {}).get("step_3"))
        n_s6 = _step_data(newer.get("data", {}).get("step_6"))
        o_s3 = _step_data(older.get("data", {}).get("step_3"))
        o_s6 = _step_data(older.get("data", {}).get("step_6"))

        owner_changes: dict[str, dict[str, bool]] = {}
        for oid, name_key in newer_name_keys.items():
            older_oid = older_by_name.get(name_key)
            if older_oid is None:
                continue
            newer_realty = _realty_keys_for_owner(n_s3, oid)
            older_realty = _realty_keys_for_owner(o_s3, older_oid)
            newer_vehicle = _vehicle_keys_for_owner(n_s6, oid)
            older_vehicle = _vehicle_keys_for_owner(o_s6, older_oid)
            flags = {
                "realty_added": bool(newer_realty - older_realty),
                "realty_removed": bool(older_realty - newer_realty),
                "vehicle_added": bool(newer_vehicle - older_vehicle),
                "vehicle_removed": bool(older_vehicle - newer_vehicle),
            }
            if any(flags.values()):
                owner_changes[oid] = flags
        changes[newer_year] = owner_changes
    return changes


def _change_marker_html(flags: dict[str, bool] | None) -> str:
    if not flags or not any(flags.values()):
        return ""
    parts: list[str] = []
    if flags["realty_added"] or flags["realty_removed"]:
        parts.append('<svg class="chg-icon"><use href="#house"/></svg>')
        if flags["realty_added"]:
            parts.append('<svg class="chg-icon chg-plus"><use href="#plus"/></svg>')
        if flags["realty_removed"]:
            parts.append('<svg class="chg-icon chg-minus"><use href="#minus"/></svg>')
    if flags["vehicle_added"] or flags["vehicle_removed"]:
        parts.append('<svg class="chg-icon"><use href="#car"/></svg>')
        if flags["vehicle_added"]:
            parts.append('<svg class="chg-icon chg-plus"><use href="#plus"/></svg>')
        if flags["vehicle_removed"]:
            parts.append('<svg class="chg-icon chg-minus"><use href="#minus"/></svg>')
    return f'<span class="year-change-marker">{"".join(parts)}</span>'


def _render_owner_assets(
    doc: dict,
    prev_doc: dict | None,
    year_tab_id: str,
    savings: float,
    owner_changes: dict[str, dict[str, bool]] | None = None,
) -> str:
    steps = doc.get("data", {})
    year: int = doc.get("declaration_year", 0)
    s1 = steps.get("step_1", {})
    s2 = _step_data(steps.get("step_2"))
    s3 = _step_data(steps.get("step_3"))
    s6 = _step_data(steps.get("step_6"))
    s8 = _step_data(steps.get("step_8"))
    s11 = _step_data(steps.get("step_11"))
    s12 = _step_data(steps.get("step_12"))
    s13 = _step_data(steps.get("step_13"))

    s11 = [_normalize_income_item(i) for i in s11]
    s13 = [_normalize_income_item(i) for i in s13]

    owners = _build_owners(s1, s2)
    sorted_owners = _sort_owners(owners, s2)
    filtered = [
        (oid, oname)
        for oid, oname in sorted_owners
        if _has_any_owner_assets(oid, s3, s6, s11, s12, s8, s13)
    ]

    # ── v.2.13: дані попереднього суміжного року для порівняння по власниках ──
    prev_s3: list | None = None
    prev_s6: list | None = None
    prev_owner_by_name: dict[str, str] = {}
    if prev_doc is not None:
        prev_s3 = _step_data(prev_doc.get("data", {}).get("step_3"))
        prev_s6 = _step_data(prev_doc.get("data", {}).get("step_6"))
        prev_owner_by_name = {v: k for k, v in _owner_name_keys(prev_doc).items()}
    name_keys_now = _owner_name_keys(doc)

    buttons: list[str] = []
    panels: list[str] = []

    # ── "Загальна" — завжди перша ─────────────────────────────────────────────
    gen_tid = f"o-{year_tab_id}-general"
    # "Загальна" активна, якщо власники відсутні; інакше — не активна
    buttons.append(
        f'<button class="owner-btn active" data-tab="{gen_tid}"'
        f' onclick="showOwnerTab(\'{year_tab_id}\',\'{gen_tid}\')">Загальна</button>'
    )
    # Для general_tab_html потрібен впорядкований dict власників
    ordered_owners: dict[str, str] = {oid: oname for oid, oname in sorted_owners}
    gen_content = general_tab_html(doc, prev_doc, savings, ordered_owners)
    panels.append(
        f'<div id="{gen_tid}" class="owner-panel active">{gen_content}</div>'
    )

    # ── вкладки по власникам ──────────────────────────────────────────────────
    if len(filtered) > 1:
        for (oid, oname) in filtered:
            tid = f"o-{year_tab_id}-{oid}"
            marker_html = _change_marker_html(
                (owner_changes or {}).get(oid)
            )
            buttons.append(
                f'<button class="owner-btn" data-tab="{tid}"'
                f' onclick="showOwnerTab(\'{year_tab_id}\',\'{tid}\')">{oname}{marker_html}</button>'
            )
            prev_oid = prev_owner_by_name.get(name_keys_now.get(oid))
            parts = [
                _realty_html(s3, oid, prev_s3, prev_oid),
                _vehicles_html(s6, oid, prev_s6, prev_oid),
                _income_html(s11, oid),
                _cash_html(s12, oid, year),
                _corporate_html(s8, oid),
                _obligations_html(s13, oid, year),
                '<p class="stub">Цінні папери: не застосовується</p>',
                '<p class="stub">Видатки: не застосовується</p>',
            ]
            content = "".join(p for p in parts if p)
            panels.append(
                f'<div id="{tid}" class="owner-panel">'
                f'{content or "<p>Немає активів</p>"}</div>'
            )

    if not filtered and not gen_content.strip():
        return '<div class="owner-panels"><p>Немає активів</p></div>'

    return (
        f'<div class="owner-tab-btns">{"".join(buttons)}</div>'
        f'<div class="owner-panels">{"".join(panels)}</div>'
    )


def render_all_declarations(user_declarant_id: int, docs: list[dict]) -> str:
    sorted_docs = sorted(
        docs, key=lambda d: d.get("declaration_year", 0), reverse=True
    )
    latest = sorted_docs[0]

    # ── header: declarant info + career history ────────────────────────────────
    s1 = latest.get("data", {}).get("step_1", {})
    d1 = s1.get("data", {})
    full_name = _proper_name(
        f"{d1.get('lastname','')} {d1.get('firstname','')} {d1.get('middlename','')}"
    )
    career = _collect_career_history(sorted_docs)
    if career:
        career_rows = []
        for entry in career:
            period = (
                f"{entry['start_year']}–{entry['end_year']}"
                if entry["start_year"] != entry["end_year"]
                else str(entry["start_year"])
            )
            career_rows.append(
                f"<tr><td>{period}</td><td>{entry['workPlace']}</td><td>{entry['workPost']}</td></tr>"
            )
        career_section = (
            "<h3>Послужний список</h3>"
            "<table>"
            "<colgroup class='tab-career'><col class='col-1'><col class='col-2'><col></colgroup>"
            "<thead><tr><th>Роки</th><th>Місце роботи</th><th>Посада</th></tr></thead>"
            f"<tbody>{''.join(career_rows)}</tbody></table>"
        )
    else:
        career_section = (
            f"<p><b>Місце роботи:</b> {d1.get('workPlace','')}</p>"
            f"<p><b>Посада:</b> {d1.get('workPost','')}</p>"
        )
    b1 = (
        "<section>"
        f"<h2>Інформація про декларанта <span class='user-declarant-id'>[id: <span onclick='copyText(this)'>{user_declarant_id}</span>]</span></h2>"
        f"<p><b>ПІБ:</b> {full_name}</p>"
        f"{career_section}"
        "</section>"
    )

    # ── family (across all years) ──────────────────────────────────────────────
    family_history = _collect_family_history(sorted_docs)
    frows = "".join(
        f"<tr><td>{yrange}</td><td>{rel}</td><td>{name}</td></tr>"
        for rel, name, yrange in family_history
    )
    family_body = (
        "<table>"
        "<colgroup class='tab-family'><col class='col-1'><col class='col-2'><col></colgroup>"
        "<thead><tr><th>Роки</th><th>Родинний зв'язок</th><th>ПІБ</th></tr>"
        "</thead>"
        f"<tbody>{frows}</tbody></table>"
        if frows
        else "<p>Немає відомостей</p>"
    )
    b2 = f"<section><h2>Склад сім'ї</h2>{family_body}</section>"

    # ── попереднє обчислення заощаджень та змін майнового стану ────────────────
    savings_by_year = _compute_savings(sorted_docs)
    changes_by_year = _compute_asset_changes(sorted_docs)
    owner_changes_by_year = _compute_owner_asset_changes(sorted_docs)

    # ── assets: year tabs (outer) + owner tabs (inner) ─────────────────────────
    year_btns: list[str] = []
    year_panels: list[str] = []

    for i, doc in enumerate(sorted_docs):
        year = doc.get("declaration_year", "?")
        ytid = f"y{year}"
        active = " active" if i == 0 else ""
        marker_html = _change_marker_html(changes_by_year.get(year))
        year_btns.append(
            f'<button class="year-btn{active}" data-year="{ytid}"'
            f' onclick="showYearTab(\'{ytid}\')">{year}{marker_html}</button>'
        )
        savings = savings_by_year.get(year, 0.0)
        prev_doc = sorted_docs[i + 1] if i + 1 < len(sorted_docs) else None
        owner_content = _render_owner_assets(
            doc, prev_doc, ytid, savings, owner_changes_by_year.get(year, {})
        )
        year_panels.append(
            f'<div id="{ytid}" class="year-panel{active}">{owner_content}</div>'
        )

    b3 = (
        "<section>"
        "<h2>Активи</h2>"
        '<div class="year-tabs">'
        f'<div class="year-tab-btns">{"".join(year_btns)}</div>'
        + "".join(year_panels)
        + "</div>"
        + "</section>"
    )

    return (
        "<!DOCTYPE html>"
        "<html lang='uk'>"
        f"<head><meta charset='utf-8'><title>Декларації — {full_name}</title>{_CSS}</head>"
        f"<body>{_ICONS_SVG}{b1}{b2}{b3}{_JS}</body>"
        "</html>"
    )
