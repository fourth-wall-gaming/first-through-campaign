"""Build First Through's two books -- the Games Master's Guide and the Players'
Guide -- as one static site with a PDF of each, plus a page for parents.

    uv run --with pyyaml --with pillow python guide/build.py [--no-pdf]

Writes `_site/` (the Pages artefact): a landing page, `gm/`, `players/`,
`for-parents.html`, a PDF of each book, and `go-on-their-count.pdf` -- the
novelization of a real run, copied in from `novels/` if it has been built.

Each book is a folder of hand-written chapters, guide/gm/ and guide/players/, in
file-name order. A chapter opens with its part, `<!-- part: Background -->`, and its
title as the first `#` heading. Everything with a number in it comes from the
campaign files through a directive on a line of its own:

    <!-- statblock: blau -->        a Non-Player Character, TDM layout, with heading and description
    <!-- sheet: randall -->         the stat tables alone (for the Players' Guide)
    <!-- statblocks: major|minor|pcs|creatures|templates -->
    <!-- map: districts/pearl -->   the sheet, downsized, with its key
    <!-- timeline -->, <!-- agendas -->, <!-- roster -->, <!-- areas -->
    <!-- lore: lore/...md -->       a lore entry, boxed
    <!-- box --> ... <!-- endbox -->
    <!-- covers: beat-a, beat-b --> renders nothing: records which beats the prose
                                    around it tells, so a test can prove every beat
                                    is in the book exactly once
"""
import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import statblock  # noqa: E402
from house import house  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "guide"
OUT = ROOT / "_site"
TITLE = "First Through"
BOOKS = [
    {"key": "gm", "title": "The Games Master's Guide", "pdf": "first-through-gm-guide.pdf"},
    {"key": "players", "title": "The Players' Guide", "pdf": "first-through-players-guide.pdf"},
]
MAP_WIDTH = 2400

WATCH = {"dawn": 0, "day": 1, "dusk": 2, "night": 3}


# ---------------------------------------------------------------- campaign data

def frontmatter(path):
    text = path.read_text()
    if not text.startswith("---"):
        return {}, text
    _, fm, body = text.split("---", 2)
    return yaml.safe_load(fm) or {}, body.strip()


def load():
    data = {"sheets": {}, "beats": {}, "agendas": {}, "locations": {}, "by_id": {}}
    for kind in ("pcs", "npcs", "creatures"):
        for f in sorted((ROOT / "characters" / kind).glob("*.json")):
            d = json.loads(f.read_text())
            d["_kind"] = kind
            data["sheets"][f.stem] = d
            data["by_id"][d["id"]] = d["name"]
    for f in sorted((ROOT / "templates").glob("*.json")):
        d = json.loads(f.read_text())
        d["_kind"] = "templates"
        data["sheets"][f.stem] = d
    for f in sorted((ROOT / "beats").glob("*.md")):
        fm, body = frontmatter(f)
        fm["_slug"], fm["_body"] = f.stem, body
        data["beats"][f.stem] = fm
    for f in sorted((ROOT / "agendas").glob("*.md")):
        fm, body = frontmatter(f)
        fm["_slug"] = f.stem
        data["agendas"][f.stem] = fm
        data["by_id"][fm["id"]] = fm["title"]
    for f in sorted((ROOT / "locations").glob("*.md")):
        fm, body = frontmatter(f)
        fm["_slug"] = f.stem
        data["locations"][f.stem] = fm
        data["by_id"][fm["id"]] = fm["name"]
    for f in sorted((ROOT / "factions").glob("*.md")):
        fm, _ = frontmatter(f)
        data["by_id"][fm["id"]] = fm["name"]
    return data


# First Through types its cast by the job it does in the story rather than by
# size, so the full layout goes to the people who drive something and the
# compact one to everybody else.
MAJOR_TYPES = {"handler", "companion", "the-heart-of-act-one", "antagonist-recurring",
               "antagonist-sympathetic", "antagonist-institutional", "antagonist-field"}


