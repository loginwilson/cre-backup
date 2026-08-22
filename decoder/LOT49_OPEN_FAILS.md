# Lot 1008000049 — open fails. The lot is NOT finished until these are zero.

**Login's rule, 2026-08-06: "you can't move on from a lot until all fails are
resolved."**

A fail is anything the parcel's own record contradicts, leaves unquantified, or
that I asserted without checking. It is NOT the same as "unread" — unread is
tracked by coverage. A fail is a place where what we have is *wrong or
unresolvable as it stands*.

Status key: **OPEN** · **RESOLVED** · **CANNOT RESOLVE** (with the reason, which
is itself a finding).

---

## OPEN

### ~~F1 — the $5,000,000 air-rights purchase has NO square footage~~ → **RESOLVED**

**EXHIBIT D IS ON PAGE 38.** "ALLOCATION OF DEVELOPMENT RIGHTS".

| | Developer | 120 | 124 | 126 | TOTAL |
|---|---|---|---|---|---|
| lot area | 15,639 | 4,077 | 2,469 | 2,469 | 24,654 |
| generated | 156,390 | 40,770 | 24,690 | 24,690 | 246,540 |
| retained | n/a | 16,906 | 9,620 | 10,046 | 36,572 |
| **excess (transferred)** | n/a | 23,864 | 15,070 | 14,644 | **53,578** |
| after transfer | 209,968 | 16,906 | 9,620 | 10,046 | 246,540 |

**53,578 sf for $5,000,000 = $93.32/BSF.** Implied **FAR 10.00** (246,540 ÷
24,654) — NOT PLUTO's current 12.0, so the earlier scenario built on 12.0 was
the wrong branch.

**Why it took so long, and the rule that comes out of it:** the bundle holds TWO
exhibit series. The purchase agreement's runs A–I (D = the Declaration); the
ZLDA's runs A-1…F (**D = the Development Rights Chart**). I chased the PSA's
Exhibit D for hours. **Rule: in a bundled recording, resolve a defined term to
its OWN instrument's exhibit schedule, never to the bundle's.** The ZLDA's
schedule is on p28.

**Three independent confirmations** — the metes parser on Exhibit B gave the
developer lot area as **15,639 sf**, matching the table exactly; the
Lovell/Belcher survey's lot areas and floor areas match rows 1 and 3 exactly.
The parser fix for space-separated fractions is what made the first of those
land on the square foot.

### ~~F1-old~~ (superseded, kept for the record)
The 2010 ZLDA (2010102601040006) is the largest of four air-rights buys and the
only one whose **quantity is still unknown**, so **$/sf cannot be computed** for
it. The grant says "the Subject Development Rights ... as shown on Exhibit D";
Exhibit D of the *purchase agreement* is the Declaration, not a schedule.
Exhibit C (the Lovell/Belcher survey, p47) gives the SELLER parcel — 9,015 sf lot
area, 36,572 sf existing floor area — but not the figure transferred.
**Resolve by:** reading the remaining pages of the 116-page bundle, specifically
the ZLDA's OWN exhibit series (distinct from the purchase agreement's A–I).
⚠ Do not compute $/sf from "unused FAR" — that is an assumption, not a reading.

### ~~F2 — page-count disagreement on 2010102601040006~~ → **RESOLVED**

Probed to the placeholder boundary:

| source | says |
|---|---|
| cover page header | **PAGE 1 OF 116** |
| cover page field | **Document Page Count: 114** |
| served images | last image **p110**, p111 onward is the placeholder |

**Three numbers, none equal.** ⚠ **RULE: the cover page's page counts are NOT a
completeness target.** Only the placeholder boundary tells you where a document
actually ends, and it must be walked to — a fetch loop with a fixed upper bound
(mine used `range(1,41)`) reports "complete" at its own limit. The two
cover-page figures probably count the recording bundle differently (endorsement
pages, blank versos), but whatever the reason, neither is the served range.

**Practical consequence:** every `pages_total` recorded from a cover page is
suspect. Record the placeholder-verified count instead, and where only the
cover figure is known, mark it as unverified.

### ~~F3 — the §255-a affidavit contradicts the index and PLUTO~~ → **CLOSED, split**
MTGE 2020081400407001 p37 swears "not more than six residential dwelling units";
the cover page says COMMERCIAL REAL ESTATE; PLUTO says class **H2, 40 storeys,
`unitsres = 0`**.

**RESOLVED (the part that is a data question):** the box did **not** change the
tax. $140,000 was collected on $5,000,000 = **2.800%**, the commercial/other rate
for >$500k — verified independently on MTGE 2023110100486009 ($25,490,000 →
$713,720, all seven components to the cent). So the wording contradicts two other
sources but had **no fiscal effect** on this filing.

**CANNOT RESOLVE (the part that is not a data question):** whether checking that
box was *appropriate* is a legal question about §255-a. The documents do not
answer it and I should not pretend otherwise. Recorded as a flag on the parcel,
not as a finding of anything.

