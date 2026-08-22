# LEGAL INSTRUMENTS — ORGANIZATION

**The phase's one claim: every doc id is KEYED to its BBL(s).** The key is
what makes derivation possible later — a document that cannot be placed on a
parcel cannot move a parcel's story. Columns owned: `keyed_by` (the route
that proved it) · `key` (the BBL(s), ";"-joined for multi-parcel).

**NO NETWORK — therefore FULLY AUTOMATABLE (login 2026-08-21).** Unlike
acquisition, every input — details, references, parties, the pdfs — is
already on disk. No pacing, no sessions, no refusals, no lag states. Pure
computation over our own table: inline keying is free in the walker, and
the convergent passes can run whenever the table is quiet, as often as
needed, at zero risk to any source. The only constraint is our own disk
contention rule, not anything external.

**WHEN IT RUNS — each route at the moment its evidence exists** (login
2026-08-21: "it should run the moment a row is done if we wanted to be
efficient"). The routes differ in what they depend on, so they key at
different moments:

- **Route 1 keys INLINE, in the walker itself.** The rd walker holds the
  parsed details in memory when it lands a row; writing keyed_by/key in the
  same transaction costs zero extra reads and cannot block anything. Most
  documents key here, instantly.
- **Routes 2–4 are CONVERGENT PASSES on a quiet table** — their evidence is
  corpus-dependent (the referenced doc, the party graph, the pdf), so each
  sweep keys whatever newly became keyable and the unkeyed remainder
  shrinks monotonically. A row that cannot key yet records what it waits
  on; it is re-asked, never forgotten.

⚠ Never a separate sweeping process against a hot table (measured
2026-08-21: a live keyer's rw connection + full sweeps blocked every
walker). Inline-in-the-walker and quiet-table passes are the only two
shapes.

⚠ These rules are CALIBRATIONS — re-measured when path testing starts
(login: "the rules may change when we get to testing the paths").

## THE EVIDENCE LADDER — three routes, each fires when ITS evidence exists

    1. parcel     details.parcels carries BBL(s) directly -> keyed_by=parcel
                  FIRES: the moment the rd lands (inline in the walker)
    2. reference  a referenced document RESOLVES to a parcel
                  (one hop v1 - depth extends only after being measured)
                  FIRES: when the referenced documents are keyed
                  (convergent passes - the remainder shrinks each round)
    3. pdf        the pdf itself is read for the parcel
                  FIRES: when the pdf is on disk

⚠ PARTY IS NOT A KEYING ROUTE (login 2026-08-21: "a doc may apply to a
piece of the asset and if we just assume its everything that party owns, it
could be a miskey"). A party match proves ASSOCIATION, not COVERAGE - a
mortgage from a multi-asset owner touches the collateral it names, not the
portfolio. Party is DECODING work and belongs with function in the later
phases (login: "party would be something we do later on with stuff like
function since thats decoding") - organization writes only what the
custodian ASSERTED; interpreting what a party relationship means is
resolution/derivation's territory. It never writes a key here.
An honest blank beats a plausible miskey.

Keys are written ONLY from custodian-asserted evidence. A row no route can
key is left unkeyed and COUNTED — an unkeyed count is a finding, not a
failure to hide.

**Function is the NEXT key up.** The user's rule, recorded: "the function
resolution is basically a key itself that requires decoding" — organization
keys documents to PARCELS; resolution (05) keys events to FUNCTIONS (the
eleven nouns). Same shape, one level up; the keyed BBL is what resolution
groups by.

## MACHINERY

**The routine:** `routine_organization.py` — the phase's labeled entry
point in the standing format (audit → pass → board → identity check:
`parcel + reference + pdf + pdf-pass + unkeyed = total`). PARKED until
acquisition fills contexts; the audit half is meaningful today.
`nav_key.py` is the keying ENGINE underneath it (routes 1, 2 and the
pdf-pass ledger — exactly the three-route ladder; refs that don't resolve
YET are left unkeyed for a later sweep, never a premature pdf-pass
verdict). Its `--loop` daemon mode is RETIRED per the blocking lesson:
organization sweeps a quiet table.

**The rules are ENFORCED BY THE DB — the `key_rules` trigger** (proven
2026-08-21 on control updates, valid and invalid):

    keyed_by ∈ '' · parcel · reference · pdf-pass · pdf   (party ABORTS)
    parcel/reference  -> require rd landed + non-empty key
    pdf-pass          -> require rd landed, key stays empty
    pdf               -> require the pdf on disk + non-empty key
    key without route -> ABORTS (unattributed evidence)

Whoever the writer is — nav_key, an inline walker key, anything future — an
ill-evidenced key cannot be written. Structural, like nav's mint trigger.

## BOARD

One row: `organization | legal instruments | keyed / total`. Status computes
like every phase; the unkeyed remainder prints with its denominator.

## THE RUNNING SYSTEM — org takes the handoff (LOCKED 2026-08-22)

Richmond rd's closure (2,501,589 rows, every parcel a full BBL in the
corpus schema) means route 1 has its richest context yet; the pass stays
PARKED while acquisition owns the cores (acris rd ~2.3 days at the locked
config) and unparks as a no-network pass the moment the machine frees —
same three-route ladder, same key_rules gate, nothing new to decide. Lane
configuration and sequencing: the acquisition md's LOCKED CONFIGURATION.

## MEASURED: ROUTE 1 IS ~99.7% OF THE CORPUS (2026-08-22)

The ladder was designed expecting reference and pdf to carry real volume.
They do not — sampled across every era:

    era                    parcel   reference   pdf-needed
    Richmond (all)         100.0%        —          0.0%
    ACRIS film   FT_       100.0%       0.0%        0.0%
    ACRIS book   BK_       100.0%       0.0%        0.0%
    ACRIS 2003-2010         99.8%       0.0%        0.2%
    ACRIS 2015-2026         99.5%       0.0%        0.5%

**Consequence: organization never needed the pdf campaign.** It needs only
the rd, which is the FAST lane. Route 2 is effectively unused in v1 (a
referenced-doc route may still matter for specific instrument types — it
is not deleted, just not load-bearing); route 3 is a ~0.3% tail (~70k
docs) that the convergent passes pick up as images land. The phase reaches
~99.7% within days of acris rd closing, not weeks behind the images.

**MULTI-BBL IS THE INTERESTING POPULATION — 6.4% Richmond · 7.0% ACRIS**
(~1.7M documents corpus-wide). Mostly 2-3 lots, with a long tail; the
largest single Richmond document touches **312 BBLs** (condo declaration /
subdivision-map shape). These are the assemblage, blanket-mortgage and
portfolio signals — the `;`-joined key column makes them queryable as
one document across many parcels, which parcel-by-parcel data cannot
express. Never collapse a multi-BBL key to its first lot.

## THE BOARD — two rows, follower semantics

`organization | acris` and `organization | richmond` (the old single
"legal instruments" row is retired). Denominator is **rd-landed, not the
whole corpus** — a row without rd has no evidence yet, and counting it
would report progress against work that does not exist. Status carries
the follower distinction (login 2026-08-22): keyed everything keyable =
**PENDING, "waiting on acq"** — not STALLED, which means partial progress
with nothing working it. COMPLETE only once the upstream rd itself is.

---

## THE ACRIS BACKFILL — MEASURED, AND DELIBERATELY NOT RUNNING YET (2026-08-22)

**The trigger works. There has simply never been a pass over the old rows.**
`key_on_rd` keys every NEW rd landing, but ~6.0M acris rows landed *before* it
existed and no one has gone back for them. That — and nothing else — is why the
board reads organization/acris at ~10% of rd instead of ~100%. The login asked
exactly the right question: *"shouldn't organization on acris be running near
100 since it should be able to key every single rd doc to date?"* Yes. The
denominator is right; the numerator is reporting **a debt, not a rate**.

**The trigger is PROVEN — bounded probe, never a scan** (4,000-row indexed
range reads at eight id points; a 24M COUNT is the WAL trap):

| window from | landed | keyed | keyed % |
|---|---|---|---|
| `2002122000001001` | 4,000 | 3,999 | **99.98%** |
| `2014` | 4,000 | 0 | **0.00%** ← pre-trigger debt |
| `FT_1000000000000` | 4,000 | 4,000 | **100.00%** |
| `FT_1000004000000` | 495 | 265 | 53.54% ← live frontier, half old |

Route-1 parcel keying carries to acris exactly as it did to richmond. ⚠ **The
debt is PATCHY, not one contiguous block** — the earliest digital range is
already 99.98% keyed while `2014` is untouched. Any backfill must sweep, not
seek to one offset.

## ⚠ DO NOT RUN THE BACKFILL WHILE THE LANES ARE HOT — MEASURED COST

`nav_key.py` **already exists** (THE KEYING PASS; it keyed all 2.5M richmond
rows). It has bounded 5,000-row batches, per-batch commits, lock retries, a
persisted cursor, `--lo/--hi` range bounds and its own board-feed log. *It does
not need to be rebuilt* — this note exists because it was nearly rebuilt from
scratch on 2026-08-22 before `grep` found it.

**What running it hot actually costs** (`--src acris --lo 2013 --limit 20000`,
against the full 4-lane fleet):

    keyed 20,000 in 176.6s · parcel 19,952 · reference 2 · pdf-pass 46

**113 rows/s** — for pure in-SQLite JSON keying with zero CPU work outside the
engine, which should run at thousands/s. It spent the whole run fighting the
lanes for the single WAL writer. And the lanes paid for it:

| lane | before | during |
|---|---|---|
| acris rd | 91 doc/s | **38 doc/s** |
| acris pdf | 6.6 doc/s | **3.2 doc/s** |

Both recovered fully the moment it stopped. **A ~58% fleet tax to buy keys at
1/20th of their idle speed is the worst trade available** — the same work costs
almost nothing once the writer is uncontended.

**THE RULE: the backfill waits for acris rd to close** (ETA ~1.9 days at
91 doc/s). Keying is a follower with no downstream consumer waiting on it —
extraction is not running — so there is nothing to buy by paying that tax now.
Until then organization/acris climbs on the trigger alone, and **~10% is an
honest reading of a real debt, not a broken row.**

## WHY KEYING COSTS ANYTHING AT ALL — IT IS THE LOCK, NOT THE ARITHMETIC

The natural objection (login 2026-08-22): *"why does it harm the runs? wouldn't
it just be as simple as grabbing the bbl's that spawn in the rd row?"* The
grabbing IS that simple — parse the json, read `parcels[].bbl`, join. Free,
no I/O. **The cost is never the extraction. It is the durable write.**

**SQLite in WAL mode permits ONE writer at a time for the whole database file**
— not per table, not per row. Six lanes (4 rd + 2 pdf) commit into that single
lock continuously. A backfill sweeper is a SEVENTH writer queueing for the same
lock, and every key it writes is a lock a lane did not get, plus a page write
into a 13.4 GB file on D:. Six million of those is real I/O however cheap the
arithmetic.

**This is exactly why the trigger is free and the sweeper is not — same work,
same BBLs, same parsing, only the lock differs:**

| | how it writes | measured cost |
|---|---|---|
| `key_on_rd` trigger | **inside the rd lane's own transaction**, lock already held | **zero** |
| backfill sweeper | its own transaction, competing for the lock | 30–40% of the fleet |

**THE DESIGN RULE THIS SETTLES: a follower phase should ride the writer that is
already there, never open a second one.** Keying rides rd's transaction and
costs nothing; the same keys bought by a standalone sweeper cost ~36 doc/s of
rd. Any future follower (extraction flags, resolution edges) gets the same
treatment — attach to the landing transaction, or wait for a quiet table.

⚠ **THE TAX IS ACQUISITION FREQUENCY, NOT HOLD TIME — MEASURED, AND IT
REFUTED THE OBVIOUS GUESS.** The plausible theory was that a big batch holds
the one writer for ~12 s and starves the lanes for that stretch, so smaller
bites at the same duty cycle should interleave better. **Tested 2026-08-22;
the opposite happened:**

| batch / sleep | keyer | acris rd | acris pdf |
|---|---|---|---|
| 2,000 / 20 s | ~170/s | ~55/s | ~4.6/s |
| 500 / 5 s | ~300/s | **5.5–43/s, erratic** | **0.5–2.7/s** |

The keyer got *faster* and the fleet nearly collapsed. Small batches take the
lock **4× as often**, and every acquisition interrupts six lanes mid-commit —
the interruption costs far more than the holding does. **Fewer, larger
acquisitions win.** To lower the tax, lengthen the SLEEP and keep the batch
large; never shrink the batch. Operating point: `--limit 3000 --sleep 45`.

This is the second time here that a rate-shaped intuition inverted under
measurement (see also: the board's own aliased rate). Lock behaviour is not
guessable from throughput — change one knob and re-measure.

## ⚠ THE "By Parcel" TREE IS PILOT RESIDUE — NEVER JUDGE COMPLETION FROM IT

Login 2026-08-22: *"we need to make sure by parcel is accurate since we've
changed to by document... just get it done then org after into by bbl so we
can maximize acq."* Verified in code the same minute:

- ONLY `keying_walk.py` writes `By Parcel/` — the 2026-08-20 combined pilot
  (400 docs). Everything in that tree is pilot-era.
- The CURRENT lanes write `By Document/YYYY/MM Mon/DD/<id>.pdf` exclusively
  (`image_walk.py`, `rc_pdf_land.py`). Acquisition never sorts; that is the
  design that maximizes acq.
- The parcel view's authority is the TABLE (`key`/`keyed_by`); the physical
  move By Document → By Parcel is ORGANIZATION's pass ("the key upgrade later
  MOVES the file — one copy always"), which runs with the post-rd backfill.

RULE: a completion question about a parcel is answered from keys + By
Document, never by listing `By Parcel/`. A tree only a retired pilot wrote is
an audit of the pilot, not of the corpus. (Same family as reading a filter's
own output.)

## ⚠ ROUTE-3 GUARD: FILED-MAP LOTS ARE NOT TAX LOTS (bootcamp R8-1, 2026-08-22)

Route 3 reads the PDF for the parcel — which means reading descriptions,
and descriptions cite lot numbers from PRIVATE FILED MAPS, not the tax
roll. Measured on `2003010601184002`: Schedule A says "Lot Nos. 359, 360,
361 and 362 in Block No. 7" — of the "Map of Rockaway Park" FILED 1889.
The tax parcel is 4-16186-0032, ONE lot. A route-3 keyer that trusts
description numbers writes FOUR phantom parcels in a block namespace that
no longer exists, each looking precise.

THE TELL is in the text itself: "as laid down on a certain map entitled
'...' filed in the Office of the County Clerk" — numbers following that
phrase belong to the MAP's namespace. RULE: route 3 keys from (in order)
the cover/back-panel block-lot block · a tax-map (Section/Block/Lot)
citation · the address resolved against the spine — NEVER from a
description's lot numbers when a filed-map citation governs them; those
are REFERENCES to the map. Same law as R5-3 (Richmond lot 0000 =
block-scope) and the reel-number-read-as-BBL incident: **a number's
namespace is part of the number, and descriptions mix namespaces
mid-sentence.**
