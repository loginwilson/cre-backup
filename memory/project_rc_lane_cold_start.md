---
name: project-rc-lane-cold-start
description: RESOLVED 2026-08-26 — ix_nav_pdf_todo drifted off the queried predicate; fixing it killed rc_lane's 12-min cold start and took it 6.03 -> 13.75 docs/s
metadata:
  type: project
---

**THE INDEX MUST MATCH THE PREDICATE, AND NOTHING WARNS YOU WHEN IT STOPS.**
`ix_nav_pdf_todo` was live as `WHERE pdf = ''` while BOTH rc_lane's worklist
and board_truth's count queried `pdf IN ('','pending')`. board_truth.py's own
comment ASSERTED "ix_nav_pdf_todo is rebuilt on the SAME predicate" — it never
was. Counts stayed correct (both used the right predicate); only speed paid,
so nothing ever surfaced it.

MEASURED before -> after the rebuild (2026-08-26):

    miner next_ids(20)     3.85 s  ->  0.08 s
    board rc_todo         8-22 s   ->  0.01 s
    rc_lane cold start    12 min at 0/s  ->  10.5 docs/s in minute ONE
    sustained rate         6.03/s  ->  13.75/s   (3-min window, not instant)
    richmond ETA            8+ h   ->  3.4 h

**THE TELL WAS `ready 0`.** rc_lane's PROGRESS prints `minted N (ready M)`
against an `--ahead 1200` buffer. Pinned at 0 = pullers starved = the MINERS
are the constraint, and they serialize on one `grab_lock` around next_ids, so
the fleet ceiling is 20/next_ids_seconds. After the fix `ready` climbs off 0.
Read that field before blaming bandwidth.

⚠ **SQLite will NOT use a `WHERE pdf IN ('','pending')` partial index for a
`pdf=''` query** — verified on a scratch db, it falls back to the PK scan.
Implication is not proved. So the two must be written IDENTICALLY.

⚠ The rebuild is DROP+CREATE inside one `BEGIN IMMEDIATE` (rollback restores
the old index). It took 2,267 s and needs the lane STOPPED — and board_truth
stopped too: its 60 s pass full-scanned the same table and dragged the build
from 11.5 MB/s to 1.9 MB/s. D: is ~300 MB/s sequential but ~3 MB/s random.

See [[project-decoder-fleet-restore]], [[project-acris-consolidated-lane]],
[[project-decoder-updates-board]].
