---
created: 2026-09-20
updated: 2026-09-23
---
# Spec — PO stamping for SGM, SUB and DEKONT documents

The single description of what this project builds and why. Tasks cite
requirement IDs (`R7`) rather than restating them. **Requirements are numbered
and testable; if a statement here can't be checked, it belongs in Plan
([[architecture/overview]]) or in a decision record, not in this file.**

Supersedes the scattered spec that lived across `architecture/`, `decisions/`
and task "Done when" lists. Those still hold — this points at them, it does not
replace them.

> **Status of the data — updated 2026-09-20:** the new workbook and the new
> sample PDFs have arrived. `PO` is now populated in **90 of 208** FATURA rows
> and **81 of 194** DEKONT rows; the remainder are genuinely empty, which makes
> the R18 empty-PO exception the majority path rather than an edge case.
> `samples/` (then `sgm_folders/`) holds ten clean inputs covering all three
> filename shapes. The
> PO path can now be built and tested. What the new data changed is recorded in
> [[architecture/data-layout]].

---

## Purpose

For a given customs document PDF, find its row in an uploaded Excel workbook and
print that row's **PO** value onto the page, then deliver the stamped file under
a new name that carries the PO.

## Users and context

- **One person.** Not a few users taking turns — one. That person uploads the
  workbook, uploads the PDFs, and downloads the results.
- **Every session is fresh.** Nothing persists between sessions by design.
- **Local during development, hosted when it's finished.** The destination is a
  hosted deployment on an Oracle Cloud Always Free VM
  ([[decisions/0017-oracle-cloud-always-free-vm]]); local and Docker are the
  development path. The gate in front of it is postponed (R26).
- **A wrong stamp is the worst outcome in the project.** Everything this tool
  does is stamping, so a plausible-looking but incorrect customs document is the
  failure that matters. The user checks the output too, but the app is expected
  to do its best independently.

---

## Requirements

### Input and routing

- **R1** — The lookup key is the input PDF's filename with `.pdf` removed. **No
  PDF content is ever parsed to obtain the key.**
- **R2** — A filename beginning `SGM` routes to the **FATURA** sheet.
- **R3** — A filename beginning `SUB` routes to the **FATURA** sheet.
- **R4** — A filename consisting **entirely of digits** routes to the **DEKONT**
  sheet. Any length is valid — 4, 5 and 6 digits are all legitimate keys.
- **R5** — A filename matching none of R2–R4 cannot be routed to a sheet and is
  an exception (R18).
- **R33** — **The app never changes a file's name.** Every name it shows (on
  the summary screen, in flash messages, and the loaded workbook's name) is
  the name exactly as uploaded. That same unchanged name is the one R1 takes
  the key from. Stated by the user 2026-09-23, "so the user would not be
  confused", after seeing `SGM2026000011171 (1).pdf` listed as
  `SGM2026000011171_1.pdf`. The only renaming is the one R14 asks for, and it
  keeps the uploaded name whole inside the new one.

### Workbook access

- **R6** — Sheets are selected **by position**: sheet 2 is FATURA, sheet 3 is
  DEKONT. Position is the authoritative reference.
- **R7** — Sheet **name is not used at all**. The app goes to sheet 2 for FATURA
  and sheet 3 for DEKONT and does not look for, match on, or gate the run by the
  name it finds there — stated by the user 2026-09-20, closing Q2. A workbook
  whose sheets are in a different order will therefore be read as if they were
  in the right one; that is accepted.
- **R8** — Within the selected sheet, the key column is `Fatura No` and the
  value column is `PO`, both found **by header text, never by column position**.
  The workbook is hand-maintained and column order shifts — see
  [[decisions/0004-match-columns-by-header]].
- **R9** — The workbook is opened with `data_only=True`, or formula cells return
  formulas instead of values.
- **R10** — Every string cell read is `.strip()`ed. Values in this workbook carry
  trailing whitespace.

### Stamping

- **R11** — The value stamped is the matched row's **`PO`** value. `Tescil No` is
  no longer stamped and is no longer part of the product.
- **R12** — The stamp reads **`PO:<value>`** — the prefix is part of the stamp,
  not decoration — drawn **bold red at 14pt**. Stated by the user 2026-09-20.
