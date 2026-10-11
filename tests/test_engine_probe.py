"""Finding the engine, and failing to find it, without taking the session down.

scripts/engine.sh is the same file as purewater-campaign's; this is the same
suite, so a fix to one is testable in both.

Every assertion here is a bug that actually happened in this repository.

The two that prompted this file: `scripts/engine.sh` expanded
${CLAUDE_PLUGIN_ROOT} bare while being sourced by a hook that runs `set -u`, so
the last-resort convenience probe aborted the whole search -- and the probe that
searches the install tree was written for one plugin layout out of the three
Claude Code actually uses, so on a real install it matched nothing and the
campaign announced that its own engine was missing.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "scripts" / "engine.sh"
HOOK = ROOT / "scripts" / "session-start.sh"
GM_REL = "skills/mythras-gm/mythras_gm.py"

# Every layout a host is known to install a plugin into. Only the Claude Code
# cache and the Codex cache have a version segment, which is exactly what the
# old probe assumed of all of them.
LAYOUTS = {
    "cache": ".claude/plugins/cache/fourth-wall-gaming/mythras-gm/1.0.0",
    "synced": ".claude/plugins/synced/aaaa_bbbb/mythras-gm",
    "marketplaces": ".claude/plugins/marketplaces/fourth-wall-gaming",
    # Codex: ~/.codex/plugins/cache/$MARKETPLACE/$PLUGIN/$VERSION/, and a
    # locally-sourced marketplace entry installs with the literal version
    # "local" rather than a number.
    "codex-cache": ".codex/plugins/cache/fourth-wall-gaming/mythras-gm/1.0.0",
    "codex-local": ".codex/plugins/cache/fourth-wall-gaming/mythras-gm/local",
}


def _clean_env(home):
    """A session with nothing pre-arranged: no explicit root, no breadcrumb,
    and no hint from the plugin or project directory."""
    env = dict(os.environ)
    for k in ("MYTHRAS_GM_ROOT", "CLAUDE_PLUGIN_ROOT", "CLAUDE_PROJECT_DIR"):
        env.pop(k, None)
    env["HOME"] = str(home)
    return env


def _source_engine(home, cwd):
    """Source engine.sh under `set -u` and report GM_ROOT and anything it
    printed to stderr. cwd matters: probe 5 looks at ../mythras-gm."""
    r = subprocess.run(
        ["bash", "-c", f'set -uo pipefail; . "{ENGINE}"; printf "%s" "${{GM_ROOT:-}}"'],
        capture_output=True, text=True, env=_clean_env(home), cwd=str(cwd),
    )
    return r.stdout.strip(), r.stderr


@pytest.fixture
def empty_home(tmp_path):
    h = tmp_path / "home"
    (h / ".claude").mkdir(parents=True)
    (h / ".codex").mkdir(parents=True)
    return h


@pytest.mark.parametrize("layout", sorted(LAYOUTS))
def test_the_engine_is_found_in_every_install_layout(layout, empty_home, tmp_path):
    """The old probe globbed '*/mythras-gm/*/skills/mythras-gm/...' under
    cache/ only. Two of these three have no version segment to fill that
    middle '*', and two of them are not under cache/ at all."""
    root = empty_home / LAYOUTS[layout]
    (root / GM_REL).parent.mkdir(parents=True)
    (root / GM_REL).touch()

    # cwd with no ../mythras-gm sibling, so only the install-tree probe can win
    nowhere = tmp_path / "nowhere"
    nowhere.mkdir()

    got, err = _source_engine(empty_home, nowhere)
    assert got == str(root), f"{layout}: expected {root}, got {got or '<empty>'}\n{err}"


def test_sourcing_under_set_u_does_not_abort_the_caller(empty_home, tmp_path):
    """`PLUGIN_ROOT: unbound variable` killed the search mid-probe, so a
    perfectly good engine elsewhere on disk was never reached."""
    nowhere = tmp_path / "nowhere"
    nowhere.mkdir()
    got, err = _source_engine(empty_home, nowhere)
    assert "unbound variable" not in err, err
    assert got == "", f"nothing should have been found, got {got}"


def test_an_explicit_root_still_wins(empty_home, tmp_path):
    """MYTHRAS_GM_ROOT is the documented escape hatch and what CI uses."""
    explicit = tmp_path / "engine"
    (explicit / GM_REL).parent.mkdir(parents=True)
    (explicit / GM_REL).touch()
    env = _clean_env(empty_home)
    env["MYTHRAS_GM_ROOT"] = str(explicit)
    r = subprocess.run(
        ["bash", "-c", f'set -uo pipefail; . "{ENGINE}"; printf "%s" "${{GM_ROOT:-}}"'],
        capture_output=True, text=True, env=env, cwd=str(tmp_path),
    )
    assert r.stdout.strip() == str(explicit), r.stderr


def test_the_breadcrumb_is_checked_before_it_is_trusted(empty_home, tmp_path):
    """init-db drops a pointer file, but a plugin upgrade can leave it naming a
    directory that no longer holds the CLI. A stale pointer must not win."""
    pointer = empty_home / ".claude" / "mythras-gm" / "engine-root"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(tmp_path / "gone-away") + "\n")

    real = empty_home / LAYOUTS["synced"]
    (real / GM_REL).parent.mkdir(parents=True)
    (real / GM_REL).touch()

    nowhere = tmp_path / "nowhere"
    nowhere.mkdir()
    got, err = _source_engine(empty_home, nowhere)
    assert got == str(real), f"stale pointer should have been skipped; got {got}\n{err}"


@pytest.mark.parametrize("plugin_root_set", [True, False])
def test_the_hook_never_exits_non_zero(plugin_root_set, empty_home, tmp_path):
    """Its own header promises this: a user who has this plugin enabled and
    opens Claude in an unrelated directory must not have the session blocked.
    With CLAUDE_PLUGIN_ROOT unset it exited 1 on an unbound variable instead.

    The hook's scripts are staged into a throwaway directory with no engine
    beside it, rather than run in place. Two reasons, both load-bearing:
    probe 5 looks at ${CLAUDE_PLUGIN_ROOT}/../mythras-gm, which IS this
    developer's checkout when the hook runs from its own repo -- and once the
    engine is found the hook calls `init-db`, which adopts any TypeDB already
    listening on the default port and reloads schema and rules into whatever
    database it finds. That is somebody's real save. A unit test does not get
    to touch it.
    """
    staged = tmp_path / "staged-plugin"
    (staged / "scripts").mkdir(parents=True)
    for name in ("engine.sh", "session-start.sh"):
        shutil.copy2(ROOT / "scripts" / name, staged / "scripts" / name)

    env = _clean_env(empty_home)
    if plugin_root_set:
        env["CLAUDE_PLUGIN_ROOT"] = str(staged)

    r = subprocess.run(["bash", str(staged / "scripts" / "session-start.sh")],
                       capture_output=True, text=True, env=env, cwd=str(staged))

    assert r.returncode == 0, f"exit {r.returncode}\nstdout: {r.stdout}\nstderr: {r.stderr}"
    assert "unbound variable" not in r.stderr, r.stderr
    assert r.stdout.strip(), "the hook must say something; its stdout reaches the model"
    assert "not installed" in r.stdout, (
        "with no engine reachable the hook must say so plainly, and must not "
        f"have gone on to touch a database:\n{r.stdout}")


def test_the_host_neutral_breadcrumb_is_read(empty_home, tmp_path):
    """The engine writes ~/.mythras-gm/engine-root as well as the original
    under ~/.claude. Reading one file beats searching four trees."""
    engine = tmp_path / "engine"
    (engine / GM_REL).parent.mkdir(parents=True)
    (engine / GM_REL).touch()
    pointer = empty_home / ".mythras-gm" / "engine-root"
    pointer.parent.mkdir(parents=True)
    pointer.write_text(str(engine) + "\n")

    nowhere = tmp_path / "nowhere"
    nowhere.mkdir()
    got, err = _source_engine(empty_home, nowhere)
    assert got == str(engine), f"host-neutral breadcrumb not read: {got}\n{err}"


def test_the_legacy_breadcrumb_still_works_alone(empty_home, tmp_path):
    """Review Focus 5: the engine is a separately versioned plugin. An install
    running an older engine writes only ~/.claude/mythras-gm/engine-root, and
    this campaign must keep working against it."""
    engine = tmp_path / "engine"
    (engine / GM_REL).parent.mkdir(parents=True)
    (engine / GM_REL).touch()
    pointer = empty_home / ".claude" / "mythras-gm" / "engine-root"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(str(engine) + "\n")

    nowhere = tmp_path / "nowhere"
    nowhere.mkdir()
    got, err = _source_engine(empty_home, nowhere)
    assert got == str(engine), f"legacy breadcrumb not read: {got}\n{err}"


def test_a_codex_install_is_found_when_the_claude_tree_exists_but_is_empty(
        empty_home, tmp_path):
    """Review Focus 1. A machine with both agents installed has both trees on
    disk; only one holds the engine. A loop that stops at the first tree that
    EXISTS rather than the first that HITS reports the engine as missing on a
    perfectly good install -- and both directories exist on this developer's
    own machine, so the bug would not show up locally."""
    (empty_home / ".claude" / "plugins" / "cache").mkdir(parents=True)
    root = empty_home / LAYOUTS["codex-cache"]
    (root / GM_REL).parent.mkdir(parents=True)
    (root / GM_REL).touch()

    nowhere = tmp_path / "nowhere"
    nowhere.mkdir()
    got, err = _source_engine(empty_home, nowhere)
    assert got == str(root), f"expected {root}, got {got or '<empty>'}\n{err}"


def test_no_home_at_all_is_a_miss_not_an_abort(tmp_path):
    """Review Focus 2: cron, or a bare container. Under `set -u` an unguarded
    ${HOME} aborts the hook that sourced this, which is the one thing the
    hook's header promises never happens."""
    import os
    import subprocess
    env = dict(os.environ)
    for k in ("MYTHRAS_GM_ROOT", "CLAUDE_PLUGIN_ROOT", "CLAUDE_PROJECT_DIR",
              "HOME"):
        env.pop(k, None)
    nowhere = tmp_path / "nowhere"
    nowhere.mkdir()
    r = subprocess.run(
        ["bash", "-c", f'set -uo pipefail; . "{ENGINE}"; printf "%s" "${{GM_ROOT:-}}"'],
        capture_output=True, text=True, env=env, cwd=str(nowhere),
    )
    assert "unbound variable" not in r.stderr, r.stderr
    assert r.returncode == 0, f"exit {r.returncode}: {r.stderr}"


