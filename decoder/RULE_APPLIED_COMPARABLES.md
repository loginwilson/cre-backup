# THE RULE, applied to comparables — and what it indicts

`RULE_DOCUMENTS_NOT_INDEXES.md` binds this decoder. Login stated the mapping,
2026-08-06:

> *"In this instance, dof provides the docs, and listing services are the doc
> (active/historical)."*

That is right, and the two halves are right for opposite reasons. Writing them
out is what makes the rule testable here instead of merely quoted.

---

## Lane 1 — StreetEasy. THE LISTING IS THE DOCUMENT.

There is no document underneath a rental listing. A residential lease is private
and is never recorded, so no deed, no ACRIS image, nothing to open. The listing —
its date, unit, SF, rent and status — **is** the primary record. StreetEasy is
not indexing something else; it is the something else.

So the rule does not say "go find the real document" here. It says the equivalent
thing one level down: **do not stop at the summary of the listing.**

| the envelope | the document |
|---|---|
| the SRP row (`32 active rentals`) | every listing, active AND historical |
| the building page's visible units | the closed lane behind "View unavailable units" |
| a rent | the rent WITH its unit label, SF and $/RSF |

**The completeness test, restated for this lane:**

> how many listings does this building have, and how many did I read?

Both lanes or it is not read. `rentalInventorySummary.availableListingDigests`
alone is the cover page — Halo LIC shows a handful of actives and
`rentalsHistoryByBuildingId` returns **3,941 closed rentals**. Reading only the
active lane would report a building as decoded on under 1% of its record.

And SF coverage is the second axis of the same test, because a listing without
`livingAreaSize` cannot produce a rate: 2-21 Malt Dr returns 167 closed rentals
and **zero** with SF (TF Cornerstone withholds it); Riverview North returns 1,487
of 1,499. Both are complete reads. One yields rates and one does not, and
`sfCoverage` full/partial/none is what keeps them from looking alike.

---

## Lane 2 — DOF condo sales. ⚠ THIS ONE IS CURRENTLY AN INDEX DECODE.

`condo_sales.py` reads `usep-8jbt` — DOF rolling sales. **That is an index.** It
is a row per transaction saying a sale happened, at a stated price, on a stated
date. It is exactly "a search result / a summary screen", and the rule names it:

> *A fact sourced from an index is not a decode. It is a citation to somebody
> else's summary of a page you never opened.*

The document is the **recorded deed in ACRIS**, and the gap between them is the
same gap this project already measured on DEVR:

| | the index | the document |
|---|---|---|
| price | `sale_price`, and **5,604 of 21,185 condo rows (26%) are $0 or nominal** | the cover-page RPTT + RETT stamps, which recover the real consideration |
| what moved | one row, one price | may bundle several units, or a unit plus parking plus storage |
| parties | absent | grantor / grantee, and the SPE that leads to a principal |

The 26% I filtered as "nominal_or_zero_price" is the tell. Those are not
non-sales — many are real transfers whose price the index does not carry, which
is the DEVR `document_amt = 0` trap wearing different clothes. Dropping them is
the correct thing to do with an INDEX and the wrong thing to believe about the
world.

**So the honest coverage line for the condo lane today is:**

```
15,581 sales indexed · 15,239 with SF from the assessment roll · 0 DEEDS READ
```

Not "condo sales decoded." The module now stamps `evidence: "index"` on every
row and prints that line, so nothing downstream can mistake tier for truth.

### What the assessment roll is, in these terms

`8y4t-faws` is not a document either — it is DOF's administrative record. But it
is not being used as a substitute for one: it is the **authoritative statement of
the unit's area**, which the deed usually does not contain at all. It is also
self-checking, because `aptno` names the unit independently of the sale, and
22 rows where the two disagreed had their SF withheld rather than guessed.

That is the rule's second legitimate use of a non-document source: **checking**.

---

## What this changes

1. Every comparables fact carries an `evidence` tier — `document` / `index` /
   `listing` — and the tiers never blend in an average.
2. The condo lane's headline coverage is `deeds_read / sales_indexed`, currently
   `0 / 15,581`, printed beside every claim.
3. Reading the deeds is an ACRIS job at ACRIS's rate limit (25 s between
   requests, hard stop on refusal). It is not a thing this lane can quietly
   absorb, and pretending otherwise would produce exactly the "one verified
   layer, and the layer underneath skipped" confession the rule was written from.
4. The rental lane's coverage is `listings_read / listings_available`, per
   building, both lanes, plus `sfCoverage`.
