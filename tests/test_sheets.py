"""Tests for the Free Home Inventory Kit.

The suite re-builds every sheet to PDF (via the repo's own build.py, using
the local headless Chrome/Chromium) and verifies each generated PDF:

  * the file exists, is a syntactic PDF (%PDF- name), and is substantial,
  * it is US Letter sized (612 x 792 pt),
  * its extracted text contains that sheet's key phrases,
  * at least one page of it has non-trivial ink coverage (backgrounds and
    rule lines actually render — i.e. the print is not blank).

It also verifies the kit's core privacy claim: no sheet references anything
external (scripts, web fonts, remote images, absolute URLs), so filling the
sheets can never leak data anywhere.

Run with:  pytest tests/
"""

import os
import re
import subprocess
import sys

import helpers as h

# Every sheet -> phrases that must appear in the printed output, plus the
# minimum page count and minimum ink fraction we'd expect from the styling.
SHEET_EXPECTIONS = {
    "01-room-by-room-log.html": {
        "mustContain": [
            "Room-by-Room Inventory Log",
            "Bought (approx. ok)",
            "Friendly tip",
            "never leaves your home",
            "Asdale Dynamics, LLC",
        ],
        "minPages": 1,
        "minInk": 0.01,
    },
    "02-photo-caption-cards.html": {
        "mustContain": [
            "Photo Caption Cards",
            "Tape or glue a printed photo here",
            "Est. value",
            "Friendly tip",
            "never leaves your home",
            "Asdale Dynamics, LLC",
        ],
        "minPages": 1,
        "minInk": 0.01,
    },
    "03-serial-number-tracker.html": {
        "mustContain": [
            "Serial Number Tracker",
            "Serial number",
            "Where serial numbers hide",
            "never leaves your home",
            "Asdale Dynamics, LLC",
        ],
        "minPages": 1,
        "minInk": 0.01,
    },
    "04-policy-contacts.html": {
        "mustContain": [
            "Policy & Contacts One-Pager",
            "Claims hotline, 24 hours",
            "Where this inventory lives",
            "never leaves your home",
            "Asdale Dynamics, LLC",
        ],
        "minPages": 1,
        "minInk": 0.01,
    },
    "05-annual-update-reminder-card.html": {
        "mustContain": [
            "Reminder Card",
            "Your once-a-year hour",
            "Yearly check-in log",
            "cut here",
            "Asdale Dynamics, LLC",
        ],
        "minPages": 1,
        "minInk": 0.01,
    },
    "90-print-test-page.html": {
        "mustContain": [
            "Print Test Page",
            "quotes",
            "em dash",
        ],
        "minPages": 1,
        "minInk": 0.005,
    },
}


def _run_build():
    """Run the repo's own build script and raise on failure."""
    result = subprocess.run(
        [sys.executable, os.path.join(h.ROOT, "build.py")],
        capture_output=True, text=True, timeout=300,
    )
    assert result.returncode == 0, (
        "build.py failed:\n"
        + result.stdout
        + result.stderr
    )


def _module_name_map():
    """Map output PDF name -> sheet expectations, keeping order robust."""
    mapping = {}
    for sheet in h.sheet_files():
        pdf_name = os.path.basename(h.output_path_for(sheet))
        # Expectation keys above are the same basenames.
        for key, expectations in SHEET_EXPECTIONS.items():
            if key == sheet:
                mapping[pdf_name] = expectations
    return mapping


def test_sheet_expectations_cover_every_sheet():
    """Guard: every shipped sheet has a matching test expectation entry."""
    all_sheets = h.sheet_files()
    assert set(all_sheets) == set(SHEET_EXPECTIONS), (
        f"sheet/test mismatch: sheets={all_sheets} vs "
        f"expected={set(SHEET_EXPECTIONS)}"
    )


def test_build_script_reproduces_every_pdf(tmp_path):
    """Running build.py succeeds and yields one PDF per sheet."""
    _run_build()
    missing = [
        pdf_name
        for pdf_name in map(
            lambda sheet: os.path.basename(h.output_path_for(sheet)),
            h.sheet_files(),
        )
        if not os.path.isfile(os.path.join(h.OUTPUT_DIR, pdf_name))
    ]
    assert not missing, f"build.py did not produce: {missing}"


def test_repeat_build_is_stable(tmp_path):
    """Second consecutive build leaves valid files (no broken half-writes)."""
    _run_build()  # already ran once above; this should succeed again
    for sheet in h.sheet_files():
        path = h.output_path_for(sheet)
        with open(path, "rb") as handle:
            assert handle.read(8).startswith(b"%PDF"), f"bad header in {path}"


