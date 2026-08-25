# CEMA BATCH — PREDICTIONS, RECORDED BEFORE OPENING

Written from specs/CEMA.md (built on r13, r45, r55) **before either document
was rendered**. This file is the scorecard. Do not edit after reading begins;
score against it.

## THE DRAW

Sampled 240,000 of 24,119,001 navigation rows (1.00%) for `CONSOLIDAT` in
recorded_details → 1,272 candidates, **736 extraction-ready**. Corpus estimate
~74,000 documents. Class draw, deliberately not random.

| # | id | shelf | borough | pages | era |
|---|---|---|---|---|---|
| 4 | `2003011000989002` | MORTGAGE AND CONSOLIDATION | BRONX | 17 | 2002/03 |
| 5 | `BK_7030040000013` | SUNDRY AGREEMENT | BROOKLYN | 8 | 1970 |

Chosen to vary what the three founding members did not: Bronx and Brooklyn are
both unread in this class (r13 Richmond, r45 Manhattan, r55 Queens). #5's
remarks carry a **discharge** — `DISCHARGED JAN 17/78 R 971 P 1` — a lifecycle
fact the spec has nothing about.

---

## ⚠ CORRECTION TO THE SPEC, FOUND BY MEASUREMENT NOT BY READING

specs/CEMA.md §1 says *"the shelf lies, and it lies differently each time"*,
drawn from three members of which one had an accurate type. **The sample says
otherwise.** Gated shelves carrying `CONSOLIDAT`:

| n | shelf |
|---|---|
| 672 | CONSOLIDATION AGR |
| 19 | EASEMENT |
| 15 | MORTGAGE AND CONSOLIDATION |
| 12 | SUNDRY AGREEMENT |
| 7 | AGREEMENT |
| 7 | MORTGAGE |
| 4 | DEED |

91.3% sit on an accurate CONSOLIDATION shelf. **Our three founding members
were an unrepresentative sample** — two of them were the oddities.

⚠ **AND THE MEASUREMENT IS BIASED, IN A KNOWN DIRECTION.** The search key was
the string `CONSOLIDAT` in recorded_details, so a CEMA is only found if its
type or remarks contain it. r55's remarks read `CONS & EXT` — **which this
search would have missed.** The 91.3% is therefore an UPPER bound on shelf
accuracy; the mislabelled members are exactly the ones under-counted. The
honest denominator is "records containing the string CONSOLIDAT", not "CEMAs".

---

## PREDICTIONS — CEMA #4 · `2003011000989002` · modern, 17pp

| # | prediction | basis |
|---|---|---|
| 4.1 | **CAPITAL·modifies, `transacts`** fires | spec §2 signature, 3/3 members |
| 4.2 | constituent debts listed with citations (CRFN or reel/page) | spec §3, ALWAYS |
| 4.3 | **new money is present and identifiable** | the shelf says MORTGAGE *AND* consolidation |
| 4.4 | **the arithmetic CLOSES** — unpaid balance + new money = consolidated | r13's shape; modern instruments recite balances, not original principals |
| 4.5 | **restated terms ARE ON THE PAGE** (rate · payment · maturity) | r13; the class's sharpest trap, tested directly |
| 4.6 | **a §255 affidavit is APPENDED** in the package | r13; 17pp is package-sized |
| 4.7 | mortgage recording tax charged on the NEW MONEY only, not on face | R13-1 |
| 4.8 | consolidated principal stated in words AND figures | spec §3 |
| 4.9 | **VALUE does not fire** | spec §2 |
| 4.10 | rd `amount` reads $0.00 against a real consolidated sum | R13-4, true on r13 and r55 |

## PREDICTIONS — CEMA #5 · `BK_7030040000013` · 1970 film, 8pp

| # | prediction | basis |
|---|---|---|
| 5.1 | **CAPITAL·modifies, `transacts`** fires | spec §2 signature |
| 5.2 | constituents recited **in the body**, not as exhibits | r55; 8pp has no room for exhibits |
| 5.3 | **restated terms are NOT on the page** — a separate extension agreement or note | r45 and r55 both |
| 5.4 | **no §255 affidavit in the file**; tax proved by backer stamps | r55 |
| 5.5 | **the arithmetic may NOT close** — original principals recited, not balances | r55's shape |
| 5.6 | a SPREAD means more than one estate or parcel is involved | the remarks say SPREADING |
| 5.7 | consideration is nominal | r55, R40-2 |
| 5.8 | the **1978 DISCHARGE (Reel 971 p.1) is a chain expectation**, not in this document | remarks |
| 5.9 | rd `doc_date` holds the RECORDING date, losing execution | r55 defect |
| 5.10 | the true caption is on the **backer**, and the register's SUNDRY shelf is a catch-all rescued by remarks | r55, R36-1 |

---

## SCORING

- **COVERAGE** = spec fields the document carries that the read found ÷ spec
  fields the document carries. Target 100%.
- **SURPRISE** = things the document carried that no spec field predicted.
- **PREDICTION HITS** = of the 10 above, how many held.

A prediction that FAILS is worth more than one that holds: it is the spec
learning. A SURPRISE is worth most of all.
