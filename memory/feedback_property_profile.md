---
name: feedback-property-profile
description: "Format for property assemblage/development site profiles — user provides the intel, Claude formats it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ba6aad1a-5118-4edc-9764-bed6926bd27e
---

When the user asks for a "property profile" on a development site, the format is:

1. **Lead paragraph** — assemblage stats (% built, remaining buildable SF), owner name, location anchor (train, neighborhood), ownership tenure. Voice is direct, analytical, broker-facing.

2. **Tenant Lease Stack table** — one row per tenant: Tenant | Status | Est. Expiry. Include all known tenants. Mark vacated units as dark. Note buyout candidates and kick-out clauses.

3. **Development window analysis** — explain the realistic timeline and why, walking through which leases expire when and what that means for the owner's clearing path.

4. **Blockers** — identify tenants or conditions that create friction (federal leases, long-term anchors, etc.).

5. **What this means for you** — representation opportunities: which displaced tenants need relocation help, timing, and why being early matters.

**Why:** User provided this format explicitly. They want to keep their own prose style — do NOT rewrite into pre-call brief format unless asked. Just add structure (lease table) and preserve the voice.

**How to apply:** User provides the research/intel. Claude formats it into this structure. Do not query the database or run scripts unless the user asks — they supply the property details.