- **R12a** — The stamp position **depends on the document type**. FATURA-routed
  documents (`SGM`, `SUB`) and DEKONT-routed documents (all-digit) have
  different layouts and therefore take different positions. A single global
  coordinate is not correct, and `(240, 170)` is **withdrawn**. **Settled
  2026-09-22** against every clean sample, closing Q5 —
  [[decisions/0014-stamp-placement-per-family]]:

  | Family | Routed from | Baseline `(x, y)` |
  |---|---|---|
  | FATURA | `SGM`, `SUB` | **`(300, 45)`** |
  | DEKONT | all-digit | **`(220, 475)`** |

  Coordinates are **absolute points**, top-left origin, and assume A4
  (595 × 842). **14pt is confirmed**, not merely a starting value. The stamp is
  drawn with `insert_text` and never `insert_textbox`: a text box is what
  wrapped a PO's last digit onto a second line in the reference sample
  `917034`.
- **R28** — The stamp is always placed on the **first page**, whatever the page
  count. DEKONT scans run to two pages; page 1 is the only page stamped —
  stated by the user 2026-09-20.
- **R13** — Source PDFs are never modified. Output is always a copy —
  [[decisions/0003-never-modify-originals]].

### Output

- **R14** — Each stamped file is renamed to `PO<value>-<original filename>.pdf`.
  `SGM2026000010461.pdf` with PO `4522142137` becomes
  `PO4522142137-SGM2026000010461.pdf`; `917023.pdf` with PO `4522182195` becomes
  `PO4522182195-917023.pdf`.
- **R15** — One file in, one file out; several files in, a zip. Packaging keys
  on the number of files **successfully stamped**: one is delivered as a bare
  PDF, two or more as a zip. The download contains stamped PDFs and nothing
  else — exceptions do not change the packaging, they are reported on the
  summary screen (R21). Agreed with the user 2026-09-20.
  - **Several files uploaded, only one stamped, is a bare PDF.** Stamped count
    decides, never upload count. Confirmed by the user 2026-09-22 during
    [[027-output-naming-and-packaging]], closing the case this requirement
    left open. Size played no part: a zip of one PDF is within a few hundred
    bytes of the PDF itself.
  - The zip is named **`stamped_<YYYYMMDD_HHMMSS>.zip`**, kept from the
    existing app. Confirmed by the user 2026-09-22.
- **R16** — *Withdrawn 2026-09-20.* There is **no manifest file**. The zip
  contains stamped PDFs only. Outcomes are reported on screen (R21) and nowhere
  else — the user's explicit decision, closing Q14. The ID is retired rather
  than reused so older references stay unambiguous.

### Verification

- **R17** — After stamping and **before the output is delivered**, the app
  confirms the literal string **`PO:<value>`** is present in the output PDF. A
  stamp that silently failed to render must not reach the user. Searching for
  the prefixed form, not the bare number, is deliberate: it distinguishes the
  app's own stamp from a number that merely happens to appear in the document —
  user's reasoning, 2026-09-20, closing Q10.

### Exceptions

- **R18** — These are exception cases. In each, **nothing is stamped, no output
  file is produced for that input**, and the user is told which file failed and
  why:
  - the key is not present in the routed sheet
  - the row is found but its `PO` cell is empty
  - the filename matches no known pattern (R5)
  - the filename is not an **exact** key — no normalisation is attempted, and a
    near miss such as `SGM2026000011171 (1).pdf` is refused rather than repaired
    (Q11, closed 2026-09-20)
  - **the key matches more than one row** in the routed sheet. Duplicate keys
    are a data-entry mistake on the workbook side, confirmed by the user
    2026-09-20; the app never guesses which row is meant (Q7)
  - **the input already carries a `PO:` stamp.** Confirmed by the user as
    something that should not occur; if it does, it is refused rather than
    stamped twice (Q9)
  - verification fails (R17) — the file is **withheld**, not delivered with a
    warning (Q3, closed 2026-09-20)
  - **the same filename is uploaded more than once in one batch.** The first
    copy is processed as normal. Each later copy is not stamped and is
    reported as a repeated upload. Nothing is renamed, so the download never
    holds two copies of one document. Stated by the user 2026-09-22.
  - **the file is not a `.pdf`.** Not expected ever to happen; if it does, the
    file is ignored and reported on the summary screen, and the rest of the
    batch goes ahead. Decided by the filename's extension, not by opening the
    file. Stated by the user 2026-09-23, closing Q16.
