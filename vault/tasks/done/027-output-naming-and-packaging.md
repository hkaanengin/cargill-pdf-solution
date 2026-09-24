---
area: code
priority: high
created: 2026-09-22
completed: 2026-09-22
---
# 027 — Name the output, and package the batch

Spec reference: **R14**, **R15**, and the withdrawal of **R16**.

## Problem

Three things are wrong with what exists:

- **The name.** `app.py` produces `f"{key}_stamped.pdf"`. R14 wants
  `PO<value>-<original filename>.pdf` — `SGM2026000010461.pdf` with PO
  `4522142137` becomes `PO4522142137-SGM2026000010461.pdf`. The PO travels in
  the filename; `_stamped` carries nothing.
- **The manifest.** `build_manifest()` and `build_zip()` write `MANIFEST.txt`
  into every zip. **R16 is withdrawn** — the zip holds stamped PDFs and nothing
  else, and the summary screen is the sole report (Q14).
- **The packaging condition.** The current rule is `len(stamped) == 1 and not
  skipped`, so one stamped file plus one skipped file yields a zip of one. R15
  keys on the number **successfully stamped**, and exceptions do not change
  packaging.

## The open edge, settled here

R15 leaves exactly one case undecided, deliberately: **several files uploaded,
only one stamped.** By stamped count that is a bare PDF; by upload count it is a
zip holding one file. The user's instruction is to confirm it **while
implementing, against the working app** — so decide it in this task, then write
the answer into R15 in [[spec]] and strike the caveat. Do not leave it
implemented-but-unrecorded.

*Inference, flagged as such:* the plain reading of R15 is stamped-count, which
makes it a bare PDF. Confirm with the user rather than shipping the inference.

## Done when

- [x] Output name is `PO<value>-<original>.pdf` (R14). `output_name()`
- [x] One stamped file → bare PDF; two or more → zip (R15). `package()`
- [x] The zip contains stamped PDFs **only** (R16 withdrawn). `package()`
      writes no manifest. **`build_manifest()` itself still lives in
      `app.py`**, and so does `unique_name()`, because `app.py` is not touched
      until [[029-wire-app-to-module]]. Deleting them was moved to 029's
      *Done when*.
- [x] The uploaded-several-stamped-one case is decided (**bare PDF**),
      confirmed with the user 2026-09-22, and folded into R15 in [[spec]] with
      its caveat removed
- [x] Two uploads that stamp to the same name cannot collide. `unique_name()`
      is **dropped, not kept**. See *What was decided* below.
- [x] Tests cover a single-file run, a multi-file run, and the edge case.
      They are in `tests/test_output.py`, 18 tests, and the suite has 259
      passing.

## What was decided — 2026-09-22, with the user

Three answers, all now in [[spec]]:

1. **Several uploaded, one stamped → bare PDF** (R15). The user first asked
   whether download size should decide it, given a free-tier host. Measured:
   no. A zip of one PDF is within a few hundred bytes of the PDF itself.
   Deflate actually shrinks the ten samples from 2.6 MB to 1.6 MB. So the
   choice was about preference, not cost.
2. **The same filename twice in one batch → stamp the first, refuse and report
   the rest** (new R18 case, `Problem.REPEATED_UPLOAD`). Nothing is renamed.
   This replaces `unique_name()`'s `_2` suffix, which would have put two
   copies of one document in the zip.
3. **Zip name stays `stamped_<YYYYMMDD_HHMMSS>.zip`** (R15). The spec had
   never named it.

## What was built

In `stamper.py`:

- `output_name(filename, po)` → `PO<po>-<filename>`, with the filename
  verbatim, extension included.
- `repeated_upload(filename, seen)` → `Lookup | None`. It returns a `Lookup`
  so a repeat groups and renders exactly like a failed lookup on 028's
  screen. The caller owns `seen` for one batch. Call order in the loop:
  `repeated_upload(name, seen) or lookup_po(index, *route_filename(name))`.
- `package(stamped, now=None)` → `Download(name, data, mimetype) | None`.
  Nothing stamped gives `None`, never an empty zip (R20).

## Findings

- **Collisions are now impossible by construction, so `package()` raises
  on one.** The output name is `PO<po>-<filename>`, and one filename always
  resolves to one PO. So two outputs can only share a name if the same
  filename was uploaded twice, and `repeated_upload()` refuses that. A
  collision reaching `package()` is therefore a bug in the caller, and it
  raises `ValueError`. This is not a per-file outcome, so it does not
  contradict [[decisions/0013-exceptions-as-returned-values]]. Without the
  check, `ZipFile` would write both entries and only warn.
- **`secure_filename()` and Q11 do not fight on anything observed.** It leaves
  every real key untouched, and the near miss `SGM2026000011171 (1).pdf`
  becomes `SGM2026000011171_1.pdf`, which is still refused. Both are tested.
  **It does repair one shape, though.** `../SGM2026000010413.pdf` comes out
  as `SGM2026000010413.pdf`, because it strips path components. Browsers send
  a bare basename, so this should not arise from the upload form. Noted on
  [[029-wire-app-to-module]] rather than designed around.
- **A delivered file fed back in is unroutable.** `PO…-917031.pdf` starts with
  neither `SGM`/`SUB` nor a digit, so it would be refused under R5 even
  before `already_stamped()` saw it. This is tested.
- **Memory on a free tier is the real size risk, and it belongs to 004.** It
  was raised by the user's size question. The whole batch sits in RAM, and
  `MAX_CONTENT_LENGTH` is 200 MB. Logged on [[004-cloud-deployment]].

## Notes

`secure_filename()` is applied to uploads today and must keep being applied — but
note it runs *before* the key is derived, so it is also part of R1's "filename
with `.pdf` removed". A name it mangles is a near miss and R18 refuses those
rather than repairing them (Q11); worth a test that the two do not fight.

A run where nothing stamped produces no download at all (R20) — that is
[[028-summary-screen-and-run-flow]]'s to report, but the packaging code must
return nothing rather than an empty zip.
