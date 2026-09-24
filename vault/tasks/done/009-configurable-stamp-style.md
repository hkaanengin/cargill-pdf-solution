---
area: cli
priority: low
created: 2026-08-07
completed: 2026-09-23
---
# 009 — Make stamp position and style configurable

## Problem

`STAMP_X`, `STAMP_Y`, `FONT_SIZE`, `FONT`, `COLOR` are constants at the top of
`stamp_tescil.py`. Changing placement means editing source. Fine for one person
on one laptop; not fine once it's hosted and someone else needs a different
position for a different document type.

> **Closed 2026-09-23 without building anything.** The CLI this task adds
> flags to was deleted ([[019-tescil-to-po-rename]]). Asked whether to rethink
> it for the web app, the user said: "No I dont need a command line script. We
> can do the testing on the app itself on local." The stamp's look and
> position stay fixed by R12 and R12a, as constants in `stamper.py`. If a
> configurable stamp is ever wanted, it starts as a requirement in [[spec]].

## Done when

- [ ] CLI flags override each constant
- [ ] Current values remain the defaults — no behaviour change without flags
- [ ] Settings are documented in `--help`
- [ ] Optionally: a config file, if flags get unwieldy

## Deliberately low priority

The constants are correct for the only document layout in use, and a stamp
position isn't something a casual user should be changing on a customs document.
Rushing this adds a way to get output subtly wrong.

Do it when there's a second real layout that needs different values — likely
falling out of [[010-confirm-placement-across-layouts]].

## Notes

If [[008-pdf-layout-robustness]] moves to proportional coordinates, do that
first — otherwise the flags get built around absolute points and then have to
change meaning. See [[decisions/0002-stamp-placement]].
