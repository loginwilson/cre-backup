# One parcel, every rung — and what it says about scaling

Queens **Block 52 Lot 1** · 11-55 45 Avenue = 44-74 21 Street = 44-80 21 Street
= 1155 45 Avenue · BIN 4430575 · 1917 (PLUTO) / **1914 (I-card)**. Run 2026-08-06.

## THE RESULT

**129 structured events, 1993 → 2025. IN SCOPE: ZERO.**
No new build. No conversion. No enlargement. No demolition.

Thirty-two years of maintenance — telecom antenna swaps, apartment-by-apartment
refurbishments, sidewalk sheds, a Dunkin Donuts fit-out.

**Its only development event is the 1914 new building plan, and that exists
nowhere except the HPD I-card.** Filed 6-17-14, approved 6-24-14, certificate
issued 5-28-15. Every structured feed on the ladder is silent on it, because
every one of them starts after 1989.

★ **That is the case for the pre-1989 layer, made concrete on a real parcel.**
A decoder that starts at BIS reports this building as having no development
history at all.

## WHAT THE WALK GAVE ANYWAY (all out of scope, all useful)

* **Ownership chain**, from permit owner fields: BANBI/BAMBI REALTY CORP
  (1993–2014) → 44-74 21ST STREET LLC / 44-74 21 STREET REALTY LLC →
  KARSTONIS REALTY, plus "BAMBI REALTY, CORP **C/O AAG MGMT**".
* **Contractor + phone on every permit** — Arrow Mechanical, Chois Contracting,
  Master Fire Prevention, Snee Construction, Home Tech Interiors, Trif General.
* **Tenanting** — Dunkin Donuts fit-out 2014, sign permits under "KEW DONUT".
* **Telecom tenancy** — AT&T antenna filings 2001 → 2023, an income stream
  visible only through DOB.

## ⚠ FOUR TRAPS THIS PARCEL EXPOSED

1. **`ipu4-2q9a` CONTAINS DUPLICATE ROWS.** Job 400353620 appears twice —
   identical job, sequence, type, subtype, status, BIN — differing **only in
   date format** (`1993-03-03` vs `03/03/1993`). Citywide: **88,238 rows (2.21%)
   are ISO-dated**; on the sampled block every ISO row duplicated a slash row
   exactly. **Dedupe on (job, permit_type, permit_subtype, permit_sequence)**;
   the published 3,989,787 is inflated.
2. **The two permit feeds OVERLAP, they do not abut.** `bty7-2jhb` (1989-2013)
   and `ipu4-2q9a` (≥1992-2022) return the same permits for 1993–2013. The
   ladder diagram implies a handoff; it is a double-count.
3. **BANBI vs BAMBI REALTY CORP** — the same owner, two spellings, in the same
   feed. Entity resolution cannot be exact-match on owner name.
4. **Dwelling units are inconsistent across filings**: 20 · 24 · 26 · 27 · 45 ·
   46 · 48 on one BIN. Whatever the cause (two buildings on the lot, or filers
   stating whatever suits), **DU from a filing is a CLAIM, not the unit count.**

---

# WHAT EACH RUNG ACTUALLY GIVES

| rung | keyed on | what it yields | document |
|---|---|---|---|
| **HPD I-card** 1914→~1985 | HPD buildingid ← BIN/BBL | NB plan no. + **filed / approved / certificate-issued dates** · alteration plans w/ dates · legal occupancy · lot size + type · unit mix by room count · per-storey counts · stores · **rents** | PDF, per building, **web only** |
| **1940s tax photo** 1939-41 | **block + lot** | what physically stood there in 1940 | image, per lot |
| **1980s tax photo** 1982-87 | **block + lot** | what stood there ~1985 | image, per lot |
| **bty7-2jhb** 1989-2013 | boro+blk+lot (UNPADDED) | job_type · permit type/subtype · permittee + phone · **owner name + mailing address + phone** | none |
| **ipu4-2q9a** ≥1992-2022 | boro+blk+lot (padded) | permittee + **direct phone 99.6%** · superintendent · owner name | none |
| **BSA** 1998→ *(Chat 3)* | boro+blk+lots | **ZR section relied on** · grant/deny · conditions binding the land | **PDF, 100%** |
| **ic3t-wcy2** 2000-2025 | boro+blk+lot (padded) | job type · zoning district · **zoning sqft (100% from 2009)** · **enlargement sf** · DU · height · applicant · owner name | route to B-Scan |
| **B-Scan** 2008→ | job + scancode | **PW1 §26 developer name/address/phone/e-mail** · §25 seal + signature · §12 zoning + **tax-lot roster** · PD1 metes and bounds · ZD1 | **PDF per scancode** |
| **DOF DAB** 2008→ | BBL | lot lineage + **CRFN (49%)**, DOB job (8.3%, 24.5% on apportionment) | none |
| **DOB NOW** 2016→ | boro+blk+lot (unpadded) | filings + **portal Zoning Information**: districts **with per-district area**, lot area, **street legal width**, yards, pre-1961 flag, zoning-lot-certification flag, `Auto Populated` provenance | portal Documents tab |

**The pattern:** everything before 1989 and everything below the form line is a
**document**; everything between is a **feed**. The feeds give you *that it
happened, when, and who was paid*. The documents give you *the envelope and the
principal* — and those two are what no feed has ever carried.

---

# HOW TO SCALE — the scope filter IS the document budget

**Structured pass: already sized, runs wholesale.**

    scoped rows   2,477,371        scoped jobs   848,935
    off-spine rows  145,661   <- lot-lineage loss, investigate not ignore

Five feeds, filtered server-side to DM/NB/conversion/enlargement, joined in
memory against the 1,175,952-parcel spine. No per-parcel calls. Minutes, not days.

**Document pass: gated, and the gate is the scope.**

★ **Only open a document for a parcel with an in-scope event.** Queens 52/1 has
zero — so it costs **zero document fetches**, and its 129 maintenance events are
answered entirely from feeds. That is the whole scaling mechanism: most parcels
never earn a document.

Then three further gates, each measured:
1. **Originals only** — `doc 01`. Amendments restate nothing (0 of 63,293).
2. **Latest scanned round only** — the folder listing gives `Form ID · Doc No ·
   PAA · DATE SCANNED · SCAN CODE`, so the operative PW1 is identifiable
   *before* opening anything. Job 421843884 had three same-day rounds.
3. **Last page only** — §26 is the last page of the PW1 (page 5 of 5 proven).
   One page render per job, not five.

**And two whole classes need no document at all:**
* **DOB NOW envelope** — the portal's Zoning Information section already carries
  districts with per-district area, lot area, street legal width, yards and the
  1961 flag. 2016→now needs no ZD1.
* **Contractor contact** — `permittee_s_phone__` on 99.6% of the permits feed.

**What remains genuinely document-bound:** the developer's identity and reach
(PW1 §26), the executed seal (§25), metes and bounds (PD1), pre-2008 zoning
floor area (ZD1), and everything before 1989 (I-card, tax photos).

## Order of work

1. Dedupe `ipu4-2q9a`, and de-overlap it against `bty7-2jhb` — before any count
   is quoted.
2. Run the structured pass over the spine; emit facts for in-scope events only.
3. Resolve the 145,661 off-spine rows through DOF lineage.
4. Rank the in-scope parcels; open documents down that ranking, last page first.
5. I-card + tax photo lookups only for parcels whose history starts before 1989.
