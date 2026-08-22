# 00 · SYNCHRONIZATIONS — the phase

> **BOOTCAMP GOVERNS THIS FILE.** Every function, mode, event row and vocabulary
> used here is defined in [`Bootcamp.md`](../Bootcamp/Bootcamp.md) - the ONE authority.
> Never redefine a term in this file; correct it there and it corrects
> everywhere. A rule that is not in the bootcamp is not a rule.


**This document is the source of truth for how synchronization runs ACROSS
SOURCES.** Each source folder inside this phase holds a source md that runs
its custodians; this md states what every one of them must satisfy, and what
they converge to.

# OVERVIEW

Synchronization answers one question for the whole system, every day: **is
our map level with everything every custodian has recorded — and if not,
exactly which document ids are missing?** It is the top of the loop: the
04:00 routine that makes "go to sleep, wake up to a fresh decoding" true.
This phase detects and names deltas; it never writes the map (01 Navigations
does). **The trigger lives at THIS level, once:** one 04:00 routine fires the
whole phase and runs every source under it — never a pile of per-source
schedules to keep aligned. Adding a source adds a folder, not a trigger; the
routine picks it up from the roster. A source lives here as its own folder — Legal Instruments today;
every future source (construction filings, zoning, tax) arrives as a sibling
folder with its own md on the same contract.

# 1 · OUTPUT — the converged product

**The day is synced when EVERY source's sync has zeroed out.** The phase
product is the union of the day's finalized dated delta tables, one set per
source, each named for the gap it closed, each carrying its delta ids in
fenced blocks. One source finalizing is a source-level event; ALL sources
finalizing is the phase-level event that means the whole system's morning
can be trusted.

# 2 · METHOD — the source roster and the contract

| source | status |
|---|---|
| Legal Instruments (ACRIS + Richmond) | **LIVE** |
| Construction Filings (DOB) | future |
| Zoning (ZR/DCP) | future |

**Every source md in this phase MUST carry:** the five sections (OVERVIEW ·
OUTPUT · METHOD · CHECK · HANDOFF); a stateless watermark derived from the
map; ids-only output (the index walk belongs to Navigations); per-custodian
methods with measured, labeled parameters; **lag as a parameter** on every
custodian; the zero-out check against the staged list; the run stamp; and
the refusal rule (on a REFUSAL: stop dead, wait for a person). A source md
missing any of these is not admitted to the phase.

# 3 · CHECK

The phase is level when every source's check reads level — no source's
delta outstanding, every finalized table handed off. A source that cannot
zero (broken probe, refusal) holds ITS handoff without holding the others:
sources are independent at this phase; they converge downstream.

# 4 · HANDOFF

Each finalized dated table triggers 01 Navigations for its source. The
phase's converged promise to the system: after this phase runs clean, no
custodian holds a recorded document the system has not named.
