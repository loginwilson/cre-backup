---
name: project-acris-open-gaps
description: "OPEN commitments on the acris lane as of 2026-08-24 — imageless sweep parked, one diagnosed source-defect doc awaiting policy, no version control, fixes pending a restart"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-24T21:18:28.997Z
---

**THE LEDGER login ASKED FOR (2026-08-24): "I dont want these gaps
forgotten."** Everything fixed is recorded in [[project-acris-consolidated-lane]]
with its measurement. This file is only what is STILL OPEN.

**1 · IMAGELESS SWEEP IS PARKED, NOT DONE.** Cursor sits at
`_working/_verify_cursor.txt` = `2003071401640001`; ~172k imageless rows are
still unverified. It was pulled off the wire at 15:45 because it consumed
100% of requests AND froze the governor. ✅ The freeze is now fixed (the
climb test counts `verified`; `settle()` still excludes it so the READY rate
stays honest), so resuming with `--verify-imageless` is safe. login asked for
this explicitly: "you could always just do a real pass on them to assure
theres no pdf." Prior result: 1,040+ re-confirmed, ZERO false verdicts.

**2 · `2003030501723001` NEEDS A POLICY, NOT A FIX.** Adjudication recorded
the cause the original 5 failures never had: **"short: 1/3 pages ·
placeholder(end-marker) at page 2"** — ACRIS serves its own end-of-document
marker at page 2 while its own map claims 3 pages. Stable across 7 attempts.
⚠ DO NOT resolve it by accepting the 1 page: that writes a valid, openable,
TRUNCATED document, which is the exact trap `Short` exists to prevent. The
open question is what verdict a SELF-CONTRADICTING SOURCE DOC should get.
⚠ The class is probably larger than one: the old fleet carried **191 Short
docs** that never landed across ~4 attempts each, and their WHY was never
captured — those are now diagnosable if re-adjudicated.

**3 · ✅ VERSION CONTROL EXISTS (2026-08-24).** Two git repos, code-only by ALLOWLIST .gitignore (the tree is 15 GB of caches, so a blacklist fails OPEN): the decoder dir (515 files, 6 MB) and the Updates board dir. ⚠ Neither has a remote — they survive a bad edit, NOT a dead disk. ⚠ A Socrata app token is hardcoded in 7 .py files, so these repos must not be pushed public as-is. SUPERSEDED BELOW: ⚠ VERIFIED, not assumed: the decoder directory is
**not a git repo** (`git rev-parse` fails). Every fix from 2026-08-24 — the
pacer, the pool sizing, contiguity dial, probe-aware governor, session
recycle, watchdog, warm resume, high-water tempo, in-run retry, adjudication,
DIAGNOSED state, 400 evidence, fail timestamps — exists ONLY on disk at
`Decoder Prompt\decoder\acris_lane.py`. Backups made: `acris_lane.py.bak`,
`.bak2` (both PRE-fix, so they are rollbacks, not backups of the work).

**4 · FIXES WRITTEN BUT NOT YET RUNNING.** The live process started 17:01 and
predates these; they take effect at the next restart:
`DIAGNOSED` terminal state · high-water tempo (the current process still saves
CURRENT tempo, which ratchets DOWN across repeated restarts) · honest startup
banner · the verify/governor fix · fail-row timestamps.
⚠ Before any restart, check `lane_tempo.json` holds the PEAK, not a
mid-climb value — seed it from the log's last `TEMPO x -> y` if needed, and
only if the run had ZERO sheds/refusals.

**5 · ~13 UNRESOLVED DOCS** sat empty at last check, single failures in the
cursor's neighbourhood. Expected to heal at cursor wrap (92% base rate) and
now much sooner via in-run retry. Unconfirmed — re-check by joining the fails
log against `navigation.pdf`.

**6 · RICHMOND `rc_lane` CONSOLIDATION** still pending under the drumroll
rule; `rc_live` + the rcpdf trio remain separate processes. See
[[project-rc-rd-coded]].

