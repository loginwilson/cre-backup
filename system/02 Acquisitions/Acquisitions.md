# 02 · ACQUISITIONS — the phase

> **BOOTCAMP GOVERNS THIS FILE.** Every function, mode, event row and vocabulary
> used here is defined in [`Bootcamp.md`](../Bootcamp/Bootcamp.md) - the ONE authority.
> Never redefine a term in this file; correct it there and it corrects
> everywhere. A rule that is not in the bootcamp is not a rule.


**This document is the source of truth for how acquisition runs ACROSS
SOURCES.** Each source folder holds a source md that runs its custodians;
this md states what every one must satisfy, and what they converge to.

# OVERVIEW

Acquisition pulls the images and gives every document an ADDRESS — the one
new column it writes back to the map. It intakes only behind Navigation's
keyed-to-zero gate, and it is the last phase that talks to a custodian:
everything downstream reads folders and tables, never the network.

# 1 · OUTPUT — the converged product

**One store, one filing system, every source.** Documents from every source
file into the SAME by-key folders — a parcel's folder holds its deeds today
and its permits tomorrow, side by side in recorded order, because the key
space is shared (01's convergence rule paying off). One document, one copy,
whatever source it came from; the address column in each source's map points
into the same store.

# 2 · METHOD — the source roster and the contract

| source | status |
|---|---|
| Legal Instruments | **LIVE** — ACRIS measured (4×20, 75–90 pg/s); Richmond browser channel + conversion gated |
| Construction Filings (DOB) | future — document access policy differs; must be settled per custodian |
| Zoning (ZR/DCP) | future — text corpus, not scans |

**Every source md in this phase MUST carry:** the five sections; per-custodian
fetch methods with measured ceilings ("max" is a measured number, never a
hope); completeness judged by CONTENT, never HTTP status; whole-or-not-at-all
landing with defects listed; one corpus format per store (conversions gated
on measured extraction accuracy); states read-only (a `present` that fetches
nothing real is a listed failure back to Navigations, never reclassified);
live-vs-disk check with the exact-sum identity; the run stamp; the refusal
rule — no workarounds of any bot detection, ever.

# 3 · CHECK

The phase is level when every source's live-vs-disk count closes:
`linked + imageless + pending = every doc id`, counted from the disk itself,
per source and per key. The lag accounting is not cleared here — it passes
along.

# 4 · HANDOFF

Per key, per source: the full index with the documents attached — the map
now carrying addresses, the folders holding the bytes. 03 Extractions reads
from here and never touches a custodian again.
