"""The three ways a campaign plugin ships broken, each one a bug that has
actually happened in a sibling repository."""
import json
import os
import re
import subprocess

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


def test_the_addendum_states_the_rule_in_both_directions():
    text = (ROOT / "TABLE-ADDENDUM.md").read_text()
    low = text.lower()
    assert "never killed" in low or "not killed" in low
    assert "knocked out" in low or "unconscious" in low
    assert "both directions" in low, (
        "the rule applies to what the PC does as well as what is done to them"
    )


def test_the_start_command_offers_both_entry_points_and_all_four_pregens():
    text = (ROOT / "commands" / "start.md").read_text()
    for slug in ("the-quiet-door", "flare"):
        assert slug in text, f"start does not offer {slug}"
    for p in (ROOT / "characters" / "pcs").glob("*.json"):
        assert json.loads(p.read_text())["name"] in text


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
    assert "--played" not in text, (
        "update-campaign has no --played flag in the shipped engine"
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
    assert "gm init-db >/dev/null 2>&1 || true" in text, (
        "init-db should be attempted and its exit code ignored"
    )
    assert "list-campaigns" in text, (
        "the failure branch must probe whether the database is readable"
    )