def test_the_hook_publishes_the_campaign_root_absolutely(empty_home, tmp_path):
    """The skill needs this package's own path and cannot compute it: a skill
    body is prose, and the plugin-root variable a host substitutes into it
    under Claude Code expands to nothing under Codex. The hook CAN resolve it
    -- both hosts set the variable for hook commands -- so the hook publishes
    it and the skill reads it from there. Same fix as the engine's own.
    """
    import shutil
    import subprocess
    staged = tmp_path / "staged-plugin"
    (staged / "scripts").mkdir(parents=True)
    for name in ("engine.sh", "session-start.sh"):
        shutil.copy2(ROOT / "scripts" / name, staged / "scripts" / name)

    env = _clean_env(empty_home)
    env["CLAUDE_PLUGIN_ROOT"] = str(staged)
    r = subprocess.run(["bash", str(staged / "scripts" / "session-start.sh")],
                       capture_output=True, text=True, env=env, cwd=str(staged))

    assert r.returncode == 0, f"exit {r.returncode}\n{r.stdout}\n{r.stderr}"
    assert f"FIRST_THROUGH_ROOT={staged}" in r.stdout, (
        "the hook must publish this package's absolute path in every branch; "
        f"without it a Codex session has no path to the campaign files:\n{r.stdout}")


def test_the_hook_names_a_skill_not_only_a_slash_command(empty_home, tmp_path):
    """Review Focus 4. Codex has no commands component, so an instruction to
    type /purewater:start is an instruction a Codex user cannot follow."""
    import shutil
    import subprocess
    staged = tmp_path / "staged-plugin"
    (staged / "scripts").mkdir(parents=True)
    for name in ("engine.sh", "session-start.sh"):
        shutil.copy2(ROOT / "scripts" / name, staged / "scripts" / name)
    env = _clean_env(empty_home)
    env["CLAUDE_PLUGIN_ROOT"] = str(staged)
    out = subprocess.run(["bash", str(staged / "scripts" / "session-start.sh")],
                         capture_output=True, text=True, env=env,
                         cwd=str(staged)).stdout

    assert "first-through-start" in out, (
        "the engine-missing branch sends the player to a Claude-Code-only "
        f"install command with no skill named:\n{out}")
    assert "/plugin install" not in out, (
        "that command does not exist in Codex; describe the plugin browser")