def layout_of(sheet):
    if sheet["_kind"] in ("creatures", "templates"):
        return "monster"
    if sheet["_kind"] == "pcs":
        return "major"
    ct = str((sheet.get("extras") or {}).get("character_type") or "").lower()
    return "major" if (ct.startswith("major") or ct in MAJOR_TYPES) else "minor"


def clock_key(when):
    m = re.match(r"d(-?\d+)/(\w+)", str(when or ""))
    return (int(m.group(1)), WATCH.get(m.group(2), 9)) if m else (99, 9)


def name_of(data, ref):
    if ref is None:
        return "-"
    return data["by_id"].get(ref, str(ref))


# ---------------------------------------------------------------- raw output helpers

def raw(html_text, typst_text):
    return f"\n```{{=html}}\n{html_text}\n```\n\n```{{=typst}}\n{typst_text}\n```\n"


def esc_t(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def esc_tc(s):
    """Escape for use inside a Typst [content] block rather than a string."""
    for ch in "\\#[]@$*_":
        s = str(s).replace(ch, "\\" + ch)
    return s


def md_table(title, headers, rows):
    """A named TDM table: header text on every column, '-' in every blank cell."""
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        cells = [house(str(c)).replace("|", "/").replace("\n", " ") if str(c).strip() else "-" for c in r]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out) + f"\n\nTable: {title.removeprefix('Table: ')}\n"


# ---------------------------------------------------------------- directives

def d_statblock(data, arg):
    s = data["sheets"].get(arg)
    if not s:
        raise SystemExit(f"statblock: no sheet '{arg}'")
    lay = layout_of(s)
    desc = house(s.get("description") or "")
    looks = re.search(r"LOOKS:\s*(.+)", s.get("actor_notes") or "")
    prose = f"#### {s['name']}\n\n{desc}\n\n"
    if looks:
        prose += f"*{house(looks.group(1).strip())}*\n\n"
    note = (s.get("extras") or {}).get("stat_note")
    if note:
        prose += f"{house(note)}\n\n"
    return prose + raw(statblock.to_html(s, lay), statblock.to_typst(s, lay))


def d_statblocks(data, arg):
    want = arg.strip()
    picked = []
    for slug, s in sorted(data["sheets"].items(), key=lambda kv: kv[1]["name"]):
        lay = layout_of(s)
        if want == "pcs" and s["_kind"] == "pcs":
            picked.append(slug)
        elif want == "creatures" and s["_kind"] == "creatures":
            picked.append(slug)
        elif want == "templates" and s["_kind"] == "templates":
            picked.append(slug)
        elif want in ("major", "minor") and s["_kind"] == "npcs" and lay == want:
            picked.append(slug)
    return "\n".join(d_statblock(data, p) for p in picked)


def _need(data, n):
    if isinstance(n, dict):
        (k, v), = n.items()
        if k == "played":
            b = data["beats"].get(v)
            return f"after '{b['title']}'" if b else f"after {v}"
        return f"{k}: {name_of(data, v)}"
    return str(n)


def d_timeline(data, _):
    beats = sorted(data["beats"].values(), key=lambda b: (clock_key(b.get("when")), b["title"]))
    rows = [[b.get("when") or "opportunity", b["title"], name_of(data, b.get("place")),
             name_of(data, b.get("agenda"))] for b in beats]
    return md_table("Table: Act One, If Nobody Interferes", ["When", "Beat", "Where", "Agenda"], rows)


def d_agendas(data, _):
    rows = []
    for a in sorted(data["agendas"].values(), key=lambda a: a["title"]):
        rows.append([a["title"], name_of(data, a.get("holder")), a.get("goal", "-"),
                     f"{a.get('clock_filled', 0)}/{a.get('clock_size', '-')}",
                     a.get("status", "-")])
    return md_table("Table: Agendas and Their Clocks", ["Agenda", "Held by", "Goal", "Clock", "Status"], rows)


def d_roster(data, _):
    out = []
    for s in sorted((s for s in data["sheets"].values() if s["_kind"] == "npcs"), key=lambda s: s["name"]):
        out.append(f"- **{s['name']}:** {house(s.get('description') or '')}")
    return "\n".join(out) + "\n"


