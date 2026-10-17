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


def test_the_tally_counts_no_crates_and_has_no_clerks():
    for rel in ("lore/organizations/the-tally.md", "factions/the-tally.md"):
        text = (ROOT / rel).read_text().lower()
        assert "lading" in text, rel
        assert "masonic" in text or "rites" in text, rel
        assert "counting house" not in text, rel


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
    # Banned at the table's request, and narrowly: the offence is not "nobody
    # has ever" as a statement of physical fact -- nobody has ever had a knack
    # without crossing, and that is a law of the setting. The offence is
    # specifically information or competence sitting UNASKED until the player
    # arrives. It makes any noun instantly significant, flatters the player,
    # fits anywhere, and flattens an NPC into somebody who was standing around
    # waiting for a fifteen-year-old.
    # Banned at the table's request: describing a thing as weather. It is a
    # tic, not an image -- it fits any noun, it always means "unremarkable
    # background nobody attends to", and it had reached the novel, both
    # guidebooks and six places in the worldbook. Literal weather is fine and
    # is all over this setting: Earth has weather, Luhman 16 has storm bands,
    # a fathom goes out to feel a sky that is not its own. The ban is on the
    # metaphor.
    "like weather",
    "is weather",
    "a weather event",
    "filed as weather",
    "describing weather",
    "calling it weather",
    "into weather",
    "a weather system passing",
    "nobody has ever asked",
    "nobody had ever asked",
    "has never been asked",
    "nobody has ever thought to ask",
    "in four hundred years nobody",
    "in six hundred years nobody",
    "in nine hundred years nobody",
    # Characters announcing their own characterisation. A card that says an NPC
    # tells you the worst thing first describes a BEHAVIOUR; the moment she says
    # so out loud it becomes a catchphrase, and three NPCs were doing it.
    "the part you won't like",
    "you're not going to like",
    "i'd rather you had it from me",
    "the thing you did not ask for",
    "the thing you didn't ask for",
    "i want to say the unwelcome thing",
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
              # Everything published, not just the campaign source: the guide
              # and the novel are shipped prose too, and chalk got into both of
              # them while this test watched only lore/.
              + sorted((ROOT / "guide").rglob("*.md"))
              + sorted((ROOT / "novels").rglob("*.md"))
              + sorted((ROOT / "novels").rglob("*.txt"))
              + [ROOT / "campaign.yaml", ROOT / "README.md"]):
        if not p.exists() or ".build" in p.parts or p.name == "source.md":
            continue
        for m in set(x.lower() for x in pattern.findall(p.read_text())):
            hits.setdefault(m, []).append(p.name)
    assert not hits, f"anachronistic materials in shipped prose: {hits}"


# Vague period language in an entry whose data file carries a real figure. This
# is how "a few years" sat in the Gliese 65 entry for the life of the campaign
# while data/systems.json knew nothing either way -- and the figure turned out to
# be 26.5, which is not a few, and which the plot then depended on.
VAGUE_PERIODS = ["a few years", "every few years", "in a few years",
                 "some years", "a handful of years"]


def test_systems_with_an_orbital_period_state_it_rather_than_waving_at_it():
    """A system whose data carries a period may not describe it vaguely in prose.

    The error this catches: the twins were written as going "round each other in
    a few years". They are an eccentric 26.5-year pair, a human career spans one
    cycle, and that is the entire reason nobody has ever seen the door do this
    twice. The vague phrasing was not merely imprecise -- it made the central
    mechanism of Act I impossible.
    """
    import re as _re
    systems = _json.loads((ROOT / "data" / "systems.json").read_text())
    timed = {k for k, v in systems.items() if v.get("orbital_period_years")}
    assert timed, "no system in the data carries an orbital period"

    offenders = {}
    for p in lore_files():
        meta, body = parse_frontmatter(p.read_text())
        if meta.get("system") not in timed:
            continue
        low = body.lower()
        for phrase in VAGUE_PERIODS:
            if phrase in low:
                offenders.setdefault(p.name, []).append(phrase)
    assert not offenders, (
        "these entries wave at a period their data file states exactly: "
        + repr(offenders))


