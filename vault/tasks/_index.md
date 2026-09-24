# Task index

Registry of every point ever created. **The folder a file sits in is its status** —
`open/`, `blocked/`, `done/`. To change a task's status, move the file and update
its row here. Nothing else to edit.

Since 2026-09-20 the project has a single spec: **[[spec]]**. Tasks cite
requirement IDs (`R11`) instead of restating requirements.

Next free ID: **037**

## Open

Ordered by the build sequence, not by importance — see *Suggested order*.

| ID | Point | Area | Priority | Spec |
|---|---|---|---|---|
| 031 | [[031-workbench-visual-style]] — restyle the templates in the chosen Workbench look | web | medium | R30 |
| 004 | [[004-cloud-deployment]] — deploy to `po-vim.help` on an Oracle Always Free VM (Frankfurt); deploy files written; live at https://po-vim.help 2026-09-24; schedules set (first run 2026-09-25), runbook Step 9 next | infra | high | R25, R26, R34, R35, R36 |
| 036 | [[036-cicd-deploy-on-merge]] — deploy on merge into master, within free tiers *(after 004; Q17–Q19 open)* | infra | medium | R37 |
| 003 | [[003-auth-and-multi-user]] — one shared gate *(postponed by the user 2026-09-23; `SECRET_KEY` from env done)* | web | low | R26 |
| 008 | [[008-pdf-layout-robustness]] — non-A4 and multi-page PDFs | cli | medium | R12 |
| 021 | [[021-run-history]] — should a run leave a trace? *(discussion)* | web | low | R23, non-goal |
| 030 | [[030-workbook-verification]] — blocking defects, then a status report *(discussion)* | data | low | Q15 |
| 018 | [[018-po-value-validation]] — should the PO be format-checked? | data | low | non-goal |
| 032 | [[032-ux-ui-rework]] — UX/UI changes the user may want later *(discussion)* | web | low | R29, R30 |
| 001 | [[001-multi-workbook-support]] — multiple workbooks / months | data | low | non-goal |

**The core implementation tasks now exist — created 2026-09-22 with the user.**
022 through 029 cover routing (R2–R5), workbook access (R6–R10), lookup and
stamping (R11, R12, R12a, R28), output naming and packaging (R14, R15),
verification (R17), exceptions (R18–R20) and the summary screen (R21, R29).
That was the whole of what step 3 had left. **The project is on step 4.**

Four decisions shaped the cut, all taken with the user and recorded in
[[decisions/0012-module-shape-and-test-tooling]]: eight tasks rather than five or
three, a single flat `stamper.py`, pytest as a dev-only dependency, and a
bottom-up build order.

**020 is closed by 025 — 2026-09-22, as planned.** Its rule was never
implemented as a task of its own; [[025-po-lookup-and-exceptions]] built it and
020 moved to `done/` alongside. All 26 duplicated DEKONT keys are refused, the
six conflicting ones are a test fixture, and the message names the workbook as
where the fix belongs.

**007 was rewritten on 2026-09-22.** It predated [[spec]] and described verifying
a `Tescil No`; it now covers R17 as written — the literal `PO:<value>`, and a
failure **withholds** the file rather than aborting — and absorbs R18's
already-stamped input check, which is the same search pointed at the input. Its
frontmatter priority finally matches the `high` this table has said since
2026-09-20.

**017 and 010 closed together — 2026-09-22.** The stamp coordinates are
settled: **FATURA `(300, 45)`, DEKONT `(220, 475)`**, baseline, absolute points,
14pt confirmed ([[decisions/0014-stamp-placement-per-family]], [[spec]] R12a).
**Q5 is closed**, which leaves only the parked Q15 open in the spec. 010 was the
validation half and closed in the same pass, as this section always said it
should.

**As of 2026-09-22 nothing is waiting on an answer.** R15's edge case was
settled during [[027-output-naming-and-packaging]], as planned: several
uploaded with one stamped is a **bare PDF**. The same session added an R18
case, the same filename uploaded twice (stamp once, report the repeat), and
fixed the zip name.
The question [[023-filename-routing]] left for 025 — whether an unroutable name
is the same kind of exception as a failed lookup — was answered **yes**:
[[decisions/0013-exceptions-as-returned-values]].

