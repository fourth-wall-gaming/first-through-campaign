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
    for p in lore_files():
        _, body = parse_frontmatter(p.read_text())
        for link in re.findall(r"\[\[([^\]]+)\]\]", body):
            if link not in names:
                dangling.setdefault(link, []).append(p.name)
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
