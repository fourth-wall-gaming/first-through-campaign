"""The spec's hard content rules, as gates rather than aspirations."""
import json

import pytest

from content_rules import (
    LAUNCH_YEARS_AGO,
    ROOT,
    door_opened_years_ago,
    parse_frontmatter,
)


def test_frontmatter_parser_matches_the_importer():
    """campaign_io._parse_md JSON-decodes each value and falls back to the raw
    string. A parser that disagreed would validate something the engine never
    sees."""
    meta, body = parse_frontmatter(
        '---\n'
        'id: "myth-lore-0001"\n'
        'sources: ["https://example.org/a"]\n'
        'bare: not json\n'
        '---\n'
        'Body text.\n'
    )
    assert meta["id"] == "myth-lore-0001"
    assert meta["sources"] == ["https://example.org/a"]
    assert meta["bare"] == "not json"
    assert body == "Body text."


def test_the_arithmetic_is_the_spec_arithmetic():
    assert LAUNCH_YEARS_AGO == 975
    assert door_opened_years_ago(4.25) == 890   # Alpha Centauri
    assert door_opened_years_ago(8.71) == 801   # Sirius
    assert door_opened_years_ago(40.66) == 162  # TRAPPIST-1
    assert door_opened_years_ago(48.8) == -1    # LHS 1140: still inbound


def test_the_manifest_is_an_unplayed_seed():
    text = (ROOT / "campaign.yaml").read_text()
    assert 'id: "myth-campaign-first-through-s1"' in text
    assert "session_number: 0" in text
    assert 'format: "mythras-gm-campaign"' in text


def test_the_opening_scene_names_no_character_and_stops_the_gm():
    text = (ROOT / "campaign.yaml").read_text()
    scene = text.split('current_scene: "', 1)[1].split('"\n', 1)[0]
    for name in ("Calloway", "Tolk", "Ferren", "Hale", "Sarn"):
        assert name not in scene, f"the seed's opening scene names {name}"
    assert "/first-through:start" in scene


from content_rules import separation_ly, systems

V1_SYSTEMS = {
    "sol", "alpha-centauri", "barnards-star", "sirius", "gliese-65",
    "gliese-887", "gl-725", "61-cygni", "van-maanens-star",
    "trappist-1", "gj-1214", "lhs-1140",
}


def test_every_system_carries_a_real_source():
    for slug, s in systems().items():
        assert s.get("sources"), f"{slug} cites no source"
        for url in s["sources"]:
            assert url.startswith("https://"), f"{slug}: {url} is not a URL"


def test_door_dates_match_the_seedship_arithmetic():
    """The arithmetic in spec section 4 is the setting's load-bearing number.
    If a door date drifts from it the map stops being self-consistent."""
    for slug, s in systems().items():
        if slug == "sol":
            continue
        expected = door_opened_years_ago(s["distance_ly"])
        assert s["opened_years_ago"] == expected, (
            f"{slug}: distance {s['distance_ly']} ly implies {expected}, "
            f"file says {s['opened_years_ago']}"
        )


def test_lhs_1140_has_not_opened_yet():
    """It is the campaign spine precisely because it is still inbound."""
    assert systems()["lhs-1140"]["opened_years_ago"] < 0


def test_the_v1_systems_are_all_present():
    missing = V1_SYSTEMS - set(systems())
    assert not missing, f"v1 needs these systems: {sorted(missing)}"


def test_coordinates_reproduce_a_known_separation():
    """Sirius and Procyon are about 5.2 ly apart. If the coordinate convention
    is wrong (radians for degrees, or dec/ra swapped) this is the test that
    notices, and every edge length in Task 3 depends on it."""
    s = systems()
    gap = separation_ly(s["sirius"], s["procyon"])
    assert 4.5 < gap < 6.0, f"Sirius-Procyon came out {gap:.2f} ly"


from content_rules import YEARS_PER_LIGHT_YEAR, edges


def test_sirius_carries_exactly_nine_edges():
    """The Nine is named for its edge count. If this drifts the station is
    misnamed and the spec's first teaching image is wrong."""
    count = sum(1 for e in edges() if "sirius" in (e["a"], e["b"]))
    assert count == 9, f"Sirius carries {count} edges, not nine"


