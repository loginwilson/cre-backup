# LEGAL INSTRUMENTS — RESOLUTION

> **BOOTCAMP GOVERNS THIS FILE.** Every function, mode, event row and vocabulary
> used here is defined in [`Bootcamp.md`](../../Bootcamp/Bootcamp.md) - the ONE authority.
> Never redefine a term in this file; correct it there and it corrects
> everywhere. A rule that is not in the bootcamp is not a rule.


**This document is the source of truth for producing a legal instruments
resolution.** An agent runs this phase from this file alone.

# OVERVIEW

**The job:** turn events into CHAINS and ACCOUNTS. Resolution takes a key's
extracted events and connects them — the events are the links; this phase
forges nothing new, it only attaches. One event graph, two traversals:

- **The TIME chain** — every event on the key in chronological order: the
  parcel's full documented history, one story front to back.
- **The FUNCTION chains** — the same events traversed by function: the
  ownership chain (who held it, when), the debt chain (borrowed -> assigned ->
  satisfied -> borrowed again), the envelope chain (air rights in and out),
  and so on per function.

Chronology and function are the FIRST TWO traversals, not the only ones: the
same event graph later yields party chains (everything one entity signed,
across all parcels) and development chains (one project across its lots) —
new contexts are new groupings of existing edges, never new machinery. And
when further sources join (DOB first), their events pour into the SAME graph,
which is what makes cross-source inferences possible downstream (e.g. the
contacts traversal: deed -> mortgage -> permit -> enriched profile — an
05 Derivations inference, noted here because the chains are what carry it).
And once a party resolves to an actual CONTACT, the party chain becomes that
person's MARKET MOVEMENT — every event they touched, across every entity they
used, in time order: the events are the footprints, the contact is the player.

**The phase runs on two tracks, and they travel together from extraction
onward.** The DATA track: a chain is not a new structure — it is a SORT AND
GROUPING of the event table (sort a key's events by date = the time chain;
group by function = the function chains; mode/subject/function/quantity/term
are the sort keys, and since 2026-08-20 **doc_type** rides in the event row's
PROVENANCE (Bootcamp r49) as one more grouping dimension: grouping by
doc_type x function is the MEASURED type->function ledger - chains built on
counted pairings, not assumed ones, and a tripwire for source mislabels).

**Two upstream feeds widened 2026-08-20 (see the Navigation md):** the nav
index now carries `references[]` - the custodian's own cross-document
citations, 11,899,912 edges over 7,986,145 documents - which are CANDIDATE
chain links this phase verifies against the events (a cited satisfaction
should meet a mortgage event; a citation with no event is a finding either
way). And `remarks[]`, whose exemption affidavits explain amounts the
accounts would otherwise flag. The WRITTEN track: the event summaries, assembled in
chain order, become the WRITTEN CHAIN — the story in prose riding with the
data. The rule binding them: **the written track is generated FROM the data
track, never independently** — the prose can never say something the table
does not hold.

## THE THREE BRIDGES — how parcel-less documents reach their parcel
(login design, 2026-08-20)

Nav's key column records ONLY what the custodian asserted. Documents the
register never keyed to a lot (measured census, same day: **1,755,495 of
24,039,303** — nav counts them every build as keyed-by-party 1,711,319 +
keyed-by-doc 44,176, reconciling with the specification's own count to the
row) reach their parcels through three bridges, each carrying its evidence:

1. **The reference bridge** — the custodian asserted a CITATION; the parcel
   is inherited through it. Strongest derived link (the county's own edge;
   we only walk it). Measured: 84.0% of parcel-less docs carry references —
   but ⚠ only 190 land DIRECTLY on a parcel-keyed doc via ref_doc_id,
   because the film-era UCC families (INIT 612k · FL 377k · RFL 192k ·
   TERM 148k · CONT 129k...) cite EACH OTHER — chains that resolve to a
   DEBTOR, not a lot (the login's read, confirmed by the type census:
   personal-property filings key to reference docs, and get lost when the
   associated document or parcel changes). Multi-hop walking + file-number
   keys raise the landing rate; measure, never assume.
2. **The entity join** — the party on a parcel-less doc appears on
   parcel-keyed docs; the doc attaches to those parcels TIME-SCOPED to the
   ownership window. An inference WE computed (name+address disambiguation;
   two SPEs can share a name) — claim-tier edge with evidence, NEVER
   written into nav's key. One wrong join must stay one overturnable edge,
   not corrupt the ground layer.
