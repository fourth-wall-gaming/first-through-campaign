#!/usr/bin/env python3
"""Render THE CAUSEWAY as an exact, editable SVG chart from the campaign data.

Every star sits at its true galactic position, computed from the RA/Dec/distance
in data/systems.json; every door is a true edge from data/edges.json. Nothing
here is drawn by eye, which is the entire point: the campaign's hard rule is that
the astronomy checks out if somebody looks it up, and a wall map is the artefact
most likely to be looked up.

Output is SVG with grouped layers and live text, so it opens in Illustrator or
Inkscape and every label can be nudged.

    python3 maps/causeway_chart.py            # -> maps/the-causeway.svg
"""
import json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(ROOT, "data", "systems.json")))
E = json.load(open(os.path.join(ROOT, "data", "edges.json")))

# --- geometry ---------------------------------------------------------------
RA_NGP, DEC_NGP, L_NCP = map(math.radians, (192.85948, 27.12825, 122.93192))

def galactic_xyz(ra_deg, dec_deg, d):
    ra, dec = math.radians(ra_deg), math.radians(dec_deg)
    sb = math.sin(dec) * math.sin(DEC_NGP) + math.cos(dec) * math.cos(DEC_NGP) * math.cos(ra - RA_NGP)
    b = math.asin(max(-1.0, min(1.0, sb)))
    yy = math.cos(dec) * math.sin(ra - RA_NGP)
    xx = math.sin(dec) * math.cos(DEC_NGP) - math.cos(dec) * math.sin(DEC_NGP) * math.cos(ra - RA_NGP)
    l = (L_NCP - math.atan2(yy, xx)) % (2 * math.pi)
    return (d * math.cos(b) * math.cos(l), d * math.cos(b) * math.sin(l), d * math.sin(b))

G = {}
for k, v in S.items():
    G[k] = (0.0, 0.0, 0.0) if k == "sol" else galactic_xyz(v["ra_deg"], v["dec_deg"], v["distance_ly"])

# Azimuth chosen by search to spread the tightest projected pairs; elevation is
# the shallow look-down that keeps the plane readable as a plane.
AZ, EL = math.radians(122.0), math.radians(20.0)

def project(p):
    """Galactic (x,y,z) ly -> (screen_x, screen_y) in ly units, y down."""
    x, y, z = p
    u = x * math.cos(AZ) - y * math.sin(AZ)
    v = x * math.sin(AZ) + y * math.cos(AZ)
    return (u, -(z * math.cos(EL) + v * math.sin(EL)))

def foot(p):
    """Where a star's dropline meets the galactic plane."""
    return project((p[0], p[1], 0.0))

# --- the sheet --------------------------------------------------------------
W, H = 1040, 1960
PAPER, INK, MID, FAINT = "#efe6d0", "#241c12", "#6d573c", "#b9a888"
DOOR, RULE = "#9a6b33", "#8a7350"
FONT = "'EB Garamond','Georgia','Times New Roman',serif"

out = []
def add(s): out.append(s)
def esc(t): return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def text(x, y, t, size=11, anchor="start", fill=INK, ls=0.0, weight="normal", style="normal"):
    add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
        f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}" '
        f'font-weight="{weight}" font-style="{style}">{esc(t)}</text>')

def caps(x, y, t, size=11, anchor="start", fill=INK, ls=1.6, weight="normal"):
    text(x, y, t.upper(), size, anchor, fill, ls, weight)

def wiki(key):
    """The system's Wikipedia article, out of its own sources list."""
    for s in (S[key].get("sources") or []):
        if "wikipedia.org" in s:
            return s
    return None

def link_open(key):
    """Open an SVG hyperlink around a star's mark or its name.

    href is SVG 2 and is what browsers follow; xlink:href is kept as well, for
    the drawing programs this chart is meant to stay editable in. A system with
    no article in its sources emits nothing and is simply not a link.
    """
    u = wiki(key)
    if not u:
        return False
    add(f'<a href="{esc(u)}" xlink:href="{esc(u)}" target="_blank" rel="noopener" '
        f'aria-label="{esc(S[key]["name"])} on Wikipedia">')
    return True

