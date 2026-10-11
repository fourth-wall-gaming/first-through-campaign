@AGENTS.md

## Why this file is two lines

The instructions live in `AGENTS.md` so that one file serves both agents. Codex
reads `AGENTS.md` directly; Claude Code reads it **only** when no `CLAUDE.md`
sits at or above the working directory — and this repository has one, so without
the import above, Claude Code would read this file and silently ignore them.

Keep the instructions in `AGENTS.md`. Add Claude-Code-specific notes below this
line, never above it, and never a second copy of anything in `AGENTS.md`.