def test_every_edge_endpoint_is_a_known_system():
    known = set(systems())
    for e in edges():
        assert e["a"] in known, f"unknown endpoint {e['a']}"
        assert e["b"] in known, f"unknown endpoint {e['b']}"
        assert e["built_from"] in (e["a"], e["b"]), (
            f"{e['a']}-{e['b']}: built_from {e['built_from']} is not an endpoint"
        )


def _door_date(slug, s):
    """Sol is open from the launch itself; everywhere else has an arrival date."""
    return LAUNCH_YEARS_AGO if slug == "sol" else s[slug]["opened_years_ago"]


def test_every_edge_opens_when_its_later_half_lands():
    """An anchor is a PAIR of independent devices. Every far half rode the one
    great launch from Sol, which is why 975 - 20d holds for every system; what
    varies is where the First Reach placed each half's mate. So a link comes
    into service on the date its later half arrives -- the smaller years-ago of
    its two endpoints -- and never before."""
    s = systems()
    for e in edges():
        a, b = _door_date(e["a"], s), _door_date(e["b"], s)
        assert e["opened_years_ago"] == min(a, b), (
            f"{e['a']}-{e['b']}: later half lands {min(a, b)} yr ago, "
            f"file says {e['opened_years_ago']}"
        )
        assert e["opened_years_ago"] > 0, f"{e['a']}-{e['b']} has not opened"


def test_built_from_is_the_end_that_already_had_its_door():
    """The mate has to be sitting there before the far half lands, so the node
    holding it is always the end that opened first."""
    s = systems()
    for e in edges():
        other = e["b"] if e["built_from"] == e["a"] else e["a"]
        assert _door_date(e["built_from"], s) >= _door_date(other, s), (
            f"{e['a']}-{e['b']}: built_from {e['built_from']} opened after "
            f"{other}, so the mate was not there yet"
        )


def test_the_graph_is_connected_from_sol():
    adj = {}
    for e in edges():
        adj.setdefault(e["a"], set()).add(e["b"])
        adj.setdefault(e["b"], set()).add(e["a"])
    seen, stack = {"sol"}, ["sol"]
    while stack:
        for n in adj.get(stack.pop(), ()):
            if n not in seen:
                seen.add(n)
                stack.append(n)
    unreachable = {k for k, v in systems().items() if v["opened_years_ago"]} - seen
    unreachable = {u for u in unreachable if u in adj}
    assert not unreachable, f"no route from Sol to {sorted(unreachable)}"


def test_lhs_1140_has_no_edge_yet():
    assert not [e for e in edges() if "lhs-1140" in (e["a"], e["b"])]


import re

from content_rules import lore_files

HEX12 = re.compile(r"^myth-lore-[0-9a-f]{12}$")
CITED_CATEGORIES = {"geography", "cosmology"}


def test_every_lore_entry_has_a_well_formed_unique_id():
    seen = {}
    for p in lore_files():
        meta, _ = parse_frontmatter(p.read_text())
        assert HEX12.match(str(meta.get("id", ""))), f"{p.name}: bad id"
        assert meta["id"] not in seen, f"{p.name} reuses the id of {seen.get(meta['id'])}"
        seen[meta["id"]] = p.name


def test_category_matches_the_directory():
    for p in lore_files():
        meta, _ = parse_frontmatter(p.read_text())
        assert meta.get("category") == p.parent.name, (
            f"{p.name}: category {meta.get('category')!r} in {p.parent.name}/"
        )


def test_gm_only_directories_are_never_player_visible():
    """A player-visible gm-secret entry hands a child the ending."""
    for p in lore_files():
        if p.parent.name in {"gm-guide", "gm-secret"}:
            meta, _ = parse_frontmatter(p.read_text())
            assert meta.get("visibility") == "gm", f"{p.name} is not gm-only"


def test_astronomical_categories_cite_their_sources():
    for p in lore_files():
        if p.parent.name not in CITED_CATEGORIES:
            continue
        meta, _ = parse_frontmatter(p.read_text())
        assert meta.get("sources"), f"{p.name} makes astronomical claims uncited"


def test_the_briefing_teaches_percentages_without_a_rules_lecture():
    """Spec section 8: nothing to read before play, and the mechanics wall does
    the teaching. The briefing must not grow into a rulebook."""
    p = ROOT / "lore/player-briefing/first-through-the-sixty-second-briefing.md"
    meta, body = parse_frontmatter(p.read_text())
    assert meta["visibility"] == "player"
    assert len(body.split()) < 400, "a sixty-second briefing is under 400 words"
    assert "Passion" in body, "Passions are the good bit; say so"
    for banned in ("d20", "Action Point", "difficulty grade"):
        assert banned not in body, f"the briefing lectures about {banned}"


