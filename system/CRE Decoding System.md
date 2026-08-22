# CRE DECODING SYSTEM

> **BOOTCAMP GOVERNS THIS FILE.** Every function, mode, event row and vocabulary
> used here is defined in [`Bootcamp.md`](Bootcamp/Bootcamp.md) - the ONE authority.
> Never redefine a term in this file; correct it there and it corrects
> everywhere. A rule that is not in the bootcamp is not a rule.


**This document is the source of truth for the system.** It runs the phases
the way a phase md runs its sources and a source md runs its custodians —
the same five sections at every altitude, because the design is FRACTAL:
the system runs phases, a phase runs sources, a source runs custodians.
Specification flows down; data flows up; each level's CHECK gates the
handoff at its altitude.

# OVERVIEW

**The job:** decode the recorded world into the present state of every
parcel and party — completely, provably, and fresh every morning. Raw
sources (county records first, then construction filings, zoning, and
beyond) are walked through six phases that turn documents into answers:
what is true about this property TODAY, at a granularity nobody else has,
with every number traceable to a page.

**The loop:** one 04:00 routine tops the system. Sync names what is new,
navigation keys and addresses it, acquisition attaches the documents,
extraction reads them into events, resolution chains the events into
stories, derivation collapses the stories into now. Go to sleep; wake up to
a fresh decoding. **Freshness is the product** — competitors are lagged,
wrong, or varying; answers stamped "proven level this morning" are the edge.

**The ladder:** `claim -> event -> account -> inference`, on two tracks —
the DATA track (tables, chains, balances) and the WRITTEN track (event
summary -> written chain -> macro summary), with the prose always generated
from the data, never authored past it.

**Procedure and judgment:** the front half (00–02) is procedure — mechanical,
complete on day one, its quality fixed by measured parameters. The back half
(03–05) is judgment — analytical, trained not written, its quality a rising
curve banked in HANDBOOKS (the constitution/case-law split: mds hold the
rules that never change; handbooks hold the learning, cold-start-survivable,
gold-set-protected, version-stamped). The bootcamp is where all of it
converges, running DURING the acquisition backfill so no time idles.

**The unit of flow is the KEY (the parcel, today).** A finished parcel
cascades through the whole back half while the corpus is still pulling —
completion is per key, never per corpus. Keys, event grammar, and the merged
graph are SYSTEM PROPERTY, converged at the phase level (keys at 01, grammar
at 03, one graph at 04) so that every source's data can join every other's.

# 1 · OUTPUT — what products stand on

The system's output is 05's present state, and it is built to hold up a
strong product surface (cards, maps, queries, feeds):

- **Per key: the answers** — every registry question answered, partial
  (source named), or blocked (break named) — plus the metrics (stored
  formulas), the macro summary, and the labeled signals.
- **Traceability as a feature:** every number walks chain -> event -> claim
  -> page. The product never shows an orphan fact.
- **Freshness as a stamp:** every answer carries the morning it was proven
  current; provisional entries surface what recorded yesterday even before
  its scan attaches.
- **Honesty as UX:** unknowns say why (a named break, a missing source) —
  the product shows the gap, never a guess.

# 2 · METHOD — the six phases

    00 Synchronizations   is the map level? name the delta        (ids)
    01 Navigations        key · doc id · index · endpoint         (the map)
    02 Acquisitions       pull images, write addresses            (the store)
    03 Extractions        documents -> events (bootcamp/bootcamp) (the tables)
    04 Resolutions        events -> chains + accounts (converge)  (the graph)
    05 Derivations        chains -> present state                 (the product)

Each phase folder holds the phase md (the contract every source must
satisfy) and one folder per source (the md that runs it + its output + its
run log — never a loose file; the tree grows WIDE with new sources, never
deep). **Adding a source:** drop a sibling folder in each phase, write its
source md on the five-section template, pass the phase contracts (the
admission audit), converge on keys/grammar/graph. No new machinery, ever.

| source | status |
|---|---|
| Legal Instruments (ACRIS + Richmond) | **LIVE** — backfill closing; back half designed, bootcamp gated |
| Construction Filings (DOB) | future — unlocks development status, contacts traversal |
| Zoning (ZR/DCP) | future — unlocks eligibility; regulatory events by applicability |
| DOF / LPC / BSA / DEC | future — named by derivation's partial answers (the registry is the source roadmap) |