def d_areas(data, _):
    out = []
    for loc in sorted(data["locations"].values(), key=lambda l: l["name"]):
        out.append(f"- **{loc['name']}:** {house(loc.get('summary') or '')}")
    return "\n".join(out) + "\n"


def d_lore(data, arg):
    fm, body = frontmatter(ROOT / arg)
    body = re.sub(r"^#\s.*\n", "", body)
    body = re.sub(r"\[\[([^\]]+)\]\]", r"\1", body)
    body = re.sub(r"^#{1,6}\s+(.+)$", r"**\1**", body, flags=re.M)
    return box(f"**{fm.get('title', '')}**\n\n{house(body)}")


MAP_IMAGE_SKIP = re.compile(r"^(edit-me|crop|unlabel|lines|preview|request|thornemere|ElevenLabs|edit-)", re.I)


def d_map(data, arg, images):
    p = ROOT / "maps" / arg
    if p.is_file():
        img, labels = p, None
    else:
        tracked = set(subprocess.run(["git", "ls-files", str(p)], cwd=ROOT, capture_output=True,
                                     text=True).stdout.split())
        cands = [f for f in sorted(p.glob("*.jpg")) + sorted(p.glob("*.png"))
                 if not MAP_IMAGE_SKIP.match(f.name) and str(f.relative_to(ROOT)) in tracked]
        if not cands:
            raise SystemExit(f"map: no finished sheet in maps/{arg}")
        img = cands[0]
        labels = p / "labels.yaml"
        labels = yaml.safe_load(labels.read_text()) if labels.exists() else None
    rel = images.add(img)
    title = (labels or {}).get("title", {}).get("text") if labels else map_title(img)
    if img.suffix.lower() == ".svg":
        # A full sheet, not an illustration. In print it gets the whole page,
        # because letting a tall plate scale to the text width runs it off the
        # bottom. On the web it is inlined rather than put in an <img>, because
        # a browser will not follow links inside an image -- and the names on
        # this sheet are links.
        return raw(
            f'<figure class="sheet">{img.read_text()}'
            f'<figcaption>{html.escape(title)} &mdash; '
            f'<a href="{rel}">open the full sheet</a></figcaption></figure>',
            f'#pagebreak(weak: true)\n'
            f'#figure(image("{rel}", height: 8.5in), caption: [{esc_tc(title)}])\n'
            f'#pagebreak(weak: true)')
    md = f"![{house(title)}]({rel})\n\n"
    if labels and labels.get("sites"):
        rows = []
        for n, s in enumerate(labels["sites"], 1):
            kind = {"amenity": "Tavern or amenity", "watch": "Watch post"}.get(s.get("type"), "Place")
            rows.append([n, s["text"], kind, s.get("note") or "-"])
        md += md_table(f"Table: {house(title)}, Key", ["No.", "Name", "Kind", "Note"], rows)
    return md


def map_title(img):
    """A sheet's title, from its notes in maps/areas/ when it has them."""
    notes = ROOT / "maps" / "areas" / f"{img.stem}.md"
    if notes.is_file():
        fm, _ = frontmatter(notes)
        if fm.get("title"):
            return str(fm["title"])
    return img.stem.replace("-", " ").title()


def d_illus(data, arg, images):
    """A photograph in a chapter: `<!-- illus: path/to.jpg | caption -->`.

    Separate from `map:`, which is for a full chart sheet and takes its own
    page in print. This is an in-line plate: it sits where it is written, at
    text width, with the caption under it.
    """
    path, _, caption = (x.strip() for x in arg.partition("|"))
    src = ROOT / path
    if not src.is_file():
        raise SystemExit(f"illus: no such image {path}")
    rel = images.add_image(src)
    cap = caption or src.stem.replace("-", " ")
    return raw(
        f'<figure class="plate"><img src="{rel}" alt="{html.escape(cap)}">'
        f'<figcaption>{html.escape(cap)}</figcaption></figure>',
        f'#figure(image("{rel}", width: 100%), caption: [{esc_tc(cap)}])')


