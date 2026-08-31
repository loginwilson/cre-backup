# PHASE A — `RC_970273` · m2 candidate · cold read, three readers

Richmond, 2 pages, recorded 1955-12-21. Readers B, C, D. Blind, identical brief.

## The headline: **NOT a member of the class. 3 of 3, unanimous.**

An N.Y.B.T.U. Form 8002 bargain-and-sale deed with covenant against grantor's acts —
two natural persons conveying **individually and as executor/executrix** of an estate.
**No restrictive covenant of any kind.**

| §1 signal | fired |
|---|---|
| 1 · grantor is a development company | **no** — two natural persons, one a fiduciary |
| 2 · filed-map reference the lots depend on | **yes** — Map 941-A, Richmond Clerk, 1907-08-15 |
| 3 · covenant block with a stated expiry | **no** |
| 4 · reserved rights running back to the grantor | **no** |

### ⚠ The finding that matters: **demote signal 2.** 3 of 3.

It fired on a **non-member**. m1's map is 995 B (filed 1907-07-05, 1906 survey); m2's
is 941-A (filed 1907-08-15, 1906 survey). Different developers, four decades apart,
same signal.

> *"Nearly every Staten Island deed of this era will fire it, because the island was
> platted. A signal that fires on the class and on the non-class is not evidence."*
> — and independently: *"it is not diagnostic of the class, it is diagnostic of
> Richmond conveyancing."*

**§1's operative test held**: *"the operative weight is in the covenants, not the
grant."* Here the weight is in the grant and the fiduciary capacity. **The test
worked; the signal list under it did not.**

**m2 does not bank. The class still has one member.**

## Scores

| | B | C | D |
|---|---|---|---|
| FEED | **100%** (15/15) | **100%** (12/12) | **100%** (16/16) |
| COVERAGE | **100%** (8/8) | **100%** (7/7) | **100%** (8/8) |
| structural surprise | 6 | 5 | 4 |
| gate | clean | clean first run | clean |

FEED holds at 100% on a **cold read of a document nobody had seen**, which is the
stronger result — the re-emit round had the reading already done.

The four uncarried §3 fields (covenant expiry, cost floor, prohibited trades, private
approval right) are **absent, not missed** — there is no scheme.

## ⚠ A scoring dispute worth preserving

**How do you score a standing prediction against a non-member?**

- One reader marked most of it **FAILED** (5 of 7 claims).
- One marked it **UNTESTABLE**: *"Predictions 1, 2, 5 and the second 4 all presuppose
  a covenant scheme; there is none. Reporting them as failures would score the spec
  against a document it never claimed to cover."*

**The second is right**, and it changes the method: a prediction is only scoreable on
a confirmed member. Class membership must be settled *before* the prediction is
scored, or every non-member manufactures fake failures and the spec looks worse the
more widely it is tested.

What survived on its own terms: **prediction 4 holds** (filed map present, not in
rd) — but that is exactly the signal now demoted as non-diagnostic. **Prediction 3
holds vacuously** (neither STRUCK nor TERMINATE appears).

## §2 deviations from m1's measured signature

- **`AS_BUILT` fires — 3 of 3.** Measured 0 of 99 rows on m1. Here: *"with the
  buildings and improvements thereon erected."* **All three volunteered the same
  caveat** — it is printed form boilerplate, and a reader folding it into TITLE is
  not wrong. One kept it because the drafter edited *that exact line* four times and
  left the clause standing; one because *"a measurable deviation is worth more than a
  tidy match."*
- **`COST` fires on an unrelated trigger — 3 of 3.** m1's five COST rows were all one
  building-cost floor. Here it is **three US Internal Revenue documentary stamps,
  $10 + $3 + $0.20 = $13.20**, cancelled `DEC 21 1955`. `SUM` reconciled it
  independently. **§2's "what fires it" column is m1-specific.**
- **`CAPITAL` and `PERMIT` hold at 0.** That half of prediction 1 survived a document
  from a different class — the strongest evidence yet that the negative prediction is
  real and not an artifact of one deed.
- **`ENVELOPE`, `OCCUPANCY`, `ENTITLEMENT` all 0** — they are covenant-scheme
  functions, and there is no scheme.

## Structural surprise — convergent

