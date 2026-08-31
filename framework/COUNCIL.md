# Council protocol

Run this after every document. It is written down because the orchestrator's
context is finite and this step must not depend on remembering it.

## 0. Precondition

Every peer has written `loop/<X>/<doc-id>/table.md`. **Nobody proceeds until all
have sealed.** A peer that reads another's table before sealing its own is no longer
independent, and the round is void.

Record each table's sha256 before widening anything. That is the proof the reading
was sealed first.

## 1. Widen

Each peer's workspace currently holds only its own folder. Add the other peers'
folders — `loop/A`, `loop/B`, `loop/C`, `loop/D`.

They read **each other's actual tables**, never the orchestrator's summary. The
orchestrator is deliberately out of the middle here; a summary is a distortion and
the whole point of the council is to remove it.

## 2. The brief each peer receives

Send **identically** to all peers:

> The other tables are now readable at `loop/<X>/<doc-id>/table.md`.
>
> **This is not "compare tables." At least one table here is wrong somewhere. Find
> it.** Asked to verify, a reader confirms; asked to refute, it looks. You are
> looking.
>
> **Read their tables, not their reasoning.** If a peer explained itself, ignore the
> explanation and re-derive from the document. Reasoning anchors.
>
> **Agreement must be paid for.** For every row you accept from another table, state
> what you independently checked — not *"I agree with E4"* but *"E4: re-read page 2,
> the quote is the whole operative clause."* Agreeing costs the same as disagreeing.
> A bare "agreed" is not a contribution.
>
> **Sort every disagreement into one of two piles and say which:**
>
> - **FACT** — *what does the page say?* Settled by looking harder, not by arguing.
>   Zoom and cite pixels. If the image cannot settle it, say so.
> - **JUDGMENT** — *how should this be represented?* Argue it here.
>
> Write to `loop/<X>/<doc-id>/challenge.md`. Then report: how many challenges you
> filed, how many rows you accepted after checking, and which single disagreement you
> think matters most.

## 3. Route the disagreements

| pile | goes to |
| --- | --- |
| **FACT** | the **referee** — a fresh context with the images and the zoom tool, which made no claim. Write the competing readings to `loop/claims/<doc>-<topic>.md` **anonymised and shuffled**; strip every name. Its workspace excludes all peer folders so it cannot attribute a claim even if it tries. |
| **JUDGMENT** | back to the peers who split, to argue directly |

About two-thirds of divergences have been FACT. Arguing those produces two confident
opinions and no answer — the flourish-vs-strike question was settled by zooming to
900 dpi in under a minute.

## 4. Coverage probe

**After** the peers seal — never before, or it contaminates them.

One agent reads the same document by **function sweep**: one function across all
pages, then the next. Its only question is *what did every peer miss?*

This measures framework **coverage**. Peer disagreement measures framework
**ambiguity**. Two different defects; do not confuse them in the log.

## 5. Framework changes

Proposed changes go to the **skeptic**, on a separate context, which rules:

- **ACCEPT** — a named document forced it, and it is the smallest thing that fixes it
- **REJECT** — no document named, or the document does not show what is claimed
- **NARROW** — real, but the wording covers more than the evidence supports

**A rule must name the document that forced it.** v2 reached 129 KB by answering
questions no document had asked.

## 6. Narrow again

Return every peer's workspace to its own folder before the next document is
dispatched. **Blind while reading, open while arguing.** Forgetting this silently
ends the experiment — every later round would be contaminated and would still look
fine.

## Checklist

- [ ] all peers sealed, hashes recorded
- [ ] workspaces widened
- [ ] identical challenge brief sent to all
- [ ] FACT disputes anonymised into `loop/claims/`
- [ ] referee ruled
- [ ] JUDGMENT disputes argued by the peers who split
- [ ] coverage probe run
- [ ] framework changes through the skeptic
- [ ] **workspaces narrowed**
- [ ] `python bin/tablecheck.py` over every table
