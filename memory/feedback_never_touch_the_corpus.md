---
name: feedback-never-touch-the-corpus
description: "Extraction reads a db and opens the files it points to — never a source, never a directory walk over the acquisition store"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9b84c0a7-ebf6-4272-98a0-50bc0177ee2b
  modified: 2026-08-31T02:46:10.864Z
---

Extraction never accesses a source. It reads the `navigation` db (`mode=ro`,
`busy_timeout`), takes the stored `pdf` value, resolves it with
`corpus_paths.doc_path()`, and opens that file. Nothing else. This binds the
orchestrator and every extractor equally.

Never run `acris_reproduction.py`, `fleet.py`, or any acquisition script. Never call
`doc_store_dir()` or hand-join a root. Never `rglob` / recursive-scan under
`02 Acquisitions`.

**Why:** the document store sits on a **USB volume the register lane writes to
continuously**, so a heavy reader contends with the writer and collapses its
throughput — no network call required. On 2026-08-30 I ran a corpus-wide `rglob`
over the acquisition store for 3.5 hours plus a full recursive scan of
`D:\CRE Decoding System` while a live registration pull ran; the pull went to zero.
Separately, a second process against ACRIS is the condition that gets the account
banned. `DOCUMENT ACCESS.md` §6 had already measured the contention (0.14 s → 112 s)
before I did it.

**How to apply:** use `docpkg.py <id>` and nothing else to reach a document. Before
running any script that walks a filesystem or opens the db, ask whether it stays
inside that one path — "it's only reading" is not a defence, because scope is the
constraint, not intent. If the tool you need doesn't exist, say so and stop rather
than improvising one. The sanctioned path was already correct every time this went
wrong; the failure was improvising around it. See
`04 Extractions/DOCUMENT ACCESS.md` (the contract) and
`04 Extractions/judge/ACCESS-DISCIPLINE.md` (the rule). Related:
[[feedback-live-source-over-transcription]], [[project-acris-access-shape]].