3. **The document's own legals** — extraction opens the pdf and the exhibit
   names the property. This one UPGRADES the nav key itself (the
   instrument's own authority outranks the register), old state kept.

⚠ **AND BEFORE ALL THREE: the rd re-pull.** Measured 2026-08-20 (the login
caught the first probe reporting 0/36 recoverable — a parser false negative:
the page writes "MANHATTAN / NEW YORK" and the parser required bare
"MANHATTAN"; re-probed FIXED, 14/25 digital-era parcel-less docs have their
BBL sitting on the custodian's OWN detail page, dropped by the bulk index
(PAT/MAPS/DECL/AGMT/SAT/TERM/CORR all recovered; same mechanism as the
ZHENG-NINA party gap). Those are not bridge work — they are capture
completion, keyed_by=parcel like any register assertion. The residue after
re-pull is the film-era UCC/lien universe, which is bridge 1-2 territory.

**Evidence ladder for the key (login, same day):** document > parcel
(register) > reference (derived via register edge) > party/doc (unresolved,
waiting). `keyed_by` records the rung, so any consumer of a parcel's
chronology knows whether each row sits there by the county's assertion, a
citation chain, or the deed's own text. The login's hypothesis — party/doc
keying mostly dissolves because a filing links through its collateral
(parcel) or its references — was MEASURED same day (125 parcel-less docs,
0 failures, stratified by era x type):

| era | parcel on rd page | ref-only | neither |
|---|---|---|---|
| digital (of 70) | **40%** — deeds, mortgages, UCCs, POAs, SATs recover their BBL by re-pull | 36% — the federal-lien family (RFL/WFL/CNFL/PRFL...) | 24% — FL/FTL/JUDG/PAT: person-level liens, party IS the key |
| film (of 55) | **0%** | 89% — but 0 of 136 targets land on a parcel-keyed doc; the UCC loop is CLOSED (INIT->CONT->AMND->TERM cite each other; 49 targets are file numbers) | 11% |

Reading: the rd re-pull converts ~40% of DIGITAL parcel-less docs to
keyed_by=parcel (capture completion). The FILM-era residue (1.34M of the
1.755M) is the personal-property/lien ledger the login named: chains that
resolve to the DEBTOR, attaching to parcels only through the entity join
(bridge 2) when the debtor owns property — a derivation-time inference,
never a nav key. Party keying does NOT dissolve for these; it is their
correct terminal state, and the party chain is where a lien meets its
owner's parcels. Richmond's version (same day, internal-id-pinned probe
after v1 read wrong documents off duplicate instrument numbers): 306,857
block-only docs are block-only AT THE CUSTODIAN (0/12 pages carry a lot;
blocks match ours exactly) — they stay block-keyed until the document image
yields the lot.

**Why this stays out of nav:** auditability. A nav key containing our
guesses makes one name collision silently corrupt the ground layer every
phase trusts; kept as resolution edges, the same mistake is one
low-confidence edge a better join overturns without touching anything
beneath it. **The lineage payoff (login):** keyed this way, a retired BBL's
chronology ENDS with the instrument that killed it and the successor's
BEGINS with the same instrument — mergers and subdivisions become readable
events with documents behind them, not silent gaps in a current-BBL pull.

Alongside the chains, resolution keeps the **ACCOUNTS** — the running balance
per subject × function that the N-legged events add up to: outstanding debt
(mortgages minus satisfactions), the SF envelope (base plus received TDRs
minus sent), ownership shares (fractions summing to 100%). The ladder is
`claim -> event -> account -> inference`: extraction delivered events;
resolution builds the account rung; inference stays downstream.
**The boundary, upstream:** resolution intakes per key, behind extraction's
per-key handoff — one event record per document (events, summary, state,
bootcamp version). It never re-reads documents and never re-extracts; a
suspected bad event goes BACK as a defect, it is not fixed here.
**The boundary, downstream:** 05 Derivations receives chains and accounts and
turns them into output metrics and macro summaries. Resolution owns NO
summary — it connects; it does not editorialize. That is what keeps it
honest.
**Two modes, same output:** BACKFILL chains each key as extraction closes it
(the parcel cascade — a finished parcel chains tonight, not when the corpus
ends); NIGHTLY DELTA merges each morning's new events into living chains —
and merge means INSERT IN TIME ORDER, not append: a late-recorded document
(the lookback exists for exactly this) lands mid-chain, and the grammar
re-audits around the insertion point.
Chains are living structures, never rebuilt from scratch when they can be
appended to — and re-chained from the events whenever a backward re-check
revises what extraction believed (the bootcamp-version stamps say which keys
need it).

---

# 1 · OUTPUT

Per key, four artifacts:

1. **The time chain** — every event in order, each entry pointing at its
   event (and through it, its document and page). Gaps are FIRST-CLASS
   entries: an `unreadable` document, a `pending` scan, or a NAMED BREAK sits
   in the chain where it belongs, visible, so no reader ever mistakes an
   unknown for a quiet period.
2. **The function chains** — one per function present on the key. Every
   event leg lands in the chain its function names; a leg that fits no chain
   is LISTED, never dropped.
3. **The accounts** — running balances per subject × function, recomputed
   purely from the chained events: after every event, what is owed, what is
   owned, what the envelope holds. An account is never edited directly — it
   is always the SUM of its chain, so chain and account cannot disagree.
4. **The chain summary** (the written chain) — the event summaries assembled
   in chain order and closed with a statement of the chain ITSELF: what the
   sequence amounts to, where it breaks, what it leaves open. The same
   two-track rule one level up — **chain resolution (data) + chain summary
   (written)** — generated FROM the data track, never authored independently,
   regenerated whenever the chain changes so prose and table cannot drift.

**Terminal states — every event ends in exactly one:**

| state | meaning |
|---|---|
| **chained** | attached into the time chain and its function chain(s) |
| **parked** | valid event, no chain to join YET (e.g. a party-keyed event whose entity has not yet appeared on any parcel) — indexed by entity, joins the day its name appears |
| **unattachable** | attachment failed at every rung of the ladder — LISTED with the rung-by-rung record of what was tried |
| **defect** | the event itself is suspect (fails chain grammar in a way that implicates the reading) — reported BACK to extraction, never patched here. A defect returned TWICE UNCHANGED escalates to a person — it never ping-pongs silently |

The state column is never blank; the exact sum holds per key:
`chained + parked + unattachable + defect = every event handed off`.

**Cross-key events chain by their LEGS.** An N-legged event touching many
keys (the 8-lot air-rights deal) appears in EACH key's chains through its leg
on that key — and the legs seen across all keys must re-add to the one event
(the balance invariant, checked ACROSS chains, so no leg can vanish between
keys and no key can double-count the whole).

**Every break has a name.** A chain that does not close carries its break as
data: WHERE it breaks (between which events), WHAT is missing (the deed that
would connect them), and the candidate explanations (document missing at the
custodian · mislabeled and sitting unattached nearby · entity mismatch). The
broken-chain ledger with denominators is the honesty of the whole decode:
"N keys chain clean; M carry a named break at a known year."

**The run stamp — every run leaves one measured line.** When, mode, keys
chained (count / denominator), events attached, parked, unattachable, defects
returned, breaks named. A rising unattachable rate is an entity-resolution
regression; a rising defect rate points at extraction.

---

# 2 · METHOD

## The attachment ladder — strongest rung decides, weaker rungs corroborate

1. **Direct citation** — the document names the document it acts on (a
   satisfaction cites its mortgage's id, an assignment cites its loan).
   Strongest; no name-matching involved. Most instruments that act on other
   instruments cite them.
2. **Shared parcel key** — events on the same key connect through chain
   grammar (see below).
3. **Entity join** — the same canonical party appearing in both events.
4. **Corroboration** — date and amount agreement. NEVER decides alone;
   only supports a rung above it.

An attachment made at rung N is checked against every rung below it; a
contradiction (the citation matches but the parties are strangers) makes the
attachment `unattachable-pending-review`, not a forced link.

## Chain grammar — how breaks are DETECTED, not suspected

Chains audit themselves; these rules are the audit:

- **Title continuity:** the grantor of deed N+1 must be the grantee of some
  earlier deed (or enter by a named door: foreclosure, inheritance, estate
  deed, referee's deed). A seller from nowhere is a NAMED BREAK.
- **Every release finds its lien:** a satisfaction with no mortgage, or a
  mortgage satisfied twice, is a break (or a defect — the grammar says which:
  a citation mismatch is a break; an impossible role is a defect).
- **Accounts must balance forward:** debt can never go negative; shares sum
  to 100%; the envelope cannot send SF it never had. An account that breaks
  its floor points at the exact event that broke it.
- **⚠ ROLE INVERSION is invisible to reading accuracy and VISIBLE to chain
  grammar.** A grantor/grantee swap scores 100% on transcription — every
  word correct, the lineage exactly backwards. The chain catches what the
  reading cannot: the swap makes title continuity fail around the event.
  When a chain breaks around an event whose words check out, SUSPECT
  INVERSION FIRST — and return it to extraction as a defect with that note.

## The entity spine — names are the weakest join, so they get the most care

- **One normalizer:** every party name passes through `canon()` — two
  spellings of one entity are one entity. The county index's party fields
  (a verified-GOOD checker) anchor the canonical forms.
- **Measured warning:** naive raw-name matching found a fraction of a
  percent of what structured matching reached in prior territory work
  (~0.3% vs ~58–61% reach). The join is never raw strings.
- **The named-debtor rule — chains follow the LAW:** a lien attaches to the
  exact legal person named, and only that person. A judgment against the
  individual never enters the LLC's parcel chain, sole member or not.
  The individual-behind-the-LLC relationship is REAL and VALUABLE — and it
  is a DERIVATION-level signal, never a chain attachment. Resolution records
  the relationship edge; derivation decides what it implies.

## The party bridge — how no-parcel documents enter parcel chains

A party-keyed event (blanket lien, judgment, all-assets filing) propagates to
parcels through TIME-STAMPED OWNERSHIP:

1. Find the entity's parcels FROM THE OWNERSHIP CHAINS — owned at the event's
   effective date, plus acquired while the event remained live (blanket liens
   reach after-acquired property; the chain knows when it was satisfied).
2. **Gate by function and mode:** only instruments that legally reach real
   property propagate (judgment lien: yes; UCC on equipment: no). The
   vocabulary carries the gate; an ambiguous mode stays `parked` — it never
   silently spreads and never silently stays home.
3. A propagated event enters each parcel's chain MARKED as party-bridged,
   pointing at the ownership span that justified it.

Until an entity appears on some parcel, its events sit `parked` — indexed,
extracted, costing nothing. **Parked is re-evaluated on a trigger, not a
timer:** whenever an entity's ownership picture changes (a new deed chains,
a new canonical alias lands), that entity's parked events re-run the bridge —
so "joins the day the name shows up" is enforced by the join itself, not by
hoping someone re-checks.

## Lineage — chains span lot changes

An old-BBL event enters the successor parcels' chains through the lot lineage
edges (the parcel spine carries them). The chain shows the seam: "...as
5-00871-0012 until 2019; continues as 5-00871-1101..." — the lot changed; the
story did not. A lineage edge that lands nowhere is a break, never a shrug.

## Unknowns stay unknown

An `unresolved` quantity rides its chain AS unresolved — the debt account
shows "outstanding: $4.4M + one unresolved mortgage {1.15M: 3, 4.15M: 1}",
never a silent pick. `pending` and `unreadable` documents hold their place in
the time chain as gaps. No chain arithmetic ever treats an unknown as a zero.

---

# 3 · CHECK — every chain closes or every break is named

1. **The exact sum, per key:** `chained + parked + unattachable + defect =
   every event handed off by Extraction` — one column, no silent remainder.
2. **Grammar audit:** title continuity holds; every release found its lien;
   every account stays on its floor (no negative debt, shares at 100%,
   envelope never overdrawn). Every violation is a NAMED BREAK carrying its
   location and candidates — or a defect returned to extraction.
3. **Account = sum of chain, always:** recompute every account from its
   chain; a mismatch is a resolution bug, full stop — accounts are never
   hand-edited into agreement.
4. **The bridge audit:** every party-bridged event points at the ownership
   span that justified it; every lineage crossing points at its edge. A
   propagation that cannot show its justification is withdrawn and parked.
5. **No unknown became a number:** sample chains for unresolved fields —
   each still carries its distribution; none was silently resolved by
   chaining.
6. **The written-track audit:** the written chain regenerates from the data
   track and says nothing the table does not hold — sample sentences back to
   their events. Prose that outruns its table is deleted and regenerated.
7. **The check NESTS PER KEY; handoff is per key.** A key whose events all
   concluded hands its chains and accounts to Derivation immediately.
   Corpus-level handoff is the day every key has closed.

Only closed-or-named hands off. On a suspected systemic failure (defect rate
climbing across keys): stop and report — do not keep chaining on events you
no longer trust.

---

# 4 · HANDOFF — the phase when said and done

05 Derivations receives, per key: the time chain (the parcel's whole
documented story, gaps visible), the function chains (ownership, debt,
envelope, each closed or carrying its named breaks), the written chain (the
same story in prose, provably generated from the data), the accounts (running
balances that provably equal their chains), the relationship edges (who is
behind what — recorded, not yet interpreted), and the parked ledger riding
alongside. Derivation turns these into output metrics and macro summaries —
the $/SF, the outstanding debt, the owner's story in a paragraph — knowing
that every number it derives traces through a chain, to an event, to a claim,
to a page. Nothing below it is editorial; everything below it is evidence.

---

*Chain grammar and the attachment ladder are design-final; entity-resolution
parameters (canon() coverage, match thresholds) are UNSETTLED until measured
in the bootcamp alongside extraction — the pilot parcels' chains get verified
by hand, and every miss becomes bootcamp there too. The numbers age; the
reasons do not.*
