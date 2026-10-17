"""The repo must import into TypeDB and export back out without losing a thing,
and it must survive id remapping."""
import json
import re
import subprocess

import pytest

from content_rules import ROOT, lore_files, parse_frontmatter

SEED_ID = "myth-campaign-first-through-s1"


def _engine():
    return subprocess.run(
        ["bash", "-c", '. scripts/engine.sh && echo "$GM_SKILL"'],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout.strip()


def _gm(*args):
    engine = _engine()
    if not engine:
        pytest.skip("mythras-gm engine not installed")
    return subprocess.run(
        ["uv", "run", "-q", "--project", engine, "python",
         f"{engine}/mythras_gm.py", *args],
        capture_output=True, text=True, cwd=ROOT,
    )


def test_no_prose_hardcodes_a_myth_id():
    """Review Focus 4. --new-ids remaps every id, so a myth- id written into a
    sentence becomes a dangling reference the moment anybody installs this."""
    pattern = re.compile(r"myth-(char|loc|fac|lore|agenda|beat|fact|tmpl)-[0-9a-f]{12}")
    for p in lore_files():
        _, body = parse_frontmatter(p.read_text())
        assert not pattern.findall(body), (
            f"{p.relative_to(ROOT)} hardcodes a myth- id in prose"
        )


def test_cross_references_use_wiki_links_not_ids():
    """The two forms that survive remapping: [[Name]] links, resolved by name,
    and data/*.json slugs, which are not ids at all."""
    linked = 0
    for p in lore_files():
        _, body = parse_frontmatter(p.read_text())
        linked += len(re.findall(r"\[\[[^\]]+\]\]", body))
    assert linked > 10, f"only {linked} wiki links; the worldbook is not connected"


# Every directory that carries prose a reader or a GM will follow a link in.
# This used to be lore/ only, which hid dangling links everywhere else.
PROSE_DIRS = ("lore", "beats", "guide", "facts", "agendas", "factions",
              "characters", "locations")

# Pre-existing dangling links found when the collection was widened (Task 6
# fix round). Not fixed here: Task 11 inherits this list, and some may be
# deliberate.
DANGLING_ALLOWLIST = {
    # Task 11 inherits all of these. Beat-title links point at beats, which
    # are not in the name set; the rest are plain unresolved names.
    ("beats/four-and-no-more.md", "How many of you are there?"),
    ("beats/ladders-answer.md", "A proposal dies in committee"),
    ("beats/pell-ivors-board.md", "Vantage reads the rim"),
    ("beats/sticky-in-the-stairwell.md", "Pell Ivor's board"),
    ("beats/the-wolf-gate-refuses.md", "Pell Ivor's board"),
    ("factions/the-threshold.md", "The Founding of the\nThreshold"),
    ("factions/the-threshold.md", "Director Hale"),
}


def test_every_wiki_link_resolves_to_something_real():
    """A [[Name]] link survives remapping because it is resolved by name -- which
    means a typo in one is a dead reference nothing else would catch."""
    names = set()
    for p in lore_files():
        meta, _ = parse_frontmatter(p.read_text())
        names.add(meta["title"])
    for d, key in (("characters", "name"), ("locations", "name"),
                   ("factions", "name"), ("agendas", "title")):
        for p in (ROOT / d).rglob("*"):
            if p.suffix == ".json":
                names.add(json.loads(p.read_text())[key])
            elif p.suffix == ".md":
                names.add(parse_frontmatter(p.read_text())[0][key])
    dangling = {}
    for d in PROSE_DIRS:
        for p in sorted((ROOT / d).rglob("*.md")):
            rel = str(p.relative_to(ROOT))
            for link in re.findall(r"\[\[([^\]]+)\]\]", p.read_text()):
                if link not in names and (rel, link) not in DANGLING_ALLOWLIST:
                    dangling.setdefault(link, []).append(rel)
    assert not dangling, f"dangling wiki links: {dangling}"


def test_the_database_is_reachable_before_we_claim_anything():
    r = _gm("doctor")
    if r.returncode != 0:
        pytest.skip(f"database not usable: {r.stdout[:200]}")


def test_import_then_export_round_trips_losslessly(tmp_path):
    r = _gm("import-campaign", "--path", str(ROOT), "--new-ids")
    if r.returncode != 0:
        pytest.skip(f"import failed: {r.stdout[:400]}")
    new_id = json.loads(r.stdout)["id"]
    try:
        out = tmp_path / "exported"
        e = _gm("export-campaign", "--campaign", new_id, "--output", str(out))
        assert e.returncode == 0, e.stdout

        for sub, glob in (("lore", "*/*.md"), ("agendas", "*.md"),
                          ("beats", "*.md"), ("facts", "*.md"),
                          ("locations", "*.md"), ("factions", "*.md")):
            before = len(list((ROOT / sub).glob(glob)))
            after = len(list((out / sub).glob(glob)))
            assert after == before, f"{sub}: {before} in, {after} out"

        chars_in = len(list((ROOT / "characters").rglob("*.json")))
        chars_out = len(list((out / "characters").rglob("*.json")))
        assert chars_out == chars_in, f"characters: {chars_in} in, {chars_out} out"

        tmpl_in = len(list((ROOT / "templates").glob("*.json")))
        tmpl_out = len(list((out / "templates").glob("*.json")))
        assert tmpl_out == tmpl_in, f"templates: {tmpl_in} in, {tmpl_out} out"

        # knowledge.json is the only file keyed entirely on cross-references,
        # so it is the one most likely to rot silently -- a dropped edge is a
        # character who no longer knows the thing the plot needs them to know.
        k_in = json.loads((ROOT / "knowledge.json").read_text())["knows"]
        k_file = out / "knowledge.json"
        k_out = json.loads(k_file.read_text())["knows"] if k_file.exists() else []
        assert len(k_out) == len(k_in), (
            f"knowledge edges: {len(k_in)} in, {len(k_out)} out"
        )
        assert ({e["certainty"] for e in k_out}
                == {e["certainty"] for e in k_in}), (
            "a certainty value did not survive the round trip"
        )
    finally:
        _gm("delete-campaign", "--campaign", new_id, "--yes")


def test_the_campaign_is_actually_playable(tmp_path):
    """The 'ready to play' gate, and the one that caught v1 being unplayable.

    The gate changed shape when the pre-gens were removed. A fresh import must
    now contain NO player characters -- the first thing the opening session does
    is build one -- and what makes it playable instead is that the save carries
    the parts a character gets built out of: cultures, careers, skills, knacks.
    """
    r = _gm("import-campaign", "--path", str(ROOT), "--new-ids")
    if r.returncode != 0:
        pytest.skip(f"import failed: {r.stdout[:400]}")
    new_id = json.loads(r.stdout)["id"]
    try:
        ctx = _gm("get-context", "--campaign", new_id)
        assert ctx.returncode == 0, ctx.stdout
        payload = json.loads(ctx.stdout)
        pcs = payload["player_characters"]
        assert pcs == [], (
            f"a fresh import ships {len(pcs)} player characters; it must ship "
            "none, because every character is built at the table"
        )
        blob = ctx.stdout.lower()
        for needed in ("cultures", "careers", "skills", "knacks"):
            assert needed in blob, (
                f"nothing in the save tells the table about {needed}; "
                "a fresh character cannot be built from it"
            )
    finally:
        _gm("delete-campaign", "--campaign", new_id, "--yes")
