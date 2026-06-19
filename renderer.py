from __future__ import annotations

from nazk_renderer import (
    _build_owners,
    _cash_html,
    _corporate_html,
    _has_any_owner_assets,
    _income_html,
    _obligations_html,
    _proper_name,
    _realty_html,
    _step_data,
    _vehicles_html,
)

_CSS = """\
<style>
*{box-sizing:border-box}
body{font-family:Arial,sans-serif;font-size:14px;color:#222;max-width:1100px;margin:0 auto;padding:16px}
h2{font-size:15px;font-weight:bold;border-bottom:1px solid #ccc;padding-bottom:4px;margin-top:24px}
h3{font-size:13px;font-weight:bold;margin:12px 0 4px}
p{margin:4px 0}
table{border-collapse:collapse;width:100%}
th,td{border:1px solid #ccc;padding:5px 10px;text-align:left}
th{background:#f0f0f0}

/* year tabs (outer, horizontal) */
.year-tab-btns{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:-1px}
.year-btn{padding:5px 16px;border:1px solid #ccc;background:#f5f5f5;cursor:pointer;
          border-radius:4px 4px 0 0;border-bottom:none;font-size:13px;font-weight:bold}
.year-btn.active{background:#fff}
.year-panel{display:none;border:1px solid #ccc}
.year-panel.active{display:flex;min-height:200px}

/* owner tabs (inner, vertical) */
.owner-tab-btns{display:flex;flex-direction:column;min-width:180px;border-right:1px solid #ccc;
                background:#fafafa;padding:6px 0;flex-shrink:0}
.owner-btn{padding:7px 14px;border:none;background:transparent;cursor:pointer;text-align:left;
           font-size:13px;white-space:nowrap;border-left:3px solid transparent}
.owner-btn:hover{background:#f0f0f0}
.owner-btn.active{background:#fff;font-weight:bold;border-left-color:#0066cc}
.owner-panels{flex:1;padding:12px;overflow:auto}
.owner-panel{display:none}
.owner-panel.active{display:block}

/* assets */
details{margin:8px 0}
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
ol{margin:6px 0;padding-left:20px}
ol li{margin:3px 0}
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


def _render_owner_assets(doc: dict, year_tab_id: str) -> str:
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

    owners = _build_owners(s1, s2)
    sorted_owners = _sort_owners(owners, s2)
    filtered = [
        (oid, oname)
        for oid, oname in sorted_owners
        if _has_any_owner_assets(oid, s3, s6, s11, s12, s8, s13)
    ]

    if not filtered:
        return '<div class="owner-panels"><p>Немає активів</p></div>'

    buttons: list[str] = []
    panels: list[str] = []
    for i, (oid, oname) in enumerate(filtered):
        tid = f"o-{year_tab_id}-{oid}"
        active = " active" if i == 0 else ""
        buttons.append(
            f'<button class="owner-btn{active}" data-tab="{tid}"'
            f' onclick="showOwnerTab(\'{year_tab_id}\',\'{tid}\')">{oname}</button>'
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
        panels.append(
            f'<div id="{tid}" class="owner-panel{active}">'
            f'{content or "<p>Немає активів</p>"}</div>'
        )

    return (
        f'<div class="owner-tab-btns">{"".join(buttons)}</div>'
        f'<div class="owner-panels">{"".join(panels)}</div>'
    )


def render_all_declarations(docs: list[dict]) -> str:
    sorted_docs = sorted(
        docs, key=lambda d: d.get("declaration_year", 0), reverse=True
    )
    latest = sorted_docs[0]

    # ── header: declarant info (from latest year) ──────────────────────────────
    s1 = latest.get("data", {}).get("step_1", {})
    d1 = s1.get("data", {})
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

    # ── family (from latest year) ──────────────────────────────────────────────
    s2 = _step_data(latest.get("data", {}).get("step_2"))
    family_rows = []
    for m in s2:
        mname = _proper_name(
            f"{m.get('lastname','')} {m.get('firstname','')} {m.get('middlename','')}"
        )
        family_rows.append(
            f"<tr><td>{m.get('subjectRelation','')}</td><td>{mname}</td></tr>"
        )
    frows = "".join(family_rows)
    family_body = (
        f"<table><thead><tr><th>Родинний зв'язок</th><th>ПІБ</th></tr></thead>"
        f"<tbody>{frows}</tbody></table>"
        if frows
        else "<p>Немає відомостей</p>"
    )
    b2 = f"<section><h2>Склад сім'ї</h2>{family_body}</section>"

    # ── assets: year tabs (outer) + owner tabs (inner, vertical) ──────────────
    year_btns: list[str] = []
    year_panels: list[str] = []

    for i, doc in enumerate(sorted_docs):
        year = doc.get("declaration_year", "?")
        ytid = f"y{year}"
        active = " active" if i == 0 else ""
        year_btns.append(
            f'<button class="year-btn{active}" data-year="{ytid}"'
            f' onclick="showYearTab(\'{ytid}\')">{year}</button>'
        )
        owner_content = _render_owner_assets(doc, ytid)
        year_panels.append(
            f'<div id="{ytid}" class="year-panel{active}">{owner_content}</div>'
        )

    b3 = (
        "<section>"
        "<h2>Активи</h2>"
        f'<div class="year-tab-btns">{"".join(year_btns)}</div>'
        + "".join(year_panels)
        + "</section>"
    )

    return (
        "<!DOCTYPE html>"
        "<html lang='uk'>"
        f"<head><meta charset='utf-8'><title>Декларації — {full_name}</title>{_CSS}</head>"
        f"<body>{b1}{b2}{b3}{_JS}</body>"
        "</html>"
    )