def box(content):
    return (raw("<div class='tdm-box'>", "#tdmbox[") + "\n" + content.strip() + "\n" + raw("</div>", "]"))


class Images:
    def __init__(self):
        self.done = {}

    def add_image(self, src):
        """Copy a finished illustration in at the size it was given."""
        rel = "img/" + src.name
        if rel not in self.done:
            dst = OUT / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
            self.done[rel] = dst
        return rel

    def add(self, src):
        # A chart drawn as SVG is already the right artefact: it is small, it
        # has live text, and both the web page and Typst take it as-is. Copy
        # rather than rasterise.
        if src.suffix.lower() == ".svg":
            rel = "maps/" + str(src.relative_to(ROOT / "maps"))
            if rel not in self.done:
                dst = OUT / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(src, dst)
                self.done[rel] = dst
            return rel
        rel = "maps/" + str(src.relative_to(ROOT / "maps")).rsplit(".", 1)[0] + ".jpg"
        if rel not in self.done:
            dst = OUT / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            im = Image.open(src).convert("RGB")
            if im.width > MAP_WIDTH:
                im = im.resize((MAP_WIDTH, round(im.height * MAP_WIDTH / im.width)), Image.LANCZOS)
            im.save(dst, "JPEG", quality=82, optimize=True, progressive=True)
            self.done[rel] = dst
        return rel


def d_sheet(data, arg):
    s = data["sheets"].get(arg)
    if not s:
        raise SystemExit(f"sheet: no sheet '{arg}'")
    lay = layout_of(s)
    return raw(statblock.to_html(s, lay), statblock.to_typst(s, lay))


def d_covers(data, arg):
    for slug in [a.strip() for a in arg.split(",") if a.strip()]:
        if slug not in data["beats"]:
            raise SystemExit(f"covers: no beat '{slug}'")
    return ""


def expand(data, text, images):
    text = re.sub(r"<!--\s*box\s*-->(.*?)<!--\s*endbox\s*-->", lambda m: box(m.group(1)), text, flags=re.S)

    def one(m):
        name, arg = m.group(1).strip(), (m.group(2) or "").strip()
        if name == "map":
            return d_map(data, arg, images)
        if name == "illus":
            return d_illus(data, arg, images)
        if name == "part":
            return ""
        fn = {"statblock": d_statblock, "statblocks": d_statblocks, "sheet": d_sheet, "covers": d_covers,
              "timeline": d_timeline, "agendas": d_agendas, "roster": d_roster,
              "areas": d_areas, "lore": d_lore}.get(name)
        if not fn:
            raise SystemExit(f"unknown directive: {name}")
        return fn(data, arg)

    return re.sub(r"^<!--\s*([a-z]+)\s*(?::\s*(.*?))?\s*-->\s*$", one, text, flags=re.M)


# ---------------------------------------------------------------- build

def chapters(book):
    out = []
    for f in sorted((GUIDE / book).glob("*.md")):
        text = f.read_text()
        m = re.search(r"^#\s+(.+)$", text, re.M)
        part = re.search(r"^<!--\s*part:\s*(.+?)\s*-->", text, re.M)
        out.append({"src": f, "slug": re.sub(r"^\d+-", "", f.stem), "title": m.group(1).strip() if m else f.stem,
                    "part": part.group(1) if part else "", "text": text})
    return out


def pandoc(args, text):
    r = subprocess.run(["pandoc", *args], input=text, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"pandoc failed: {r.stderr}")
    return r.stdout


def nav_html(chs):
    out, part = [], None
    for c in chs:
        if c["part"] != part:
            if part is not None:
                out.append("</ol></li>")
            part = c["part"]
            out.append(f"<li class='part'><span>{html.escape(part)}</span><ol>")
        out.append(f"<li><a href='{c['page']}'>{html.escape(c['title'])}</a></li>")
    out.append("</ol></li>")
    return "".join(out)


