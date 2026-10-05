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