def test_the_sum_entry_states_the_load_bearing_number():
    p = ROOT / "lore/cosmology/twenty-years-to-the-light-year.md"
    _, body = parse_frontmatter(p.read_text())
    assert "975" in body and "twenty" in body.lower()
    assert "48.7" in body or "48.8" in body, "the frontier distance must appear"


def test_geography_entries_name_a_system_in_the_data():
    """A geography entry either names exactly one real system -- and is then held
    to that system's distance -- or declares none and is a survey covering many.
    The filename special-case this replaces only ever covered one survey."""
    known = set(systems())
    found = set()
    for p in lore_files("geography"):
        meta, _ = parse_frontmatter(p.read_text())
        slug = meta.get("system")
        if slug is None:
            continue
        assert slug in known, f"{p.name}: system {slug!r} is not in data/systems.json"
        found.add(slug)
    assert V1_SYSTEMS - {"sol", "alpha-centauri", "gl-725"} <= found, (
        f"v1 systems with no prose: {sorted(V1_SYSTEMS - found)}"
    )


def test_geography_prose_agrees_with_the_data_on_distance():
    """Prose and data drifting apart is how a campaign starts lying to a kid
    who looked it up."""
    for p in lore_files("geography"):
        meta, body = parse_frontmatter(p.read_text())
        slug = meta.get("system")
        if not slug:
            continue
        ly = systems()[slug]["distance_ly"]
        assert f"{ly:.1f}" in body or f"{ly:.2f}" in body or str(round(ly)) in body, (
            f"{p.name} never states its own distance ({ly} ly)"
        )


NON_LETHAL_WEAPON_WORDS = ("stunner", "shock baton", "restraint", "net", "gel")


def test_the_tally_wants_prisoners_not_corpses():
    """Spec section 12: the antagonist's own motive supplies the non-lethal rule.
    If this entry ever loses that, the convention becomes a house rule again."""
    p = ROOT / "lore/organizations/the-tally.md"
    _, body = parse_frontmatter(p.read_text())
    assert "manifest" in body.lower()
    assert any(w in body.lower() for w in NON_LETHAL_WEAPON_WORDS)


def test_the_kit_entry_explains_charge_without_naming_power_points():
    """The mechanics wall: prose never contains rules vocabulary."""
    p = ROOT / "lore/technology/a-first-throughs-kit.md"
    _, body = parse_frontmatter(p.read_text())
    assert "charge" in body.lower()
    for banned in ("Power Point", "POW", "Boost", "Limit"):
        assert banned not in body, f"the kit entry leaks the rules word {banned!r}"


import json as _json

NAMED_CAST = {
    "calloway", "tolk", "ferren", "councillor-hale",
    "tallyman-captain-brace", "sep-anwar", "meriel-koll",
    "tace-orun", "benno-raske", "rill",
}


def test_the_named_cast_is_present():
    have = {p.stem for p in (ROOT / "characters" / "npcs").glob("*.json")}
    assert NAMED_CAST <= have, f"missing: {sorted(NAMED_CAST - have)}"


def test_every_character_declares_pronouns():
    """Guessing a character's pronouns from their name misgenders them in a way
    the neutral default never does."""
    for p in (ROOT / "characters").rglob("*.json"):
        c = _json.loads(p.read_text())
        assert (c.get("extras") or {}).get("pronouns"), f"{p.name} declares none"


def test_no_hill_proper_nouns_anywhere_in_the_repo():
    """Global Constraints: we inherit the shape, never the names."""
    banned = ("Keill", "Randor", "Glr", "Moros", "Veynaa",
              "Overseer", "Deathwing", "Galactic Warlord")
    for p in list(ROOT.rglob("*.md")) + list(ROOT.rglob("*.json")):
        if ".git" in p.parts or "docs" in p.parts or ".superpowers" in p.parts:
            continue
        text = p.read_text()
        for word in banned:
            assert word not in text, f"{p.relative_to(ROOT)} contains {word!r}"


