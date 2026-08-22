# When is a decode EXACT ENOUGH? — the standard, and an audit against it

**Login, 2026-08-06: "I wouldn't worry about inferring yet, but the decode of
data should be so clear that you can clearly make inferences from them. The
decode should be so exact in how it interprets the document that it can make it
into structured data."**

Inference is parked. This file is about the bar the decode has to clear so that
inference is *possible later* — and an honest audit of where the current tables
miss it.

---

## THE TEST

> **Can you answer a question you did not anticipate, without reopening the
> document?**

That is the whole standard, and it is deliberately harsh. A decode that answers
the questions you had in mind when you wrote it is a summary. A decode that
answers questions you had not thought of is structured data.

It decomposes into five properties every recorded value must have.

### 1 · MAGNITUDE with UNIT
`130` is not a fact. `130 ft` is not a fact either — see (2).

### 2 · DATUM — what the number is measured FROM
`130 ft` above **what**? The instrument says: above the datum used by the
Manhattan Topographic Bureau, which is 2.75 ft above NGVD 1929 mean sea level at
Sandy Hook. A height stored without its datum cannot be compared to a DOB
elevation, a survey, or another easement — so it cannot be used, only re-read.

### 3 · EXTENT — over what REGION does it bind
The property this system got wrong first. Two easements on this parcel:

| | vertical | horizontal |
|---|---|---|
| lot 22 (2013) | above **130 ft** | the **WHOLE LOT** |
| lot 53/55/56 (2010) | above **23 ft** above curb | a **BAND 20 ft deep** from the lot line |

These are different shapes. Stored as a single `limit_value`, they are
indistinguishable — and "how much of lot 53's ground plane is burdened?" is
unanswerable without the document. **A constraint is a volume, not a scalar.**

### 4 · DURATION and TRIGGER — when does it bind
Perpetual, for a term, or on a condition? The lot 21 unit cap runs with the land
for ever. The Parking Lane Letter binds only during construction. Same table,
opposite lifespans.

### 5 · PARTY and DIRECTION — who is burdened, who benefits
Already carried. Without it a row of numbers cannot say whether a lot is a
buyer or a seller — the difference between a development site and a dead one.

---

## THE AUDIT — where the current tables stand

| table | 1 unit | 2 datum | 3 extent | 4 duration | 5 party | verdict |
|---|---|---|---|---|---|---|
| `acris_claims` | ✓ | partial | ✗ | ✗ | ✓ | **passes for money, fails for geometry** |
| `acris_rights_allocation` | ✓ | ✓ | ✓ (the lot) | n/a | ✓ | **passes** |
| `acris_envelope_ledger` | ✓ | ✓ | ✓ | n/a | ✓ | **passes** |
| `acris_constraints` | ✓ | ✓ | **✗** | partial | ✓ | **FAILS on extent** |
| `acris_documents/events` | ✓ | ✓ | n/a | n/a | ✓ | passes |

### The failure, precisely

`acris_constraints` stored the 2010 easement as `limit_value = 23,
limit_unit = ft_elevation`, with "20 ft DEEP from the lot line" written into the
`datum` prose. So:

* the horizontal dimension is **not queryable** — it is a sentence
* the same schema renders a whole-lot plane and a 20-ft band identically
* nothing can compute burdened area, and nothing can compare the two easements

That is a decode that reads correctly and stores incorrectly, which is the
failure mode hardest to notice: **the prose in the field is right.**

### The fix

Replace one scalar with the region it actually describes:

```
vertical_from      numeric     23        -- lower bound of the burdened volume
vertical_to        numeric     null      -- null = unlimited above
vertical_datum     text        'curb level' | 'Manhattan Topo Bureau datum
                                            (2.75 ft above NGVD 1929)'
horizontal_scope   text        WHOLE_LOT | BAND | PORTION
horizontal_extent  numeric     20        -- depth of the band, in feet
horizontal_from    text        'the shared lot line with lot 49'
duration           text        PERPETUAL | TERM | DURING_CONSTRUCTION
```

Now "which lots have a burden within 25 ft of their shared line?" is a query,
and the two easements are no longer the same shape.

---

## WHAT "EXACT" DOES NOT MEAN

* **It does not mean complete.** Lot 21's `generated` and `retained` are NULL
  because they were not transcribed. That is exact — it says precisely what is
  and is not known. A back-computed figure would be *complete* and *wrong*.
* **It does not mean interpreted.** "MetLife lends on stabilised assets" is a
  rule about the world, not a reading of a document. It belongs above this
  layer, and it is parked.
* **It does not mean summarised.** A summary chooses what matters. The decode
  does not get to choose, because it does not know what will be asked.

---

## THE RULE THIS PRODUCES

> **Record the SHAPE of the fact, not the number you happened to need.**

Every collapse of a structure into a scalar is a decision that some future
question is not worth answering — made by whoever was writing at the time,
silently, on behalf of everyone who reads it later.