| finding | count |
|---|---|
| **Two acknowledgments, one `acknowledged:` slot.** Two signers, two dates, two counties, two notaries. *"A multi-grantor deed acknowledged separately is not exotic; it is the normal case whenever grantors live apart."* | **3** |
| **Lien Law §13 statutory trust over the sale proceeds.** Binds the grantors personally, does not run with the land, benefits unnamed mechanics' lienors who are not parties. *"`CAPITAL` asks what is owed, `ENCUMBRANCE` what burdens the land, `COST` what must be spent; **none of the eleven asks a fiduciary question.**"* **Second class in a row to produce a candidate function.** | **3** |
| **Dual capacity in one signature.** Each grantor conveys individually *and* as fiduciary — two sources of title, one granting clause, apportioned nowhere. `parties` is `X → Y`. m1's corporate officer signing *for* an entity is a different and handled case. | **3** |
| **Land conveyed that has no BBL** — the street beds, *"to the center lines thereof."* No `bbls` form reaches *the parcel plus the abutting road bed*. One reader used `UNPLACED` and noted: m1's single `UNPLACED` was called *false* by its author; **this one is true, and §7's baseline cannot tell them apart.** | **3** |
| **A rule of construction** — *"the word 'party' shall be construed as if it read 'parties'."* Operative with two grantors on a form written in the singular, but it asks nothing about a parcel. | **2** |
| **`bbls` cannot say "block-level only."** rd is `5001590000` — block confirmed, lot `0000` — while the deed names map lots 24 and 25 in a numbering system rd does not carry. The placeholder *"renders exactly like a measured lot-level BBL."* | **2** |
| **The filed map as a parcel definition, filed under `IDENTITY`.** Logged as a candidate on m1; **recurs here. Two members, two instances** — moves from candidate to recurring. | 1 |

## Five defects in the orchestrator's work, found by three readers on one document

1. **A fabricated party in the worked example.** It read `→ Ella J. Bergen`; the m1
   grantee is `MINNIE A. SWEENEY` — in all five sealed tables and in crisp typewriting
   on p1. Published under the words *"every value below is transcribed from a sealed
   reader table"*, **directly beneath a box saying a worked example is the worst place
   in the system to guess.** Two readers caught it independently, on a different
   document, while doing something else. The `parties` cell was also the wrong shape.
   **Fixed — now copied character-for-character from a sealed table.**
2. **The `SEARCH RECORD` split matched the first occurrence anywhere**, so a prose
   cross-reference inside a `terms` cell moved the block start into the table and the
   region count read **16 instead of 5** — silently inflated, no failure. *"A search
   record that over-reports coverage is the one failure mode this check exists to
   prevent."* The reader renamed its cross-reference rather than loosen the check.
   **Fixed — anchored to a heading on its own line.**
3. **The `BBL` check false-alarmed on a placeholder.** With lot `0000` in rd it printed
   its own placeholder warning **and then failed the correct table**. One reader passed
   only because the deed's phrasing did not match `LOTWORD`, and said so rather than
   take the pass: *"that is luck of phrasing, not correctness, and the next reader who
   paraphrases will get a false FAIL and may 'fix' a correct table to clear it."*
   **Fixed — now `NOT_CHECKABLE`, which is card 9's distinction.**
4. **`recorded` was legal in the checker and invalid in two prose files.** *"I followed
   the checker as the mechanical authority. One of the three needs to change."*
   **Fixed — it was the two prose files.**
5. **The m2 package is not native.** Delivered `page-01.png` is 3000 × 3900; the native
   scan is 3164 × 4190 — a **non-uniform ~1.9% anisotropic squeeze**, different in x
   and y. Its `MANIFEST.json` has no `geometry` block: it predates the fix. **Crops now
   come from the native scan, but the page images readers eyeball do not**, so a rect
   measured on the delivered page does not land identically on the crop, and any
   percentage measured on `page-0N.png` is distorted anisotropically. **OPEN.**

## Open, carried to the ruling

- **Demote §1 signal 2** and find signals that discriminate. Unanimous.
- **A fiduciary function candidate** — second class, second instance.
- **`acknowledged:` needs to hold more than one.** Unanimous, and it is the labelled
  block rather than the row schema.
- **`expires:` needs card 5's three states**, as `until` was given.
- **Rebuild every package that has no `geometry` block** before it is read again.
- **The documentary-stamp routing.** framework.md sends stamps to the registry lane,
  where rows never fan; one reader emitted them as an event row **deliberately against
  the file** and said so. *"If the lane assignment is right, every documentary stamp in
  the corpus is invisible to Resolve."*