- **R19** — An exception never aborts the batch. Every other file is still
  stamped and delivered — [[decisions/0006-skip-missing-keys-with-warning]].
- **R20** — A batch in which *every* input fails produces no download, and says
  so plainly.
- **R21** — At the end of a run the user sees a **summary screen**, on the same
  screen that offers the download. It accounts for **every input file**, grouped
  by outcome:
  - those **stamped**, each named with the PO it received — `x.pdf → PO:123`
  - those **not stamped because the key is not in the workbook**
  - those **not stamped because the row exists but `PO` is blank**
  - those not stamped for any other exception in R18, each with its reason
  Shape confirmed by the user 2026-09-20. This screen is the **only** report of
  what happened — see R16.

### The run, end to end

- **R29** — The web app walks one path, in this order. Described by the user
  2026-09-20:
  1. the user lands on the app
  2. they are asked to upload the **Excel workbook**
  3. once it is loaded, they are asked to upload the **PDF files**
  4. they press a **Stamp** button
  5. the app stamps
  6. they land on a screen offering the **download** — a bare PDF or a zip
     (R15) — and showing the **summary** (R21) beside it

  **The download starts only when the user clicks it.** It never starts by
  itself on arriving at the results screen. Stated by the user 2026-09-23 after
  the first click-through, reversing the automatic download the old app had.

  **The user can go back and forth between the steps**: the workbook step,
  the PDF step, and the results of the last run. Each is reachable from the
  step list once it has something to show: the workbook step always, the PDF
  step once a workbook is loaded, the results once a run exists. Looking at a
  step changes nothing, and the loaded workbook and the last run survive it.
  Stated by the user 2026-09-23, "to double check". *Carried over, not newly
  stated:* loading a **different** workbook still clears the last run, as it
  always has.