def test_the_flare_twins_orbit_is_cited_and_specific():
    """The number Act I turns on. Pinned here so prose, data and plot agree."""
    g = _json.loads((ROOT / "data" / "systems.json").read_text())["gliese-65"]
    assert g["orbital_period_years"] == 26.5
    assert g["eccentricity"] > 0.5, "an eccentric pair is the whole mechanism"
    assert any("Luyten" in s for s in g["sources"]), \
        "the orbital claim needs a source naming the system properly"


from content_rules import all_content_files, edges, lore_ids  # noqa: E402,F401

# Captured 2026-10-17, before the v3 rewrite began. These ids are the join
# keys to myth-campaign-first-through-s1, which is live at session 6. A
# rewrite may change every word of a file and may not change its id.
FROZEN_LORE_IDS = {
    "myth-lore-00f5a2ee8da5",
    "myth-lore-05fed24a8ade",
    "myth-lore-097b6b387d5a",
    "myth-lore-0c2a6f8d41be",
    "myth-lore-0e572f6e6a9d",
    "myth-lore-110b1d05a1e5",
    "myth-lore-16eb77a71842",
    "myth-lore-2108cfa5c688",
    "myth-lore-2377b7ce1f63",
    "myth-lore-279ae6bae609",
    "myth-lore-3979ec5f87f3",
    "myth-lore-3bef00a7d4e2",
    "myth-lore-3dec75146a40",
    "myth-lore-3e8342b40612",
    "myth-lore-439f3a242ea1",
    "myth-lore-5613432aa61f",
    "myth-lore-5b1e7c4d9a20",
    "myth-lore-5f0e076b4984",
    "myth-lore-5fee0ba432ef",
    "myth-lore-659a9ff9a80d",
    "myth-lore-73eea8e24ff0",
    "myth-lore-749358146117",
    "myth-lore-75d9a4de9bd2",
    "myth-lore-7755c4a9f7ed",
    "myth-lore-8731e70dfa10",
    "myth-lore-8770c99bc8be",
    "myth-lore-8bcd4d760526",
    "myth-lore-8c4b31f0e76a",
    "myth-lore-8eb6ff2d406a",
    "myth-lore-8ebc99246045",
    "myth-lore-8ecc45aa88cb",
    "myth-lore-8f41c0d7b3e2",
    "myth-lore-8f522365c640",
    "myth-lore-8fd22ae103b9",
    "myth-lore-a4332cad97d3",
    "myth-lore-a459177a8189",
    "myth-lore-a47dd64a96ab",
    "myth-lore-afdaeb1c5584",
    "myth-lore-b6e40e30b51d",
    "myth-lore-ba9f231a772d",
    "myth-lore-c1f7f44d3517",
    "myth-lore-c594ab5a2972",
    "myth-lore-c6d0912602a4",
    "myth-lore-c90f1f5d276f",
    "myth-lore-d486f7ce9720",
    "myth-lore-d505b6391a05",
    "myth-lore-d7adc12b2427",
    "myth-lore-dabd9cbe122f",
    "myth-lore-dd6b9847d91b",
    "myth-lore-df675e04ba0d",
    "myth-lore-e083adf7a80b",
    "myth-lore-ec404a2af3a0",
    "myth-lore-ec9c42d1a5ed",
    "myth-lore-f4b65d700def",
    "myth-lore-f8d1d0bd3403",
    "myth-lore-fdaef1cb24de",
    "myth-lore-fe204c24a122",
    "myth-lore-febec6062bc0",
}

# Ids deliberately removed by a later task, each with the task that did it.
REMOVED_LORE_IDS = {
    # Task 6 deleted lore/cosmology/the-cold-arm.md: a passive affliction with
    # no move in it. The field survives as what the Listen reads.
    "myth-lore-c73a0e51f8bd",
}


