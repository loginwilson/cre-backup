# Isolated draft notes for framework v1-B

Written before exposure to Extractor A's draft or reasoning. These are not settled rules; they identify where this draft is vulnerable and what evidence should be sought when it is reconciled or tested.

## Least-confident boundaries

1. **One clause, multiple functions.** I chose one event per independently changed function with a shared group id. That handles a mortgage as Capital plus Encumbrance and a facade easement as Encumbrance plus Envelope, but it risks double-counting when a physical restriction is merely descriptive of the burden rather than an independently matrix-relevant Envelope state.
2. **Assertions from administrative attachments.** I allow signed transfer reports and affidavits to create Value, Occupancy, or As Built ASSERT events when they state a present matrix field. This preserves useful assertions but may make event volume depend too much on attached forms. A stricter design could treat them as evidence fields on the principal transaction only.
3. **Named “subject to” burdens.** The deed module permits a present Encumbrance ASSERT for a specifically identified declaration/easement stated to burden the estate. That is defensible as a present assertion, but it can also be read as a historical recital whose current effect should remain unknown. This rule is likely to need examples that distinguish operative acceptance from boilerplate exception language.
4. **Zoning-lot certifications.** I classified a certification of present parcel composition/geometry as Identity ASSERT unless it grants capacity. A competing view is that zoning-lot composition is inherently an Entitlement state. The present choice avoids importing zoning law but may understate the economic function.
5. **Occupancy.** I separate lawful authorized use from actual use and permit an executed transfer report to support ACTUAL occupancy/use assertions. Transfer forms may describe property class rather than literal occupancy, so the threshold for “current use” needs pressure-testing on real variants.
6. **Filing as event date.** I permit filing date only when the act extracted is explicitly the filing or filing termination. UCC forms support that, but some recorded notices may have an operative legal effect by filing that the page never explains. Because outside law is prohibited, the draft would leave those dates unknown; that may reduce recall but is more auditable.
7. **Partial and conflicting dates.** The matrix uses connected components of overlapping date intervals. This is deterministic and refuses false order, but one broad year interval can bridge many precise dates into one uncertainty batch and conceal useful partial ordering.
8. **Fallback object keys.** Instrument-local group keys prevent accidental merges but can fragment two clauses that modify the same unnamed object. Merging them from matching parties, amounts, or parcels would be unsafe; the reconciliation needs to decide whether an explicit within-document anaphora rule is necessary.
9. **Parcel subset over indexed cover.** I let operative clauses override a cover's enumerated BBL list when they expressly narrow the act. The declaration survey made that necessary, but unit-to-BBL linkage can be ambiguous when the clause names units and only the cover supplies BBLs. The draft currently demands document-supported linkage rather than positional matching.
10. **State after assertion.** The matrix gives ASSERT events assertion basis but does not infer lifecycle ACTIVE. That avoids turning a certification into creation, yet may make a plainly existing physical condition look weaker than readers expect.

## Rules I expect to break first

- A consolidation, extension, and modification agreement that combines several debts, releases only part of collateral, advances new money, and states a consolidated maximum will stress event splitting, object identity, and quantity conservation simultaneously.
- A declaration with dozens of units, cross-easements, changing benefited/burdened roles, and exhibits that use different labels will stress the affected-set and same-BBL/different-scope rules.
- An assignment described as effective “as of” a past date but executed later, or an instrument with retroactive correction language, will expose whether date precedence needs an explicit retroactivity term separate from event date.
- A partial satisfaction or release that states a dollar reduction without stating remaining balance will test whether lifecycle and Capital/Encumbrance deltas stay local.
- A building-loan or construction instrument with committed amount, advanced amount, budget, project cost, and maximum lien on one page will test Cost/Capital/Encumbrance quantity typing.
- A permit, certificate of occupancy, appraisal, construction contract, or as-built survey may reveal gaps because the surveyed corpus is heavily weighted toward deeds, leases, liens, UCC filings, easements, and declarations.
- An incomplete or low-resolution image package will test whether provenance closure and package failure are practical for a mid-size reader rather than merely correct on paper.
- A multi-parcel transfer with stated percentage interests that do not explicitly say they allocate consideration will test whether NOT_DERIVABLE is applied consistently instead of silently multiplying totals.

## Decisions I could argue the other way

| draft decision | credible alternative | why the alternative may win |
|---|---|---|
| Emit linked events for every independently affected function. | Choose one primary function and encode secondary effects as typed terms. | Fewer events reduce duplication and reader burden; downstream consumers may not need both columns. |
| Treat full sale price and assessed value on an executed transfer report as linked Value ASSERT events. | Keep them as quantities attached to the Title transfer. | They are transaction metadata rather than a separate legal act, and ASSERT events may overstate their independence. |
| Treat certified zoning-lot composition as Identity. | Treat it as Entitlement, or linked Identity plus Entitlement. | In practice zoning-lot configuration governs development capacity even when the document does not quantify or transfer it. |
| Use only the explicit operative unit subset when a declaration cover lists a larger condo BBL set. | Fan to every indexed BBL and mark four as directly changed. | A declaration amendment may bind the whole condominium even when only four unit appurtenances change. |
| Split a corrected mortgage maturity into linked Capital and Encumbrance events only if both obligation and security terms are expressly changed. | Always reflect a mortgage modification in both functions. | The lien may incorporate the note's maturity by reference, but that conclusion may require outside contract doctrine. |
| Treat same-day unsequenced changes as simultaneous conflicts on the same field. | Use page order or event order as a deterministic last-wins tie-break. | A total order is simpler and may match drafting sequence, but it invents legal precedence absent express text. |
| Keep undated events outside dated cells. | Fold them in a separate UNKNOWN-DATE row before or after dated rows. | Excluding them preserves temporal honesty but means the main matrix omits document-supported state changes. |
| Let signed property-use fields create Occupancy assertions. | Never create Occupancy without a governmental occupancy instrument or explicit narrative of actual occupants. | Transfer-report use codes can be administrative categories and could be mistaken for actual or authorized occupancy. |
| Let the filing date operate for a UCC filing event. | Leave event date unknown unless the form states its legal effectiveness. | The alternative applies the no-outside-law rule more literally, but loses the only document-supported date for the filed act. |
| Build uncertainty batches from connected overlapping date intervals. | Keep one row per distinct interval and attach pairwise “order unknown” relations. | Pairwise relations preserve more order information but make folding and equality comparison materially more complex. |

## Corpus and implementation risks

The survey contains no representative permit, appraisal, construction-cost agreement, certificate of occupancy, or full as-built survey. Rules for Permit, Cost, Value beyond transfer reports, As Built, and authorized Occupancy are therefore taxonomy-first rather than corpus-hardened. The corpus is also drawn from a narrow recording period and may not expose later form designs or scan artifacts.

The framework is written for a mid-size instruction-tuned reader, but its determinism depends on accurate clause grouping, visual reading order, and typed path generation. Those tasks are easy to describe and hard to execute consistently. The first blind extractions should measure not only final matrix agreement but intermediate divergence in evidence atoms, candidate acts, object keys, and affected BBL sets; otherwise an apparently matching cell can hide compensating errors.