## Blocked

| ID | Point | Blocked on |
|---|---|---|

*Nothing is blocked.* 010 was unblocked by the new sample PDFs and 020 by the
user's answer on duplicate keys, both 2026-09-20.

## Done

| ID | Point | Completed |
|---|---|---|
| 035 | [[035-uploaded-names-verbatim]] — names shown and keyed exactly as uploaded; a folder part is unroutable | 2026-09-23 |
| 009 | [[009-configurable-stamp-style]] — *closed unbuilt*: the CLI is gone and the user wants none | 2026-09-23 |
| 019 | [[019-tescil-to-po-rename]] — CLI deleted, `sgm_folders/` → `samples/`, notes match the code, acceptance criteria checked | 2026-09-23 |
| 034 | [[034-click-through-feedback]] — manual download, PDF list adds and refuses duplicates, remove button, step navigation | 2026-09-23 |
| 029 | [[029-wire-app-to-module]] — `app.py` is upload, call, render; `/result`; Dockerfile copies `stamper.py` | 2026-09-23 |
| 033 | [[033-turkish-language]] — Turkish by default, English on a switch, reviewed by the user | 2026-09-23 |
| 028 | [[028-summary-screen-and-run-flow]] — `run()`, `summarise()`, `result.html`; clicking through moved to 029 | 2026-09-23 |
| 027 | [[027-output-naming-and-packaging]] — `PO<v>-<name>.pdf`, bare PDF or zip, repeats refused | 2026-09-22 |
| 007 | [[007-verify-stamp-after-write]] — `stamp_checked()`: refuse pre-stamped, verify, withhold | 2026-09-22 |
| 026 | [[026-stamp-the-po]] — `PO:<value>`, page 1, per family, no ink underneath | 2026-09-22 |
| 017 | [[017-dekont-stamp-placement]] — FATURA `(300, 45)`, DEKONT `(220, 475)` | 2026-09-22 |
| 010 | [[010-confirm-placement-across-layouts]] — two layouts, neither overlapped | 2026-09-22 |
| 025 | [[025-po-lookup-and-exceptions]] — the PO, or a named reason | 2026-09-22 |
| 020 | [[020-duplicate-dekont-keys]] — a key matching >1 row is an exception | 2026-09-22 |
| 024 | [[024-workbook-access]] — by position, by header, stripped | 2026-09-22 |
| 023 | [[023-filename-routing]] — filename to sheet, and the key | 2026-09-22 |
| 022 | [[022-core-module-and-tests]] — `stamper.py`, pytest, fixtures, `pytest.ini` | 2026-09-22 |
| 002 | [[002-batch-upload-zip]] — multi-PDF upload, zip + manifest | 2026-09-16 |
| 005 | [[005-shared-session-state]] — *closed unbuilt*: [[decisions/0008-single-user-session-scoped]] removed the problem | 2026-09-16 |
| 006 | [[006-missing-key-handling]] — skip the file, warn by name | 2026-09-08 |
| 016 | [[016-vault-working-memory]] — this vault + session protocol | 2026-08-07 |
| 015 | [[015-two-step-excel-upload]] — Excel uploaded per session, not baked in | 2026-08-06 |
| 014 | [[014-docker-packaging]] — Dockerfile, gunicorn *(the `.dockerignore` it claims is **missing** — see the task)* | 2026-08-06 |
| 013 | [[013-flask-web-app]] — in-memory web stamping | 2026-08-06 |
| 012 | [[012-batch-stamping-cli]] — `stamp_tescil.py` | 2026-08-06 |
| 011 | [[011-data-exploration-and-feasibility]] — mapping + stampability confirmed | 2026-08-06 |

## Suggested order

Dependencies, not preference. The build order below was set 2026-09-22, when
the implementation tasks were created; the two subsections before it are the
2026-09-20 record of what the new data answered, kept as history.

