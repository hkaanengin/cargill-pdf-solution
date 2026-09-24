# CLAUDE.md

## What this project does

Stamps a **PO number** onto customs document PDFs. For a given PDF, it routes to
a sheet in an Excel workbook by the shape of the filename, looks up the matching
row, prints that row's `PO` value onto the page, and renames the output to carry
the PO.

One entry point, the Flask web app (`app.py`). All routing, lookup, stamping,
verification, naming and packaging lives in `stamper.py`, which `app.py` and the
tests import. `app.py` is upload, call, render. `i18n.py` holds the Turkish and
English strings.

`vault/spec.md` is the description of what the product does. **Where the code
and the spec disagree, the spec wins** and the code is the bug.

**Direction:** hosted, single-user cloud deployment. Local during development.

---

## How we work — spec-driven, in this order

**This project runs a loop. Do not skip steps, and do not run them backwards.**

| Step | Lives in | Means |
|---|---|---|
| **1. Spec** | `vault/spec.md` | What we're building and why. Numbered requirements, non-goals, acceptance criteria. No code decisions. |
| **2. Plan** | `vault/architecture/`, `vault/decisions/` | Architecture, tech choices, data model, risks. *How* the spec gets satisfied. |
| **3. Tasks** | `vault/tasks/` | An ordered queue. Each task small enough for one session, each citing the requirements it satisfies. |
| **4. Execute** | the code | Take the next task, implement it, test it. The user commits — not you. |
| **5. Update state** | back into `vault/` | Move the task file, write down what you learned, adjust the plan if reality disagreed with it. |

**Which step we are on right now is recorded in `vault/Home.md`**, under
*Where we are in the loop*. It is status, so it lives in the vault and never in
this file. Read it before picking up work — arriving at step 4 when the project
is on step 3 is how a session starts writing code nobody asked for.

### The rules that make the loop mean something

- **No code without a requirement.** If you are about to build something that no
  requirement in `vault/spec.md` asks for, stop. Either the spec is missing
  something — fix the spec first, with the user — or the work isn't wanted.
- **Never assume a requirement.** Anything the user has not plainly stated is an
  **open question**, not a sensible default. Add it to the *Open questions*
  section of `vault/spec.md` and ask. This is an explicit instruction from the
  user, given 2026-09-20.
- **Tasks cite requirement IDs** (`R14`), they do not restate them. A
  requirement lives in exactly one place so that changing it changes one place.
- **Changing behaviour means changing the spec first.** A code change that makes
  the spec untrue is a bug, whichever one you meant to be right.
- **The spec's acceptance criteria define done for the product.** A task's own
  "Done when" defines done for that task. They are different things.
- Mark inference as inference. If you are inferring rather than reading, say so.

---

## Working memory — read this before doing anything

**Project knowledge lives in `vault/`, an Obsidian vault inside this repo.**
It is the source of truth for what's being built, what's done, and why.

### At the start of every session

1. Read `vault/spec.md` — what we're building, and the open questions
2. Read `vault/Home.md` — where things stand in ~10 lines
3. Read `vault/tasks/_index.md` — the queue

**Do not ask the user where things left off.** The vault is the answer. If it
doesn't say, say so and update it.

| Need | Read |
|---|---|
| What we're building, and why | `vault/spec.md` |
| What is deliberately *not* being built | `vault/spec.md` → *Non-goals* |
| What's unresolved | `vault/spec.md` → *Open questions* |
| Every point and its status | `vault/tasks/_index.md` |
| What to work on next | `vault/tasks/open/` |
| What's stuck, and on what | `vault/tasks/blocked/` |
| What's already been built | `vault/tasks/done/` |
| How the system works | `vault/architecture/overview.md` |
| Excel sheet + column specifics | `vault/architecture/data-layout.md` |
| How it runs and ships | `vault/architecture/deployment.md` |
| Why a choice was made | `vault/decisions/` |
| Unsettled thinking | `vault/brainstorm/` |

