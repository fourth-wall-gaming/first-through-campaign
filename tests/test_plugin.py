"""The three ways a campaign plugin ships broken, each one a bug that has
actually happened in a sibling repository."""
import json
import os
import re
import subprocess

import pytest

from content_rules import ROOT

SEED_ID = "myth-campaign-first-through-s1"


def test_the_hook_never_takes_the_session_down():
    """Review Focus 1. purewater's engine.sh header records why: the hook runs
    under `set -u`, so one bare ${CLAUDE_PLUGIN_ROOT} aborts the caller and the
    campaign reports the engine missing when it is installed and working.

    Run it with no engine, no plugin root and no HOME pointer, which is the
    worst case, and require exit 0."""
    env = dict(os.environ)
    for k in ("CLAUDE_PLUGIN_ROOT", "MYTHRAS_GM_ROOT", "VIRTUAL_ENV"):
        env.pop(k, None)
    env["HOME"] = "/nonexistent-home-for-this-test"
    r = subprocess.run(
        ["bash", str(ROOT / "scripts" / "session-start.sh")],
        capture_output=True, text=True, env=env, timeout=120,
    )
    assert r.returncode == 0, (
        f"the hook exited {r.returncode}; it must always exit 0\n"
        f"stderr: {r.stderr}"
    )
    assert r.stdout.strip(), "the hook said nothing; its stdout reaches the model"
    assert "unbound variable" not in r.stderr


def test_no_shell_variable_lacks_a_default():
    """The `set -u` trap, checked statically so it cannot regress.

    Three refinements over the naive check, each one a false positive it would
    otherwise raise on correct code. Comments are stripped, because engine.sh's
    header quotes the very bug it documents. A variable the script assigns
    itself needs no default -- only an unassigned environment variable can be
    unset under `set -u`. And a variable counts as safe if it is expanded with
    `:-` anywhere, because the idiomatic guarded pair
    `[ -n "${X:-}" ] && [ -f "${X}/p" ]` is correct."""
    for name in ("engine.sh", "session-start.sh"):
        text = (ROOT / "scripts" / name).read_text()
        code = "\n".join(l for l in text.splitlines()
                         if not l.lstrip().startswith("#"))
        assigned = set(re.findall(
            r"^\s*(?:local\s+|export\s+)?([A-Z_][A-Z0-9_]*)=", code, re.M))
        assigned |= set(re.findall(r"\bfor\s+([A-Z_][A-Z0-9_]*)\s+in\b", code))
        assigned |= {"GM_ROOT", "GM_SKILL", "GM_CLI", "BASH_SOURCE"}
        defaulted = set(re.findall(r"\$\{([A-Z_][A-Z0-9_]*):-", code))
        bare = set()
        for m in re.finditer(r"\$\{([A-Z_][A-Z0-9_]*)([^}]*)\}", code):
            if m.group(1) in assigned:
                continue
            if not m.group(2).startswith(":-"):
                bare.add(m.group(1))
        missing = bare - defaulted
        assert not missing, f"{name}: no default anywhere for {sorted(missing)}"


def test_the_hook_never_imports():
    """Importing writes hundreds of rows. It belongs to a command the user ran,
    not to a hook that fires every time they open a terminal."""
    text = (ROOT / "scripts" / "session-start.sh").read_text()
    assert "import-campaign" not in text, "the hook imports; it must not"


def test_the_start_command_refuses_to_clobber_a_game_in_progress():
    """Review Focus 2. A start command that resets somebody's campaign is worse
    than no start command at all."""
    text = (ROOT / "commands" / "start.md").read_text()
    assert "get-campaign" in text, "it must look before it imports"
    assert "/mythras-gm:play" in text, "it must hand a live game to the play command"
    low = text.lower()
    assert "do not import" in low or "stop" in low


def test_the_start_command_states_the_non_lethal_rule():
    """Review Focus 5. If the GM has not read it before the first roll, a
    child's first character can die on one bad exchange."""
    text = (ROOT / "commands" / "start.md").read_text()
    assert "TABLE-ADDENDUM.md" in text


def test_the_addendum_puts_the_risk_on_the_table_before_the_dice():
    """Danger is real, so the protection a child gets is information, not a
    guarantee. A character may die only from a risk the player could see when
    they chose it -- which is a constraint on the GM, not on the player."""
    low = " ".join((ROOT / "TABLE-ADDENDUM.md").read_text().lower().split())
    assert "people die in this campaign" in low
    assert "before the dice are" in low or "before it is taken" in low
    assert "luck points" in low, "the player's out must be named"
    assert "never a lethal surprise" in low


def test_the_start_command_offers_every_entry_point_and_builds_a_character():
    """Derived from what is actually in lore/entry-points/, so retiring or adding
    a scenario cannot leave the start command silently out of date.

    The pre-gen half of this test used to loop over characters/pcs/*.json; with
    those deleted it asserted nothing. What it checks now is that the start
    command carries the three-stage build, because that IS the opening session.
    """
    text = (ROOT / "commands" / "start.md").read_text()
    low = text.lower()
    slugs = [p.stem for p in (ROOT / "lore" / "entry-points").glob("*.md")]
    assert slugs, "no entry points to offer"
    for slug in slugs:
        assert slug in text, f"start does not offer {slug}"

    for stage in ("culture", "career", "bonus"):
        assert stage in low, f"start.md never mentions the {stage} stage"
    assert "100" in text and "150" in text, (
        "start.md does not state the point pools (Culture 100, Career 100, "
        "Bonus 150)"
    )
    assert "15" in text, "start.md does not state the 15-per-skill-per-round cap"
    assert "there are no pre-gens" in low, (
        "start.md must say plainly that there are no pre-gens"
    )
    for retired in ("The Runner", "The Tinker", "The Talker", "The Fieldhand"):
        assert retired not in text, f"start.md still offers the pre-gen {retired!r}"


