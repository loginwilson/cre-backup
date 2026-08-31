# BATCH — RE-EMIT-1 · RC_1598772 · schema fillability

Five readers, identical brief, blind, re-emitting sealed v1 tables into the redefined
event table. **No new reading.** One question: *is the schema fillable from a real
document?*

Answer: **yes, on all five, first gate run, no loosening.**

## The numbers

| reader | v1 rows | v2 rows | FEED | rects | reported |
|---|---|---|---|---|---|
| A | 16 | 16 | **100%** | 16/16 | flourish 1, plain 12, struck 2, uncertain 1 |
| C | 29 | **16** | **100%** | 16/16 | flourish 1, plain 14, struck 1 |
| E | 27 | 19 | **100%** | 19/19 | flourish 1, plain 15, struck 2, uncertain 1 |
| D | 26 | 22 | **100%** | 22/22 | flourish 1, plain 20, struck 1 |
| B | 27 | **26** | **100%** | 26/26 | inserted 2, plain 23, struck 1 |

**Baseline was 0 of 125.** Every row now carries a rect — rule 1 had no field evidence
until this round.

**Row spread narrowed 16–29 → 16–26 on identical readings.** C went 29→16 and stated
it was the schema, not a re-read: `until` absorbed the expiry row, card 2 absorbed
twelve. D's 26→22 and E's 27→19 were the same mechanism. **The splitting policy and
`until` are doing the work they were added for.**

## Confirmed against me — the orchestrator was wrong, again

**All five, independently, from the page.** These are errors in files I wrote.

### 1. The grantor's name is not on the page as I wrote it — 5 of 5

The page reads **`WOOD HARMON RICHMOND REALTY COMPANY`** (D verified at 1600 dpi,
p1 `[0.50,0.115,0.95,0.130]`; C counts it six times across two pages). My spec §1 says
*"The Wood, Harmon Company"* and my worked example says *"The Wood, Harmon Co."* —
**neither string exists on the document.**

*Wood, Harmon & Co.* is a **third, different** name, appearing only as the firm the
plat was surveyed for and as the return-to party. **The deed states no relationship
between them.** I merged three names into one.

### 2. Spec §5 mis-scopes the covenants — 5 of 5

The covenants bind *"any part of the **herein-described premises**"*. The phrase
reaching the plat — *"any part of South New York, Addition Number Four"* — is in the
grantor's **reservation**, its exemption from its own scheme, not the scheme's reach.

> B: *"Had I followed the spec, fourteen rows would have fanned to the wrong parcels —
> the covenants would have reached the whole subdivision and missed lots 16 and 17
> entirely."*

**This is the most damaging error in the round.** It would not have produced a wrong
reading; it would have produced a wrong *parcel history*, silently, at Reorganize.

### 3. Cost floors vary by family count, not street — 4 of 5

$2,000 *"if built for use and occupancy of one family only"*; $3,000 *"if built as a
double house … or as a double tenement."* Street never enters it. My worked example
says *"$2,000 on Heberton; $3,000 on the avenue frontage"* and spec §4 generalises it.

### 4. My worked example is wrong in five ways at once — 3 of 5

E: *"quoting text that is not on the page."* It is wrong on **function** (COST vs
ENVELOPE), **page** (p1, not p2), **quote**, **bbls** (the cost floor binds the
premises, not the plat), and **party direction** (the covenant runs grantee → company,
not company → grantees).

> **The worked example is what the next reader calibrates against.** D: *"If that
> example is what m2's reader calibrates against, it will import all three errors."*

**Root cause, and it is the same one as the flourish dispute:** I wrote the example
and the spec from my own reading instead of transcribing the page. That reading was
the one five readers overturned 5–0. I had no business seeding a class spec from it.

### 5. `framework.md` contradicts itself on this document's own clause — 3 of 5

The function table names *"shall cost not less than $2,000"* — this deed's exact
clause — under **COST**. The worked example and spec §2 file cost floors under
**ENVELOPE**. Readers followed the normative table and filed COST.

> D: *"This is not stylistic: Resolve projects on `function`, so two readers with
> identical readings produce different state records."*

A predicted **file disagreement that would have read as reader disagreement.** This is
v3's rules-1-and-5 failure repeating, one file later.

## Schema gaps — ranked by independent confirmations

