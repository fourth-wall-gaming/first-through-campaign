"""Invariants that keep this campaign installable in both Claude Code and Codex.

This campaign started with NO skills/ directory at all: everything it carried
lived in commands/, which Codex does not have. So under Codex nothing of it
loaded -- no entry point, no implicit trigger, and none of the campaign's own
conventions. The engine's skill could still resume a save from the database,
which is what made it look like it half worked.

Codex reads this repository's Claude manifests directly -- `.claude-plugin/
plugin.json` is a recognised compatibility manifest and `hooks/hooks.json` is
discovered by default -- so there is no second plugin to build. What Codex does
NOT have is a commands component, and it does not substitute a plugin-root
variable into skill prose. These tests are what stops either difference
quietly returning.

The engine's equivalent is mythras-gm/tests/test_portability.py; the reasoning
is argued there in full.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

VENDORED = (".venv", "__pycache__", "node_modules", "site-packages")
SKILL_DOCS = sorted(p for p in (ROOT / "skills").rglob("*.md")
                    if not any(part in VENDORED for part in p.parts))
COMMANDS = sorted((ROOT / "commands").glob("*.md"))
SKILL_FILES = sorted((ROOT / "skills").glob("*/SKILL.md"))


def frontmatter(path):
    """The YAML block between the opening and closing `---`, as a flat dict.
    Regex rather than PyYAML so this guard has no dependency of its own."""
    match = re.match(r"^---\n(.*?)\n---\n", path.read_text(), re.DOTALL)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        if re.match(r"^\s", line) or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip("\"'")
    return fields


def test_there_are_files_to_check_at_all():
    """If a layout change empties a glob, every test below passes vacuously."""
    assert SKILL_DOCS, "no skills/**/*.md found"
    assert COMMANDS, "no commands/*.md found"
    assert SKILL_FILES, "no skills/*/SKILL.md found"


@pytest.mark.parametrize("doc", SKILL_DOCS, ids=lambda p: str(p.relative_to(ROOT)))
def test_no_plugin_root_literal_in_shipped_prose(doc):
    """A path a Codex session cannot resolve. The variable is host-substituted
    text, not a shell variable -- it is absent from the model's environment in
    both hosts, and Claude Code was expanding it when it loaded the file. Under
    Codex it expands to nothing, so `. "/scripts/engine.sh"` fails and the
    campaign reports its own engine as missing on a working install."""
    hits = [n for n, line in enumerate(doc.read_text().splitlines(), 1)
            if "CLAUDE_PLUGIN_ROOT" in line]
    assert not hits, (
        f"{doc.relative_to(ROOT)} names CLAUDE_PLUGIN_ROOT on line(s) {hits}; "
        f"use $FT, which the preflight publishes as FIRST_THROUGH_ROOT.")


@pytest.mark.parametrize("command", COMMANDS, ids=lambda p: p.name)
def test_every_command_delegates_to_a_skill(command):
    """Codex has no commands component, so a command file is a Claude-Code-only
    entry point and its body must live in a skill both hosts can load. The
    delegation is a frontmatter field rather than inferred from the prose:
    every one of these files mentions "first-through" somewhere."""
    names = {f.parent.name for f in SKILL_FILES}
    declared = frontmatter(command).get("skill")
    assert declared, (
        f"commands/{command.name} declares no `skill:`, so its body reaches no "
        f"Codex session. Move the body into a skill and point at it.")
    assert declared in names, (
        f"commands/{command.name} delegates to {declared!r}, not one of {sorted(names)}")


@pytest.mark.parametrize("skill", SKILL_FILES, ids=lambda p: p.parent.name)
def test_every_skill_declares_itself(skill):
    """Both hosts match on the description and address the skill by `name`."""
    fields = frontmatter(skill)
    assert fields.get("name"), f"{skill.relative_to(ROOT)} has no `name`"
    assert fields.get("description"), f"{skill.relative_to(ROOT)} has no `description`"
    assert fields["name"] == skill.parent.name, (
        f"{skill.relative_to(ROOT)} is named {fields['name']!r} but sits in "
        f"{skill.parent.name!r}")


def test_the_start_skill_can_resolve_its_own_root(skill=None):
    """Review Focus 3. On a fresh Codex install the hooks are not trusted yet,
    so the preflight never ran and FIRST_THROUGH_ROOT was never published. The
    skill must say where else to get the path rather than sourcing an empty
    one, because sourcing an empty one reports the engine as missing."""
    text = (ROOT / "skills" / "first-through-start" / "SKILL.md").read_text()
    assert "FIRST_THROUGH_ROOT" in text, "the skill never says where $PW comes from"
    assert "directory" in text.lower(), (
        "the skill gives no fallback for a session where the preflight did not "
        "run; it must say the package root is this skill's own parent")


@pytest.mark.parametrize("doc", SKILL_DOCS, ids=lambda p: str(p.relative_to(ROOT)))
def test_no_shipped_skill_names_a_slash_command_without_its_skill(doc):
    """Review Focus 4: a Codex session cannot type /first-through:start. Naming the
    slash command is fine -- as a parenthetical beside the skill."""
    text = doc.read_text()
    for command, skill in (("/first-through:start", "first-through-start"),
                           ("/mythras-gm:play", "mythras-play"),
                           ("/mythras-gm:setup", "mythras-setup")):
        if command in text:
            assert skill in text, (
                f"{doc.relative_to(ROOT)} tells the reader to run {command} and "
                f"never names the {skill} skill, which is the only route in Codex")


def test_hook_timeouts_are_plausible_seconds():
    """`timeout` is seconds in both hosts (Claude Code: "Seconds before
    cancelling", default 600; Codex: the same, and it caps most events at 600).
    A millisecond value reads as days and silently disables the timeout."""
    spec = json.loads((ROOT / "hooks" / "hooks.json").read_text())
    found = []
    for event, groups in spec.get("hooks", {}).items():
        for group in groups:
            for hook in group.get("hooks", []):
                if "timeout" in hook:
                    found.append((event, hook["timeout"]))
    assert found, "no hook declares a timeout; this test would pass vacuously"
    too_long = [(e, t) for e, t in found if t > 600]
    assert not too_long, (
        f"timeout is in SECONDS, not milliseconds: {too_long}")


def test_the_contributor_instructions_reach_both_agents():
    """Claude Code reads AGENTS.md only when no CLAUDE.md sits at or above the
    working directory; Codex reads AGENTS.md only. So a bare AGENTS.md beside a
    CLAUDE.md is read by one and ignored by the other. The documented way to
    have one file serve both is a CLAUDE.md that imports it.

    This repository's AGENTS.md is GM orientation and carries the GM canon, so
    a Codex session that cannot read it is a session run without the canon --
    not merely a contributor missing some notes."""
    agents = ROOT / "AGENTS.md"
    claude = ROOT / "CLAUDE.md"
    assert agents.exists(), "no AGENTS.md: a Codex contributor gets no instructions"
    assert claude.exists(), "no CLAUDE.md"
    assert "@AGENTS.md" in claude.read_text(), (
        "CLAUDE.md does not import AGENTS.md, so Claude Code reads CLAUDE.md "
        "only and the two can drift")
    assert "THE GM CANON" in agents.read_text(), (
        "AGENTS.md exists but does not hold the GM canon")