def link_close(opened):
    if opened:
        add("</a>")

def frame(x, y, w, h, sw=1.1, stroke=RULE, fill="none"):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{sw}"/>')

# ---------------------------------------------------------------------------
def plate(ox, oy, pw, ph, radius, members, scale, title, subtitle,
          rings, label_all=True, nine=False):
    """Draw one perspective plate. Returns nothing; writes into `out`."""
    cx, cy = ox + pw / 2.0, oy + ph / 2.0 + ph * 0.015
    k = scale

    def sx(p): return cx + project(p)[0] * k
    def sy(p): return cy + project(p)[1] * k
    def fx(p): return cx + foot(p)[0] * k
    def fy(p): return cy + foot(p)[1] * k

    add(f'<g id="plate-{title.lower().replace(" ","-").replace(".","")}">')
    frame(ox, oy, pw, ph)

    # --- the galactic plane: rings + radial spokes, drawn recessive
    add('<g id="galactic-plane" fill="none">')
    for r in rings:
        pts = []
        for i in range(181):
            a = 2 * math.pi * i / 180.0
            px, py = project((r * math.cos(a), r * math.sin(a), 0.0))
            pts.append(f"{cx + px*k:.1f},{cy + py*k:.1f}")
        heavy = abs(r - radius) < 1e-6
        add(f'<polyline points="{" ".join(pts)}" stroke="{MID if heavy else FAINT}" '
            f'stroke-width="{1.5 if heavy else 0.6}"/>')
    for i in range(12):
        a = 2 * math.pi * i / 12.0
        px, py = project((radius * math.cos(a), radius * math.sin(a), 0.0))
        add(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx + px*k:.1f}" y2="{cy + py*k:.1f}" '
            f'stroke="{FAINT}" stroke-width="0.45"/>')
    add('</g>')
    # ring distances, read off the right-hand side of the plane
    add('<g id="ring-labels">')
    # the rim nearest the viewer is wherever the projection puts y lowest
    _best = max(range(360), key=lambda d: project((math.cos(math.radians(d)),
                                                   math.sin(math.radians(d)), 0.0))[1])
    nx, ny = math.cos(math.radians(_best)), math.sin(math.radians(_best))
    for r in rings:
        px, py = project((nx * r, ny * r, 0.0))
        caps(cx + px * k, cy + py * k + 12,
             f"{r:g}" + (" ly" if abs(r - rings[-1]) < 1e-9 else ""), 8.4, "middle", MID, 1.0)
    if abs(radius - 48.75) < 1e-6:
        pxf, pyf = project((nx * radius, ny * radius, 0.0))
        caps(cx + pxf * k, cy + pyf * k + 30, "the frontier", 11, "middle", INK, 2.4)
    add('</g>')

    # --- doors
    sirius_edges = []
    add('<g id="doors" fill="none">')
    for e in E:
        a, b = e["a"], e["b"]
        if a not in members or b not in members:
            continue
        is_nine = nine and "sirius" in (a, b)
        if is_nine:
            sirius_edges.append(e)
        x1, y1, x2, y2 = sx(G[a]), sy(G[a]), sx(G[b]), sy(G[b])
        w_ = 1.7 if is_nine else (0.75 if max(S[a]["distance_ly"], S[b]["distance_ly"]) > 20 else 1.0)
        add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{DOOR}" stroke-width="{w_}" opacity="0.95"/>')
        mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
        add(f'<g transform="translate({mx:.1f},{my:.1f}) rotate({ang:.1f})">'
            f'<polygon points="-3.4,0 0,-2.1 3.4,0 0,2.1" fill="{PAPER}" '
            f'stroke="{DOOR}" stroke-width="0.8"/></g>')
    add('</g>')

    # --- droplines and stars
    add('<g id="stars">')
    for m in members:
        p = G[m]
        add(f'<line x1="{fx(p):.1f}" y1="{fy(p):.1f}" x2="{sx(p):.1f}" y2="{sy(p):.1f}" '
            f'stroke="{MID}" stroke-width="0.7"/>')
        add(f'<line x1="{fx(p)-3:.1f}" y1="{fy(p):.1f}" x2="{fx(p)+3:.1f}" y2="{fy(p):.1f}" '
            f'stroke="{MID}" stroke-width="0.7"/>')
    for m in members:
        p, X, Y = G[m], sx(G[m]), sy(G[m])
        open_ = S[m]["opened_years_ago"] is not None and S[m]["opened_years_ago"] < 0
        _a = link_open(m)
        if m == "sol":
            add(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="5.4" fill="none" stroke="{INK}" stroke-width="1.3"/>')
            for i in range(8):
                a = 2 * math.pi * i / 8.0
                add(f'<line x1="{X + 6.6*math.cos(a):.1f}" y1="{Y + 6.6*math.sin(a):.1f}" '
                    f'x2="{X + 10*math.cos(a):.1f}" y2="{Y + 10*math.sin(a):.1f}" '
                    f'stroke="{INK}" stroke-width="1.0"/>')
            add(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="2.3" fill="{INK}"/>')
        elif m == "sirius" and nine:
            for i in range(9):
                a = 2 * math.pi * i / 9.0 - math.pi / 2
                add(f'<line x1="{X:.1f}" y1="{Y:.1f}" x2="{X + 13*math.cos(a):.1f}" '
                    f'y2="{Y + 13*math.sin(a):.1f}" stroke="{MID}" stroke-width="0.6"/>')
            add(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="4.6" fill="{PAPER}" stroke="{INK}" stroke-width="1.4"/>')
            add(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="2.6" fill="{INK}"/>')
        elif open_:
            add(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="4.4" fill="{PAPER}" stroke="{INK}" stroke-width="1.5"/>')
            add(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="1.5" fill="none" stroke="{INK}" stroke-width="1.0"/>')
        else:
            add(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="3.5" fill="{INK}"/>')
        link_close(_a)
    add('</g>')

    # --- labels: a column down each side, ordered by screen height.
    # Placing labels in the plot and pushing them apart cannot be made to
    # converge with twenty-two of them; a column per side is collision-free by
    # construction, which is how engraved star charts have always done it.
    if label_all:
        left = sorted([m for m in members if project(G[m])[0] < 0], key=lambda m: sy(G[m]))
        right = sorted([m for m in members if project(G[m])[0] >= 0], key=lambda m: sy(G[m]))
        add('<g id="labels">')
        for side, col in (("left", left), ("right", right)):
            if not col:
                continue
            lx = ox + 26 if side == "left" else ox + pw - 26
            anchor = "start" if side == "left" else "end"
            span = ph - 150
            step = min(17.0, span / max(1, len(col) - 1))
            top = cy - (step * (len(col) - 1)) / 2.0
            for i, m in enumerate(col):
                ly = top + i * step
                X, Y = sx(G[m]), sy(G[m])
                elbow = lx + (74 if side == "left" else -74)
                add(f'<polyline points="{lx + (4 if side=="left" else -4):.1f},{ly-3:.1f} '
                    f'{elbow:.1f},{ly-3:.1f} {X + (-7 if side=="left" else 7):.1f},{Y:.1f}" '
                    f'fill="none" stroke="{MID}" stroke-width="0.45" opacity="0.8"/>')
                _a = link_open(m)
                caps(lx, ly, S[m]["name"], 9.6, anchor, INK, 1.0)
                link_close(_a)
        add('</g>')

    # scale bar
    bar = 10.0 * k if radius > 20 else 5.0 * k
    bx, by = ox + 26, oy + ph - 30
    add(f'<line x1="{bx}" y1="{by}" x2="{bx + bar:.1f}" y2="{by}" stroke="{INK}" stroke-width="1.3"/>')
    for t in (0, 1):
        add(f'<line x1="{bx + t*bar:.1f}" y1="{by-4}" x2="{bx + t*bar:.1f}" y2="{by+4}" stroke="{INK}" stroke-width="1.3"/>')
    caps(bx, by - 9, f"{10 if radius > 20 else 5} light years", 8.4, "start", MID, 1.2)
    # compass: galactic centre is +X in galactic coords
    gx, gy = ox + pw - 70, oy + 54
    cxp, cyp = project((1.0, 0.0, 0.0))
    ang = math.degrees(math.atan2(cyp, cxp))
    add(f'<g transform="translate({gx},{gy}) rotate({ang:.1f})">'
        f'<line x1="-22" y1="0" x2="22" y2="0" stroke="{INK}" stroke-width="1.1"/>'
        f'<polygon points="22,0 14,-4 14,4" fill="{INK}"/></g>')
    caps(gx, gy + 20, "galactic centre", 7.6, "middle", MID, 1.2)

    caps(ox + 20, oy + 30, title, 19, "start", INK, 2.4, "bold")
    for i, line in enumerate(subtitle):
        caps(ox + 20, oy + 50 + i * 15, line, 9.6, "start", MID, 1.4)
    add('</g>')
    return cx, cy

# ---------------------------------------------------------------------------
add(f'<svg id="causeway" xmlns="http://www.w3.org/2000/svg" '
    f'xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" '
    f'viewBox="0 0 {W} {H}">')
add("<title>The Causeway — the known network, 975 years after the Reach</title>")
# Scoped to the sheet's own id, because this file is also inlined into a page.
# Print renderers ignore it; on screen a name is visibly a link on hover.
add(f"""<style>
  #causeway a {{ cursor: pointer; }}
  #causeway a text, #causeway a circle {{ transition: fill .12s ease; }}
  #causeway a:hover text, #causeway a:focus text {{ fill: {DOOR}; }}
  #causeway a:hover circle[fill="{INK}"] {{ fill: {DOOR}; }}
  #causeway a:focus {{ outline: none; }}
</style>""")
add(f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')
add(f'<rect x="14" y="14" width="{W-28}" height="{H-28}" fill="none" stroke="{INK}" stroke-width="2.4"/>')
add(f'<rect x="21" y="21" width="{W-42}" height="{H-42}" fill="none" stroke="{INK}" stroke-width="0.7"/>')

# title cartouche
frame(34, 34, W - 68, 92, 1.1)
caps(W / 2, 76, "The Causeway", 40, "middle", INK, 5.0, "bold")
caps(W / 2, 100, "The known network, 975 years after the Reach", 13, "middle", MID, 2.2)
caps(W / 2, 118, "28 systems  ·  26 doors  ·  one humanity", 9.4, "middle", MID, 2.6)

INNER = [k for k, v in S.items() if v["distance_ly"] <= 17.0]
ALL = list(S.keys())

plate(34, 140, W - 68, 800, 48.75, ALL, 7.4,
      "Plate I.  The whole network",
      ["Radius 48.75 light years", "Galactic plane in perspective, elevation 20°",
       "Positions computed from SIMBAD parallaxes"],
      rings=[10, 20, 30, 40, 48.75], label_all=False)

# frontier labels on Plate I only (the inner knot is deferred to Plate II)
cx1, cy1 = 34 + (W - 68) / 2.0, 140 + 800 / 2.0 + 800 * 0.015
add('<g id="plate1-labels">')
for m in [k for k, v in S.items() if v["distance_ly"] > 17.0]:
    X, Y = cx1 + project(G[m])[0] * 7.4, cy1 + project(G[m])[1] * 7.4
    right = project(G[m])[0] >= 0
    # clamp: a label that would run past the plate edge flips to the inside
    _w = len(S[m]["name"]) * 7.9 + 14          # 11px small caps + tracking
    if right and X + _w > (34 + W - 68) - 16:
        right = False
    _a = link_open(m)
    caps(X + (12 if right else -12), Y + 4, S[m]["name"], 11, "start" if right else "end", INK, 1.4)
    link_close(_a)
    if S[m]["opened_years_ago"] is not None and S[m]["opened_years_ago"] < 0:
        caps(X + (12 if right else -12), Y + 19, "not yet open", 8.6,
             "start" if right else "end", DOOR, 1.6)
add(f'<rect x="{cx1-96:.0f}" y="{cy1-74:.0f}" width="192" height="150" fill="none" '
    f'stroke="{INK}" stroke-width="0.9" stroke-dasharray="5 4"/>')
caps(cx1, cy1 - 84, "see plate II", 9.4, "middle", INK, 1.8)
add('</g>')

plate(34, 960, W - 68, 700, 17.0, INNER, 17.4,
      "Plate II.  The Inner Reach",
      ["Radius 17 light years — 22 of the 28 systems",
       "Outer ring 17 light years — not the frontier",
       "Heavy lines are the Nine, the doors meeting at Sirius"],
      rings=[5, 10, 15, 17], label_all=True, nine=True)

# --- conventions + table ----------------------------------------------------
ty = 1680
frame(34, ty, 470, 246)
caps(52, ty + 28, "Conventions", 14, "start", INK, 2.2, "bold")
rows = [("filled", "System, door open"), ("open", "System, door not yet open"),
        ("drop", "Dropline to the galactic plane"), ("door", "Door — bidirectional"),
        ("loz", "Door midpoint"), ("nine", "The Nine — Sirius's nine doors")]
for i, (kind, lbl) in enumerate(rows):
    y = ty + 54 + i * 30
    if kind == "filled": add(f'<circle cx="68" cy="{y-4}" r="3.5" fill="{INK}"/>')
    elif kind == "open": add(f'<circle cx="68" cy="{y-4}" r="4.4" fill="{PAPER}" stroke="{INK}" stroke-width="1.5"/>')
    elif kind == "drop": add(f'<line x1="68" y1="{y-12}" x2="68" y2="{y+3}" stroke="{MID}" stroke-width="0.7"/>')
    elif kind == "door": add(f'<line x1="56" y1="{y-4}" x2="80" y2="{y-4}" stroke="{DOOR}" stroke-width="1.0"/>')
    elif kind == "loz": add(f'<polygon points="64,{y-4} 68,{y-7} 72,{y-4} 68,{y-1}" fill="{PAPER}" stroke="{DOOR}" stroke-width="0.8"/>')
    else: add(f'<line x1="56" y1="{y-4}" x2="80" y2="{y-4}" stroke="{DOOR}" stroke-width="1.7"/>')
    text(94, y, lbl, 11.4, "start", INK)

frame(520, ty, W - 554, 246)
caps(538, ty + 28, "The twenty-eight systems", 14, "start", INK, 2.2, "bold")
order = sorted(S.items(), key=lambda kv: kv[1]["distance_ly"])
col, per = 0, 14
for i, (k, v) in enumerate(order):
    c, r = i // per, i % per
    x = 538 + c * 160
    y = ty + 50 + r * 12.4
    _a = link_open(k)
    text(x, y, v["name"], 9.0, "start", INK)
    link_close(_a)
    text(x + 142, y, f'{v["distance_ly"]:.2f}', 9.0, "end", MID)
text(538, ty + 228, "Distances in light years from Sol, computed from SIMBAD parallaxes.", 8.6, "start", MID, style="italic")
text(52, ty + 228, "On screen, every star name links to its Wikipedia article.", 8.6, "start", MID, style="italic")

add('</svg>')
dest = os.path.join(ROOT, "maps", "the-causeway.svg")
open(dest, "w").write("\n".join(out))
print(f"wrote {dest}  ({len(''.join(out))//1024} KB, {len(ALL)} systems, {len(E)} doors)")
