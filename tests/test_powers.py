"""The pre-gens must be engine-legal and must obey the spec's power whitelist.

They live in characters/pcs/, not templates/. In this engine `templates/` means
creature stat blocks for `spawn`, and spawn hardcodes type npc and discards
passions and powers -- so a pre-gen shipped as a template cannot be played.
"""
import json
import re
import subprocess

import pytest

from content_rules import ROOT

PREGENS = sorted((ROOT / "characters" / "pcs").glob("*.json"))

PERMITTED = {
    "Life Support", "Inherent Armor", "Savant", "Heightened Sense",
    "Enhanced Reactions", "Durability", "Enhanced Strength",
    "Enhanced Speed", "Combat Expert", "Lucky",
}
FORBIDDEN = {
    "Teleport", "Flight", "Vaporous Form", "Animation",
    "Elemental Control", "Energy Blast",
}


def test_there_are_four_pregens():
    assert len(PREGENS) == 4, [p.name for p in PREGENS]


def test_every_pregen_is_a_playable_pc():
    """The bug this file was reorganised around: a pre-gen that is not type pc
    cannot be handed to a player at all."""
    for path in PREGENS:
        t = json.loads(path.read_text())
        assert t["type"] == "pc", f"{path.name} is type {t['type']!r}"
        assert t.get("location"), (
            f"{path.name} has no location -- without one they are nowhere and "
            "every beat reads as offscreen"
        )


@pytest.mark.parametrize("path", PREGENS, ids=lambda p: p.stem)
def test_template_is_engine_shaped(path):
    t = json.loads(path.read_text())
    assert re.match(r"^myth-char-[0-9a-f]{12}$", t["id"])
    for key in ("name", "description", "characteristics", "attributes",
                "skills", "passions", "powers"):
        assert key in t, f"{path.name} has no {key}"
    for stat in ("STR", "CON", "SIZ", "DEX", "INT", "POW", "CHA"):
        assert isinstance(t["characteristics"][stat], int)
    assert t["passions"], "a pre-gen with no Passions is a stat block"


@pytest.mark.parametrize("path", PREGENS, ids=lambda p: p.stem)
def test_powers_are_whitelisted_and_teleport_is_absent(path):
    """Spec section 7: personal teleportation being impossible is why the
    Causeway matters. A pre-gen that could teleport would unmake the setting."""
    for p in json.loads(path.read_text())["powers"]:
        assert p["name"] in PERMITTED, f"{path.name}: {p['name']} is not permitted"
        assert p["name"] not in FORBIDDEN


@pytest.mark.parametrize("path", PREGENS, ids=lambda p: p.stem)
def test_power_count_matches_the_build_table(path):
    """core powers = POW + INT on the tech/training branch, per the table:
    <=12 -> 1, 13-20 -> 2, 21-30 -> 3, 31-40 -> 4, 40+ -> 5; and each Limit
    taken beyond the first buys a core power, the first buys a Boost."""
    t = json.loads(path.read_text())
    pool = t["characteristics"]["POW"] + t["characteristics"]["INT"]
    allowed = 1 if pool <= 12 else 2 if pool <= 20 else 3 if pool <= 30 else 4 if pool <= 40 else 5
    limits = {l for p in t["powers"] for l in p["limits"]}
    if len(limits) >= 2:
        allowed += 1
    assert len(t["powers"]) <= allowed, (
        f"{path.name}: POW+INT={pool} allows {allowed} core powers, "
        f"file has {len(t['powers'])}"
    )


@pytest.mark.parametrize("path", PREGENS, ids=lambda p: p.stem)
def test_every_power_rule_id_resolves_in_the_rules_graph(path):
    """Review Focus 3. A typo here does not raise -- it yields a sheet with no
    powers at all, which a player would discover mid-mission."""
    engine = subprocess.run(
        ["bash", "-c", '. scripts/engine.sh && echo "$GM_SKILL"'],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout.strip()
    if not engine:
        pytest.skip("mythras-gm engine not installed")
    for p in json.loads(path.read_text())["powers"]:
        out = subprocess.run(
            ["uv", "run", "-q", "--project", engine, "python",
             f"{engine}/mythras_gm.py", "get-rule", "--id", p["rule"]],
            capture_output=True, text=True,
        )
        assert json.loads(out.stdout).get("success"), (
            f"{path.name}: power {p['name']} cites rule {p['rule']}, "
            "which does not resolve"
        )


@pytest.mark.parametrize("path", PREGENS, ids=lambda p: p.stem)
def test_pregens_start_with_full_luck_and_charge(path):
    """Import defaults luck_current to 2 when the file does not state it, so a
    pre-gen with 3 Luck Points would hand a child a safety valve one short on
    session one. Luck is the spec's named safety valve; it starts full."""
    t = json.loads(path.read_text())
    assert t.get("luck_current") == t["attributes"]["luck_points"], (
        f"{path.name}: luck_current {t.get('luck_current')} != "
        f"luck_points {t['attributes']['luck_points']}"
    )
    assert t.get("magic_current") == t["attributes"]["magic_points"], (
        f"{path.name}: the suit's charge does not start full"
    )
    assert t.get("fatigue") == "Fresh", f"{path.name} does not start Fresh"