def test_no_lore_id_is_lost_or_changed():
    """Subset semantics, not equality: later tasks legitimately create new
    lore files. What must never happen is a frozen id going missing or being
    edited, because the ids are the join keys to a live save."""
    expected = set(FROZEN_LORE_IDS) - REMOVED_LORE_IDS
    missing = expected - lore_ids()
    assert not missing, f"lore ids lost or changed: {sorted(missing)}"


def test_every_system_has_a_population_and_a_door_count():
    for key, s in systems().items():
        assert isinstance(s.get("population"), int), f"{key} has no population"
        assert isinstance(s.get("doors"), int), f"{key} has no door count"


def test_the_scale_is_thirty_billion():
    total = sum(s["population"] for s in systems().values())
    assert 25_000_000_000 <= total <= 35_000_000_000, total


def test_sol_holds_most_of_humanity_and_sirius_holds_almost_none():
    s = systems()
    assert s["sol"]["population"] > 9_000_000_000
    assert s["sirius"]["population"] == 40_000
    assert s["sirius"]["doors"] == 9
    assert s["sol"]["doors"] == 7


WORD_NUMS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60, "sixty-one": 61,
    "a hundred": 100, "two hundred": 200, "four hundred": 400,
}
SCALES = {"thousand": 1_000, "million": 1_000_000, "billion": 1_000_000_000}

# Geography pages whose people-figures contradict their data row on purpose
# or pending a rewrite. Each entry names the task that owns the fix. Content
# is never edited to satisfy this gate from Task 1.
GEOGRAPHY_POPULATION_ALLOWLIST = {
    # "page-name.md": "Task N rewrites the figure",
}


def people_figures(body):
    """Every population figure in a body, as integers: digit-form
    ("12,000 people") and spelled-out ("Forty thousand people"). This repo
    spells its numbers out, so a digits-only matcher can never fire."""
    import re as _re
    words = "|".join(sorted(map(_re.escape, WORD_NUMS), key=len, reverse=True))
    digits = _re.compile(r"\b(\d[\d,]*)\s+people\b", _re.I)
    spelled = _re.compile(
        rf"\b({words})(?:\s+({'|'.join(SCALES)}))?\s+people\b", _re.I)
    found = [int(m.replace(",", "")) for m in digits.findall(body)]
    for word, scale in spelled.findall(body):
        found.append(WORD_NUMS[word.lower()] * (SCALES[scale.lower()] if scale else 1))
    return found


def test_people_figures_reads_both_house_styles():
    assert people_figures("Forty thousand people live in it.") == [40_000]
    assert people_figures("Four\nthousand people farm it") == [4_000]
    assert people_figures("a crew of 61 people; 3,000 people") == [61, 3_000]
    assert people_figures("sixty-one people") == [61]
    assert people_figures("two million people") == [2_000_000]
    assert people_figures("what people built here") == []


def test_no_geography_page_contradicts_its_data_row():
    """van Maanen's with two staff is the line that broke this setting's
    credibility. Deliberately narrow: every "N people" figure on a geography
    page (digits or spelled out) must equal that system's data population.
    It is not a prose parser."""
    s = systems()
    bad, checked = [], 0
    for p in lore_files("geography"):
        meta, body = parse_frontmatter(p.read_text())
        key = meta.get("system")
        if key not in s or p.name in GEOGRAPHY_POPULATION_ALLOWLIST:
            continue
        for n in people_figures(body):
            checked += 1
            if n != s[key]["population"]:
                bad.append(f"{p.name}: {n} people, data says "
                           f"{s[key]['population']}")
    assert checked, "the gate found no population figure on any page"
    assert not bad, "\n".join(bad)


