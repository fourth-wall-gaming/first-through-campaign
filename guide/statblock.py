"""Render a Mythras sheet as a Design Mechanism stat block, in HTML and in Typst.

Three layouts, as the TDM Guidelines for Writers define them:

  major   -- characteristics, attributes and hit locations side by side, then
             skills and passions, then the combat style and its weapons.
  minor   -- the same without the characteristics column.
  monster -- a characteristics/attributes header row, for creatures and for the
             troop templates the engine can `spawn`.

The sheet JSON is the single source. Nothing here invents a number: a value the
sheet does not carry is printed as '-'.
"""
import html
import math
import re

from house import house

LOC_ORDER = ["Right Leg", "Left Leg", "Abdomen", "Chest", "Right Arm", "Left Arm", "Head"]

NO_DM = re.compile(r"crossbow|sling|garrot|demon-surge|spectral", re.I)


def _range(r):
    if not r:
        return "-"
    a, b = r[0], r[-1]
    return f"{a}" if a == b else f"{a}–{b}"


def movement(attrs):
    m = str(attrs.get("movement") or "").strip()
    try:
        metres = float(m)
    except ValueError:
        return m or "-"
    feet = int(round(metres / 0.3 / 5.0) * 5)
    return f"{feet}' ({metres:g} metres)"


def armour_text(sheet):
    items = [e for e in sheet.get("equipment") or [] if isinstance(e, dict) and e.get("armor")]
    named = [e["name"] for e in items if e.get("ap")]
    if named:
        return "; ".join(named)
    if any(h.get("ap") for h in sheet.get("hit_locations") or []):
        return "As listed by location"
    return "None"


def abilities_text(sheet):
    ab = (sheet.get("extras") or {}).get("abilities") or []
    powers = sheet.get("powers") or []
    parts = [a for a in ab if "see powers" not in a.lower()]
    parts += [f"{p['name']} ({', '.join(p.get('boosts') or [])})" if p.get("boosts") else p["name"]
              for p in powers if isinstance(p, dict) and p.get("name")]
    return "; ".join(parts) if parts else "None"


def magic_text(sheet):
    sp = sheet.get("spells")
    if not sp:
        return "None"
    if isinstance(sp, dict):
        out = []
        for kind, names in sp.items():
            label = {"arcane": "Arcane", "memorized": "Divine (memorised)", "divine": "Divine"}.get(kind, kind.title())
            if names:
                out.append(f"{label}: {', '.join(names)}")
        return "; ".join(out) or "None"
    if isinstance(sp, list):
        return ", ".join(s if isinstance(s, str) else s.get("name", "") for s in sp) or "None"
    return str(sp)


def skills_text(sheet):
    sk = sheet.get("skills") or {}
    return ", ".join(f"{k} {v}%" for k, v in sorted(sk.items())) or "-"


def passions(sheet):
    p = sheet.get("passions") or {}
    if isinstance(p, dict):
        return [f"{k} {v}%" for k, v in p.items()]
    return [str(x) for x in p]


def styles(sheet):
    cs = sheet.get("combat_styles") or {}
    if isinstance(cs, dict):
        return [f"{k} {v}%" for k, v in cs.items()]
    return [str(x) for x in cs]


def weapons(sheet):
    dm = str((sheet.get("attributes") or {}).get("damage_modifier") or "").strip()
    add_dm = dm and dm not in ("+0", "0", "-", "None", "none")
    rows = []
    for e in sheet.get("equipment") or []:
        if not isinstance(e, dict) or e.get("armor") or not e.get("damage"):
            continue
        dmg = str(e["damage"])
        if add_dm and dmg not in ("special", "-") and not NO_DM.search(e["name"]):
            dmg = f"{dmg}{dm if dm.startswith(('+', '-', '−')) else '+' + dm}"
        size = e.get("size") or e.get("force") or "-"
        reach = e.get("reach") or e.get("range") or "-"
        rows.append([e["name"], size, reach, dmg, e.get("ap_hp") or "-"])
    return rows


def locations(sheet):
    hl = {h["name"]: h for h in sheet.get("hit_locations") or []}
    ordered = [hl[n] for n in LOC_ORDER if n in hl] + [h for n, h in hl.items() if n not in LOC_ORDER]
    return [(_range(h.get("range")), h["name"], f"{h.get('ap', 0)}/{h.get('hp', '-')}") for h in ordered]


def attribute_rows(sheet):
    a = sheet.get("attributes") or {}
    return [
        ("Action Points", a.get("action_points", "-")),
        ("Damage Modifier", a.get("damage_modifier", "-")),
        ("Magic Points", a.get("magic_points", "-")),
        ("Movement", movement(a)),
        ("Initiative Bonus", f"+{a['initiative_bonus']}" if isinstance(a.get("initiative_bonus"), int) else "-"),
        ("Armour", armour_text(sheet)),
        ("Abilities", abilities_text(sheet)),
        ("Magic", magic_text(sheet)),
    ]


