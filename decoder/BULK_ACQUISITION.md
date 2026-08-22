# Getting the ACRIS corpus at bulk scale — within their rules and ours

**The question:** how do we obtain and decode all 17,036,716 ACRIS documents on a
timeline of weeks-to-months?

**The short answer, established 2026-08-05:** acquisition is a *procurement*
problem, not an engineering one. Processing is the engineering problem, it is
ours, and it is comfortably inside the timeline. Every hour spent trying to make
the public viewer into a bulk channel is an hour spent on the one step that
cannot work.

---

## 1. Why the viewer can never be the channel — two independent walls

**Wall one: their rate limit.** Measured, not guessed. The block landed at ~97
requests in ~90 minutes ≈ **1.1 requests/minute**. A 60-day pull of the
envelope classes alone needs ~30 requests/minute sustained. That is **28× beyond
the rate that already got us cut off**, and the full corpus is 13× larger again.

**Wall two: physics, and this one holds even if the rate limit vanished.** The
corpus is **~14.3 TB** (17.0M documents × ~15 pages × ~60 KB). At 100 Mbps that
is **14 days of continuous transfer**; the viewer serves one page per request
with HTML overhead around each. Corpora this size move on **physical media**.
Nobody downloads 14 TB through a document viewer, with or without permission.

The second wall is the important one. It means the answer was never "fetch more
politely" or "fetch more cleverly" — those address a limit that is not the
binding constraint.

---

## 2. What is ruled out, and why it stays ruled out

Rotating identity, resetting sessions on block, distributing across access
points, or pacing to look human. All of these share one property: **they do not
reduce the load on ACRIS, only the accuracy of its accounting.** A million
requests is a million requests however it is attributed. Slowing down is
compliance because it genuinely reduces burden; resetting is not, because it
does not.

This is a standing constraint on the project and it does not move with framing,
volume, or purpose. Recorded here so it does not need re-litigating.

---

## 3. The legitimate channels, ranked

### 3a. DOF Electronic Data Services — "Index/Image Retrieval" ★ the live lead

Research on 2026-08-05 confirmed this is a **named subscriber service, distinct
from the public viewer**, sitting on a separate path (`/EDS/`) from the public
document search (`/DS/`). It has its own Web Administration Interface for
subscription management and an electronic payment path.

That separation matters enormously: **a subscriber retrieval service is designed
for volume and would not be governed by the public bandwidth notice.** The
notice itself points here — *"If you need large amounts of data, please contact
the City Register to learn about our subscription data services."*

Published price: **$8,670 / 30 days citywide** (a 90-day tier also exists);
$1,820 / 30 days Manhattan. Against 17.0M documents that is **$0.0005 per
document**.

**What is NOT publicly known, and cannot be learned from the web** — the service
documentation sits on the blocked host and the fee PDF returns 403:

> **Does Index/Image Retrieval deliver bulk transfer of image files (FTP/SFTP,
> batch, or physical media), or only credentialed per-document retrieval?**

This single unknown decides the entire program:

| answer | consequence |
|---|---|
| bulk transfer | corpus in hand in 30 days for ~$8,670. Timeline met. |
| per-document only | the ceiling is real; fall to 3b/3c and stop testing it |

Ask it before price, before tiers, before anything. **212-487-6300.**

Secondary questions once that is answered: is there a rate ceiling on the
subscriber channel; is a one-time historical extract available separate from the
subscription; can they supply media if we ship drives.

### 3b. FOIL — Public Officers Law Article 6

Full draft in `FOIL_REQUEST_DRAFT.md`, scoped to the 15 envelope/encumbrance
classes (1,278,242 documents), citing §87(1)(b)(iii)'s limit of **actual cost of
reproduction** against the commercial subscription price. Costs a letter and
starts a 5-business-day statutory clock. Expect the "available in another form"
objection; worth testing anyway because the downside is being pointed back at
3a, which we are pursuing regardless.

Offer to supply drives — it converts a burden objection into a logistics detail.

### 3c. Licensed commercial aggregators

Organizations holding full or partial ACRIS image corpora, obtained through
licensed bulk channels: **DataTrace** (confirmed 2021 release of digitally
enhanced *pre-ACRIS* New York images plus indices — evidence a bulk market
exists and that even the microfilm era has been digitised), First American /
DataTree, CoreLogic, ATTOM, PropertyShark, Regrid.

Best suited to targeted volume rather than the full corpus; per-document pricing
typically makes 17M prohibitive but makes thousands trivial. Also the only
realistic route to **pre-1966 records**, which are not in ACRIS at all.

### 3d. Title company relationship

Title insurers hold standing bulk access as a condition of business and pull
chains of title, prior mortgages, easements and declarations as routine work
product. Legitimate at volume precisely because the volume is licensed. Practical
for deal-driven depth rather than corpus-wide breadth.

---

## 4. What we hold already, free and unlimited

**The complete index.** NYC Open Data carries every ACRIS master, legals, parties,
references and remarks record — 17.0M documents, parcel↔document mapping,
party names and roles — on Socrata, unmetered, on a different host that has
never blocked us.

This is not a consolation prize. It means **we already know exactly which
documents exist, which parcels they touch, who signed them, and in what order.**
The images add the *contents*. Everything about *selection, sequencing and
prioritisation* can be built and perfected today, corpus or no corpus.

---

## 5. What to build regardless of which channel wins — the real work

Acquisition is one phone call or one letter. **Processing is weeks of
engineering, and it is entirely ours.** Measured on commodity hardware:

| stage | rate | 16 workers | 64 workers |
|---|---|---|---|
| layout + fast OCR | 0.5 s/doc | 6.2 days | 1.5 days |
| careful OCR | 2.0 s/doc | 24.6 days | 6.2 days |
| OCR + full decode | 8.0 s/doc | 98.6 days | 24.6 days |

So the whole corpus decodes in **weeks**, for roughly **$9,000 all-in**
including media. Storage is ~$400 of mirrored drives, or ~$1,000/year in cloud
object storage — a rounding error, and *not* the constraint it was assumed to be.

### The architectural change this forces

**`fetch → decode → delete` must become `store → query`.** The delete rule exists
only because the images are borrowed. Eight parser bugs were fixed in a single
session on 2026-08-05, and because images were transient, **every document read
before each fix stayed mis-read** — only the transcriptions already made could
be re-checked.

With the corpus on disk, every parser improvement re-runs against everything.
That single change is worth more to decode accuracy than any other item on this
list, and it is the strongest technical argument for owning rather than borrowing.

### Pipeline requirements — built for 17M, not for 50/day

- **type-routed batch decode** — manifest in, per-type handler dispatch
- **parallel workers** over local files, where nothing is rate limited
- **checkpointing** — a run that dies at document 400,000 resumes at 400,000
- **the validators at scale** — metes traverse and closure, envelope
  conservation, the 22 audit checks, the 44 self-tests
- **quality sampling with printed denominators** — because, as this project has
  now learned repeatedly, **large N hides bugs**: a duplicate-BBL defect invisible
  at 98,000 rows failed loudly at 364. Never report a rate without its denominator.
- **positive-signal acceptance everywhere** — the recurring failure shape here,
  seen eight times, is *a check that reports success because it looked in the
  wrong place*. At 17M documents a silent-skip bug is undetectable by inspection.

---

## 6. Decision, in one line

**Make the call to 212-487-6300 and ask whether Index/Image Retrieval delivers
bulk transfer or per-document retrieval.** Everything else — cost, tier,
timeline, architecture — is downstream of that one answer, and no amount of
engineering substitutes for it.

Meanwhile, build the processing pipeline, which pays off identically under every
outcome.