- **R32** — On the PDF step, choosing files **adds** them to the list already
  chosen and never replaces it. The user may pick files in several goes before
  pressing Stamp. A file whose name is already on the list is **not added
  again**, and the user is told which ones, by name. Stated by the user
  2026-09-23. Same name means same file, the rule R18's repeated-upload
  check already uses on the server, which stays as the backstop.
  The user's own examples, 2026-09-23, which are the acceptance tests:
  - list `1, 2, 3`, then choosing `4, 5, 6`, gives `1, 2, 3, 4, 5, 6`
  - list `1, 2, 3`, then choosing `2, 3, 4`, gives `1, 2, 3, 4`, and
    `2` and `3` are named as already on the list

  Order is first-chosen first. Each file on the list has a **remove button**
  that takes it off the list before Stamp is pressed. Asked for by the user
  2026-09-23.
  *Limitation, flagged to the user:* the list lives in the browser page until
  Stamp is pressed, so leaving the PDF step (R29's back-and-forth) drops files
  chosen but not yet stamped.
- **R30** — The web app's look follows the **Workbench** direction, chosen by
  the user on 2026-09-23 from three drawn options: a dark UI, a sidebar
  carrying the steps and the loaded workbook, monospace file lists with status
  dots, and one warm accent. The reference is the canvas linked from
  [[brainstorm/visual-refresh]]. It governs **look only**. R20, R21 and R29
  hold as written. Where the mockup contradicts them, the requirement wins.
  (The mockup's results list is flat, but R21 requires grouping.) Reworking the
  UX beyond this look is later work, in [[032-ux-ui-rework]].
- **R31** — The web app speaks **Turkish by default**, with a switch to
  **English**. The users may not read English well. Stated by the user
  2026-09-23. It covers every word the app shows: page text, buttons, step
  names, flash messages, summary headings, and **each file's reason for not
  being stamped**. It does not cover data: file names, PO values, sheet names
  (`FATURA`, `DEKONT`), column headers (`Fatura No`, `PO`) and the stamp text
  `PO:<value>` (R12) stay as they are. The choice holds for the session.
  The Turkish is drafted by Claude and **reviewed by the user**, and it is
  not done until it has been reviewed.

### Session and deployment

- **R22** — One person, one session. Concurrent use is not a supported case —
  [[decisions/0008-single-user-session-scoped]].
- **R23** — Nothing persists between sessions. The workbook and all results are
  lost when the session ends, by design.
- **R24** — The workbook is uploaded every session by the person stamping —
  [[decisions/0001-excel-per-session-upload]].
- **R25** — The deployment runs **exactly one gunicorn worker**. State lives in
  process memory; a second worker breaks it. Do not raise the worker count.
- **R26** — Before the app is reachable from outside: `SECRET_KEY` from the
  environment rather than source, and HTTPS. **The gate in front of every route
  is postponed** — the user said on 2026-09-23 that nobody needs to log in at
  the moment, and moved it to low priority in [[003-auth-and-multi-user]].
  Accepted with its consequence: while the app is up, anyone who has the URL
  can use it. R35 bounds how long that is.
- **R34** — An upload is capped at **100 MB**, and a larger one is refused with
  a message naming the limit, not an error page. The whole batch is held in
  RAM, so the cap bounds memory. Set by the user 2026-09-23 (was 200 MB).
- **R35** — The app does **not** need to be up all the time. It runs **every day
  from 14:00 to 15:00 Istanbul time** (UTC+3), started and stopped
  automatically. Outside that window **the user can start it by hand when they
  need it, and stop it again**. Stated 2026-09-23, replacing an earlier "by
  hand, 2–3 hours a day". Every stop ends the session, which R23 already
  accepts.
- **R36** — **No uploaded PDF is ever written to the server's disk**, not even
  temporarily. It is uploaded, stamped and downloaded in memory, and it is gone
  once the session ends. Stated by the user 2026-09-23. It covers the web
  framework's own upload handling too: Werkzeug writes any upload over 500 KB
  to a temporary file by default, so the app overrides that. The override
  covers every upload, so the workbook is kept in memory as well.
- **R37** — *Withdrawn 2026-09-24.* It asked for a merge into `master` to
  deploy automatically. After weighing the options for Q17–Q19, the user
  preferred neither: "I think I will deploy it manually. lets get rid of
  cicd-deployment completely." **The user deploys by hand** with
  `deploy/deploy.sh`, at a time they choose outside 14:00–15:00. See
  *Non-goals* and [[decisions/0018-manual-deploy-no-cicd]].
- **R27** — *Withdrawn 2026-09-20.* There is **one entry point, the web app.**
  `stamp_tescil.py` existed so the logic could be exercised without a browser;
  the user confirmed it is only a local test path and can go, since `app.py`
  runs locally too. Keeping two entry points in permanent agreement was pure
  cost. The testability it provided is preserved by keeping the stamping logic
  in a module the tests import directly —
  [[decisions/0011-one-entry-point]]. The ID is retired, not reused.

---

## Non-goals

Ruled out deliberately. Each one is a thing this project will **not** do, and
several were expensive decisions to reach.

- **No multiple concurrent users.** No accounts, no per-user isolation, no
  tenancy. One person (0008, narrowing 0007).
- **No persistence.** No stored workbook, no history, no "which month is
  loaded", no database, no Redis, no session backend (0008).
- **No external customers.** Not a public product — no signup, no password
  reset, no billing (0007).
- **No multi-workbook sessions.** One workbook at a time; uploading another
  replaces it. Cadence is irrelevant — hourly, daily or monthly, the app works
  with whatever it is handed ([[001-multi-workbook-support]]).
- **No PDF content parsing.** The filename is the key and always will be (R1).
- **No PO format validation.** The PO is taken from the workbook as-is and not
  checked against any expected shape — [[018-po-value-validation]].
- **No second source of truth.** The uploaded Excel is the only authority. There
  is no external system to reconcile against.
- **No FATURA↔DEKONT cross-check of the PO.** Measured against the new workbook
  and ruled out: `PO` does not follow `Dosya No` across the two sheets. Of the
  70 DEKONT rows whose `Dosya No` also carries a FATURA `PO`, 52 agree and **18
  disagree**. (`Tescil No` still agrees 192/192 — the property belonged to
  Tescil, not to PO.) Closed Q1, 2026-09-20.
- **No modification of source PDFs, ever** (0003).
- **No second entry point.** The web app is the only way to run this. The
  command-line script is retired — Q13, [[decisions/0011-one-entry-point]].
- **No manifest, no report file, no exported log.** What happened is shown on
  the summary screen and is not written to disk — Q14. Combined with R23
  (nothing persists), this means **the record of a run does not outlive the
  screen**. Accepted deliberately.
  *Reopened as a discussion, not a commitment:* the user asked on 2026-09-20
  that keeping some history be explored later — [[021-run-history]]. Explicitly
  not a priority, and it blocks nothing. Until that discussion concludes, this
  non-goal stands.
- **No CI/CD.** No pipeline builds, tests or deploys on a push or merge. The
  user deploys by hand from their Mac (R37 withdrawn 2026-09-24,
  [[decisions/0018-manual-deploy-no-cicd]]).
- **No handling of malformed inputs.** Non-A4 or rotated pages, encrypted or
  corrupt PDFs, and workbooks with fewer than three sheets are all out of scope.
  Removed from the spec entirely at the user's instruction, 2026-09-20. Every
  sample seen so far is A4, unrotated and unencrypted; if that stops being true
  the question returns, but nothing is built for it now.

---

## Acceptance criteria

The product is correct when all of these hold against the new workbook and the
new sample PDFs. **Checked 2026-09-23** by [[019-tescil-to-po-rename]]: one
mixed batch of all ten samples plus made-up cases, sent through the Flask app
with the real workbook. Each tick is backed by that run and by the suite.

- [x] An `SGM`-named PDF is stamped with its FATURA `PO` and delivered as
      `PO<value>-<original>.pdf` — `PO4522142137-SGM2026000010413.pdf`
- [x] A `SUB`-named PDF resolves through FATURA identically
- [ ] A digit-named PDF of 4, 5 and 6 digits each resolve through DEKONT —
      *6 digits (`917031`) and 5 digits (`14898`) stamped from the real
      workbook. **4 digits cannot be checked with real data:** the workbook has
      no 4-digit key. Routing of a 4-digit name is covered in
      `tests/test_routing.py`. Stays open until a 4-digit key exists*
- [x] A two-page DEKONT is stamped on page 1 only (R28) — *asserted on all
      three DEKONT samples in `tests/test_stamp.py`, 2026-09-22*
- [x] An `SGM`/`SUB` and a digit-named PDF each receive the stamp at their own
      type's position, and neither covers existing content (R12) — *measured
      clear on all ten samples, 2026-09-22, with a prototype; re-confirmed in
      `stamper.py` by [[026-stamp-the-po]] the same day, with no ink at all
      under the stamp on any sample*
- [x] A PDF whose key is absent from its sheet produces an exception, no output
      file, and a named reason
- [x] A PDF whose row exists but whose `PO` is empty produces an exception, no
      output file, and a named reason
- [x] A PDF whose name matches no pattern produces an exception
- [x] A mixed batch containing all of the above delivers the good files in one
      zip and reports the bad ones on the summary screen
- [x] The summary screen accounts for every input, grouped by outcome, naming
      the PO for each stamped file (R21)
- [x] A run with exactly one successfully stamped file downloads as a bare PDF,
      two or more as a zip (R15)
- [x] Several uploaded with exactly one stamped downloads as a bare PDF (R15)
- [x] A filename uploaded twice in one batch is stamped once, and the second
      copy is reported (R18)
- [x] A duplicated key is refused and named as a workbook problem (R18)
- [x] An already-stamped input is refused rather than stamped twice (R18)
- [x] Every delivered PDF is confirmed to contain its PO value before delivery
      — *`stamp_checked()` withholds anything `verify()` cannot find; every
      file in the zip was re-read and carries `PO:<value>` on page 1*
- [x] No file in the input directory is modified — *`samples/` hashed before
      and after the run*
- [x] The web app walks the six steps of R29 in order — `tests/test_app.py`
- [x] A file is listed on the summary screen under the exact name it was
      uploaded with, including one the app refuses (R33) —
      [[035-uploaded-names-verbatim]], `tests/test_app.py`
- [x] The container answers on 8000 with `--workers 1` — *first real build and
      run 2026-09-23: one `gthread` worker, full walk through the container,
      [[004-cloud-deployment]]*

---

## Open questions

Unsettled. Each becomes a decision or a task; none is a licence to guess.
**Everything answered has been folded into the requirements above and is
recorded under *Settled* below** — a closed question stays visible so it is not
reopened from scratch.

**Q5 closed 2026-09-22**, the way it was always meant to be: during
[[017-dekont-stamp-placement]], against the real samples. The coordinates are
in R12a. **Q16 closed 2026-09-23**; see *Settled*. **Q15 is parked by the
user.** Q17–Q19 were opened 2026-09-23 with R37 (CI/CD) and **closed
2026-09-24** when R37 was withdrawn; see *Settled*.


**Q15 — Is the uploaded workbook checked before the run, and how far?**
Raised 2026-09-22 while implementing [[024-workbook-access]]. Today the loader
checks three structural things — a header row exists, and `Fatura No` and `PO`
are present — and nothing else. Measured behaviour of the rest:

| Upload | Today |
|---|---|
| Fewer than three sheets | `IndexError` from the loader; the app shows it as a message |
| Not an xlsx, or corrupt | `BadZipFile` from the loader; the app shows it as a message |
| Sheets in the wrong order | loads, backwards |
| Empty sheets, no data rows | loads, empty index |
| Last month's workbook | loads |

Two of these matter differently, and the distinction is the question:

- **Correctness is not at risk from a reordered workbook.** No key shape
  appears in both sheets, so a swapped workbook makes *every* file fail lookup
  and R20 stops the run with no download. The reason shown is misleading
  ("key not in workbook" rather than "this workbook is not the one you think"),
  but nothing is stamped wrongly.
- **An unreadable workbook is a message, not a crash.** Since
  [[029-wire-app-to-module]], `POST /excel` catches whatever the loader raises
  and shows it on the workbook step (checked again 2026-09-23). The message is
  the raw Python error, which is not friendly, and it is not translated. What
  the user *should* see is part of this question.

**The shape of the answer is decided; the detail and the timing are not.**
The user's direction, 2026-09-22 — verification happens in **two phases**:

1. **Blocking.** Critical defects that genuinely stop the process, checked
   before a run starts. The example given: sheets 2 and 3 not existing.
2. **Non-blocking.** A status report on the workbook, shown to the user without
   stopping anything. The example given: duplicated `Fatura No` values in sheet
   2 or sheet 3.

**Deliberately not being built yet** — the user asked on 2026-09-22 to discuss
it at a later time. Parked as [[030-workbook-verification]], the same way
[[021-run-history]] is parked. Nothing depends on it: correctness is already
protected, because a workbook of the wrong shape makes every lookup fail and
R20 stops the run with no download.

Two things to bring into that discussion, both found while raising this:

- **Phase 2 is not a restatement of R18.** R18 already refuses a duplicated key
  *for an uploaded file that hits one*. A workbook-level report is different in
  kind: it would surface all 26 duplicated DEKONT keys at upload time,
  including the ones no uploaded PDF touches. Worth deciding which is meant.
- **A name-free swap check is available.** FATURA keys are 100% non-digit and
  DEKONT keys 100% digit, so a reordered workbook is detectable from the data
  alone, without ever reading a sheet title — it would not contradict R7. It
  could sit in either phase. An option, not a proposal.

Until that discussion concludes, the loader checks three structural things and
nothing else. An unreadable workbook raises, and the app turns that into a
message.

---

### Settled — 2026-09-24

| | Question | Answer |
|---|---|---|
| **Q17** | A merge while the VM is stopped (R37) | **Moot.** R37 withdrawn: there is no pipeline. The user starts the VM, deploys by hand, and stops it again. |
| **Q18** | What the pipeline tests (R37) | **Moot.** For the record: the full suite runs in about 3 s, but on a clean checkout (no workbook, no `samples/`) 206 pass and 256 fail or error. The local deploy checklist (`DEPLOY.md`, not in git) runs the full suite before deploying. |
| **Q19** | A merge while the app is in use (R37) | **The user avoids 14:00–15:00** when deploying. Stated 2026-09-24, before R37 was withdrawn, and it still holds for manual deploys. |

### Settled — 2026-09-23

| | Question | Answer |
|---|---|---|
| **Q16** | An uploaded file that is not a PDF | Never expected. If it happens, it is an **exception**: not stamped, reported on the summary screen, batch continues (R18). Raised in [[028-summary-screen-and-run-flow]] after measuring that `SGM….docx` aborted the whole batch. **Inference, to confirm:** the extension check ignores case, so `.PDF` counts as a PDF. That is what the app already did, so behaviour doesn't change. |

### Settled — 2026-09-22

| | Question | Answer |
|---|---|---|
| **Q5** | Exact stamp coordinates, per document type | **FATURA `(300, 45)`, DEKONT `(220, 475)`**, absolute points, 14pt confirmed. Measured against all ten clean samples, and matching where the manual process already stamps — R12a, [[decisions/0014-stamp-placement-per-family]]. |

### Settled — 2026-09-20

Kept as a record. Each is now a requirement or a non-goal.

| | Question | Answer |
|---|---|---|
| **Q1** | Does `PO` follow `Dosya No` across sheets? | **No** — 18 of 70 pairs disagree. Measured, not asked. Non-goal. |
| **Q2** | Sheet name mismatch — stop or warn? | **Neither.** Name is not consulted at all; position only (R7). |
| **Q3** | File that fails verification | **Withheld** (R18). |
| **Q4** | Files or folders? | **Files.** |
| **Q6** | Leading-zero digit keys | **Do not occur**, in filenames or in the workbook. No normalisation rule needed. |
| **Q7** | Key matching more than one row | Workbook-side data-entry mistake. **Exception for that input**, batch continues, reported in the summary (R18, R19, R21). |
| **Q8** | Stamp appearance and text | **`PO:<value>`, bold red, 14pt** (R12). Size revisitable during 017. |
| **Q9** | Input already stamped | Should not occur; if it does, **exception** (R18). |
| **Q10** | What R17 checks | Search for the literal **`PO:<value>`**, not the bare number — the prefix is what makes it decisive (R17). |
| **Q11** | Near-miss filenames | **Refused.** No normalisation, no repair (R18). |
| **Q12** | Malformed inputs, non-A4, encrypted, short workbook | **Dropped entirely** at the user's instruction — see *Non-goals*. |
| **Q13** | Keep the command-line entry point? | **No.** `stamp_tescil.py` was only a local test path; `app.py` runs locally too. One entry point (R27 withdrawn). |
| **Q14** | Manifest file inside the zip? | **No.** Zip holds stamped PDFs only; the summary screen is the sole report (R16 withdrawn, R21 rewritten). |

**A note on Q10.** The user's answer settles what verification *checks*. It does
not cover the other half raised at the time: text search confirms the stamp
exists, never where it landed, so a stamp rendered on top of existing content
would still pass. That half is not a verification problem — it is handled by
choosing good coordinates in [[017-dekont-stamp-placement]] and confirming them
in [[010-confirm-placement-across-layouts]]. Recorded here so it is not
mistaken for an oversight.

## What this spec changes

Against the project as it stood before 2026-09-20:

| Was | Now |
|---|---|
| Stamp `Tescil No` | Stamp `PO` (R11) |
| One sheet, `FATURA`, hardcoded | Routed by filename to sheet 2 or 3 (R2–R6) |
| `SGM` filenames only | `SGM`, `SUB`, and all-digit names (R2–R4) |
| Output keeps its input filename | Renamed `PO<value>-<name>.pdf` (R14) |
| Missing key is the only exception | Empty PO and unroutable name join it (R18) |
| Nothing checks the stamp landed | Verified before delivery (R17) |
| Outcomes reported in a manifest file | An on-screen summary only (R21); no manifest (R16 withdrawn) |

`Tescil No` leaves the product entirely (R11). `stamp_tescil.py` and its
`load_tescil_map()` were deleted on 2026-09-23 by [[019-tescil-to-po-rename]].
`Tescil No` is still a column in the workbook; the app does not read it.
