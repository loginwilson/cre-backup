# Agent system — roadmap

Three tiers. Fifteen functions. Five products.

    EXTRACTOR   touches the outside world     document -> claims       only tier that can be blocked
    RESOLVER    touches only the claim store  claims   -> settled claim
    DERIVER     touches only the claim store  claims   -> outputs, nothing durable

Puzzle: extractors cut the pieces, resolvers assemble them by function, derivers
let a person see what it is.

---

## THE FUNCTIONS, LAYERED

**Spine** — everything keys to these, build first.

    IDENTIFY   which parcel, and its identity OVER TIME (lineage, merger, subdivision,
               reapportionment, condo conversion). ⚠ not identity — identity-over-time.
    PARTY      humans and entities. An AXIS, not an attribute. Every other function
               emits parties; this one resolves them.

**Record** — resolved from documents, every claim carries a proof crop.

    TITLE · ENCUMBER · ENVELOPE · ENTITLE · PERMIT · ASBUILT · PARCEL · OCCUPY
    CAPITAL · DISTRESS

**External** — no document to crop; confidence comes from source + vintage instead.

    COST · CONTEXT · VALUE (market half)

⚠ Do not build one claim schema and then discover a third of your functions cannot
satisfy it. External claims need a different evidence model from day one.

**Products are views, not functions.**

    Property Info   IDENTIFY · PARCEL · ASBUILT · TITLE
    Opportunity     ENVELOPE − ASBUILT − ENCUMBER · ENTITLE · DISTRESS · CAPITAL
    Development     PERMIT · ASBUILT · CAPITAL · PARTY, ordered in time
    Comparables     VALUE · OCCUPY · ENVELOPE
    Contacts        PARTY  ← the only product keyed by person, not parcel

---

## PHASE 0 — WRITE THE REGISTERS   (days, transcription not discovery)

1. **Output register.** Every row the card shows. You already have it — the two card
   screenshots are the spec.
2. **Function register.** The fifteen above, layered. Done.
3. **Document register.** Per function, which documents answer it. Half-written
   already in `docs/sources/`.

Nothing gets built before these exist. Building decoders before knowing the outputs
produces decoders for things nobody displays.

---

## PHASE 1 — PROVE THE PATH ON ONE SLICE

**Goal is not value. It is proving the architecture before anything depends on it.**

    claim ledger      value · citation · proof_crop · as_of · decoded_at
                      · confidence · superseded_by · party_id
    one extractor     BIS PW1  (most mature trap list, working canary)
    one deriver       the developer contact row

**Canary:** job 320917503 doc 18 → Hale Everets · AUTHORIZED SIGNATORY ·
DOMINO A PARTNERS LLC · (718) 907-5800 · hevorets@twotreesny.com ·
45 Main Street 12th Floor Brooklyn 11201 · signed 8.13.25.

**Success test:** change a derive rule and see the answer change instantly with
zero re-fetching. If that does not happen, the tiers are still fused.

⚠ **Why this test matters.** 2026-08-07 the stage rule was changed five times and
each change forced a re-pull of 7.4M permit rows, ~15 min per run, because derive
logic was fused to extraction in `devbatch.py`. Under the tiers all five iterations
are seconds and zero API calls.

---

## PHASE 2 — THE SPINE

    IDENTIFY   lot lineage over time. A job filed 2014 keys to a lot that no longer
               exists (280 Kent: lot 1 → lot 3, reapportioned 7/17). Every function
               silently loses records at the lineage boundary and the loss is
               invisible because filters return clean-looking output.
    PARTY      first-class entity with its own id. Claims point at party_id, never
               at a name string — otherwise the contacts product cannot answer the
               only question it exists for.

⚠ **People-primary, entities as edges.** Measured 2026-08-07 on the 2021+ cohort:
person name matches at 24.5%, entity at 5.1%. SPEs are minted per deal and die;
people recur. Most CRE data is organised the opposite way and it is why entity
matching fails.

---

## PHASE 3 — CITYWIDE PAYERS   (feeds only, no documents, no rate limits)

