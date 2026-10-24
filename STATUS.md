# STATUS.md

Project: **Free Home Inventory Kit** — printable room-by-room inventory
sheets for insurance/estate peace of mind.
Owner: Asdale Dynamics, LLC. Status: **complete, verified 2026-10-23**.

## What was built

- **6 printable HTML/CSS sheets** in `sheets/` (offline-only — no scripts,
  no web fonts, no external references of any kind):
  1. `01-room-by-room-log.html` — room-by-room inventory log table
  2. `02-photo-caption-cards.html` — 4-up photo caption cards
  3. `03-serial-number-tracker.html` — make/model/serial tracker
  4. `04-policy-contacts.html` — policy & emergency contacts one-pager
  5. `05-annual-update-reminder-card.html` — yearly reminder card with
     fold line, checklist, and multi-year check-in log
  6. `90-print-test-page.html` — self-test page (glyphs, fills, backgrounds)
- **`build.py`** — zero-dependency print-to-PDF build script. Prints every
  sheet with the locally installed headless Chrome/Chromium (`--browser`
  flag overrides auto-detection). Installs nothing, downloads nothing.
- **Ready-to-print PDFs** of every sheet in `output/` (built and committed).
- **`GUIDE.md`** — friendly, plain-English usage guide with a 20-minute
  quick start; explicitly documents that nothing leaves your home.
- **`README.md`** — overview, run instructions, test instructions.
- **`LICENSE`** — MIT, `Copyright (c) 2026 Asdale Dynamics, LLC`; credit in
  README.
- **`tests/`** — pytest suite (stdlib only + poppler-utils) verifying PDF
  output for **every** sheet.

## Privacy guarantees (test-enforced)

- Sheets contain no `<script>`, `<iframe>`, remote images, external
  stylesheets, or absolute URLs — enforced by
  `tests/test_sheets.py::test_sheets_reference_nothing_external`.
- Sheets contain no keys/tokens/passwords — enforced by an automated scan
  (`test_sheets_contain_no_placeholder_secrets`).
- Built PDFs render the "never leaves your home" line on every sheet.

## How to run

```sh
python3 build.py          # prints every sheet to output/*.pdf
python3 build.py --check  # verify a browser is found, no build
pytest tests/             # rebuild + verify every PDF (9 tests)
```

Or simply double-click any `sheets/*.html` and press Ctrl+P.

## Verification results (final clean run, 2026-10-23)

- `python3 build.py` → **6/6 PDFs built** (85–122 KB each), exit 0.
- `python3 -m pytest tests/` → **9 passed** (15 s). Coverage per sheet:
  valid `%PDF` header, US Letter (612×792 pt), expected text present,
  non-blank ink coverage (backgrounds/rules render), page-count minimums.
- Visual spot-check: rendered all 6 PDFs with `pdftoppm` and reviewed
  them; fixed two layout issues found this way (a stray character in the
  reminder card markup, and a wasted trailing page on the photo cards —
  now exactly one Letter page each for sheets 2–5; sheet 1's 20 rows +
  tipbox also fit one page).
- Edge cases tested: build with a nonexistent browser fails cleanly with
  guidance (`--browser /nonexistent/no/browser` → exit 1, friendly error);
  repeat builds stay stable with valid headers.

## Known gaps / future ideas

- Layout is tuned for US Letter; A4 prints fine but table row spacing
  isn't A4-optimized.
- Fill-in lines are for hand-writing; there is no editable/typed-PDF form
  mode (browser Ctrl+P on the HTML lets you type before printing).
- `build.py` supports Chrome/Chromium only — no Firefox/WeasyPrint
  backends (Chrome is effectively universal; fallback could be added).
- No Spanish/other-language sheet translations yet.
- The annual reminder card's "cut & fold" is a printable guide rather
  than an actual interactive card.
- Tests rely on `pdftotext`/`pdfinfo` (poppler-utils) being installed; on
  Windows/macOS without poppler, the ink/text checks would need
  `brew install poppler` or similar.
