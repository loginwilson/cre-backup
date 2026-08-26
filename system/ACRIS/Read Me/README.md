# ACRIS

Everything for the ACRIS source lives here: the lane that runs it, the
helpers it imports, and its docs.

ACRIS is the **PIANO METHOD** source. Requests are SEQUENCED on a metronome
that self-adjusts so two requests never collide. Whether one note or a chord
sounds at a time is a separate question — `--max-inflight 1` is single notes,
64 is chords, and **both are piano**, because both depart on the beat.
Richmond is the drum: no pacer at all, latency the only governor.

## The pipeline

    sync (crfn walk)  ->  doc id + rd IN THE SAME REQUEST
    db trigger        ->  rd_url and pdf_url minted
    db trigger        ->  pass-1 key (parcel / BBL) on the rd
    backfill          ->  pdf

The image never jumps the queue. The sync lands the id, the urls, the rd and
the key — everything freshness-sensitive — and the image waits its turn in
the ordinary backfill pass.

## Standing rules

- **On a refusal: STOP.** Do not retry, do not rotate anything. ACRIS served
  its Bandwidth Notice at 08:10 on 2026-08-25 and the lane stopped itself,
  which is correct.
- **A refused rate is a ceiling for ever, never a target.** A rung that
  produces well for ten minutes is not evidence the server tolerates it for
  hours.
- **A warm resume is a RAMP, not a jump.**
- Do not build a bulk image scraper and do not work around bot detection.
