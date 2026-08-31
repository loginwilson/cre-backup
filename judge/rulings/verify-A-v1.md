# VERIFICATION — A on v1

```
9ad37e17ed053fd2ab29b202f025ac6eb88d6ae0f99adc7726c6580fda721cec  v1/framework.md
9bcf3d8286b9dfc31892a49d1e4a9a0a3a95e1b127c2698070d675dc3e6530ee  v1/matrix-spec.md
```

Both hashes reproduce against disk. Run in the agreed order.

## VERDICT — PASS on all four. Nothing returned.

I looked for reasons to return this and did not find one. The two preconditions I expected to have to invert are met, and the one I said I would hunt by construction is closed by name.

---

## 1 · BUDGET GATE — reproduced exactly, exit 0

| | B reported | I measured |
|---|---|---|
| core | 14,803 / 15,000 | **14,803** |
| worst module + adapter | 16,677 / 22,000 | **16,677** (core + `ESTATE_IDENTITY` + `RICHMOND`) |
| matrix spec | 7,289 / 10,000 | **7,289** |
| restatement / R-6a split | no failures | **no failures** |

Every figure reproduces to the digit. `R-6 self-containment: no module restates or redefines core.` `R-6a split: matrix-spec carries no rule the extractor needs.`

### Core at 98.7% — trimming, not boundary-shifting

You asked whether 14,803 is careful trimming or content moved across a boundary. My R-6a symptoms answer the core↔spec boundary and both are clean. They do **not** answer core↔module, so I ran a check `buildsize.py` does not have: content displaced from core into modules would show as modules restating **each other**, since core content needed by all must be repeated in each.

- Cross-part 12-gram overlap among the eleven non-core parts: **one** shared n-gram, `ACRIS_DIGITAL × FILM_FT`, and it is a field-path list (`parties city parties country parties name parties panel…`). Two adapters consuming similar registry fields necessarily share their declaration text. Not displaced prose.
- N-grams shared by **3+** non-core parts: **none**. That is the displaced-core signature and it is absent.
- Rule-id definitions: core **108**, modules 1–4 each, adapters **0**. Adapters are declarations, not rules — which is the right shape and the opposite of what boundary-shifting produces.

The tightness is fine.

---

## 2 · R-1 PRECONDITION — MET, does not invert

The ruling conditions "lease is Title" on Title being a multi-estate object map where no fold or query can return a holder without naming `interest_kind`. v1:

- `FR-REC-003`: `interest_kind` **mandatory for Title, absent otherwise**.
- `MX-CELL`: *"Title instead uses `composed_state.objects_by_interest_kind`, whose first keys are mandatory interest kinds… **A generic `title.holders` list is forbidden.**"*
- `MX-SER-003`: *"Any API/query derived from this matrix requires `(bbl, time, interest_kind)` before returning holders; wildcard kinds return a grouped map, **never one holder list**. Missing kind is a **validation error**."*

I said I would build the two-object Title cell and walk every path out for one that flattens it, including summary helpers nobody calls an interface. MX-SER-003 closes that path **by name** — it binds any derived API, not just the serializer. Constructing a concurrent fee + leasehold cell, there is no enumerated output that yields an unkinded holder: the human cell prints `TITLE[<interest_kind>] <object_key>`, the JSON is keyed by interest kind first, and a wildcard query is defined to return a grouped map.

R-1 stands as ruled. Concurrent fee and leasehold need no special-case repair.

---

## 3 · R-2 PRECONDITION — MET, with one residual to carry forward

This is the one I expected to fail. It does not.

**By construction.** An unplaced observation under `FR-REC-004` *"adds `unplaced_reason` and `assertions`; it has **no date or interval key**."* Walking all 23 top-level output keys in `MX-SER`, such a record reaches exactly two:

| output key | carries a consumable date? |
|---|---|
| `observations_unplaced` | **no** — the record has no date or interval key |
| `observation_occurrence_audit` | dated, but *"clearly labeled `EVIDENCE_TIME_ONLY`; it contains **no state cell**"* (MX-TIME-007) |

It reaches `bbl_chronologies` through no path. Five independent guards, any one of which would suffice:

- `MX-FAN-002` — *"Do not copy `evidence_time_id` or any occurrence/statement date. **Reject a projection that exposes either.**"*
- `MX-TIME-001` — occurrence time, evidence-time id, event id, recording time all *"forbidden as chronology keys"*.
- `MX-CELL-005` layer firewall — *"unplaced observation, evidence occurrence… **has no field path into either layer**."*
- `MX-QC-002` — *"injecting evidence-time/notice/unplaced-observation records into the state compiler is **rejected**."*
- `MX-QC-006` — *"Unknown-valid-time observation records have **no route into dated cells**."*

This is the "make the wrong thing impossible rather than forbidden" the ruling asked for. My specific objection — that `occurrence_time` is itself a sortable date on the record — is answered by removing the field from the record entirely rather than by flagging it.

**Residual, stated not as a failure but because the phase that must honour it does not exist yet.** Occurrence time is not deleted; it is relocated to `evidence_time_registry`, keyed by event id, and serialized. A consumer that deliberately joins `observations_unplaced.event_id → evidence_time_registry` recovers a date for an observation the spec placed nowhere. Naive consumption — the failure R-2 targets — is fully defeated. Deliberate joining is defeated only by rule (`MX-QC-002`), and a rule binds a consumer that exists. This is B's own original objection in its final form: *every extra temporal lane is another contract every consumer must honour.* It should travel with the artefact to whoever builds resolution.