def test_failing_browser_produces_clean_error(tmp_path):
    """If the browser binary is missing/invalid, build.py fails cleanly."""
    result = subprocess.run(
        [sys.executable, os.path.join(h.ROOT, "build.py"),
         "--browser", "/nonexistent/no/browser"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 1
    assert "Could not find" in result.stdout


def test_check_flag_lists_engines_without_building():
    result = subprocess.run(
        [sys.executable, os.path.join(h.ROOT, "build.py"), "--check"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0
    assert "Browser:" in result.stdout


def test_each_pdf_is_valid_letter_sized_printable_output():
    """The core 'PDF output for every sheet' test."""
    _run_build()
    mapping = _module_name_map()
    for pdf_name, expectations in mapping.items():
        pdf_path = os.path.join(h.OUTPUT_DIR, pdf_name)
        assert os.path.isfile(pdf_path), f"missing built PDF: {pdf_name}"

        with open(pdf_path, "rb") as handle:
            magic = handle.read(5)
        assert magic == b"%PDF-", f"not a PDF: {pdf_name}"
        assert os.path.getsize(pdf_path) > 5_000, (
            f"PDF suspiciously small: {pdf_name}"
        )

        width, height = h.pdf_page_size(pdf_path)
        assert abs(width - h.LETTER_W) < 1.0 and abs(height - h.LETTER_H) < 1.0, (
            f"{pdf_name}: page {width}x{height} isn't US Letter"
        )

        pages = h.pdf_page_count(pdf_path)
        assert pages >= expectations["minPages"], (
            f"{pdf_name}: only {pages} page(s)"
        )

        # pdftotext breaks lines at wrapping points, so collapse all
        # whitespace before matching phrases that may wrap mid-phrase.
        text = re.sub(r"\s+", " ", h.pdf_text(pdf_path))
        for phrase in expectations["mustContain"]:
            assert phrase in text, f"{pdf_name}: missing phrase {phrase!r}"


def test_each_pdf_page_actually_prints_ink():
    """No blank printouts: backgrounds and rules render in the PDF."""
    _run_build()
    mapping = _module_name_map()
    for pdf_name, expectations in mapping.items():
        pdf_path = os.path.join(h.OUTPUT_DIR, pdf_name)
        ink = h.fraction_dark(pdf_path)
        assert ink >= expectations["minInk"], (
            f"{pdf_name}: page 1 ink fraction {ink:.4f} < "
            f"{expectations['minInk']}; looks like a blank/broken printout"
        )


def test_sheets_reference_nothing_external():
    """The privacy promise, tested: sheets are sealed offline HTML/CSS."""
    banned_patterns = [
        re.compile(r"<script", re.I),
        re.compile(r"<iframe", re.I),
        re.compile(r"<img\s+[^>]*(?:src=|srcset=)\s*[\"']?(?:https?:)?", re.I),
        re.compile(r"(?:href|src)\s*=\s*[\"']https?://", re.I),
        re.compile(r"@import\s+url", re.I),
        re.compile(r"(?:src|href)\s*=\s*[\"']//", re.I),
        re.compile(r"fonts\.g(?:oogleapis|static)\.com", re.I),
        re.compile(r"javascript:", re.I),
        re.compile(r"<link[^>]*rel=[\"']stylesheet[\"'][^>]*href=[\"']https?:", re.I),
    ]
    for sheet in h.sheet_files():
        html = h.text_of_html(sheet)
        for pattern in banned_patterns:
            assert not pattern.search(html), (
                f"{sheet}: found external/loading pattern {pattern.pattern!r}"
            )


def test_sheets_contain_no_placeholder_secrets():
    """No API keys, tokens, or personal data hiding in the sources."""
    secret_patterns = [
        re.compile(r"api[_-]?key", re.I),
        re.compile(r"(?:secret|token|password)\s*[:=]", re.I),
        re.compile(r"(?:sk|pk)_[A-Za-z0-9]{20,}"),      # OpenAI/Stripe style
        re.compile(r"AIza[0-9A-Za-z_\-]{30,}"),          # Google style
        re.compile(r"-----BEGIN [A-Z ]*KEY-----"),
    ]
    for sheet in h.sheet_files():
        html = h.text_of_html(sheet)
        for pattern in secret_patterns:
            assert not pattern.search(html), (
                f"{sheet}: possible secret/token pattern {pattern.pattern!r} "
                "found in source"
            )
