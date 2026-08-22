# What a decode IS — the shape, before any more summarising

**Login, 2026-08-06: "I shouldn't be attempting to summarise yet. We need to
figure out what decode should look like. How do we decode to structured data in
tables, but also allow a narrative to form, but also in chronological order."**

Three requirements that look like three outputs. They are not. They are **three
readings of one atom**, and picking the atom is the whole design.

---

## 1 · The atom is the CLAIM, not the document and not the event

A document does not say one thing. The Brick Farms ZLDA
(`2013052101674004`, 45 pp) states, on five different pages:

| | page | belongs in |
|---|---|---|
| lot 22 transfers 10,726 sf | p040 | envelope ledger |
| consideration $1,450,000 | p001 | value |
| therefore $135.19/sf | *derived* | comparables |
| light-and-air easement above elev. 130 ft | p042 | encumbrances |
| Brick Farms Cooperative Ltd is fee owner of lot 22 | p032 | party |
| David L. Berliner, VP, signs | p025 | party |
| Ridgewood Savings Bank consents as mortgagee | p032 | party / encumbrance |
| lots 49·53·55·56·23·22 form one zoning lot | p033 | envelope |

**Eight claims, five pages, five destinations.** So:

* one row per DOCUMENT → the seven other facts have nowhere to go
* one row per EVENT → coarser still; a batch of five documents becomes one row
* one row per CLAIM → each fact lands in its own table, keeps its own page cite,
  and carries its own evidence grade

Documents and events do not disappear — they become **groupings** of claims, which
is what they actually are.

```
claim
  claim_id
  bbl                 the parcel this claim is FILED under
  subject_bbl         what the claim is ABOUT  ← often NOT the same
  document_id, page   where it came from. never null.
  predicate           closed vocabulary
  value_num, value_text, unit, parties
  effective_date      when the thing HAPPENED
  stated_date         when the document SAID it
  answers[]           which of the 16 questions
  evidence            read | derived | index
  verbatim            the words, when read
  derivation          the arithmetic, when derived
  supersedes          the claim this corrects
```

### `subject_bbl` is not decoration

The single most valuable output of lot 49's decode is that **seven neighbouring
lots are development-dead**. Every one of those claims is *about* lots 20–56 and
was *found in* lot 49's documents. Without a separate subject, that finding is
unfileable — it would either be lost or wrongly attached to lot 49.

This is also how the "the story exceeds the parcel" problem gets solved:
a claim found here about lot 20 is written once, indexed under lot 20, and
lot 20's own decode later either **corroborates or contradicts** it.

---

## 2 · There are TWO time axes, and using one produces a false chronology

This is the finding that "chronological order" forces into the open.

| document | filed | describes something that happened |
|---|---|---|
| 1971 deed | 1971 | a **1816** partition — the boundary |
| 2003 CEMA | 2003 | a **1990** mortgage — the debt root |
| 2019 EASE | 2019 | the lot 49/50 **subdivision**, already done in 2018 |
| 2014 MTGE | 2014 | a **2008** lot 20 ZLDA — the assemblage's first move |

A chronology built on document dates puts every one of these in the wrong place.
Worse, it makes the 2008 instrument — **the earliest act in the whole
assemblage** — appear as a 2014 event.

So `effective_date` and `stated_date` are both required, always, and:

* **the NARRATIVE orders by `effective_date`** — when things happened
* **the AUDIT orders by `stated_date`** — when the record learned of them
* the gap between them is itself a finding: a 7-month recording lag, an
  1816 boundary surviving as a recital, a subdivision recorded a year late

⚠ Where a claim is dated only by its document, `effective_date = stated_date`
and `evidence` says so. It must never be silently assumed.

---

## 3 · The narrative is GENERATED from claims. It is never written beside them.

**This rule is the direct lesson of 2026-08-06 and it cost most of a day.**

Prose and data were maintained side by side. Within hours:

* `LOT49_TIMELINE.md` carried "~32 of 1,654 pages read" long after four more
  exhibits had been decoded
* the same file listed the Horne chart as unread while its own table stated the
  $202.00/BSF derived from it
* the event ledger omitted a **1998 deed** and a **2003 CEMA** that were sitting
  on disk — a 36-year hole in the chain of title, and **the prose read
  perfectly well without them**

That last point is the whole argument. **A missing fact does not leave a hole in
hand-written prose; it leaves a smooth story.** Nothing in a narrative can flag
its own omissions, because narratives are built to be coherent.

So: **prose is a function of the claim set.** Every sentence is rendered from
claims by a template per predicate. Then

* a new claim changes the prose automatically
* a corrected claim rewrites the sentence that depended on it
* a claim with no sentence is *visible* — it is in the table and not in the text
* a sentence with no claim is *impossible* — there is nothing to render it from

The one-pager and the summary come last, and they are **views, not documents**.

---

## 4 · Causality is a DERIVED EDGE, not a claim

Narrative needs "because", and no document contains it. The 2015 construction
loan does not say it financed the tower; the 2013 sale does not say Extell was
exiting a completed assemblage.

Those links are **derived relations between claims**, and they must be stored as
their own thing with their own evidence:

```
claim_edge(from_claim, to_claim, relation, basis, confidence)
  relation: FINANCES · ENABLES · SUPERSEDES · CORROBORATES ·
            CONTRADICTS · SAME_BATCH · CROSS_REFERENCES
```

`CROSS_REFERENCES` is the only one a document states outright (a CRFN, a reel and
page). The rest are inference and must be labelled as such — otherwise the
narrative asserts causation the record never claimed.

**`CONTRADICTS` is the most valuable edge in the system.** It is how the 2018
lot 50 filings contradict the 2019 "subdivision" date, and how DOB's TCO will
either confirm or break the 2016 delivery. A decode that cannot represent
disagreement will always paper over it.

---

## 5 · The three readings, from one table

| reading | the query |
|---|---|
| **structured** | pivot claims by `predicate` → typed columns per question |
| **chronological** | order by `effective_date`, group by document/event |
| **narrative** | order by `effective_date`, render each claim through its template, join with edges for "because" |

Plus the one that only exists because claims are atomic:

| **the gap report** | claims expected for this predicate that are ABSENT — the query that finds a missing 1998 deed |

---

## 6 · What this changes about how decoding is DONE

* Decoding a document means **emitting claims until the document is exhausted**,
  not writing a paragraph about it.
* "Read the document" becomes checkable: pages with no claim and no
  `nothing_here` marker are unaccounted for.
* A parser fix re-emits claims and **supersedes** the old ones; the narrative
  redraws itself. Under hand-written prose, a parser fix requires rewriting
  every sentence that ever depended on it, which is why the corrections in
  `LOT49_OPEN_FAILS.md` had to be tracked by hand.
* Evidence grade travels with the claim, so `[read]` vs `[type]` can never drift
  apart from the fact it qualifies — today they drifted within one file.

---

## The order of work

1. `claim` + `claim_edge` tables, and the predicate vocabulary
2. Re-emit lot 49 as claims — it is fully decoded, so it is the fixture that
   proves the shape carries everything already established
3. Render the chronology and the narrative FROM those claims, and diff the
   output against the hand-written ledger. **Every difference is either a bug in
   the renderer or a fact the prose invented.** Both are worth finding.
4. Only then: the one-pager, as a view

⚠ Step 3 is the one to not skip. The hand-written ledger is the control, and it
is already known to contain at least two omissions and one wrong date — so a
clean diff would mean the renderer inherited them.
