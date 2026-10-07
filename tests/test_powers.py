"""The powers a fresh character can take must be legal and must not break the setting.

There are no pre-gens. Every character is built at the table, so the guard that
used to run over shipped pre-gen JSON now runs over the thing a player actually
reads at creation: the knack-to-power table in lore/character-creation/the-knacks.md.

That table is the only place in the campaign that names Mythras powers, so it is
the only place a forbidden one can get in.
"""
import json
import re
import subprocess

import pytest

from content_rules import ROOT

KNACKS = ROOT / "lore" / "character-creation" / "the-knacks.md"

PERMITTED = {
    "Life Support", "Inherent Armor", "Savant", "Heightened Sense",
    "Enhanced Reactions", "Durability", "Enhanced Strength",
    "Enhanced Speed", "Combat Expert", "Lucky",
}
FORBIDDEN = {
    "Teleport", "Flight", "Vaporous Form", "Animation",
    "Elemental Control", "Energy Blast",
}

ROW = re.compile(r"^\|\s*(The [A-Z]\w+)\s*\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|$",
                 re.MULTILINE)


def knack_rows():
    return ROW.findall(KNACKS.read_text())


def cited_rules():
    """Every rule id the knack lore cites, table rows and prose alike."""
    return sorted(set(re.findall(r"`(magic/power-[a-z-]+)`", KNACKS.read_text())))


def test_the_knack_table_exists_and_covers_the_knacks():
    """A knack with no power is a knack a built character cannot actually take."""
    rows = knack_rows()
    assert rows, "no knack-to-power table in the knacks lore"
    named = {k for k, _, _ in rows}
    prose = set(re.findall(r"\*\*(The [A-Z]\w+)\.\*\*", KNACKS.read_text()))
    # The Hold is deliberately not offered at creation.
    missing = prose - named - {"The Hold"}
    assert not missing, f"knacks described but not mapped to a power: {sorted(missing)}"


def test_the_hold_is_not_offered_at_creation():
    """It would make the rest of the setting's problems negotiable."""
    text = KNACKS.read_text()
    assert "The Hold is not available at creation" in text
    assert "The Hold" not in {k for k, _, _ in knack_rows()}


@pytest.mark.parametrize("power", sorted({p for _, p, _ in knack_rows()}))
def test_every_offered_power_is_whitelisted(power):
    """Spec section 7: personal teleportation being impossible is why the
    Causeway matters. A knack that granted Teleport would unmake the setting."""
    assert power in PERMITTED, f"{power} is not a permitted power"
    assert power not in FORBIDDEN


def test_no_forbidden_power_is_named_anywhere_as_available():
    """The prose says these are unreachable; it must not also offer one."""
    for _, power, _ in knack_rows():
        assert power not in FORBIDDEN, f"{power} is offered by a knack"


def test_the_build_table_is_stated_so_a_character_can_be_costed():
    """Core powers = POW + INT. Without the table in front of the player, the
    number of powers a fresh character gets is whatever the GM remembers."""
    text = KNACKS.read_text()
    assert "POW + INT" in text
    for bound in ("13-20", "21-30", "31-40"):
        assert bound in text, f"the build table does not state {bound}"


@pytest.mark.parametrize("rule", cited_rules())
def test_every_power_rule_id_resolves_in_the_rules_graph(rule):
    """A typo here does not raise -- it yields a sheet whose power cannot be
    looked up, which a player would discover mid-mission."""
    engine = subprocess.run(
        ["bash", "-c", '. scripts/engine.sh && echo "$GM_SKILL"'],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout.strip()
    if not engine:
        pytest.skip("mythras-gm engine not installed")
    out = subprocess.run(
        ["uv", "run", "-q", "--project", engine, "python",
         f"{engine}/mythras_gm.py", "get-rule", "--id", rule],
        capture_output=True, text=True,
    )
    assert json.loads(out.stdout).get("success"), f"{rule} does not resolve"


def test_the_membrane_suit_is_a_limit_not_a_birthright():
    """Life Support is the suit. Shipping it without External Power Source makes
    a child who cannot be put in danger by having her kit taken off her."""
    text = KNACKS.read_text()
    assert "magic/power-life-support" in text
    assert "External Power Source" in text


def test_no_pregens_ship():
    """Always a fresh character. A shipped pre-gen is a character nobody built,
    and the whole point of the opening session is building one."""
    stray = sorted(p.name for p in (ROOT / "characters" / "pcs").glob("*.json"))
    assert not stray, f"pre-gens still shipped in characters/pcs/: {stray}"
    stray = sorted(p.name for p in (ROOT / "templates").glob("the-*.json"))
    assert not stray, f"pre-gens still shipped in templates/: {stray}"