def characteristic_rows(sheet):
    c = sheet.get("characteristics") or {}
    return [f"{k}: {c.get(k, '-')}" for k in ("STR", "CON", "SIZ", "DEX", "INT", "POW", "CHA")]


# ---------------------------------------------------------------- HTML

def _e(s):
    return html.escape(house(str(s)))


def to_html(sheet, layout):
    name = _e(sheet["name"])
    attrs = attribute_rows(sheet)
    locs = locations(sheet)
    chars = characteristic_rows(sheet)
    n = max(len(attrs), len(locs) + 1)
    rows = []
    head = ["<tr class='sb-head'>"]
    if layout in ("major", "monster"):
        head.append("<th>Characteristics</th>")
    head.append("<th>Attributes</th><th>1d20</th><th>Hit Location</th><th>AP/HP</th></tr>")
    rows.append("".join(head))
    for i in range(n):
        r = ["<tr>"]
        if layout in ("major", "monster"):
            r.append(f"<td>{_e(chars[i]) if i < len(chars) else ''}</td>")
        if i < len(attrs):
            k, v = attrs[i]
            r.append(f"<td><b>{k}:</b> {_e(v)}</td>")
        else:
            r.append("<td></td>")
        if i < len(locs):
            r += [f"<td class='c'>{_e(x)}</td>" for x in locs[i]]
        else:
            r.append("<td></td><td></td><td></td>")
        r.append("</tr>")
        rows.append("".join(r))
    span = 5 if layout in ("major", "monster") else 4
    pas = "".join(f"<br>{_e(p)}" for p in passions(sheet))
    rows.append(f"<tr><td colspan='{span}' class='sb-skills'><b>Skills:</b> {_e(skills_text(sheet))}"
                + (f"<br><b>Passions:</b>{pas}" if pas else "") + "</td></tr>")
    main = f"<table class='statblock sb-{layout}' aria-label='{name}'>{''.join(rows)}</table>"

    wrows = ["<tr class='sb-head'><th>Weapon</th><th>Size/Force</th><th>Reach/Range</th><th>Damage</th><th>AP/HP</th></tr>"]
    for w in weapons(sheet) or [["-", "-", "-", "-", "-"]]:
        wrows.append("<tr>" + "".join(f"<td>{_e(x)}</td>" for x in w) + "</tr>")
    style = "; ".join(styles(sheet)) or "None"
    combat = (f"<table class='statblock sb-combat'><tr><td colspan='5' class='sb-style'>"
              f"<b>Combat Style:</b> {_e(style)}</td></tr>{''.join(wrows)}</table>")
    return f"<div class='sb-wrap' id='sb-{_slug(sheet['name'])}'>{main}{combat}</div>"


# ---------------------------------------------------------------- Typst

def _t(s):
    s = house(str(s))
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _cell(s, **kw):
    opts = "".join(f", {k}: {v}" for k, v in kw.items())
    return f'table.cell([#"{_t(s)}"]{opts})'


def _bold(label, value, **kw):
    opts = "".join(f", {k}: {v}" for k, v in kw.items())
    return f'table.cell([*{_t(label)}:* #"{_t(value)}"]{opts})'


def to_typst(sheet, layout):
    attrs = attribute_rows(sheet)
    locs = locations(sheet)
    chars = characteristic_rows(sheet)
    wide = layout in ("major", "monster")
    cols = "(auto, 1fr, auto, auto, auto)" if wide else "(1fr, auto, auto, auto)"
    span = 5 if wide else 4
    cells = []
    hdr = (["Characteristics"] if wide else []) + ["Attributes", "1d20", "Hit Location", "AP/HP"]
    cells += [f'table.cell(fill: sbhead)[*{h}*]' for h in hdr]
    n = max(len(attrs), len(locs) + 1)
    for i in range(n):
        if wide:
            cells.append(_cell(chars[i] if i < len(chars) else ""))
        cells.append(_bold(*attrs[i]) if i < len(attrs) else "[]")
        if i < len(locs):
            cells += [_cell(x) for x in locs[i]]
        else:
            cells += ["[]", "[]", "[]"]
    skills = f'[*Skills:* #"{_t(skills_text(sheet))}"'
    pas = passions(sheet)
    if pas:
        skills += " \\ *Passions:* " + " \\ ".join(f'#"{_t(p)}"' for p in pas)
    skills += "]"
    cells.append(f"table.cell(colspan: {span}, {skills})")
    main = f'#sbtable(columns: {cols}, ' + ", ".join(cells) + ")"

    wcells = [f'table.cell(colspan: 5)[*Combat Style:* #"{_t("; ".join(styles(sheet)) or "None")}"]']
    wcells += [f'table.cell(fill: sbhead)[*{h}*]' for h in ("Weapon", "Size/Force", "Reach/Range", "Damage", "AP/HP")]
    for w in weapons(sheet) or [["-", "-", "-", "-", "-"]]:
        wcells += [_cell(x) for x in w]
    combat = '#sbtable(columns: (1fr, auto, auto, auto, auto), ' + ", ".join(wcells) + ")"
    return "#block(breakable: false)[\n" + main + "\n" + combat + "\n]"


def _slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