def test_the_start_command_uses_a_cli_path_that_actually_exists():
    """The bug that made v1 unplayable: start.md told the GM to run
    `create-character --template`, and no such flag exists in the engine. A
    start command must only name commands and flags the CLI really has."""
    text = (ROOT / "commands" / "start.md").read_text()
    assert "--template" not in text or "spawn" in text, (
        "start.md uses --template; only `spawn --template` takes one, and spawn "
        "makes an NPC and discards passions and powers"
    )
    assert "create-character --campaign <id> --template" not in text

    # Ask the installed engine which flags each command really takes, rather
    # than hard-coding a list. This assertion used to ban --played outright,
    # which pinned an engine bug (the flag was bound to the wrong subparser)
    # into the campaign's own test suite.
    engine = subprocess.run(
        ["bash", "-c", '. scripts/engine.sh && echo "$GM_SKILL"'],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout.strip()
    if not engine:
        pytest.skip("mythras-gm engine not installed")
    # Flags are scoped to the invocation they appear in: a line `gm <command>`
    # plus any backslash-continued lines after it. Checking "flag in text"
    # would let a flag that is legal on one command excuse an illegal use on
    # another -- which it did, hiding `create-character --powers`.
    invocations = {}
    lines = text.splitlines()
    for n, line in enumerate(lines):
        m = re.match(r"\s*gm ([a-z-]+)\b", line)
        if not m:
            continue
        span, k = [line], n
        while span[-1].rstrip().endswith("\\") and k + 1 < len(lines):
            k += 1
            span.append(lines[k])
        invocations.setdefault(m.group(1), []).append(" ".join(span))

    for command, spans in sorted(invocations.items()):
        helptext = subprocess.run(
            ["uv", "run", "-q", "--project", engine, "python",
             f"{engine}/mythras_gm.py", command, "--help"],
            capture_output=True, text=True,
        ).stdout
        if "usage:" not in helptext:
            continue          # not a real subcommand name; another test covers that
        for span in spans:
            for flag in sorted(set(re.findall(r"(--[a-z][a-z-]+)", span))):
                assert flag in helptext, (
                    f"start.md uses `{command} {flag}`, which the installed "
                    f"engine does not accept"
                )


def test_the_plugin_manifest_declares_the_engine_dependency():
    m = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert m["name"] == "first-through"
    assert "mythras-gm" in m["dependencies"]
    assert m["hooks"] == "./hooks/hooks.json"


def test_the_hook_manifest_points_at_the_script():
    h = json.loads((ROOT / "hooks" / "hooks.json").read_text())
    cmd = h["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert "session-start.sh" in cmd
    assert "CLAUDE_PLUGIN_ROOT" in cmd


def _embedded_python(text):
    """Every `python3 -c '...'` snippet in a shell script."""
    return re.findall(r"python3 -c '\n(.*?)\n' ", text, re.S)


def test_embedded_python_in_the_hook_actually_compiles():
    """The bug that made the hook lie. The snippet inherited from purewater used
    \\" escapes inside an f-string expression, which is a SyntaxError -- so it
    fell through to the fallback every time, took the in-progress branch, and
    told the player NOT to run the start command. A broken snippet cannot be
    seen by eye and leaves no trace at runtime, because stderr is discarded."""
    text = (ROOT / "scripts" / "session-start.sh").read_text()
    snippets = _embedded_python(text)
    assert snippets, "no embedded python found; has the hook been restructured?"
    for snip in snippets:
        assert "'" not in snip, (
            "a single quote inside a single-quoted shell string terminates it"
        )
        assert "\\" not in snip, (
            "backslash escapes inside the snippet are what broke it before"
        )
        compile(snip, "session-start.sh snippet", "exec")


def test_the_hook_reads_an_unstarted_seed_as_unstarted():
    """Run the hook's own state snippet against the shape get-campaign really
    returns, and require session 0 to come back as 0 rather than '?'."""
    text = (ROOT / "scripts" / "session-start.sh").read_text()
    snip = _embedded_python(text)[-1]
    fixture = json.dumps({"success": True, "campaign": {
        "id": SEED_ID,
        "myth-game-date": "d0/dawn -- the morning of the player's first posting",
        "myth-session-number": 0,
    }})
    r = subprocess.run(["python3", "-c", snip], input=fixture,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    clock, _, session = r.stdout.strip().partition("|")
    assert session == "0", f"session read as {session!r}; the hook would misreport"
    assert clock.startswith("d0/dawn"), f"clock read as {clock!r}"


def test_the_hook_does_not_gate_on_init_db_exit_code():
    """init-db is not concurrency-safe, and the engine's own SessionStart hook
    calls it at the same moment this one does. Run two together and whichever
    loses the race exits 1 with a traceback -- which made this hook announce
    PREFLIGHT FAILED on a healthy install, in a real session.

    So the failure branch must be driven by whether the database can be READ,
    not by init-db's exit status."""
    text = (ROOT / "scripts" / "session-start.sh").read_text()
    assert "if ! INIT=$(gm init-db" not in text, (
        "the hook gates on init-db's exit code, which is racy"
    )
    assert text.count("gm init-db") == 1, (
        "init-db should appear once, as a last resort only -- the engine's own "
        "hook owns startup and calling it here races that hook"
    )
    assert "gm init-db >/dev/null 2>&1 || true" in text, (
        "the last-resort init-db must ignore its own exit code"
    )
    assert "list-campaigns" in text, (
        "readiness must be decided by whether the database can be read"
    )
