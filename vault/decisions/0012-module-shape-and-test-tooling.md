---
status: accepted
date: 2026-09-22
---
# 0012 — One flat `stamper.py`, pytest as a dev-only dependency

## Decision

[[decisions/0011-one-entry-point]] settled *that* the logic lives in an
importable module and said nothing about its shape. Agreed with the user
2026-09-22, during the task breakdown:

- **A single flat `stamper.py` at the repo root**, not a `stamper/` package.
- **pytest, in a separate `requirements-dev.txt`.** `requirements.txt` keeps its
  four runtime dependencies — `openpyxl`, `pymupdf`, `flask`, `gunicorn` — and
  gains nothing.
- **Bottom-up build order:** the module is built and tested headless
  ([[022-core-module-and-tests]] → [[026-stamp-the-po]]) before any of it is
  wired to the web app ([[027-output-naming-and-packaging]] →
  [[029-wire-app-to-module]]).

## Why

**Flat module.** The whole of the logic is five functions over twenty-odd
requirements — routing, workbook, lookup, stamp, verify — and comes to a few
hundred lines. A package of five one-function files would add import ceremony
and a navigation step without separating anything that is actually entangled.
The project is small and the requirements are dense; one file that can be read
top to bottom is the better match. Revisit if it stops fitting on a screenful of
scrolling.

**pytest, and dev-only.** 0011 assumes tests but none exist and no framework was
installed. pytest earns its place over stdlib `unittest` on fixtures and
`parametrize` — [[025-po-lookup-and-exceptions]] alone has six conflicting
duplicate keys to table-drive, and every task's fixtures are the same workbook
and the same ten samples. Keeping it out of `requirements.txt` keeps it out of
the container image, which ships to a hosted deployment
([[004-cloud-deployment]]) and has no reason to carry a test runner.

**Bottom-up.** The alternative was a vertical slice — one file end to end
through the browser first, then broaden. Rejected because the requirements that
matter most here are not visible in a browser. A duplicate key stamps a
perfectly normal-looking document with the wrong PO
([[020-duplicate-dekont-keys]]); a blank `PO` is the majority path, not an edge
case; `917034` in `samples_stamped_reference/` is a **real** document from the
current manual process whose stamp is silently truncated. Those are caught by
assertions, not by looking. Building the module first means every requirement is
tested before any of it is reachable through a UI. The cost — nothing works in a
browser until [[029-wire-app-to-module]] — is accepted.

*All three are engineering choices, not product requirements. The user was asked
and chose; nothing in [[spec]] constrains them.*

## Consequences

- [[022-core-module-and-tests]] creates `stamper.py`, `requirements-dev.txt` and
  `tests/conftest.py` before any behaviour is written.
- `Dockerfile` installs from `requirements.txt` only — check it does not widen
  to a glob.
- Acceptance criteria in [[spec]] are checked by module tests plus one
  click-through of R29, per 0011.

## Revisit if

`stamper.py` outgrows comfortable reading, or a second front end appears — the
case 0011 named, where a package's seams would start to pay.