### ~~F4 — 91 of 98 documents are cover-only~~ → **RESOLVED**

**96 of 96 documents, 1,654 pages, 89 MB — every document walked to its
placeholder boundary. Zero documents with no pages.**

Throughput measured on the way: **6 parallel workers, 128 pages in 41 seconds =
187 requests/minute, no refusal.** Yesterday's block was attributed to ~1.1
req/min. Whatever caused it, it was not request rate.

⚠ **A concurrency bug surfaced and was fixed.** Four THREADS calling
`store.put()` produced a torn manifest line and a `JSONDecodeError`. `sink.py`'s
"one write, one line" guarantee holds across PROCESSES but not across threads
sharing an interpreter. `store.put()` now takes a lock. Blast radius was one
unreadable line (records() skips it), which is precisely the kind of failure
that gets ignored until it isn't.

Also: `2007062101109002` ends at **p1** — a single-page RPTT return. It was never
"cover-only"; it was complete. **Cover-only and one-page are indistinguishable
without walking to the boundary**, so a coverage metric that counts
`pages == 1` as incomplete over-reports the gap.

### ~~F4-old~~ (superseded)
Coverage, not contradiction, but it gates the lot. The financing companions
(SAGE 17, AL&R 8, TL&R 7, CERT 5, AALR 3) are entirely unread, and AL&R/TL&R are
the instruments that assign leases and rents — the ones that reveal whether the
hotel's income is pledged.
**Resolve by:** the full sweep now running.

### ~~F5 — my own 40-page truncation~~ → **RESOLVED**

All five walked to the placeholder boundary:

| document | true end | my artifact? |
|---|---|---|
| 2007062101109005 | p41 | yes |
| 2012122701550003 | **p55** | yes — 15 pages hidden |
| 2013052101674004 | p45 | yes |
| 2013080901116002 | **p40** | **NO — genuinely ends at 40** |
| 2019071700601003 | p44 | yes |

⚠ One of the five really does end at 40, so "all five stopped at my limit" was
itself an over-generalisation. **Four artifacts and one coincidence** — worth
having CHECKED rather than assumed, which is the same lesson as F2: only the
placeholder boundary establishes an end.

### ~~F6 — "Exhibit D is absent from both 2013 DEVR recordings"~~ → **RESOLVED: FALSE, my error**

Mid-read of 2013052101674004 I declared the Development Rights Chart missing
from the recorded bundle — every page seemed accounted for as A/B/C/E/F/G. The
"survey" I had skipped (p40, 982 KB; and p41, 1,126 KB in ...008) **WAS Exhibit D
in both documents** — the chart is a LANDSCAPE scan, so it weighs 5–10× a portrait
text page and the file-size heuristic classified it as a survey drawing.

⚠ **RULE: page-weight profiling NAVIGATES, it never CLASSIFIES.** File size may
choose which page to open first; it may not stand in for opening the page. The
claim "X is absent from the record" is only utterable after every page has been
LOOKED AT — absence is a conclusion about the whole document, so it inherits the
100%-coverage requirement. The correction happened only because the coverage rule
forced the read anyway.

Both charts verified internally (FAR 10.00 exact per lot; row/column sums exact;
each chart restates the prior chart's figures ✓) and against each other
(243,539 + 10,722 = 254,261). The delta method from the 2012 chart independently
produced 22,845 for Horne — the 2013 charts state 22,845 for lot 23. **Three
generations of charts, one consistent ledger.**

---

## RESOLVED

* **the fourth DEVR's seller** — 133 West 24th Street LLC, lot 21, $1,340,250
  (RPTT $35,181.56 ÷ 2.625% exact; RETT $5,362 → the $500-rounded window)
* **the 2015 DEVR** — NOT a fifth purchase. Zero tax, 8 pages, cross-references
  CRFN 2010000384312: the Sabetfard entity CONFIRMING the 2010 ZLDA to the new
  owner. ⚠ New rule: *a DEVR with zero tax may be a confirmation, not a transfer.*
* **"DEVR always shows $0 in the index"** — FALSE. 605 of 1,201 (50.4%). I
  generalised from one document to the population.
* **Extell's gross** — $12.4M, not the $19.8M I first reported; I had found one
  air-rights purchase of four.
* **`reconcile()` false CONFLICTs** — NYS RETT rounds UP to the next $500, so the
  two witnesses legitimately differ by up to $500 while my tolerance was $1. It
  had only ever agreed because $5,000,000 is an exact multiple of $500.
* **MRT rate treated as a constant** — the 1998 mortgage was taxed at exactly
  **2.0000%** against the table's 2.800%. Now refuses to answer pre-2005 or
  sub-$500k rather than return a confident wrong number.

---

## The rule this register enforces

A parcel is **done** when:
1. every document has been opened and read to its last page, and
2. this file has **zero OPEN entries**, and
3. every CANNOT RESOLVE states *why* — because an unresolvable fail is a fact
   about the record, and a silently dropped one is a lie about it.
