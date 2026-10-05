"""Seed invariants. A seed that has been played is not a seed."""
import glob
import json
from pathlib import Path

from content_rules import ROOT, parse_frontmatter

SEED_ID = "myth-campaign-first-through-s1"


def test_every_beat_is_pending():
    paths = glob.glob(str(ROOT / "beats" / "*.md"))
    assert len(paths) >= 20, f"only {len(paths)} beats"
    for b in paths:
        meta, _ = parse_frontmatter(Path(b).read_text())
        assert meta.get("status") == "pending", f"{Path(b).name} is not pending"


def test_the_journal_holds_one_seed_note():
    events = json.loads((ROOT / "journal" / "events.json").read_text())
    assert len(events) == 1, f"a seed carries one note, not {len(events)}"
    assert events[0]["type"] == "gm-note"


def test_agendas_reference_real_characters():
    ids = {json.loads(p.read_text())["id"]
           for p in (ROOT / "characters").rglob("*.json")}
    paths = sorted((ROOT / "agendas").glob("*.md"))
    assert len(paths) >= 12, f"only {len(paths)} agendas"
    for p in paths:
        meta, _ = parse_frontmatter(p.read_text())
        assert meta["holder"] in ids, f"{p.name}: holder {meta['holder']} unknown"
        for t in meta.get("targets") or []:
            assert t in ids, f"{p.name}: target {t} unknown"
        assert meta["clock_filled"] == 0, f"{p.name} has a started clock"


def test_beats_reference_real_agendas_and_places():
    agendas = {parse_frontmatter(p.read_text())[0]["id"]
               for p in (ROOT / "agendas").glob("*.md")}
    places = {parse_frontmatter(p.read_text())[0]["id"]
              for p in (ROOT / "locations").glob("*.md")}
    for p in (ROOT / "beats").glob("*.md"):
        meta, _ = parse_frontmatter(p.read_text())
        assert meta["agenda"] in agendas, f"{p.name}: agenda {meta['agenda']}"
        assert meta["place"] in places, f"{p.name}: place {meta['place']}"


def test_both_entry_point_systems_have_a_living_world():
    """A player who takes either route must still meet a world in motion."""
    place_system = {}
    for p in (ROOT / "locations").glob("*.md"):
        meta, _ = parse_frontmatter(p.read_text())
        place_system[meta["id"]] = meta["system"]
    count = {}
    for p in (ROOT / "beats").glob("*.md"):
        meta, _ = parse_frontmatter(p.read_text())
        s = place_system[meta["place"]]
        count[s] = count.get(s, 0) + 1
    for s in ("gliese-887", "gliese-65"):
        assert count.get(s, 0) >= 6, f"{s} has only {count.get(s, 0)} beats"


def test_the_act_two_reveal_is_a_fact_not_a_memory():
    """Spec section 13: the facts graph carries what the player has learned, so
    the reveal is computed rather than improvised."""
    paths = sorted((ROOT / "facts").glob("*.md"))
    assert len(paths) >= 9, f"only {len(paths)} facts"
    titles = [parse_frontmatter(p.read_text())[0]["title"].lower() for p in paths]
    assert any("forty years" in t or "has known" in t for t in titles), (
        "no fact records the Threshold's forty-year silence"
    )
    for p in paths:
        meta, _ = parse_frontmatter(p.read_text())
        assert meta["status"] in ("not-yet-true", "established")
        assert meta["truth"] in ("true", "false")


def test_a_believed_falsehood_exists():
    """Status and truth are independent in this engine, which makes a believed
    falsehood a first-class object. The campaign's central lie needs to be one."""
    falsehoods = [p for p in (ROOT / "facts").glob("*.md")
                  if parse_frontmatter(p.read_text())[0]["truth"] == "false"]
    assert falsehoods, "nothing in the fact graph is established and false"


def test_knowledge_edges_point_at_real_facts_and_knowers():
    k = json.loads((ROOT / "knowledge.json").read_text())
    facts = {parse_frontmatter(p.read_text())[0]["id"]
             for p in (ROOT / "facts").glob("*.md")}
    chars = {json.loads(p.read_text())["id"]
             for p in (ROOT / "characters").rglob("*.json")}
    assert k["knows"], "no knowledge edges"
    for e in k["knows"]:
        assert e["fact"] in facts, f"knowledge edge cites unknown fact {e['fact']}"
        assert e["knower"] in chars, f"knowledge edge cites unknown knower {e['knower']}"
        assert e["certainty"] in ("knows", "believes", "suspects")


import re

WATCHES = ("dawn", "day", "dusk", "night")
TIME_KEY = re.compile(r"^\s*d\s*(-?\d+)\s*/\s*([a-z]+)\s*$", re.I)


def _parse_time_key(key):
    """Mirrors mythras_engine.parse_time_key. A beat whose `when` does not
    parse fails the whole import, not just itself -- which is how this was
    found."""
    m = TIME_KEY.match(key or "")
    assert m, f"bad time key {key!r}: expected '<day>/<watch>', e.g. 'd-3/night'"
    assert m.group(2).lower() in WATCHES, f"bad watch in {key!r}"
    day = int(m.group(1))
    index = (day + 16) * 4 + WATCHES.index(m.group(2).lower())
    assert index >= 0, f"time key too early to represent: {key!r}"
    return index


def test_every_beat_when_parses_as_a_time_key():
    for p in (ROOT / "beats").glob("*.md"):
        meta, _ = parse_frontmatter(p.read_text())
        _parse_time_key(meta["when"])


def test_the_manifest_clock_agrees_with_its_own_game_date():
    text = (ROOT / "campaign.yaml").read_text()
    game_date = re.search(r'game_date: "([^"]+)"', text).group(1)
    time_index = int(re.search(r"time_index: (\d+)", text).group(1))
    assert _parse_time_key(game_date.split(" --")[0]) == time_index, (
        f"game_date {game_date!r} and time_index {time_index} disagree"
    )


def test_no_beat_is_already_due_at_the_seed_clock():
    """A seed whose beats are in the past fires them all on the first tick."""
    text = (ROOT / "campaign.yaml").read_text()
    start = int(re.search(r"time_index: (\d+)", text).group(1))
    for p in (ROOT / "beats").glob("*.md"):
        meta, _ = parse_frontmatter(p.read_text())
        assert _parse_time_key(meta["when"]) > start, (
            f"{p.name} is at or before the seed clock"
        )