| # | gap | count |
|---|---|---|
| 1 | **`until` has no third state.** Blank = "never ends", an affirmative perpetuity claim. The expiry sentence sweeps *"all restrictions and covenants"*; whether it reaches the grantor's reserved rights is unsettleable. C wrote blank on two rows and 1915 on an adjacent one — *"two adjacent rows, opposite guesses, same unresolvable clause."* | **5** |
| 2 | **A private discretionary approval right still has no function — and this document has TWO** (fence design; plans and materials), not the one the spec logs. `ENVELOPE` keeps the constraint and loses the veto holder. | **5** |
| 3 | **`bbls` has no value meaning "about a party."** Rows asserting corporate existence, signing capacity, acknowledgment. `INSTRUMENT` is false, `UNPLACED` is false. D wrote the BBLs, making Resolve hold *"Keever is Vice-President"* as a fact about lots 16 and 17. | **4** |
| 4 | **The registry lane is mandated and unfillable, and escapes every gate.** `basis` has no `recorded` (it is listed as *invalid*); no function of the eleven asks about filing; the 9 a.m. recording time has no field. Numbered `R#`, the rows are skipped by CITE, MARK **and** FEED. B forced `basis: effective` + `function: IDENTITY` and **the checker passed it silently.** | **4** |
| 5 | **`until` is a machine field with no citation.** Up to fourteen rows carry `1915-01-01` sourced from one sentence that none of them quotes. Every other machine field is backed by its own row's citation. D: *"a row can carry two dates and only one citation."* | **3** |
| 6 | **Cards 1 and 3 contradict.** Card 3 defines `STRUCK` as removal *"before execution"*; card 1 says stroke order is unrecoverable, so that is permanently uncertain. **The mode's definition asserts what the card set forbids claiming.** | **3** |
| 7 | **The filed-map date has no home.** 1907-07-05 is not instrument, acknowledgment, recording or expiry; `basis` has no term; it survives only in `terms`, where a checker once misread it. | **3** |
| 8 | **A citation holds one page; one operative act spans the page break.** A split the occupancy covenant across p1/p2 — *"the format forces exactly the splitting artifact card 2 warns about."* | 1 |
| 9 | **No mark vocabulary term for "unclassified."** D found a faint horizontal crossing the grantor's own name mid-word, confident it is not a cancellation and unable to say what it is. `uncertain` overstates doubt about the text. **D dropped the row rather than mislabel it** — a row the schema lost. | 1 |
| 10 | **No way to write "this set, minus what this instrument conveys,"** nor to link an exception row to the row it excepts. The reservation's set literally contains the subject parcel. | 1 |

## Genuine split — for argument, not measurement

**Is *"lots on Richmond Turnpike, Merrill Avenue and Watchogue Road…"* a valid `SET:`?**
`framework.md` names this exact clause as *"prose — a row that failed."*

- **A:** wrote `UNPLACED`, and says that is false — the deed places it *precisely*, just
  not evaluably. Wants `SET_UNRESOLVED: <criterion>`.
- **B, C, E:** it **is** mechanically evaluable given a street map — no less so than
  `SET: all lots in plat 995 B`, just different evidence.
- **All four agree on the real obstacle**, which the framework does not mention: **the
  deed never bounds the set to plat 995 B or to any county.** Narrowing it to make it
  fannable would be deriving.

**Three of four readers say the framework is wrong about its own worked failure case.**
Judgment, not fact — argue it, do not measure it.

## Bugs in my own code, found by readers

1. **Zoom crops leaked to a shared `loop/zoom/`** — 27 of them. My guard refused the
   *package* but not `loop/` itself, so a reader whose cwd was `loop` wrote where all
   five could see. Crop filenames **are** the rects chosen, so this told every reader
   where the others looked. My verification had checked `docs/**/zoom` and
   `loop/<X>/zoom` and never `loop/zoom` — **I looked where I expected the bug, not
   where it was.** Fixed: any non-per-reader path is now refused.
2. **The row-level `until < date` check was dead on every v4 table.** Its guard read
   `if "time" in hdr` — I renamed the column to `date` and never updated the guard, so
   it fired only on the v3 shape it replaced. Fixed.
3. **`BBLS_OK` accepts `SET:` followed by any string.** Typing five characters in front
   of prose passes clean, and the probe used the same string *without* the prefix so it
   never tested this. **Open** — a regex cannot judge whether a criterion is evaluable,
   and finding 3 above says the judgment is contested. Making it report rather than
   pretend to check.
4. **FEED is sensitive to row numbering** (A, C, E). Registry rows numbered `R#` are
   invisible to every check; numbered `E#` they would score as unready. A flagged that
   counting them would have reported 16/19 = 84% instead of 100% — and **flagged it
   rather than take the higher number.**

## Also worth keeping

- **C audited its own v1 work and found a fabrication.** Its v3 index-check table
  asserted rd's `book`, `page`, `doc_type`, `recorded`, `status` and `parcels`
  *without having opened `registration.json`* — and the two BBLs it "checked" were
  composed from borough + block + lot, exactly the derivation now forbidden. Every
  value happened to be right. *"It rendered identically to a measured value and nothing
  would have caught it."*
- **D on what the schema won:** `mark` + rect turned its longest prose argument — the
  flourish-vs-strike dispute — into one citable cell. *"A referee settles that in a
  minute without reading a word of my reasoning."*
- **E deleted two rows on the merits**, not granularity: the AS_BUILT row (the spec's
  prediction that AS_BUILT does not fire on a vacant platted lot **held**) and a
  TERMINATE row for the 1915 expiry — *"a TERMINATE row invents an act on a date when
  nothing happened."*

## Ruling — deferred, deliberately

The batch is closed but **not ruled**. Every change above must name the clause that
forced it, be checked against RC_1598772 itself, and route to spec / checker / card
rather than accreting in `framework.md`. The card set is capped at twelve, so findings
6 and 9 must **displace** a card or go elsewhere.

Two things must happen before m2 regardless, because they are factual errors rather
than design choices, and the next reader calibrates against them:

- **the grantor's name** in spec §1 and the worked example
- **spec §5's scope** — it would fan fourteen rows to the wrong parcels

The COST-vs-ENVELOPE contradiction must also be settled before m2: `function` is a
machine field, and two readers with identical readings currently produce different
state records.