def test_doors_are_derived_from_the_edge_data():
    """data/edges.json is the authority on the network and existing tests
    already gate it. A door count written by hand in a second place is the
    exact drift this project exists to fix."""
    import collections
    deg = collections.Counter()
    for e in edges():
        deg[e["a"]] += 1
        deg[e["b"]] += 1
    for key, s in systems().items():
        assert s["doors"] == deg[key], f"{key}: {s['doors']} != {deg[key]}"
    assert sum(deg.values()) == 54, sum(deg.values())
    assert deg["lhs-1140"] == 0


NAKEDNESS = re.compile(
    r"\b(naked|nakedness|undress(?:es|ed|ing)?|disrobe\w*|dressing[- ]room)\b",
    re.I)


def test_nobody_ever_arrives_naked():
    """Audience constraint, not flavour: this is a game a 10-15 year old plays
    alone with an AI GM, and a mandatory undress-cross-dress beat on every
    transit is not acceptable regardless of how elegant the physics is."""
    bad = []
    for p in all_content_files():
        for n, line in enumerate(p.read_text().splitlines(), 1):
            if NAKEDNESS.search(line):
                bad.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()}")
    assert not bad, "\n".join(bad)


def test_the_weave_crosses_and_freight_does_not():
    text = (ROOT / "lore/the-crossing/what-crosses-easily.md").read_text().lower()
    assert "weave" in text
    assert "freight does not cross" in text
    assert "grown" in text


# ---- Task 3: there is no paper ------------------------------------------
from content_rules import FIRST_PASS_DIRS, content_files  # noqa: E402

PAPER = re.compile(
    r"\b(ledger|ledgers|logbook|log ?book|tome|tomes|clerk|clerks|clerical"
    r"|filing cabinet|paperwork|bureaucrat\w*|rubber[- ]stamp\w*"
    r"|carbon copy|in triplicate|typed|typewrit\w*)\b", re.I)

# Inside a system there is no reason to write anything down. Between stars
# the channel is living cells. Paper is a v1 artefact in both places.
PAPER_ALLOWED = {
    "docs",                      # specs and plans may discuss what was deleted
    "lore/history",              # the Sorting and the First Reach are historical
}

# Per-file, each naming the task that owns the fix. Task 11 empties this list
# and asserts it is empty. A NEW offender fails loudly; this only shrinks.
PAPER_ALLOWLIST = {
    "lore/geography/earth.md",                        # Task 11
    "lore/entry-points/how-many.md",                  # Task 11
    "lore/gm-guide/running-a-staged-crisis.md",       # Task 11
    "lore/technology/stunners-and-restraints.md",     # Task 11
}


def _exempt(p):
    rel = str(p.relative_to(ROOT))
    return any(rel.startswith(a) for a in PAPER_ALLOWED) or rel in PAPER_ALLOWLIST


def test_there_is_no_paper_left_in_the_causeway():
    bad = []
    for p in content_files(FIRST_PASS_DIRS):
        if _exempt(p):
            continue
        for n, line in enumerate(p.read_text().splitlines(), 1):
            if PAPER.search(line):
                bad.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()}")
    assert not bad, "\n".join(bad)


# Character sheets are .json, which the *.md walk above never saw. Edits here
# touch live passions in a running campaign and a TypeDB save, so they are
# Task 11 and Task 12 together. This only shrinks.
SHEET_PAPER_ALLOWLIST = {
    "characters/creatures/tallyman.json",             # Task 11/12: passion "The ledger balances" (55)
    "characters/npcs/tallyman-captain-brace.json",    # Task 11/12: passion "The ledger balances" (80), narrative
    "characters/npcs/calloway.json",                  # Task 11/12: "haunted bureaucrat"
    "characters/npcs/councillor-hale.json",           # Task 11/12: "Clerks at van Maanen's"
    "characters/npcs/mina-haral.json",                # Task 11/12: filing clerks, "Lore (the Tally's paperwork)" skill
    "characters/npcs/oyen.json",                      # Task 11/12: "records clerk" in description and role
    "characters/npcs/sep-anwar.json",                 # Task 11/12: "records clerk"
}