**A task's folder is its status.** There is no `status:` field — `ls
vault/tasks/open/` is the work queue. Task frontmatter carries only `area`,
`priority`, and dates.

### Before ending a session, you MUST

This is step 5 of the loop. Skipping it leaves stale memory, which is worse than
none — the next session will trust it.

1. **Status changed?** Move the task file between `open/`, `blocked/`, and
   `done/`, and update its row in `vault/tasks/_index.md`. Add a `completed:`
   date when moving to `done/`; note the blocker in `_index` when moving to
   `blocked/`.
2. **Reality disagreed with the spec?** Update `vault/spec.md` — the requirement,
   or the open question it turned out to be. Never let code and spec drift.
3. **Learned something while working a task?** Write it into that task file —
   findings, dead ends, and revised design questions are the point of one file
   per task.
4. **New point discovered?** Create it in the right folder using the next free ID
   from `_index`, cite the requirement it serves, and add its row.
5. **Made a non-obvious choice?** Add a file to `vault/decisions/` with an
   explicit **Why** section.
6. **Learned something structural?** Update the relevant `vault/architecture/` file.
7. **Priorities shifted?** Update the *Suggested order* section of `_index`, so
   the next session starts in the right place.

Link tasks by bare filename — `[[017-dekont-stamp-placement]]` — never with a
folder path in front of it. Folder paths break as soon as a task changes status.

### The one rule

**Status and decisions live only in the vault. Never add a status section, a
to-do list, or a "next steps" checklist to this file.** Three competing trackers
is the problem the vault was created to fix — see
`vault/decisions/0005-vault-as-working-memory.md`.

Access `vault/*.md` with plain Read/Edit/Grep — that always works. The `obsidian`
MCP server is also scoped to this vault, but is convenience, not a requirement.

---

## Environment

- Python venv at `.venv/`. Use `source .venv/bin/activate` or call
  `.venv/bin/python3` directly. **It is not in the repo** — an absent `.venv/`
  means create it and install both requirement files, not that something is
  broken.
- Runtime dependencies (`requirements.txt`, and all the container installs):
  `openpyxl` (Excel), `pymupdf` / `fitz` (PDF), `flask`, `gunicorn`.
- Dev dependencies (`requirements-dev.txt`): `pytest`. Deliberately out of the
  image — `vault/decisions/0012-module-shape-and-test-tooling.md`.

```bash
python3 -m venv .venv && .venv/bin/python3 -m pip install -r requirements-dev.txt

.venv/bin/python3 -m pytest                    # the test suite
.venv/bin/python3 app.py                       # web app → http://localhost:8000

docker build -t sgm-stamper . && docker run -p 8000:8000 sgm-stamper
deploy/deploy.sh ubuntu@<vm-ip>                 # ship to the Oracle VM — vault/architecture/deployment.md
```

The user handles git and commits. Do not commit.

## Data gotchas — each one causes silently wrong output

Mirrored here deliberately because getting these wrong produces a plausible-looking
but incorrect customs document. Full detail in `vault/architecture/data-layout.md`,
requirements in `vault/spec.md` R6–R10.

- **Over half the rows have an empty `PO`** (118/208 FATURA, 113/194 DEKONT).
  That is the data, not a bug: each is an R18 exception, reported and not
  stamped.
- **Select sheets by position, never by name** (R6, R7). Sheet 2 is FATURA,
  sheet 3 is DEKONT. Sheet 1 is an empty `PIVOT TABLE`. The sheet name is not
  read at all.
- **DEKONT keys are numbers, FATURA keys are strings.** `Fatura No` in DEKONT
  comes back as `int` (`915623`), in FATURA as `str` (`SGM2026000010413`).
  Always `str(cell).strip()`, never `cell.strip()`.
- **`.strip()` every string cell, keys included.** Values carry trailing
  whitespace and newlines, and 27 FATURA keys carry trailing spaces.
- **Open the workbook with `data_only=True`**, or formula cells return formulas.
- **Match columns by header text, not letter, and exactly.** The two sheets put
  the columns in different places, and both carry a `PO Tarihi` / `PO TARIHI`
  column that a prefix match would pick up instead of `PO`.
- **Never modify the PDFs in `samples/`.** They are the test inputs. The app
  works on uploaded bytes and never writes PDFs to disk.
