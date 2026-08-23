---
name: feedback-decisive-execution
description: "Login wants decisive execution on clear directives, not repeated deliberation; verify in the sandbox before pushing"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c3e8ae92-3911-481d-b7fa-c3a885743b7a
  modified: 2026-07-22T23:08:08.377Z
---

When Login gives a clear directive — e.g. "revert to before commit X," "keep A and B, fix C," a specific target — **execute it decisively**. Do not re-litigate the decision, re-offer menus, or write long option-comparisons; they experience that as churn and it erodes trust.

**Why:** On 2026-07-22 a chaotic day (over-built audit system, a self-inflicted regression, a wrong Factory House diagnosis) left Login frustrated. They repeatedly said "I told you where to go, what to keep, what to fix" — the problem was my indecision, not missing information.

**How to apply:**
- Confirm the *target* once if genuinely ambiguous (e.g. which commit), then act.
- Own mistakes plainly and briefly; don't be defensive or bury the correction.
- Prefer **surgical** over sweeping, but if changes are entangled and trust is low, a clean **revert to a known-good commit + rebuild the keepers** is what Login asked for — do it (safe snapshot revert, no force-push, recoverable).
- **Sandbox-first:** verify every change in the running local sandbox (`bkrea-sandbox.localhost:3000`, off OneDrive) before committing/pushing — `tsc` + tests are necessary but not sufficient. A push deploys to production. See [[project_bkrea_territory_intel]] and [[project_bkrea_sandbox_env]].
- Never run the repo from a OneDrive/cloud-synced folder — it triggers endless Next.js Fast Refresh remounts. Repo lives at `C:\dev\bkrea-territory-intelligence-app`.