def test_there_is_no_paper_on_a_character_sheet():
    from content_rules import character_sheets, sheet_strings
    bad = []
    for p in character_sheets():
        rel = str(p.relative_to(ROOT))
        if rel in SHEET_PAPER_ALLOWLIST:
            continue
        for text in sheet_strings(p):
            for line in text.splitlines():
                if PAPER.search(line):
                    bad.append(f"{rel}: {line.strip()}")
    assert not bad, "\n".join(bad)


def test_the_new_vocabulary_is_defined_somewhere():
    text = (ROOT / "lore/technology/lading-and-attestation.md").read_text().lower()
    for word in ("lading", "attestation", "budding", "drift", "reconciliation"):
        assert word in text, word


# The Standing is a living archive, not a board on a wall. Paragraph-level so
# that "the Standing ... with a pen" two lines apart is still caught.
STANDING_AS_BOARD = re.compile(
    r"\b(board|chalk|pen|stool|hand-kept|by hand|written up)\b", re.I)

# Task 11 empties this list and asserts it is empty.
STANDING_BOARD_ALLOWLIST = {
    "lore/geography/the-nine-in-detail.md",       # Task 11, line ~35
    "lore/gm-guide/playing-the-old-man.md",       # Task 11, lines ~24, 33-36
    "lore/cosmology/straying.md",                 # Task 11, summary: "the Standing is pen"
}


def test_the_standing_is_never_a_board():
    bad = []
    for p in content_files(FIRST_PASS_DIRS):
        rel = str(p.relative_to(ROOT))
        if _exempt(p) or rel in STANDING_BOARD_ALLOWLIST:
            continue
        n = 0
        for para in re.split(r"\n\s*\n", p.read_text()):
            first = n + 1
            n += para.count("\n") + 2
            if "standing" in para.lower() and "the standing" in para.lower() \
                    and STANDING_AS_BOARD.search(para):
                bad.append(f"{rel}:{first}: {para.strip()[:90]!r}")
    assert not bad, "\n".join(bad)


# "bred for", "stock" and "kept" applied to fetches is the v1 framing. Under v3
# that framing is an atrocity the setting itself repudiated.
FETCH_AS_LIVESTOCK = re.compile(
    r"\b(bred for|breeding|kept as stock|a book is an animal"
    r"|written to by strangers|handed over at the far end"
    r"|every book|carrying books|rather than books|books and buds"
    r"|books come from|bred from one|bred out|breed it"
    r"|what a book is|written payload|writing a payload"
    r"|written into a (book|sixlimb)|library a courier carries"
    r"|reader'?s trade)\b", re.I)


# Files that still carry the old framing and belong to a later task.
LIVESTOCK_ALLOWLIST = {
    "lore/geography/bell.md",                     # Task 11: "where books come from"
    "lore/gm-secret/what-tolk-is.md",             # Task 11: "before you breed it"
    "lore/character-creation/skills.md",          # Task 11: Reading as the book trade
    "lore/character-creation/careers.md",         # Task 11: "carrying books"
    "lore/organizations/the-threshold.md",        # Task 11: "every book"
}


def test_fetches_are_never_described_as_livestock():
    bad = []
    for p in content_files(FIRST_PASS_DIRS):
        if str(p.relative_to(ROOT)).startswith("docs"):
            continue
        if str(p.relative_to(ROOT)) in LIVESTOCK_ALLOWLIST:
            continue
        text = p.read_text()
        for n, line in enumerate(text.splitlines(), 1):
            if FETCH_AS_LIVESTOCK.search(line):
                bad.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()}")
    assert not bad, "\n".join(bad)


def test_the_book_trade_is_recorded_as_having_ended():
    text = (ROOT / "lore/organizations/the-councils.md").read_text().lower()
    assert "council" in text
    assert "ended" in text
    assert "within living memory" in text


