"""Shared helpers for the Free Home Inventory Kit test suite.

Zero external Python dependencies: only the standard library plus the
poppler-utils command-line tools (pdftotext / pdfinfo / pdftoppm).
"""

import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEETS_DIR = os.path.join(ROOT, "sheets")
OUTPUT_DIR = os.path.join(ROOT, "output")

# US Letter: 612 x 792 points.
LETTER_W = 612
LETTER_H = 792


def sheet_files():
    """All printable sheet HTML files, sorted (excluding shared css)."""
    return sorted(
        name for name in os.listdir(SHEETS_DIR) if name.endswith(".html")
    )


def output_path_for(sheet_html_name):
    return os.path.join(
        OUTPUT_DIR, os.path.splitext(os.path.basename(sheet_html_name))[0] + ".pdf"
    )


def pdf_text(pdf_path):
    """Extracted text of a PDF (all pages), via pdftotext."""
    return subprocess.run(
        ["pdftotext", pdf_path, "-"],
        capture_output=True, text=True, check=True,
    ).stdout


def pdf_page_size(pdf_path):
    """(width_pts, height_pts) of page 1 of a PDF, via pdfinfo."""
    info = subprocess.run(
        ["pdfinfo", pdf_path],
        capture_output=True, text=True, check=True,
    ).stdout
    for line in info.splitlines():
        if line.startswith("Page size:"):
            nums = re.findall(r"[\d.]+", line)
            return float(nums[0]), float(nums[1])
    raise AssertionError(f"pdfinfo output had no 'Page size:' line:\n{info}")


def pdf_page_count(pdf_path):
    info = subprocess.run(
        ["pdfinfo", pdf_path],
        capture_output=True, text=True, check=True,
    ).stdout
    for line in info.splitlines():
        if line.startswith("Pages:"):
            return int(line.split()[1])
    raise AssertionError(f"pdfinfo output had no 'Pages:' line:\n{info}")


def rendered_page_bitmap(pdf_path, dpi=72):
    """Raw PGM (grayscale) bytes of page 1, via pdftoppm."""
    import glob
    prefix = os.path.join("/tmp/opencode", "testppm")
    subprocess.run(
        ["pdftoppm", "-gray", "-r", str(dpi), "-f", "1", "-l", "1",
         pdf_path, prefix],
        capture_output=True, check=True,
    )
    matches = glob.glob(prefix + "*.pgm")
    assert matches, "pdftoppm produced no .pgm output"
    with open(matches[0], "rb") as chunk:
        return chunk.read()


def fraction_dark(pdf_path):
    """Fraction of renders on page 1 that are 'ink' (roughly, not white).

    A genuinely blank page renders ~0.0; a styled kit sheet renders well
    above 0.01 because of drawn table rules, headers, fills and tints.
    """
    data = rendered_page_bitmap(pdf_path)
    # join PGM header parts: b"P5", b"<w> <h>", b"<max>" then binary
    parts = data.split(b"\n", 2)
    # strip possible '255 ' style max marker inside third part
    _, dims, rest = parts[0], parts[1], parts[2]
    marker = b"255 "
    idx = rest.find(marker)
    if idx != -1 and idx < 8:
        rest = rest[idx + len(marker):]
    total = len(rest)
    assert total > 100, f"decoded bitmap suspiciously small for {pdf_path}"
    dark = sum(1 for value in rest if value < 245)
    return dark / total


def text_of_html(sheet_html_name):
    with open(os.path.join(SHEETS_DIR, sheet_html_name),
              encoding="utf-8") as handle:
        return handle.read()
