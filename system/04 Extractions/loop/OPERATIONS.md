# OPERATIONS — the plumbing the loop runs on

> This file is operational only: paths, tools, isolation, reporting. It says
> nothing about how to extract a document or what the framework should
> contain. That is yours, and deliberately not seeded here.
>
> The operative specification is **`D:\CRE Decoding System\04 Extractions\TRAYCER.md`**.
> Read it in full before you do anything. Where this file and TRAYCER.md
> disagree about the work, TRAYCER.md wins. Where they disagree about
> mechanics, this file wins.

---

## 1 · WHO IS WHO

| | |
|---|---|
| **A** | Claude Code. A peer. |
| **B** | Codex. A peer. |
| **orchestrator** | agent `663740bc-5dde-4f8f-aa2a-e422380ab12c`, "CRED Preparation". Issues document ids, publishes outputs at reveal, keeps the hash ledger, runs the fresh-context checks in Block 3d, arbitrates when you deadlock. |

Neither of you is senior. Neither defers. The orchestrator is not a tiebreaker
you can appeal to instead of arguing from the document — it rules only on
questions TRAYCER.md gives no procedure for, and it rules once, in writing.

## 2 · THE ISOLATION RULE — READ THIS TWICE

From the moment a document id is issued until the orchestrator tells you the
round is revealed, you are blind. Concretely, **you may not**:

- read, list, glob, stat or open anything under the other agent's directory
- call `traycer_list_agents`, `traycer_get_transcript`, or any tool that would
  show you another agent's session — **`traycer_get_transcript` would hand you
  the other agent's entire reasoning, and using it voids the round**
- send a message to any agent other than the orchestrator
- ask the orchestrator what the other agent found, is doing, or has decided —
  it will not answer, and asking is itself a signal you should not be sending
- read anything under `rounds\` for the current round

You may, freely: read your own directory, the framework, the document package,
`TRAYCER.md`, `DOCUMENT ACCESS.md`, and run the tools in `bin\`.

**If isolation breaks, say so immediately and plainly.** A contaminated round
that is reported costs one document. A contaminated round that is concealed
costs the credibility of every round after it. There is no penalty here for
reporting it — the round is simply dropped and restarted on a different id.
That is cheap. Nothing else in this workflow is.

## 3 · PATHS

```
D:\CRE Decoding System\04 Extractions\
  TRAYCER.md              the operative spec
  DOCUMENT ACCESS.md      the read contract — four real traps, all of them cost someone a day
  framework\              the deliverable. v1, v2, ... and the matrix spec
  rounds\<N>\A\ B\ joint\ published outputs — populated by the orchestrator AT REVEAL, not by you
  loop\
    OPERATIONS.md         this file
    bin\                  docpkg.py, dbq.py
    docs\<id>\            the document package — identical bytes for both agents
    A\   B\               your private working directory. Yours is the one you were bound to.
    ledger\               hash ledger and round log, orchestrator-owned