COLD_ARM = re.compile(r"cold[- ]arm|the cold arm", re.I)


def test_the_cold_arm_is_gone():
    """A passive affliction with nothing to do in it. What survives is the
    field an unsettled mouth has, which is the thing the Listen reads."""
    assert not (ROOT / "lore/cosmology/the-cold-arm.md").exists()
    bad = []
    for p in content_files(FIRST_PASS_DIRS):
        if str(p.relative_to(ROOT)).startswith("docs"):
            continue
        for n, line in enumerate(p.read_text().splitlines(), 1):
            if COLD_ARM.search(line):
                bad.append(f"{p.relative_to(ROOT)}:{n}: {line.strip()}")
    assert not bad, "\n".join(bad)


def test_the_listen_reads_an_unsettled_door():
    text = (ROOT / "lore/character-creation/the-knacks.md").read_text().lower()
    assert "the listen" in text
    assert "unsettled" in text
    assert "the hold" in text


def test_nobody_can_grash_a_door_on_purpose():
    text = (ROOT / "lore/cosmology/the-open-problem.md").read_text().lower()
    assert "nobody" in text
    for phrase in ("the mathematics", "mass", "instrument"):
        assert phrase in text, phrase
    assert "child" in text


def test_the_quorum_suppresses_rather_than_grashes():
    text = (ROOT / "lore/gm-secret/the-quorum.md").read_text().lower()
    assert "suppress" in text
    assert "overwrit" in text
    assert "children cannot be overwritten" in text
    # the file used to cite a rule that does not exist in TABLE-ADDENDUM
    assert "non-lethal rule" not in text


def test_the_late_exist_and_nobody_in_them_knows():
    text = (ROOT / "lore/gm-secret/the-late.md").read_text().lower()
    assert "the late" in text
    assert "flash" in text        # identified by the cut-out flash
    assert "none of them know" in text


# ---- Task 9: somebody to hate, and somebody to fight --------------------
from content_rules import character_sheets  # noqa: E402

NEW_ANTAGONISTS = (
    "characters/npcs/marek-sollen.json",
    "characters/npcs/sabra-ode.json",
    "characters/npcs/tobin-ashe.json",
    "characters/npcs/ines-caul.json",
)


def test_the_new_antagonists_exist_and_are_playable():
    """A card the engine cannot load is not a character, and a stat block
    with no actor notes is not somebody a GM can voice."""
    required = ("id", "name", "type", "status", "description",
                "characteristics", "attributes", "skills", "passions",
                "actor_notes", "extras")
    for rel in NEW_ANTAGONISTS:
        p = ROOT / rel
        assert p.exists(), rel
        d = json.loads(p.read_text())
        for key in required:
            assert key in d, f"{rel} has no {key}"
        assert d["extras"].get("pronouns"), f"{rel} has no pronouns"
        notes = d["actor_notes"]
        for field in ("CORE", "NATURE", "WOUND", "WANTS", "PRESSURE", "KEY"):
            assert field in notes, f"{rel} actor_notes has no {field}"


def test_no_actor_note_contains_a_rules_word():
    """TABLE.md: nothing on a card may contain a skill name, a number, or a
    rules word. The numbers live in the stat block, not in the voice."""
    banned = re.compile(r"\b(d100|hit points|action points|skill roll"
                        r"|difficulty|opposed roll)\b", re.I)
    for p in character_sheets():
        d = json.loads(p.read_text())
        notes = d.get("actor_notes") or ""
        m = banned.search(notes)
        assert not m, f"{p.name} actor_notes contains '{m.group(0)}'"


def test_ines_caul_can_actually_fight():
    """She is the campaign's first lethal antagonist. A commander a
    fifteen-year-old outmatches is not a threat."""
    d = json.loads((ROOT / "characters/npcs/ines-caul.json").read_text())
    styles = d.get("combat_styles") or {}
    assert styles, "Ines Caul has no combat style"
    assert max(styles.values()) >= 80, styles
