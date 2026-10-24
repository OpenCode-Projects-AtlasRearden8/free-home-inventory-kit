#!/usr/bin/env python3
"""Build script for the Free Home Inventory Kit.

Prints every HTML sheet in sheets/ to a matching PDF in output/
using the local copy of Chrome or Chromium in headless mode.
(That is the same engine your browser would use if you pressed
Ctrl+P yourself — the PDFs look exactly like the paper printouts.)

No dependencies beyond the browser: nothing is installed,
nothing is downloaded, nothing leaves your computer.

Usage:
    python3 build.py                 # build all sheets
    python3 build.py --check         # just report what's missing
    python3 build.py --browser PATH  # use a specific browser binary
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS_DIR = os.path.join(HERE, "sheets")
OUTPUT_DIR = os.path.join(HERE, "output")

# Common browser binary names, checked with shutil.which in order.
BROWSER_CANDIDATES = [
    "google-chrome-stable",
    "google-chrome",
    "chrome",
    "chromium",
    "chromium-browser",
    # Flatpak / Snap installs, checked last because they are slower to start.
    "/var/lib/flatpak/exports/bin/org.chromium.Chromium",
]

EXTRA_EXE_PATHS = [
    "/opt/ungoogled-chromium",   # ungoogled-chromium tarball installs
    "/opt/google/chrome",        # official Chrome tarball installs
]


def find_browser(requested=None):
    """Return the path to a usable headless-capable browser, or None."""
    if requested:
        return requested if os.path.exists(requested) else None
    for name in BROWSER_CANDIDATES:
        found = shutil.which(name)
        if found:
            return found
    for directory in EXTRA_EXE_PATHS:
        for base in ("chrome", "chromium", "chrome-wrapper"):
            candidate = os.path.join(directory, base)
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
    return None


def chrome_pdf_command(browser, html_path, pdf_path):
    """One invocation of headless Chrome printing html_path to pdf_path."""
    url = "file://" + os.path.abspath(html_path)
    return [
        browser,
        "--headless",
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        url,
    ]


def build_sheet(browser, html_path):
    """Print one HTML sheet to PDF. Returns True on success."""
    name = os.path.splitext(os.path.basename(html_path))[0]
    pdf_path = os.path.join(OUTPUT_DIR, name + ".pdf")
    cmd = chrome_pdf_command(browser, html_path, pdf_path)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60
        )
    except subprocess.TimeoutExpired:
        print(f"  FAIL {name}: browser timed out after 60s")
        return False
    if result.returncode != 0 or not os.path.exists(pdf_path):
        print(f"  FAIL {name}: exit {result.returncode}")
        if result.stderr.strip():
            print("        " + result.stderr.strip().splitlines()[-1])
        # Clean up any partial file so we never ship a broken PDF.
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        return False
    size = os.path.getsize(pdf_path)
    if size < 1000:
        print(f"  FAIL {name}: PDF suspiciously small ({size} bytes)")
        os.remove(pdf_path)
        return False
    print(f"  built output/{name}.pdf  ({size:,} bytes)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Print all kit sheets to PDF.")
    parser.add_argument("--browser", help="path to a Chrome/Chromium binary")
    parser.add_argument("--check", action="store_true",
                        help="check for a browser and list sheets, don't build")
    args = parser.parse_args()

    sheets = sorted(glob.glob(os.path.join(SHEETS_DIR, "*.html")))
    if not sheets:
        print("No HTML sheets found in sheets/. Nothing to build.")
        return 1

    browser = find_browser(args.browser)
    if not browser:
        print("Could not find a Chrome or Chromium browser.")
        print("Options:")
        print("  * install Google Chrome (free)")
        print("  * run:  python3 build.py --browser /path/to/chrome")
        return 1

    print(f"Browser: {browser}")
    print(f"Sheets:  {len(sheets)} found in sheets/")
    if args.check:
        return 0

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    failures = 0
    for html_path in sheets:
        name = os.path.basename(html_path)
        # Only feed the kit's own print sheets to the browser (any stray
        # .html in sheets/ is skipped via the leading-number convention
        # being optional; every .html here is meant to be printable).
        if not build_sheet(browser, html_path):
            failures += 1
            print(f"  (while building {name})")

    if failures:
        print(f"\n{failures} sheet(s) failed to build.")
        return 1
    print(f"\nDone — {len(sheets)} PDFs in output/. "
          "Print them, or bring the folder to any print shop.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
