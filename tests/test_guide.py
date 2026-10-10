"""The two books, as gates rather than aspirations.

The guide is generated from the campaign files, so the failure modes are a
directive pointing at a file that has been renamed, a chapter that drops out of
the navigation because it lost its part marker, and house style drifting in
hand-written prose. All three are cheap to catch and invisible until somebody
reads the built site.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
GUIDE = ROOT / "guide"
sys.path.insert(0, str(GUIDE))

from house import violations  # noqa: E402

BOOKS = ("gm", "players")
CHAPTERS = sorted(
    p for book in BOOKS for p in (GUIDE / book).glob("*.md")
)
HAND_WRITTEN = CHAPTERS + [GUIDE / "parents.md"]


def rel(p):
    return str(p.relative_to(ROOT))


def test_both_books_have_chapters():
    for book in BOOKS:
        assert list((GUIDE / book).glob("*.md")), f"{book} has no chapters"


@pytest.mark.parametrize("path", CHAPTERS, ids=rel)
def test_every_chapter_is_numbered_titled_and_in_a_part(path):
    """A chapter with no part marker opens its own unlabelled group in the
    navigation, which is how a part silently splits in two."""
    text = path.read_text()
    assert re.match(r"\d\d-", path.name), "chapters sort by a two-digit prefix"
    assert re.search(r"^#\s+\S", text, re.M), "no level-one heading"
    assert re.search(r"^<!--\s*part:\s*\S.*?-->", text, re.M), "no part marker"


@pytest.mark.parametrize("path", HAND_WRITTEN, ids=rel)
def test_directives_point_at_files_that_exist(path):
    text = path.read_text()
    for arg in re.findall(r"<!--\s*lore:\s*(.+?)\s*-->", text):
        assert (ROOT / arg).is_file(), f"lore directive: missing {arg}"
    for arg in re.findall(r"<!--\s*map:\s*(.+?)\s*-->", text):
        target = ROOT / "maps" / arg
        assert target.is_file() or target.is_dir(), f"map directive: missing maps/{arg}"


def test_the_causeway_chart_is_the_generated_one():
    """The chart is rendered from data/, not drawn, which is the only reason
    its astronomy can be trusted. Keep the generator next to its output."""
    assert (ROOT / "maps" / "the-causeway.svg").is_file()
    assert (ROOT / "maps" / "causeway_chart.py").is_file()


def _wikipedia_sources():
    systems = json.loads((ROOT / "data" / "systems.json").read_text())
    return {k: [s for s in (v.get("sources") or []) if "wikipedia.org" in s]
            for k, v in systems.items()}


def test_every_system_cites_a_wikipedia_article():
    """The chart links every star name out to its article, and it takes the
    address from the system's own sources rather than guessing one."""
    missing = [k for k, urls in _wikipedia_sources().items() if not urls]
    assert not missing, f"no Wikipedia source: {missing}"


def test_every_star_on_the_chart_is_a_link():
    """A regenerated chart that quietly stopped emitting anchors would look
    identical. Check the hyperlinks are in the file, not just the names."""
    svg = (ROOT / "maps" / "the-causeway.svg").read_text()
    assert svg.count("<a href=") == svg.count("</a>"), "unbalanced anchors"
    for key, urls in _wikipedia_sources().items():
        assert f'href="{urls[0]}"' in svg, f"{key} is not linked on the chart"


@pytest.mark.parametrize("path", HAND_WRITTEN, ids=rel)
def test_hand_written_prose_is_in_house_style(path):
    found = violations(path.read_text())
    assert not found, "; ".join(f"line {n}: {tok}" for n, tok in found)


def test_the_parents_page_links_the_novel():
    """It is the whole reason that page exists, and the build copies the file
    in only when it has been generated."""
    assert "go-on-their-count.pdf" in (GUIDE / "parents.md").read_text()


@pytest.mark.skipif(not shutil.which("pandoc"), reason="pandoc not installed")
def test_the_site_builds():
    r = subprocess.run(
        [sys.executable, str(GUIDE / "build.py"), "--no-pdf"],
        cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    out = ROOT / "_site"
    for page in ("index.html", "for-parents.html", "gm/index.html", "players/index.html"):
        assert (out / page).is_file(), f"{page} not built"