def build_book(book, data, images, pdf):
    key = book["key"]
    other = [b for b in BOOKS if b["key"] != key][0]
    dest = OUT / key
    dest.mkdir()
    chs = chapters(key)
    for i, c in enumerate(chs):
        c["md"] = expand(data, c["text"], images)
        c["page"] = "index.html" if i == 0 else f"{c['slug']}.html"
    nav = nav_html(chs)
    for i, c in enumerate(chs):
        prev_l = f"<a href='{chs[i - 1]['page']}'>&larr; {html.escape(chs[i - 1]['title'])}</a>" if i else ""
        next_l = (f"<a href='{chs[i + 1]['page']}'>{html.escape(chs[i + 1]['title'])} &rarr;</a>"
                  if i + 1 < len(chs) else "")
        out = pandoc(["-f", "markdown", "-t", "html5", "--template", str(GUIDE / "templates" / "page.html"),
                      "--toc", "--toc-depth=3", "-M", f"pagetitle={c['title']}", "-V", f"book={TITLE}",
                      "-V", f"booktitle={book['title']}", "-V", f"bookkey={key}",
                      "-V", f"other={other['title']}", "-V", f"otherkey={other['key']}",
                      "-V", f"part={c['part']}", "-V", f"nav={nav}", "-V", f"prev={prev_l}",
                      "-V", f"next={next_l}", "-V", f"pdf=../{book['pdf']}"], c["md"])
        out = out.replace('src="maps/', 'src="../maps/')
        out = out.replace('src="img/', 'src="../img/')
        out = re.sub(r"<table(?! class='scene-card')", "<div class=\"table-scroll\"><table", out)
        out = out.replace("</table>", "</table></div>")
        (dest / c["page"]).write_text(out)

    if pdf:
        parts, prev = [], None
        for c in chs:
            if c["part"] != prev:
                prev = c["part"]
                parts.append(raw("", f'#parttitle("{esc_t(prev)}")'))
            parts.append(c["md"])
        typ = pandoc(["-f", "markdown", "-t", "typst", "--template", str(GUIDE / "templates" / "book.typ"),
                      "-V", f"book={TITLE}", "-V", f"booktitle={book['title']}"], "\n\n".join(parts))
        tmp = OUT / f"{key}.typ"
        tmp.write_text(typ)
        r = subprocess.run(["typst", "compile", "--root", str(OUT), str(tmp), str(OUT / book["pdf"])],
                           capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"typst failed: {r.stderr}")
        tmp.unlink()
    return len(chs)


NOVEL_SRC = ROOT / "novels" / "first-through" / "first-through.pdf"
NOVEL_DST = "go-on-their-count.pdf"


def build_parents(data, images):
    """The page a parent lands on: one chapter, no navigation, its own template."""
    src = GUIDE / "parents.md"
    md = expand(data, src.read_text(), images)
    title = re.search(r"^#\s+(.+)$", md, re.M)
    out = pandoc(["-f", "markdown", "-t", "html5",
                  "--template", str(GUIDE / "templates" / "standalone.html"),
                  "-M", f"pagetitle={title.group(1).strip() if title else 'For parents'}",
                  "-V", f"book={TITLE}"], md)
    (OUT / "for-parents.html").write_text(out)


def build(pdf=True):
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copy(GUIDE / "static" / "style.css", OUT / "style.css")
    shutil.copy(GUIDE / "templates" / "landing.html", OUT / "index.html")
    (OUT / ".nojekyll").write_text("")
    data = load()
    images = Images()
    chart = ROOT / "maps" / "the-causeway.svg"
    if chart.is_file():
        images.add(chart)   # the landing page uses it as its hero
    counts = {b["key"]: build_book(b, data, images, pdf) for b in BOOKS}
    build_parents(data, images)
    # The novelization is built separately, by the engine's novelist.py, and
    # committed. Carry it onto the site when it is there; the page that links
    # to it says so either way.
    novel = "no"
    if NOVEL_SRC.exists():
        shutil.copy(NOVEL_SRC, OUT / NOVEL_DST)
        novel = "yes"
    print(f"built {counts}, {len(images.done)} maps, novel={novel} -> {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-pdf", action="store_true")
    build(pdf=not ap.parse_args().no_pdf)