```

Write your blind-phase work to **`loop\<you>\work\`**. The orchestrator copies
it into `rounds\<N>\<you>\` at reveal. You never write into `rounds\`
yourself — that is what makes the sibling's output genuinely absent from the
place you would otherwise look for it.

## 4 · GETTING A DOCUMENT

The package is built centrally so that you and the other agent read the *same
bytes*. Do not build your own — a difference in render resolution between you
would show up as a disagreement about the document and teach the loop nothing.

```
python "D:\CRE Decoding System\04 Extractions\loop\bin\docpkg.py" <id>
```

writes `loop\docs\<id>\`:

| file | what it is |
|---|---|
| `registration.json` | the `recorded_details` blob for that row, pretty-printed |
| `page-01.png` … | one image per page of the stored PDF, 300 dpi |
| `MANIFEST.json` | sha256 of every artefact above |

**The renders are faithful.** One image per page of the stored PDF, in order,
nothing added, nothing dropped, nothing straightened or cleaned. What you see
is what is on the page.

**The documents have no text layer.** They are scans. Every character you cite
you read off an image with your eyes — there is no `pdftotext` shortcut, and
anything claiming to be extracted text is something you or a tool invented.

If a stamp, a marginal note, or a handwritten date is too small to read,
re-render it rather than guessing:

```
python bin\docpkg.py <id> --page 2 --dpi 900
python bin\docpkg.py <id> --page 2 --dpi 900 --rect 0.10,0.62,0.90,0.78
```

`--rect` takes `x0,y0,x1,y1` as fractions of page width and height. Zoom
renders land in `docs\<id>\zoom\` and are a reading aid — cite the page, not
the zoom.

## 5 · QUERYING THE DB

```
python bin\dbq.py --row <id>                     one row, resolved and readable
python bin\dbq.py --type "DEED" -n 30            sample readable rows of a type
python bin\dbq.py "SELECT id, pdf FROM navigation WHERE ... ORDER BY id LIMIT 50"
```

Read-only, `busy_timeout` preset. The guard refuses queries without `LIMIT`,
`LIMIT` without `ORDER BY`, and `LIKE 'RC_%'`. Those are not style rules:

- a 24M-row scan stalls WAL checkpointing and starves the reproduction lanes —
  measured 2026-08-29, a 0.14 s count took **112 s** and made the update board
  print a negative rate
- unordered paging silently drops and duplicates rows
- `_` is a single-character wildcard, so `LIKE 'RC_%'` is a full scan; the
  range form is `id >= 'RC_' AND id < 'RC\``

`--unbounded` exists. Use it when you have decided to, not to get past an error.

**Only rows with `pdf LIKE '%.pdf'` are readable.** `''`, `pending`, `absent`
and `imageless` are determinations, not files; a row can be fully processed
upstream and still have no image.

## 6 · REPORTING

You talk to the orchestrator and to nobody else.

**During a blind round, the only thing you send is `A DONE` or `B DONE`** —
that exact string, alone, plus the hash block in §7. Not a summary, not a
count, not "done, though the date rule gave me trouble." The channel passes
through a shared orchestrator; a headline from you is a hint to the other.

Outside blind rounds, talk normally: argue, object, ask.

**Escalate to the orchestrator when** a document is out of scope, the framework
has no procedure for something and you cannot write one without a ruling, or
you and the other agent have deadlocked. State the question, both positions,
and what each would cost. Do not escalate to avoid a hard call.

## 7 · THE HASH COMMITMENT

At `DONE`, and in the same message, post the sha256 of each file you produced:

```powershell
Get-FileHash -Algorithm SHA256 "D:\CRE Decoding System\04 Extractions\loop\A\work\*" |
  ForEach-Object { "{0}  {1}" -f $_.Hash.ToLower(), (Split-Path $_.Path -Leaf) }
```

The orchestrator records them, and re-verifies at reveal. A hash that changed
between commitment and reveal means a committed file was edited after seeing —
or after being able to see — the other table. That voids the round.

Ten seconds of work. It is the only thing that makes "we extracted
independently" a claim with evidence behind it rather than an assurance.

**Nothing is edited after `DONE`.** Not a typo, not a mis-sorted row, not a
number you realise on reflection is wrong. Corrections happen in Block 3, in
the open, with reasons — which is also where they become useful, because a
correction you argue for in front of a peer is evidence and a correction you
make quietly is not.

## 8 · WRITING

Write for the model that has never seen this conversation. That is the whole
test: not whether your rules are correct, but whether they are *followable* by
a reader with no context, no memory of why a rule exists, and no ability to ask.

Rules are decision procedures with stable, immutable ids. If two careful
readers could apply one and get different answers, it is not a rule yet. The
words "consider whether", "generally", "typically", "as appropriate" and "use
judgment" are all defects — each one is an instruction to interpolate, and
interpolation is indistinguishable from observation everywhere downstream.
