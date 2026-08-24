---
name: feedback-never-assert-unfetchable
description: "NEVER assert a fetch can't be done — every \"impossible\" fetch in this project later worked; treat blocked endpoints as unsolved puzzles, distinct from explicit refusals which still stop work"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2812a9cb-82a0-4f82-b389-d0bead413962
  modified: 2026-08-24T11:40:10.076Z
---

**Never assert that a source or endpoint can't be fetched.** (login,
2026-08-24: "remember you originally thought none of this could be fetched
at all... I am near certainty that we can for the others.")

**Why:** the track record is one-sided. Richmond pdf was declared to need
"a browser / TLS fingerprint" — RETRACTED: the 403 was the User-Agent
(honest `acris-decoder/1.0` → 200, 10.8–13/s pure python). ACRIS rd/pdf
were both figured out. Every wall so far was a puzzle (UA, Referer chain,
session-grant, query-param form) not a wall. The standing DOB claim
("document access REFUSED at the BIS Akamai edge") is an OLD probe result
and must be RE-VERIFIED with the lessons since (honest UA, referer chain,
in-session grant) before being repeated.

**How to apply:** when a fetch fails, report it as "blocked so far, here's
what I tried" — never "can't be done." Probe the known ladder first: honest
UA · Referer chain · fetch-the-listing-page-in-session · query-param vs
POST form. DISTINCT from the refusal rule, which still binds: an EXPLICIT
refusal (bandwidth notice, denial text) means stop-don't-retry per
[[project-acris-refusal-20260824]]; a bare 403/error page is a puzzle, not
a refusal — fetch_pages already encodes that distinction (matched notice
signals stop everything; an ordinary error page does not).

Related: [[project-rc-rd-coded]], [[project-dob-decoder-state]]
