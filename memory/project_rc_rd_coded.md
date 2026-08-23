---
name: project-rc-rd-coded
description: "Richmond rd is CODED on the redesigned site — the per-fetched-page grant rule, the corpus schema, and the county's real concurrency envelope"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-22T14:38:52.949Z
---

**THE GRANT RULE (re-cracked 2026-08-21 night):** on the redesigned
Richmond site, a detail (`/Search/viewDocumentInfo/{id}`) unlocks after the
SAME SESSION fetches THE LISTING PAGE the id appears on — not the whole
search (an id whose page was never fetched gets the 4,212-byte shell; the
same id right after its page: full detail). So Richmond rd is PURE CODE:
window → pages → targets' details. `rc_rd_walk.py` owns it (decoder root);
the census db supplies every id's window; `--shard i/n` splits windows
across processes. Chrome's ONLY remaining Richmond job is pdfs (the iapps
image host refuses headless — 302 chain, batch via rc_mint).

**LAND THE CORPUS SCHEMA or downstream breaks** (a lesser first version
landed 7,914 rows that had to be reset): `doc_type` · book/page ·
recorded · amount · status · **image_state** (present/absent — rc_mint's
pdf selector reads it) · **parcels as full BBLs** (`5 + block(5) + lot(4)`
— nav_key reads `p["bbl"]`; raw block/lot rows never key) · parties with
the person/company COLUMN kept (the SPE distinction).

**RICHMOND RD CLOSED 2026-08-21 ~11:55 PM: 2,501,589/2,501,589,
table-counted, empty 0.** The last 339 hid in TWO DEEP census-recovery
windows (2000-08-22 ×182 · 2001-04-19 ×144, hundreds of listing pages):
the walker restarts a failed window from page 1, so one mid-walk timeout
aborted the whole window every sweep — **the retry unit must never be
bigger than the failure unit**; per-page retry (now folded into
rc_rd_walk.get()) landed all 339 in one pass. The walker is the daily
follower: sync lands ids → trigger mints urls → empty cell = work list.
⚠ Board counter lessons the closure taught: baseline is DATA never a
hardcoded literal; one board writer only (schtask disabled, live daemon
owns it); a bridge must skip task outputs older than the baseline stamp
(else it resurrects consumed logs → >100%); >1:1 rd per id is impossible
in the TABLE — any over-100% is counter arithmetic, fix by re-baselining
from a true count, never by capping.

**⚠ TWO NUMBER NAMESPACES** (looked like a corpus-wide pdf mismatch,
2026-08-21): RC_{n} = INTERNAL id (ViewDocumentInfo key, unique). The
clerk's "Document Number" SEARCH queries the INSTRUMENT number — an
overlapping sequence (internal 1008528 = #9566/Bk847/Pg195/1942;
instrument #1008528 = internal 2815386, a 2026 deed). Verify a pdf's
identity by Vol/PG stamp (old era) or LAND DOC # = rd `instrument`
(modern — it will NOT equal the filename and that's CORRECT); never by
searching the filename as a Document Number. Mint is id-faithful
(granted vs feed-style A/B: identical handles). ⚠ A doc landed the DAY it
was recorded freezes PREMATURE — instrument blank (the label is
"Document No.:" with a PERIOD on modern pages; the old parser missed it)
and image_state 'absent' (scan lag) — which hides it from instrument
audits AND from pdf selection forever: `rc_rd_refresh.py` (inside the
daily sync) re-walks young premature docs until they mature.
Pdf lane: feed mints ahead → browser WORKER loop → rc_pdf_land --raw
lands ~10/s → rc_convert is OPTIONAL (raw IS the acquired doc; ~870 GB
raw vs ~350 GB converted against 18 TB free).

**THE COUNTY'S REAL ENVELOPE — never under-run it again:** night_chain ran
rc_detail_pull at conc 80 ×2 CONCURRENT SWEEPS = 160 connections,
2,498,810 details in ~26 h (Aug 18 20:57 → 19 22:49, ~27 docs/s sustained,
no trip). The "4.4 docs/s at conc 8" docstring number was an early probe,
not the ceiling. New-site walk: 40 workers ramped 13.7→21+ docs/s; our GIL
pins a process near one core, so scale = processes × ~40-80 workers.
⚠ The user's memory of "instant" = nav_land BULK-LOADING rc_detail.jsonl
from disk into the table (2.4M rows in ~1 h on Aug 20) — local load, not
network. No bulk DETAILS endpoint is known; the block ledger (8,999 reqs =
2.4M index rows) has no parties.

**The walker is the DAILY follower too:** sync lands new RC ids with empty
rd → the walk fills them coded (empty cell = work list). ⚠ 8 heavy python
processes ≈ all 8 cores — at 160-conn Richmond + 4 rd + 2 pdf, machine CPU
binds before either server; read ACRIS sag as OUR cpu, not their pool.

**⚠ RICHMOND PDF IS THE ONE NON-PYTHON LANE — SETTLED 2026-08-22, do not
re-litigate.** Python asking the FINAL image url with a valid fresh token
and a wholly normal request (real Chrome UA, Referer, Accept) gets **HTTP
403** while the browser is served the same token seconds later: the host
fingerprints below the header layer (TLS), and presenting a fake
fingerprint = working around bot detection = the line we don't cross.
So: acris rd · acris pdf · richmond rd = pure python; richmond pdf = a
real user-driven browser with the extension, permanently.

**THE WALL IS PER-CONNECTION-POOL, not per-cookie (measured):** a second
worker fetching `credentials:'omit'` SPLIT the same ~1.8 docs/s
(0.93+0.88) — cookie identity is not the key. Two separate browsers
STACKED (Edge+Chrome = 3.09 docs/s). Separate profiles have separate
pools too, so they should stack; but each full browser instance costs
~1.5 GB and the machine runs at ~2.4 GB headroom — the 2nd browser is
what dragged acris rd 100 → 55 docs/s (RAM/paging, never CPU: the census
showed 5 of 8 cores idle, all four lanes remote-bound).

**THE LOOP IS A WEB WORKER (v7):** page-timer loops get throttled when
the window is hidden/covered/screen-locked (~0.5-1 docs/s, and overnight
the crawl let every queued token expire → a false refusal stop at 00:30).
Worker timers are exempt: 1.85 docs/s measured WITH THE WINDOW HIDDEN,
2 runners at 250 ms (3 runners = no gain, the wall is the host's). The
feed enforces a 600 s TOKEN TTL and releases stale ids to re-mint, so a
paused consumer can never poison the queue again.
