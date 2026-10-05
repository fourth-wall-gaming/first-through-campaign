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