**Storage & substrates — BINDINGS, not foundation.** This tree is the
LOGICAL truth; what follows is the physical binding as of today, kept in
this one section so that swapping any of it touches one paragraph and zero
logic — substrates age; the structure does not: the corpus (documents, map,
tables) lives on the corpus drive (20 TB — sized for the largest
acquisition) through acquisition; extraction compute runs on the parallel
cluster (Torch); model candidates are named in the extraction md as
candidates. **Backup is tiered:** the working corpus on the 20 TB primary;
backups onto smaller SSDs for the irreplaceable-in-time layers (the map, the
tables, the handbooks — small next to the store); cloud storage (NYU) as the
possible off-site tier; and **Supabase is the serving database** — it holds
what we DEEM worth serving (the product-facing tables: present state,
chains, the map's serving view), never the raw store. The serving wiring is
detailed here when the product layer lands. Big
outputs appear in the tree as their access points; nothing is stored twice
WITHIN the system — and yet everything is RECOVERABLE: the front half
re-derives from the custodians, the back half re-derives from the phase
beneath it, so catastrophe costs time (a re-pull measured in weeks), never
truth.

# 3 · CHECK — the system-level audit

The system is healthy when three audits hold:

1. **Every phase's check gates its handoff** — the universal law: output
   proven against something external (a custodian's counter, the disk, the
   chain's own grammar), exact-sum identities with no silent remainder,
   breaks and unknowns named, never smoothed. A phase that cannot prove
   itself does not hand off.
2. **Every md carries TIME × COST × ACCURACY** — time in measured
   throughputs and windows (never under 15 minutes), cost in request budgets
   and model tiers, accuracy in denominators and gates. Optimization is not
   a vibe; it is a checklist this document runs against every md below it.
   Every rate has a denominator; every parameter has its measurement and its
   failure mode; every unsettled value is LABELED unsettled.
3. **The conduct laws hold everywhere:** on a REFUSAL stop dead — no retry,
   no rotation, no workaround of any bot detection; never spoof an identity;
   never repair a number to make a check pass; never make information up —
   an empty cell beats a plausible fabrication; credentials are never
   printed. These are not per-phase rules; they are the system's character.

**The system's own heartbeat:** the nightly routine ends by writing ONE
morning line — synced, landed, extracted, chained, derived, with counts —
the union of the phases' run stamps, appended to the System Run Log beside
this document (no file is homeless, this one included). **A missing morning is itself an
alarm:** silence must never look like success at the top when it is banned
everywhere below.

**Product-readiness is the final benchmark:** an answer reaches the surface
only if it traces, its stamp is current, its unknowns are named, and its
tier (fact vs signal) is labeled. The check that fails withdraws the answer
— the product is never wrong quietly.

# 4 · HANDOFF — the phase when said and done

To the products and the person: a decoded market. Open a parcel — its
documented history, its present state, its pressure. Open a party — their
holdings, their movement, their story. Every answer fresh as of this
morning's proven level, every number a click from the page that recorded
it. The registry's unanswered questions name the next source; the run
stamps show the system getting sharper against a past that never changes,
even as the corpus grows every night;
and tomorrow at 04:00 the loop runs again.

---

*The mds beneath this one carry the granular law: phase mds hold the
contracts, source mds hold the methods, handbooks hold the learning. The
numbers age; the reasons do not.*

---

## 2026-08-21 — THE SETTLED ARCHITECTURE (append-only; Claude reads this first)

**Two databases, one boundary.** Phases 00–03 build THE RECORD; 04–06 build
THE READING; 07 packages. The shape changes at the extraction boundary
(one row per document -> many rows per document), which is why the store
splits there:

    custodians ──[00 sync]──> Legal Instruments.db  (tree root - THE RECORD)
        one table `navigation`, columns in phase order:
        id | rd_url | pdf_url | recorded_details | pdf | keyed_by | key
        \__ 01 nav __________/ \__ 02 acq ______/ \__ 03 org ____/
                       |
                       v
        [04 extraction, Bootcamp-governed] ──> Legal Instruments Decoded.db
        (THE READING: events/claims/quantities; 05 resolution chains them,
         06 derivation answers "what matters today"; doc id + key = the join)
                       |
                       v
        [07 productizations]

**The four bands (the login's grammar):** sync = actively staying aligned
with the sources · nav→org = the database · ext→der = analyzing the
database · productization = packaging outputs.

**Per phase, the standing trio + watch:** routine_<phase>.py (the six-step
grammar) · a concise md (the claim, the methods, the doctrine) · the shared
db — plus a row on the Updates board (D:\CRE Decoding System\Updates\,
5-minute ticks, status COMPUTED never hand-set).

**Structural enforcement lives IN the record db** (bad states
unrepresentable, not detected): `mint_urls` trigger - no id without its two
urls; `key_rules` trigger - keys only by the three-route ladder
(parcel/reference/pdf; party is DECODING, not a key) and only with their
evidence landed.

**Completeness doctrine (proven 2026-08-21):** each custodian is closed by
its OWN enumeration - ACRIS: Socrata distinct ids + the CRFN counter census
(7,010 residues -> 6,808 void · 201 found documents landed); Richmond: the
full 1850->today window census, identity held + missed + void = range.
A zero is only believed after a known-nonzero control; an unreachable
source is a report, not a crash; never repair a number to make a check
pass.