**⚠ HONEST NOTE ON PROVENANCE.** Several 2026-08-24 defects were introduced
BY ME while patching a live system with heredoc string-replacement:
ratchet-down warm resume, `stuck` undefined when adjudication is off, a banner
printing the cold rate, two monitor crashes (cp1252 on `⚠`, then a blanket
`·`→`|` replace that broke the log regexes). Compile checks and offline
self-tests caught them before they reached ACRIS; the lane never broke. **The
habit that stopped it: verify every anchor EXISTS before editing, prefer
line-based edits over string replacement, and self-test the mechanism offline
(the burst test, the ratchet simulation) rather than on the live source.**

---

**⚠ THE PASS-2 BUILD SPEC (measured 2026-08-24) — NONE OF THIS EXISTS YET.**
login's model, confirmed against the data: *"in the type it would be parcel,
reference, pdf. pass 1 can give every bbl. pass 2 once everything is done can
do bbl through the reference since it can cross crfn or doc id in the rd.
Then, pdf is the final way of keying when its all thats left."*

`nav_key.py` now writes THREE types; **the TYPE is the evidence class, the KEY
is the answer:**

    keyed_by='parcel'     key='BBL;BBL'   done at pass 1
    keyed_by='reference'  key='BBL'       resolved early (target already pulled)
    keyed_by='reference'  key=''          ⚠ THE PASS-2 WORKLIST
    keyed_by='pdf-pass'   key=''          the pass-3 worklist ("pdf" type;
                                          stored under the legacy name for
                                          continuity with rows already written)

⚠ Previously an unresolvable reference was SKIPPED (nothing written), so
"pending" and "never looked at" were the same state and the only way to find
the population was `--rescan`, which WALKS ALL 24M ROWS. Marking it makes
pass 2 a lookup. ⚠ Consequence: a marked row no longer matches the sweep's
`keyed_by IS NULL OR keyed_by=''`, so **pass 2 MUST select
`keyed_by='reference' AND key=''`** or it finds nothing.

**REFERENCE SHAPES, MEASURED over 857 rd rows across 2003/2009/2026:**

    crfn                370   81%   ⚠ THE DOMINANT FORM
    doc_id               63   14%   resolves locally today
    borough + file_nbr   22    5%   ⚠ neither - unhandled, unknown if derivable

⚠ **`ref_bbls()` ONLY ACCEPTS A doc_id TARGET**, so ~86% of references cannot
resolve at pass 1 today. That is CORRECT, not a defect — login: "the crfn will
be in the rd thats why reference is saved for all rd to be done so we can draw
that connection." **100% of sampled docs carry their own `crfn`**, so the
CRFN→doc_id map is built FROM OUR OWN CORPUS at zero ACRIS cost — but only
once every rd has landed. That is the whole reason pass 2 waits.

**FOUR THINGS TO BUILD BEFORE THE ARM FIRES:**
1. **CRFN→doc_id map.** `crfn` lives INSIDE the recorded_details JSON, not as
   a column — a one-time extraction over the corpus, then an index.
2. **Teach `ref_bbls` the crfn hop**: crfn → doc_id → that doc's BBL.
3. **Iterate to a FIXED POINT.** `ref_bbls` inherits ONLY from a target keyed
   `parcel`, never from another `reference` (deliberate: no inference stacked
   on inference). So A→B→C chains need repeated passes until nothing new
   resolves — pass 2 LOOPS, it does not sweep once.
4. **Decide the `borough`+`file_nbr` form** (5%) — is file_nbr derivable from
   rd at all? Unknown. Resolve before the run, not during it.

**ALSO PENDING:** partial indexes `WHERE keyed_by='reference' AND key=''` and
`WHERE keyed_by='pdf-pass'` to make the worklists instant. ⚠ CREATE INDEX
takes an EXCLUSIVE write lock — it has already killed the keyer mid-sweep and
taken the fleet down (2026-08-21). Build them in a quiet window, never during
a climb.
