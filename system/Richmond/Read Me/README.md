# RICHMOND

Everything for the Richmond County Clerk source lives here.

Richmond is the **DRUM**: no pacer, latency is the only governor, and
concurrency is the single dial. Measured ceiling is ~16 pullers — 32 draws
SSL/connection resets from the courts host, which is pushback to obey.

⚠ **THE PDF DOES NOT LIVE ON RICHMOND.** Minting asks richmond for
`/ViewVscmsDocument/ViewContent` with redirects disabled; the **302 is the
product** and its `Location` points at the NY State courts viewer
(`iapps.courts.state.ny.us`) with a self-authenticating token. So "no limits
on the richmond side" does not govern the download — the courts host does.

## The pipeline (login's model, 2026-08-25)

    sync (date range)  ->  new doc id
    db                 ->  rd_url and pdf_url minted
    backfill rd        ->  recorded_details
    db trigger         ->  pass-1 key (parcel / BBL) — needs the rd
    backfill pdf       ->  ask the url:

        it serves a file          ->  the PATH goes in the pdf cell
        dead end, recorded < 7d   ->  'pending'  — STAYS IN THE QUEUE
        dead end, recorded > 7d   ->  'absent'   — a determination

⚠ **`pending` is TODO. `absent` is DONE.** Without `absent` counting as a
determination, completion can never reach 100%. Without `pending` counting as
todo, a row leaves the worklist AND is counted landed the moment it is marked.
The todo predicate, the partial index and the board's denominator must always
agree; if they ever disagree the count silently uses the wrong set.

⚠ **A FAILED FETCH IS NOT A DEAD END.** A timeout, reset, 5xx or refusal says
nothing about the document and must produce a RETRY, never a verdict.

## Standing rules

- On a 401/403/429: STOP. Do not retry, do not rotate anything.
- A lone 4xx on ONE document is a verdict about that document (sealed or
  restricted), not a refusal of us — quarantine the id, keep its column
  honest, never stop the lane.