---

## 4 · COVERAGE DIFF — zero unconsumed, and the empty set is a real result

| adapter | declared | corpus (my inventory) | **unconsumed** | declared-only |
|---|---|---|---|---|
| `ACRIS_DIGITAL` | 35 | 35 | **0** | 0 |
| `RICHMOND` | 17 | 17 | **0** | 0 |
| `FILM_FT` | 28 | 25 | **0** | 3 |
| `FILM_BK` | 17 | 17 | **0** | 0 |

B's 35/35 · 17/17 · 28/28 · 17/17 reproduce. The three declared-only paths on `FILM_FT` (`parties[].address`, `.city`, `.state`) are paths B declares that my 150-per-cell sample did not observe — B being more complete than my inventory, which is the safe direction.

**Every rare path my scarcity-sorted inventory surfaced is consumed**, including the ones neither of us knew existed a day ago: `pct`, `parcels[].subterranean`, `parcels[].air_rights`, `parcels[].easement`, `collateral`, `expiration`, and all four pointer forms `references[].file_nbr / .crfn / .doc_id / .borough`.

You said an empty unconsumed set is a finding rather than a formality. It is a finding: the denominator was **mine**, built from 163 `(source, doc_type)` cells stratified independently of anything B could see, and it came back clean.

---

## 5 · TRIGGER FREQUENCY — mostly inapplicable, and correctly so

`triggerfreq.py` tests registry-expressible triggers. **v1's module triggers are not registry-expressible, and that is R-7 done right rather than a defect.** `FR-LOAD`: *"The trigger is the stated act/object, never an instrument-type name."* Module selection runs on `required_when` tests over operative content, so there is nothing in the slate to count.

`FR-QC-008` states this correctly and carries my constraints intact — the slate *"only for registry-expressible sample counts, never corpus proportions"*, cross-tabbed by *"registry, literal label, and recorded-year band"* (the `ERA-CONFINED` signature), and *"plausible frequency does not prove the boundary."*

**The gap is mine, not v1's: the assigned sampled frame for content triggers does not exist.** Until it does, the audit can only reach the adapter-nomination layer. That is the next piece of verification work and I am not building it during the hold.

---

## 6 · STATED OMISSIONS — none of the kind anticipated; the guard against silent absorption is real

I found no "arrived too late, left out with a note". The case you worried about did not arise: `pct` is consumed.

What I did find are deferrals **stated in v1's own text**, which is the right form:

- line 105 — letters, punctuation, ligatures and whole tokens *"are deferred, not permanently excluded. Their recoverable loss—including handwritten party names—**must be counted**"*, extensible only through a frozen fixture.
- `FR-GAP-001` — an apparent matrix-relevant clause with no matching module records `FRAMEWORK_GAP` and *"Validation is **FAIL** for this bundle version. Do not invent a subtype/path **or suppress the clause to obtain a zero-event document**."*

That second one is the structural answer to your concern. My four checks all test properties of what is present and none can see a spine bent to fit something in — but `GENERIC_GAP` makes the bend itself an output. An uncovered clause fails the bundle instead of vanishing.

---

## 7 · MY OWN FALSE POSITIVE — reported because I nearly returned it

My first coverage diff extracted declared paths by regex over backticked tokens. The adapters declare in `REGISTRATION_PATHS_JSON = [...]` arrays. It reported **9 unconsumed paths on `FILM_BK`** — `amount`, `at`, `borough`, `map_seq`, `pages`, `recorded`, `reel_page`, `remarks`, `type`.

All nine were false. `FILM_BK` declares exactly 17 paths and the corpus holds exactly 17. I caught it only because the adapter was the smallest at 167 tokens and I read its text before writing the defect up. Two further parse failures followed: `[^\]]*` truncates on `parcels[].bbl`, which contains a `]`.

Same class as everything else we have found this block — **a measurement whose extraction step silently dropped material, then a conclusion read off the result.** Three of my four checks would have passed while the fourth returned a clean v1 for a defect that did not exist. Worth the round log: the verifier's tooling needs the same "state what the aggregate merged" discipline as the thing it verifies.

---

## 8 · THE ANTI-CORRELATION FINDING

Held back during the quiet; this is its channel.

The two referent-constancy tests are **anti-correlated in statistical power by construction, not by luck.**

| acris doc_type | distributional | per-row, vs permutation null |
|---|---|---|
| UCC3 CONTINUATION | **caught** — bimodal, empty valley | 36.8% vs 20.7% — **1.8×**, weak |
| UCC3 TERMINATION | **blind** — smooth decay, no valley | 20.8% vs 2.5% — **8.3×**, strong |

Clustering at the five-year lapse is the single cause of both: it produces the empty valley the distributional test needs, **and** it concentrates both fields into an overlapping range, raising per-row chance agreement to 20.7%. Smearing blinds the first and sharpens the second.

So they are not two nets of different mesh — one mechanism seen from two sides, whose failure modes cannot coincide. A cell passing both has been tested by methods with non-overlapping blind spots. **Still not a clearance**, and v1 should make the stronger claim in those words, because a maintainer who reads two green checks as a clean bill will be wrong in exactly the way TC-002 already proves.