**The long-standing blocker is gone.** The workbook now has `PO` populated in
90/208 FATURA and 81/194 DEKONT rows, and `sgm_folders/` holds ten clean inputs
across all three filename shapes. The PO path can be built and tested.

### What the new files answered

The checklist this section used to hold, with results:

- [x] **`SUB` routes to FATURA (R3)** — confirmed. 164 `SUB` keys, all in
      FATURA. No all-digit key appears in FATURA and no non-digit key in DEKONT,
      so routing is unambiguous.
- [x] **Leading zeros (Q6)** — none observable. Three keys are 5-digit but they
      are genuinely low numbers, not truncations. Q6 stays open in principle;
      the workbook cannot settle it.
- [x] **Does `PO` follow `Dosya No` (Q1)** — **no.** 18 of 70 comparable pairs
      disagree. Closed as a non-goal; `Tescil No` still agrees 192/192.
- [x] **Characterise the PO values** — 10-digit, `45…`, almost always `int` but
      one is a string with a trailing newline. Feeds
      [[018-po-value-validation]].
- [x] **Re-check [[010-confirm-placement-across-layouts]]** — unblocked, moved
      to open.
- [x] **Start [[017-dekont-stamp-placement]]** — DEKONT samples exist; measured
      placement evidence is recorded in the task.
- [x] **Update [[spec]]** — Q1 closed, Q5 half-answered (R12, R28 added), Q6
      sharpened, Q7 and Q8 opened.

### What they raised

- **[[020-duplicate-dekont-keys]]** — new, blocked on the user. `Fatura No` is
  not unique in DEKONT.
- **[[spec]] Q8** — the stamp's colour, size and text format. *Settled the same
  day:* `PO:<value>`, bold red, 14pt (R12), with the size revisitable during
  017.
- **The current manual process ships defects.** One of six reference samples
  (`917034`) carries a PO whose last digit wrapped onto the next line. Strong
  evidence for R17 — and worth the user's attention independently of this app.

### Build order — set 2026-09-22

Bottom-up, by explicit choice: the module is built and tested headless before
any of it is wired to a browser. The reasoning, and what was rejected, is in
[[decisions/0012-module-shape-and-test-tooling]].

1. ~~**[[022-core-module-and-tests]]**~~ — **done 2026-09-22.** The frame is
   standing: `stamper.py` declares the five functions, `tests/` runs green, and
   `pytest.ini` puts the repo root on `sys.path`. **Start at 023.** Two things
   it decided that the next tasks inherit: the index is
   `dict[Family, dict[str, list[str]]]`, so 024 cannot rebuild the flat dict
   that hides duplicates, and one `Family` enum is both the routed sheet and
   the stamp family.
2. ~~**[[023-filename-routing]]**~~ — **done 2026-09-22.** Routing is total
   and never raises: it returns `Routed(key, family)`, with `family=None` for
   R5.
3. ~~**[[024-workbook-access]]**~~ — **done 2026-09-22.** The index is
   `dict[Family, dict[str, list[str]]]` and duplicates survive it.
4. ~~**[[025-po-lookup-and-exceptions]]**~~ — **done 2026-09-22**, closing
   [[020-duplicate-dekont-keys]] with it. `lookup_po()` returns a `Lookup` —
   a PO, or a `Problem` and a reason in words — and never raises, so R19 holds
   by construction ([[decisions/0013-exceptions-as-returned-values]]). Two
   things the rest of the build inherits: **[[026-stamp-the-po]] has no
   empty-PO case**, because every blank and every ambiguity is refused before
   it is called; and **[[028-summary-screen-and-run-flow]] groups on
   `Problem`**, which today has four members and gains two more from
   [[007-verify-stamp-after-write]].