def test_v1_never_shows_the_quorum_his_face():
    """Spec section 11: v1 ships only the bottom rung of the reveal ladder."""
    for p in (ROOT / "characters").rglob("*.json"):
        c = _json.loads(p.read_text())
        assert c["name"] != "Sarn", "Sarn has no sheet in v1"
    player_visible = [
        p for p in lore_files()
        if parse_frontmatter(p.read_text())[0].get("visibility") == "player"
    ]
    for p in player_visible:
        body = p.read_text()
        assert "pattern transfer" not in body.lower(), f"{p.name} leaks Act 3"
        assert "copies of himself" not in body.lower()


def test_invented_life_is_flagged_and_placed():
    """Spec section 12's correction to 3.1: astronomy is fixed and real, life is
    invented but constrained. An organism placed without a flag and a host system
    is the one way this repo could quietly start making things up."""
    organisms = [p for p in lore_files()
                 if parse_frontmatter(p.read_text())[0].get("invented")]
    for p in organisms:
        meta, _ = parse_frontmatter(p.read_text())
        assert meta["invented"] == "life", f"{p.name}: invented={meta['invented']!r}"
        assert meta.get("system") in set(systems()), (
            f"{p.name} places life in {meta.get('system')!r}, not a real system"
        )
    creature_homes = {
        (_json.loads(p.read_text()).get("extras") or {}).get("home_system")
        for p in (ROOT / "characters" / "creatures").glob("*.json")
    }
    for home in creature_homes - {None}:
        assert home in set(systems()), f"a creature is from {home!r}, not a real system"


def test_locations_sit_in_a_known_system():
    known = set(systems())
    paths = sorted((ROOT / "locations").glob("*.md"))
    assert paths, "no locations"
    for p in paths:
        meta, _ = parse_frontmatter(p.read_text())
        assert re.match(r"^myth-loc-[0-9a-f]{12}$", str(meta.get("id", "")))
        assert meta.get("system") in known, f"{p.name}: system {meta.get('system')!r}"


def test_both_entry_points_have_somewhere_to_happen():
    systems_used = {
        parse_frontmatter(p.read_text())[0].get("system")
        for p in (ROOT / "locations").glob("*.md")
    }
    assert "gliese-887" in systems_used, "entry point A has no location"
    assert "gliese-65" in systems_used, "entry point B has no location"
    assert "sirius" in systems_used, "the Nine has no location"


ENTRY_POINTS = {"how-many"}


def test_every_entry_point_declares_itself():
    for p in lore_files("entry-points"):
        meta, _ = parse_frontmatter(p.read_text())
        assert meta.get("entry_point") in ENTRY_POINTS, (
            f"{p.name} declares entry_point={meta.get('entry_point')!r}"
        )


def test_each_entry_point_is_solvable_without_a_particular_character():
    """Spec section 6: every scenario must be solvable by whoever the player
    built. With the pre-gens gone there is no cast list to check against, so the
    guard inverts: an entry point must NOT require a named pre-gen, and must not
    assume one approach is the only way through.

    This test used to iterate characters/pcs/*.json. When those were deleted it
    passed by iterating nothing, which is worse than failing."""
    gone = {"The Runner", "The Tinker", "The Talker", "The Fieldhand"}
    found = list(lore_files("entry-points"))
    assert found, "no entry points"
    guides = "\n".join(p.read_text() for p in lore_files("gm-guide"))
    for p in found:
        body = p.read_text()
        for name in gone:
            assert name not in body, (
                f"{p.stem} still names the retired pre-gen {name!r}; a built "
                "character has no idea who that is"
            )
    for name in gone:
        assert name not in guides, f"a gm-guide entry still names {name!r}"


def test_the_tally_alone_is_armed_non_lethally():
    """Not a safety net -- a motive. The Tally wants prisoners because a body is
    not a line on a manifest, which makes the professionals the safest people in
    the setting and the frightened civilians the dangerous ones. That is the
    right way round, and it only reads if the Tally's own gear says so."""
    tally = [p for p in (ROOT / "characters").rglob("*.json")
             if (_json.loads(p.read_text()).get("extras") or {}).get("faction") == "the-tally"]
    assert tally, "no Tally characters to check"
    for p in tally:
        c = _json.loads(p.read_text())
        gear = " ".join(c.get("equipment", [])).lower()
        assert any(w in gear for w in ("baton", "restraint")), f"{p.name} carries no restraints"
        for lethal in ("rifle", "sidearm", "blade", "knife", "pistol", "sword"):
            assert lethal not in gear, f"{p.name}: a tallyman carries a {lethal}"


