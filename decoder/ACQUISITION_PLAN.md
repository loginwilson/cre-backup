# Acquisition plan — what happens the moment the map finishes

The map partitions all 17,021,446 ACRIS documents into three states. **Every
one of them gets acquired.** Only the *mode* differs.

```
hid_TotalPages    share    meaning                   acquisition
─────────────────────────────────────────────────────────────────────────
  > 0             97.65%   normal document           INDEX + IMAGE
  = 0              1.99%   no image exists           INDEX only
  < 0  (-1)        0.36%   no image exists           INDEX only
```

⚠ **Both non-positive states were verified live, 28/28**, across RTXL, MAPS,
MISC, PSAT, WSAT and LOCC: `GetImage` returns ACRIS's placeholder (13,684 bytes,
md5 `4081a3f2…`). They are the same finding recorded two different ways by the
City, and neither is a failure.

---

## Step 0 — repair the map before trusting it

`amap.parse` computed `instrument = [cov+1, tot]` whenever `tot` was truthy,
and **-1 is truthy**, so ~19,570 records carry `[1, -1]` — an empty span that
reads as valid. The parser is fixed going forward; the already-written rows
must be corrected in one pass:

```
where hid_TotalPages <= 0:   instrument = null,  no_image = true
```

⚠ Harmless to acquisition (an empty range fetches nothing) but poisonous to
counting: any "pages to acquire" total that sums these silently under-reports.
Fix before the numbers are used for planning.

## Step 1 — INDEX acquisition, universal, free

Runs for **all 17M**, not just the image-less. Socrata, unthrottled, no image
budget: MASTER + PARTIES + LEGALS + REFERENCES + REMARKS.

Yields one **event claim** per document — kind, dates, parties with addresses,
BBLs, cross-references, remarks — with `evidence = "index"` and the query as
its proof.

⚠ **This is what makes "no image" survivable.** A release of estate tax lien, a
1936 will, a landmark designation — all fully recorded without a single page.
And the remarks often carry `BOOK/PAGES: 217/128` style pointers, meaning the
paper document exists in the physical archive even though ACRIS never scanned
it. *Never scanned* is a different fact from *does not exist*, and only the
remark distinguishes them.

Cost: ~34,000 batched queries at 500 ids each. Hours, free, resumable.

## Step 2 — IMAGE acquisition, only where pages exist

For the 97.65%, ordered by whatever selection prioritises (type, parcel,
watchlist). Uses the map's `instrument` range so only instrument pages are
fetched — never a range scan.

```
measured   ~100 req/s at 128 connections, warm, 2 sessions x 8
           ⚠ pipe-limited at ~37 Mbps on the current link
           ethernet is worth more than any code change here
```

⚠ **Skips the 127,660 image-less documents by intent, not by accident** — they
are already complete after Step 1, and the map records *why*. Roughly 1.1M page
requests never attempted.

## Step 3 — the ledger decides what is finished

A document is DONE when it has either:

```
an event claim + its term claims + proof crops        (image documents)
an event claim + no_image_reason                      (index-only documents)
```

⚠ Anything else is UNFINISHED and must stay on the queue. The failure this
guards against is the one that cost a night already: a document that silently
produced nothing, was never marked done, and jammed every subsequent run.

---

## Ordering

Step 1 does not wait for Step 2, and neither waits for the map to finish
completely — both can run against whatever the map has already partitioned.
**Index acquisition should start first regardless**, because it is free, it
covers every document, and it makes the event timeline complete before a single
page is fetched.

⚠ Blocked on `schema.sql`. Until the four tables exist there is nowhere for a
claim to land, and everything above writes to JSONL files that will need
re-loading later.