5. ~~**[[017-dekont-stamp-placement]] with
   [[010-confirm-placement-across-layouts]]**~~ — **done 2026-09-22.** The two
   coordinates are measured and written into R12a. Two things
   [[026-stamp-the-po]] inherits beyond the numbers: the stamp must be drawn
   with **`insert_text`, never `insert_textbox`** (a text box is what wrapped
   `917034`'s last digit in the reference sample), and `Family` is now the key
   for layout as well as for sheet, so one enum indexes both.
6. ~~**[[026-stamp-the-po]]**~~ → ~~**[[007-verify-stamp-after-write]]**~~ —
   **both done 2026-09-22.** `stamp_checked()` refuses an input that is already
   stamped, stamps it, and withholds the output unless `PO:<value>` is found
   whole on page 1 ([[decisions/0015-verification-and-prestamp-detection]]).
   `917034` is a regression fixture. The module's surface is complete, and
   `Problem` covers all seven of R18's cases.
7. ~~**[[027-output-naming-and-packaging]]**~~ — **done 2026-09-22.**
   `output_name()`, `repeated_upload()`, `package()`. →
   ~~**[[028-summary-screen-and-run-flow]]**~~ — **done 2026-09-23**, built
   headless: `run()` is the whole batch, `summarise()` the R21 groups,
   `templates/result.html` the screen. →
   ~~**[[029-wire-app-to-module]]**~~ — **done 2026-09-23.** It inherited 028's two
   click-through checks. [[spec]] Q16 (a non-PDF upload) was raised and closed
   in 028: it is an R18 exception, refused inside `run()`. The app becomes thin last, so there is
   never a window where it is half-wired and neither path works. 029 has
   inherited deleting `build_manifest()` / `unique_name()` from 027.
8. ~~**[[019-tescil-to-po-rename]]**~~ — **done 2026-09-23.** The run is
   closed: the CLI is gone, `samples/` replaces `sgm_folders/`, the notes match
   the code, and the acceptance criteria are ticked except 4-digit keys and the
   container.
9. **Start here, when the user has nothing new: [[004-cloud-deployment]].**
   2026-09-23: platform chosen (Oracle Always Free VM,
   [[decisions/0017-oracle-cloud-always-free-vm]]), image built and verified,
   `.dockerignore` back. **[[003-auth-and-multi-user]] no longer comes first**:
   the user postponed the gate (R26 amended). Next is creating the VM and
   deploying. The same day added R36 (no PDF on disk, a Werkzeug gap fixed)
   and a daily 14:00–15:00 Istanbul schedule (R35). Two questions are still
   answered the same evening (domain `po-vim.help`, stop the VM), and the
   `deploy/` files were written and tested locally. **What is left is the
   runbook in [[architecture/deployment]]**, which needs the user's Oracle
   console. **Then [[036-cicd-deploy-on-merge]]** (R37): deploy on merge into
   master, once [[spec]] Q17–Q19 are answered.

Two details are settled **during** implementation rather than before it, by
explicit instruction — neither is an open blocker. **The first is done:** the
exact coordinates and font size ([[spec]] Q5) were settled inside task 017 on
2026-09-22 and written back into R12a, which is what this paragraph asks for.
**The second is done too:** R15's several-uploaded-one-stamped case was
settled in task 027 on 2026-09-22 (bare PDF) and written into R15.

[[021-run-history]] and [[030-workbook-verification]] are discussions the user
parked deliberately. Neither blocks anything and neither should be picked up
ahead of the web app working. 030 was parked 2026-09-22 with its shape already
given — two phases, one blocking and one a status report ([[spec]] Q15).

[[008-pdf-layout-robustness]] and [[009-configurable-stamp-style]] both depended
on what 017 found. **It found "not urgent" for 008**: every sample is A4 and
unrotated, and within a family the layout does not vary at all. 008 inherits one
real risk — a DEKONT whose line-item table grows into the stamp band — recorded
there rather than designed around. 009 was closed unbuilt on 2026-09-23: the CLI it
extended is gone and the user wants none. [[018-po-value-validation]] and [[001-multi-workbook-support]]
remain parked by explicit decision.

## Not tasks

Unresolved questions live in [[spec]] under *Open questions* — that is now the
single home for them. [[open-questions]] is historical: its answered entries are
the record of how 0007 and 0008 were reached. Platform thinking lives in
[[cloud-hosting-options]].
