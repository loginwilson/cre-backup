# THE RULE: decode DOCUMENTS. The index is a finding aid, not a source.

**This binds every decoder — ACRIS, DOB, BSA, LPC, DCP, DOS, StreetEasy.**
Read it before you write a single fact.

---

## The rule

> **An index row tells you a document EXISTS. Only the document tells you what it
> SAYS. A cover page, a summary screen, or a search result is not the document —
> it is the envelope the document came in.**
>
> **Read the document. All of it. To the last page.**

A fact sourced from an index is not a decode. It is a citation to somebody
else's summary of a page you never opened.

---

## Why — measured, not asserted

### The index is silent on the number that matters

| type | what the index says | the truth |
|---|---|---|
| DEVR (development rights) | `document_amt = 0`, always | **$5,000,000**, provable only from the cover-page tax stamps |
| microfilm DEED (1,367,900 docs) | `amt = 0` on **100%** | the entire pre-2000 sales record exists only on images |
| AGMT consolidation | `$410,000,000` | **$0 new money** — taxable was zero, exemption 255 |

The index is not *wrong* in these cases. It is **silent**, which reads exactly
like zero and is believed exactly like zero.

### The cover page is not the document either

Decoding one 116-page ZLDA fully produced four traps, **none of which is visible
on page 1**:

1. **The $10 recital.** The body reads *"in consideration of Ten Dollars
   ($10.00)"*. The real price was $5,000,000. Wrong by 500,000×, and it looks
   like a real number.
2. **The quantity is not in the granting clause.** The grant says *"conveys the
   Subject Development Rights"* — no figure. The square footage was in a sealed
   surveyor's exhibit, forty pages later.
3. **One recording contains several instruments.** Three separate documents —
   a purchase agreement, a declaration, and the ZLDA — each with its own control
   number, bundled under a single document ID.
4. **An exhibit was blank.** A metes-and-bounds header with no description under
   it. A defect visible only by looking.

### And the confession that produced this rule

After that walk I decoded five more types from **one page each**:

| type | pages read | pages in the document |
|---|---|---|
| MTGE | 1 | **38** |
| AGMT | 1 | **59** |
| DEED | 1 | 5 |
| SAT / ASST | **0** | — |

The cover-page facts were *true* — tax-stamp arithmetic matched to the cent. But
they were **only the money question**, and the DEVR walk had already proved that
everything else lives past page 1. SAT/ASST was worse: "they carry no money" is
an INDEX fact (`document_amt = 0`), asserted about documents I had never opened.

**One verified layer, and the layer underneath skipped.**

---

## What this means in practice

**Do**
* open every document you write a fact about, and read to the last page
* record `document_id` + `page` on every fact — if you cannot cite a page, you
  did not decode it
* follow defined terms to where they are defined — *"as shown on Exhibit D"*
  means the number is in an exhibit, not in the clause you are reading
* check the last page as deliberately as the first — exhibits, schedules,
  signatures and conditions live there
* when a document references another, resolve it; chains are multi-hop

**Do not**
* write a fact whose only source is an index row, a search result, or a
  summary/detail screen
* treat a zero in an index as a zero in the world
* stop at the cover page because the cover page answered the question you
  happened to ask
* report a type as "decoded" on the strength of one document, or one page

**Use the index for exactly two things**
1. **finding** — which documents exist, on which parcel, in what order
2. **checking** — a free, independent witness to test a decode against (an index
   amount that predicts a tax stamp to the cent is a real validation)

Both are legitimate. Neither is decoding.

---

## The completeness test

Before reporting any decode, answer:

> **How many pages does this document have, and how many did I read?**

If those numbers differ, say so in the finding. `pages_read / pages_total`
belongs beside every claim, exactly as `documents_read / documents_exist`
belongs beside every parcel timeline.

**A decode that cannot state its own coverage is not finished — it is unmeasured.**