These reach all ~1.16M parcels. Development reaches only the 316,585 with a filing.

    DISTRESS   arrears · liens · ECB · HPD violations, and the TRAJECTORY.
               Rising distress on a long-held asset is the strongest sell signal.
    OCCUPY     rollover schedule · vacancy · regulated unit count.
               Highest-frequency actionable output for a brokerage; nothing to do
               with development.
    TITLE      tenure, acquisition mode (arm's length vs deed-in-lieu vs inherited)
    CAPITAL    debt maturity, refinance history
    VALUE      assessment vs last sale vs comps → tax appeal

**Build these before widening the document tier.** They pay sooner, cover every
parcel, and have no Akamai in the path.

---

## PHASE 4 — WIDEN THE DOCUMENT TIER

    BIS ZD1              floor-area schedule (⚠ gross ≠ zoning: 951,971 vs 611,305
                         on the same form) + the applicant contact block
    DOB NOW PW1          different surface entirely — portal panels, not a scanned
                         form. Owner Information has NO contact fields; Statements
                         & Signatures is NOT §26.
    DOB NOW documents    per-filing list, sparse, concentrated on -I1
    ACRIS deed/mortgage  coordinate with the ACRIS chat rather than rebuilding

⚠ **Throughput is capped here and always will be.** Document decode is
navigation-paced and edge-limited. 316,585 folders will never be read this way.
The batch covers the city; the document tier covers a watchlist. Any product
promising citywide document-level depth is promising something the pipeline
cannot do.

---

## PHASE 5 — RESOLVERS

    OWNERSHIP   deed → mortgage → PW1 §26 → search, IN THAT ORDER.
                Internal transfers excluded as ownership events but read for the
                c/o line. §26 valid only if it post-dates the last arm's-length
                deed. Profiled output.
    ENVELOPE    ⚠ ENVELOPE − ASBUILT is WRONG. It must be
                ENVELOPE − ASBUILT − ENCUMBER. A lot showing 40,000 SF unused FAR
                that already sold its rights via a ZLDA has ZERO. Remaining-rights
                without ENCUMBER produces confident wrong numbers.
                Not additive either — split districts need ZR 77-22.

**Resolvers are pure functions over stored claims.** Change a precedence rule and
re-run over the whole corpus with no network calls. That is the entire payoff of
keeping the expensive tier thin.

★ **The ZD1 is the envelope deriver's canary at scale.** It is the developer's own
computation of the same number, signed by an RA and accepted by DOB. Compare
computed envelope to the filed figure on every job that filed one; disagreements
are either a rules bug or a real anomaly worth a call.

---

## PHASE 6 — MONITORING LANES

Feeds detect, agents decode. Never re-read folders on a schedule.

    LANE                WATCH SIGNAL                       DISPATCH
    DOB NOW PW1         new job_filing_number              new development enters
    BIS PW1 / ZD1       new scan datetime in folder        an amendment landed
    OWNERSHIP           new deed or mortgage in ACRIS      owner may have changed
    DISTRESS / OCCUPY   feed delta                         recompute, no agent needed
    PARTY               any new claim naming a party_id    ← lead generation

★ The party lane inverts monitoring: parcel lanes ask "what changed here", the
party lane asks "what did this person do lately". A new §26 under a new SPE is not
a data update, it is a lead.

⚠ **Reconciliation lane.** When two agents disagree, that is not an error to
suppress — it is the signal that a sale or restructure happened between two
documents. Surface it; do not let the newer source silently win.

---

## CROSS-CUTTING RULES

**Every agent ships with a canary.** A known document with known values that it
re-verifies. The trap list is a dependency on a government site's current
behaviour; BIS is already being replaced. The canary fails loudly instead of the
agent quietly returning nothing.

⚠ **The failure that motivates this:** 2026-08-07 a folder sweep reported
"54 processed · 49 no-folder · 0 errors" — a clean-looking 91% coverage collapse
that was entirely HTTP 403s. **Record HTTP status; treat non-200 as a distinct
outcome from an empty result.** A parser that only asks "did I find the thing"
converts every block into a negative observation.

**Blank ≠ absent.** §26 is frequently empty on any given PW1. Walk the series
until populated; only report not-found after exhausting it. Same for §9D CRFNs,
same for ZD1 figures.

**Three dates on every claim.** signature/effective · document received ·
decoded. The contact is valid as of the signature, not the scan.

**Derivers write nothing you treat as truth.** Materialise for speed if needed,
but every derived value must be reproducible from the ledger. The moment
`stage = construction` is stored as fact you own cache invalidation forever.

**Superseded claims stay.** That is what makes the ownership timeline queryable
instead of just the latest answer — and what let a crop correct an inferred
phone number (718-222-2503 → 718-907-5800) without losing the audit trail.

---

## WHAT NOT TO DO

- **Do not migrate the existing Supabase.** Define the claim ledger, write only new
  decodes into it, leave the old schema read-only until the new path beats it on a
  parcel checkable by hand.
- **Do not rewrite the trap knowledge.** Forty-odd measured traps across
  `DOB_TRAPS.md`, `PW1_SECTION26.md`, `JOB_OWNER_MODEL.md`,
  `CONTACT_ARCHITECTURE.md`, `docs/sources/`. Migrate them into agent definitions.
  That is the asset and the moat; it does not get re-derived.
- **Do not split agents by job type or borough.** Test: would they share a trap
  list? NB and DM use the same PW1 — one agent, job type is a filter. Manhattan
  and Queens use the same form — one agent, borough is a partition for throughput.
  Splitting gives you five copies of the same bug.
- **Do not build composite scores.** "Development potential 87" cannot be defended
  on a phone call. "You are 40,000 SF under your as-of-right envelope per your own
  ZD1" can.
- **Do not derive restatements.** If it is a field on a document, that is
  extraction. Every valuable derivation is a comparison across time or across
  functions.

---

## BUILD ORDER, COMPRESSED

    0  registers                    days
    1  ledger + BIS PW1 + 1 deriver prove the path, canary 320917503
    2  IDENTIFY(time) + PARTY(id)   the spine
    3  DISTRESS · OCCUPY · TITLE    citywide, feeds only, pays first
       · CAPITAL · VALUE
    4  ZD1 · DOB NOW · ACRIS        widen documents, watchlist-scoped
    5  OWNERSHIP · ENVELOPE         resolvers, pure over the ledger
    6  monitoring lanes             feeds detect, agents decode

The risk to manage is scope creep — rewriting to parity and never shipping. Rule:
nothing migrates without a canary that fails loudly, and the app keeps reading the
old outputs until the new path wins on a parcel you can check yourself.