def test_the_opener_gives_a_guaranteed_early_success():
    """Spec section 8, fourth onboarding device: one guaranteed success before
    the first real risk, so the first mechanics block a player ever sees is one
    that worked. It was implemented in The Quiet Door only -- and Flare is the
    track an impulsive first-timer is more likely to pick."""
    for p in lore_files("entry-points"):
        _, body = parse_frontmatter(p.read_text())
        # Prose wraps, so match on collapsed whitespace rather than the
        # accident of where a line happened to break.
        low = " ".join(body.lower().split())
        assert "cannot fail" in low and "guaranteed" in low, (
            f"{p.name} has no guaranteed early success"
        )


BANNED_IN_PROSE = [
    "arithmetic", "the calculus of", "the math of", "the ledger of it",
    "wallpaper", "nobody has ever asked me that", "cost her something to say",
    "tilts her head", "lets the silence do the work",
    # Used twice in one session, two hours apart, for two different creatures.
    # The guard only scans shipped files and cannot see live narration, which is
    # where these actually land -- but banning it here at least stops it reaching
    # the worldbook.
    "pretending to be furniture",
]


def test_no_banned_constructions_in_shipped_prose():
    """TABLE.md section 1 and the Gamesmaster style card ban these outright --
    'arithmetic' as a *word*, not merely as a metaphor, because it was the most
    characteristic tic in the baseline.

    They were banned for narration and dialogue, and lore gets read aloud and
    paraphrased at the table all session, so it leaks. It had leaked into twelve
    files and an entry title before anybody noticed.

    facts/, locations/ and setting/ were missing from this list, and a fact file
    kept the word through the whole sweep because nothing looked at it. Fact
    statements are read at the table like any other prose."""
    hits = {}
    for p in list(lore_files()) + sorted((ROOT / "beats").glob("*.md")) \
            + sorted((ROOT / "agendas").glob("*.md")) \
            + sorted((ROOT / "facts").glob("*.md")) \
            + sorted((ROOT / "locations").glob("*.md")) \
            + sorted((ROOT / "setting").glob("*.md")) \
            + sorted((ROOT / "characters").rglob("*.json")):
        low = p.read_text().lower()
        for w in BANNED_IN_PROSE:
            if w in low:
                hits.setdefault(w, []).append(p.name)
    assert not hits, f"banned constructions in shipped prose: {hits}"


# Materials that put the setting in the wrong century. The interstellar layer is
# low-tech for a sound reason -- nothing outruns a courier, so paper in a hand is
# genuinely the fastest channel between stars -- and that reasoning was once
# wrongly extended inward, leaving a forty-thousand-person cylinder that
# engineers gravitational potential keeping its most important record on a slate.
#
# Writing by hand on a surface is still normal and current: monomer sheets, pens,
# boards, displays. It is the MATERIAL that was wrong, not the gesture.
ANACHRONISTIC_MATERIALS = ["chalk", "slate", "chalked", "chalkboard"]


def test_no_chalk_or_slate_in_shipped_prose():
    """A hub that manipulates gravity does not keep records in chalk dust.

    Word-bounded on purpose: 'translate' and 'translation' contain 'slate' and
    are perfectly good words. An unbounded match flagged four files that were
    entirely innocent.
    """
    import re as _re
    pattern = _re.compile(
        r"\b(" + "|".join(ANACHRONISTIC_MATERIALS) + r")\b", _re.I)
    hits = {}
    for p in (list(lore_files())
              + sorted((ROOT / "beats").glob("*.md"))
              + sorted((ROOT / "agendas").glob("*.md"))
              + sorted((ROOT / "facts").glob("*.md"))
              + sorted((ROOT / "locations").glob("*.md"))
              + sorted((ROOT / "setting").glob("*.md"))
              + sorted((ROOT / "characters").rglob("*.json"))
              + [ROOT / "campaign.yaml", ROOT / "README.md"]):
        if not p.exists():
            continue
        for m in set(x.lower() for x in pattern.findall(p.read_text())):
            hits.setdefault(m, []).append(p.name)
    assert not hits, f"anachronistic materials in shipped prose: {hits}"
