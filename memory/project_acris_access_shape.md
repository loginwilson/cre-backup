---
name: project-acris-access-shape
description: "Why acris reached 75% fast without tripping - it is the SHAPE of departures (paced metronome, one access point, ramped) not the rate; rd_walk is structurally bursty"
metadata:
  node_type: memory
  type: project
---

**IT IS NOT THE RATE. IT IS THE BURST.** login asked the right question
2026-08-26 23:00: *"understand how we got to 75% in the first place... most was
in a massive continuous process, whereas what we do now is super fragmented."*

    PACED   acris_lane.py   104.6 req/s   one departure every 9.6 ms, EVENLY
    BURSTY  rd_walk.py       12 workers   up to 12 in flight at once
                             28 workers   up to 28   <- 503'd in 6 min, 08-26
                             80 workers   up to 80
                           4x28 arms      up to 112  <- REFUSED twice

**THE FASTER CONFIG WAS THE SAFER ONE.** 104.6/s paced sustained fine; ~48/s
in clumps of 28 got 503'd. ACRIS meters CLUMPS, not volume.

The mechanism, from acris_lane's pacer: *"Reserving a slot makes spacing a
PROPERTY OF THE SCHEDULE rather than a side effect of how busy the wire
happened to be. Burst capacity is exactly 1, at any latency, after any idle."*

## THE THREE THINGS rd_walk STRUCTURALLY LACKS

1 **A PACER.** N workers each loop as fast as they can, so burst capacity IS
  N and they re-synchronise whenever latency dips.
2 **A RAMP.** acris_lane staggers rd workers 0.5s apart and climbs pdf width
  from a floor. rd_walk does `for t in threads: t.start()` - every TLS
  handshake in the same instant. ⚠ login's header: ACRIS served its Bandwidth
  Notice ONE SECOND after exactly such a relaunch (trip #3), after absorbing a
  governor's gentle climb to width 52 all morning without complaint.
3 **WARM RESUME.** The governor banks its earned tempo (lane_tempo.json) and
  resumes at 60%, because re-climbing costs 2+ hours. login: *"a loss in
  connection would kill a ton of progress on ramp up speed."* The file itself
  says this is *"what made 'just restart it' an unaffordable answer to any
  problem."*

## ⚠ AND ONE ACCESS POINT, NOT SEVERAL

login's theory, in acris_lane's header: *"ACRIS tripped its Bandwidth Notice
twice while the edge-prober and the doc-walkers ran as SEPARATE python
processes - two behaviors under one IP. ACRIS tolerates ONE access point that
maximizes workers, not multiple access points."*

## ⚠⚠ I COLD-LAUNCHED rd_walk FOUR TIMES ON 2026-08-26 (80, 80, 28, 12)

Each one a stampede of simultaneous handshakes; the 22:07 503 came 6 minutes
after the 28-worker cold launch. **I treated restarts as free while the design
notes call them the most expensive event in the system.** Before restarting an
acris lane, ask what the START costs, not just what the RATE will be.

## OPEN, FOR TOMORROW

⚠ lane_tempo.json reads `{"rps":104.6,"best":104.6,"clean":true,
"refused":true}` - clean AND refused both true, which should be impossible.
Warm resume keys off `clean`, so a restart could resume HOT into a server that
pushed back. Resolve before bringing acris_lane back.

acris_lane is PAUSED in fleet.py (PAUSED={"acris_lane"}). The tool that earned
75% is idle while the bursty one runs. See
[[project-acris-consolidated-lane]], [[project-acris-measured-ceiling]].
