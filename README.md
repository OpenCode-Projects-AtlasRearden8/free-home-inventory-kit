# Free Home Inventory Kit

Printable, paper-first sheets for documenting the belongings in your home —
for insurance claims, estate peace of mind, and the general relief of knowing
where things stand. Made with plain HTML/CSS, printed to PDF with the browser
you already have.

**Privacy in one sentence: nothing here touches the internet.** The sheets are
offline-only HTML/CSS (no JavaScript, no web fonts, no external resources) and
your filled-in pages never need to leave your house. No signups, no accounts,
no app, no cloud — ever.

## What's included

| File | Purpose |
|---|---|
| `sheets/01-room-by-room-log.html` | Room-by-room inventory log table |
| `sheets/02-photo-caption-cards.html` | 4-up caption cards for printed photos |
| `sheets/03-serial-number-tracker.html` | Serial/make/model tracker for appliances & electronics |
| `sheets/04-policy-contacts.html` | One-page policy numbers, agent & emergency contacts |
| `sheets/05-annual-update-reminder-card.html` | Yearly "check the binder" reminder card + log |
| `sheets/90-print-test-page.html` | Self-test page for checking your printer & the build |
| `output/*.pdf` | Ready-to-print PDFs of every sheet (built by `build.py`) |

## How to run it

Easiest: open any `sheets/*.html` file in a browser and press Ctrl+P / Cmd+P.

Fully automatic build (uses headless Chrome/Chromium already on your machine):

```sh
python3 build.py            # prints every sheet to output/*.pdf
python3 build.py --check    # verify a browser is found, without building
python3 build.py --browser /path/to/chrome   # if auto-detection misses yours
```

`build.py` requires only Python 3 and a locally installed Chrome or Chromium
(no pip packages, no npm, no downloads, no network access).

## Tests

```sh
pytest tests/
```

The tests rebuild every sheet to PDF and verify, for each of the five sheets:
the PDF exists and is valid, it is US Letter sized, key text is present,
pages are not blank (backgrounds rendered), and that sheet sources contain no
external/remote references — i.e. the "no data leaves your home" promise is
test-verified, not just promised. Tests use only the Python standard library
plus `pdftotext`/`pdfinfo` (poppler-utils).

## Usage guide

See **[GUIDE.md](GUIDE.md)** — a friendly, step-by-step walkthrough in plain
English ("like a friend would explain it"), including the 20-minute quick
start. Not legal or insurance advice.

## License

MIT — see [LICENSE](LICENSE).
Copyright (c) 2026 **Asdale Dynamics, LLC**. Part of the beginner-friendly
tools and guides published by Asdale Dynamics, LLC (visit
dylanasdale.github.io).
