# v3 is superseded by v4

`framework.md` in this directory — sha256 `c6fce8c1ab9ca976…`, 9,507 B — is the
version the five extractors used on `RC_1598772`. It is kept unchanged so that
round's tables remain readable against the rules that produced them.

**Do not dispatch a document against v3.** Use `../v4/framework.md`.

Two defects in this file are documented and were the reason for v4:

- **rules 1 and 5 contradict each other** on a recording endorsement — rule 5 names
  the return-to party as worth catching, rule 1 obeyed literally deletes the row
  that would hold it
- **the citation column carries characters only**, which cannot support any claim
  about how text is marked — and on `RC_1598772` that was the difference between
  conveying two lots and conveying none

See `../RULING-RC_1598772.md` and `../v4/CHANGES.md`.
