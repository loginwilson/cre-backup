# The parcel bank — what every extraction keys to

⚠ **This was never written down, and everything above it depends on it.** A
claim filed against the wrong parcel is wrong at every layer, and the loss is
invisible because a filter returns clean-looking output.

---

## The bank is the DOF Digital Tax Map spine. Not ACRIS. Not PLUTO.

    spine/spine.jsonl     1,192,472 parcels    1,176,797 live · 15,675 retired
                          with succession edges from the Digital Alteration Book

**Not ACRIS**, because ACRIS records the BBL *as filed on the day*, which is a
historical assertion, not an identity. Two documents twenty years apart legally
describing the same dirt carry different BBLs.

**Not PLUTO**, because PLUTO omits condo unit lots — 307,436 of them. Keying to
PLUTO silently loses every condominium.

---

## ⚠ THE EXTRACTOR NEVER TOUCHES THE BANK

This is already the rule in ARCHITECTURE.md and it survives contact with the
lineage problem, which is the real test:

    the extractor writes    bbl_raw   exactly as ACRIS filed it
    IDENTIFY assigns        subject_bbl  afterwards, using the spine

An extractor that resolved lineage would have to know that lot 49 became
something else in 2015 — knowledge that does not exist inside the document it
is reading, and that changes after the extraction is done. Keep the extractor
dumb; re-run IDENTIFY when the spine improves.

---

## Every raw BBL resolves to one of four states. None may be silent.

    LIVE       matches a live spine parcel                     -> key to it
    RETIRED    matches a retired parcel                        -> follow
               `succession.successors` to the live successor, and RECORD THE
               HOP, because the claim was made about the OLD parcel
    ABSENT     well-formed, not in the spine at all            -> key to
               bbl_raw, flag `unresolved`. NEVER DISCARD.
    MALFORMED  block=0 or lot=0 (622 distinct in ACRIS)        -> flag, keep

⚠ **`ABSENT` AND `MALFORMED` ARE ROWS, NOT DELETIONS.** The first attempt to
count ACRIS's BBLs wrapped the parse in `except: continue` and reported 949,535
distinct BBLs against a true 1,249,947 — it silently dropped 300,000 and looked
like it had worked. That is the same failure as the range scan, the p001
fingerprint, and the regex ground truth: *a check that runs, produces a number,
and answers a question nobody asked.*

---

## Measured: how well ACRIS matches the bank

    ACRIS LEGALS distinct (borough, block, lot)   1,249,947
    genuinely malformed (block=0 or lot=0)              622

On the DEVR population (1,201 documents, 5,460 distinct BBLs):

    live in the spine        4,766   87.3%
    RETIRED but resolvable     642   11.8%
    absent, nothing to key      52    1.0%

⚠ **11.8% retired against a 1.31% citywide baseline — 9x.** Lots named on a
development-rights transfer retire nine times more often than an average lot,
because that is what the instrument leads to. **Lineage is not an edge case for
this project; it is the main case.** Any pull that gates on "lot exists today"
loses a tenth of the population and reports success.

---

## ⚠ Known defects in the bank itself — do not build around them silently

These are recorded in project memory and they are load-bearing:

* **Condo BILLING lots are in neither DTM layer** — 11,132 parcels covering
  412,507 apartments, and they are the new towers. A claim about a condo's
  financing lands on the billing lot, which the bank does not contain.
* **The C/R/A/S/E flags are RELATIONSHIPS, not identities** — 19,419 lots are
  mis-kinded by reading them as types. **Never gate on `kind == "ground"`.**
* **Merger and subdivision lineage is incomplete**, and the Digital Alteration
  Book only starts **2008-05-20**. Pre-2008 lineage must come from PLUTO
  vintages (the archive runs 02a–26v1) or from documents' own prior-deed
  recitals. DEVR documents run from 2003, so the earliest five years of that
  population sit outside published lineage.

---

## The key format

BBL is written `B` + `block` zero-padded to 5 + `lot` zero-padded to 4.

⚠ **That format is only safe while every lot is ≤ 9999 and every block is
≤ 99999.** Outside those bounds the padding overflows and two different parcels
can produce one string — a collision that would merge two parcels' histories
silently. Measured against the live ACRIS universe in `_bbl_collisions`; until
that returns clean, **carry the `(borough, block, lot)` tuple alongside the
string** and treat the string as a display form, not the identity.
