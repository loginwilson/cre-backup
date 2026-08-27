---
name: project-preparation-lab-env
description: "The local multi-agent extraction lab at C:\\Users\\smile\\preparation-lab — Traycer/Claude/Codex/OpenCode→Ollama→Qwen, its measured limits and its memory traps"
metadata: 
  node_type: memory
  type: project
  originSessionId: 681841a4-5283-4d18-803f-e32b24982d0f
  modified: 2026-08-26T15:53:09.201Z
---

Built 2026-08-26 on LOGINSURFACE (Surface Laptop, Intel Core Ultra 7 266V / Arc 140V
iGPU, **15.7 GB RAM shared with the GPU** — RAM is the binding constraint, not disk).

Workspace: `C:\Users\smile\preparation-lab` (git repo, tag `env-verified-2026-08-26`).
Full reproduction doc lives in its `SETUP.md`; measurements + traps in
`logs/verification-2026-08-26.md`.

**The chain, and why each layer exists:** Traycer orchestrates *agents*, not models.
Qwen is only weights. **OpenCode IS the harness** (agent loop, tools, file access);
Ollama is the serving layer. Nothing else needed.

**Model reality (verified against the HF API, not release notes):** Qwen3.5 is the
newest generation that ships small sizes at all — **Qwen3.6 and Qwen3.8 floor at 27B
and Qwen3.7 never existed.** Qwen3.5-9B/4B are **dense** (no expert keys in
`config.json`; the `-A<n>B` suffix is the MoE tell). MoE rejected on *resident* weight
size not active params: 35B-A3B is 24 GB at q4 despite 3B active.

**9B is not viable here.** Measured: 142.8 s load, 5.35 tok/s. **4B is the default:**
7.9–13.3 s load, 18–27 tok/s, vision works. 9B archived at `D:\ollama-models\models`
(One Touch USB) — moving a model to another drive does **not** reduce its RAM need.

⚠ **Traps that cost real time:**
- Loading 6.6 GB with 0.5 GB free RAM ballooned the pagefile ~9 GB and **froze the
  laptop**. Judge headroom by `Available MBytes` (free + reclaimable standby), **never**
  `FreePhysicalMemory`.
- `OLLAMA_KEEP_ALIVE=0` is the setting that lets a model coexist with the ACRIS/Richmond
  sync lanes — it unloads the instant a call ends. Login autostart disabled.
- **Thinking silently eats the token budget**: a capped `num_predict` on a thinking model
  returns HTTP 200 with an **empty content field** — looks like success, produces nothing.
  Same shape as the VLM harness trap in [[project-acris-vlm-harness-traps]].
- **`think:false` is not portable** — harmless on `qwen3.5:4b`, blanks output entirely on
  `qwen3-vl:4b`. Omit the param unless measured.
- **Schema-valid ≠ complete**: a run emitted perfect JSON while silently dropping a party.
- Ollama **drops integrated GPUs by default** — needs `OLLAMA_IGPU_ENABLE=1`.
- **OpenCode adds ~20× wall-clock** (298 s vs 16 s direct). Batch extraction → the direct
  runner; OpenCode → agentic work.
- Codex lives in a **content-hashed folder that changes on update** (moved mid-session).
  A shim at `C:\Users\smile\bin\codex.cmd` resolves it at call time.

**The two tiers — the local 4B is NOT a production candidate.** It is a *lower-bound
instrument*: if a contract is unambiguous enough that a 4B executes it, it is genuinely
unambiguous. Production will be ~20B active or more, which **cannot run on this laptop**
(27B q4 ≈ 17 GB) and must be a hosted OpenAI-compatible endpoint. A disabled
`qwen-scale` provider placeholder already exists in `~/.config/opencode/opencode.json`.
⚠ Triage 4B failures as *ambiguous instruction* (fix contract) vs *small-model capability
limit* (ignore) — testing only against the floor **over-diagnoses**.

Contracts in `contracts/` are deliberate **placeholders**; methodology is not yet written
and belongs to [[project-decoder-bootcamp]]. Independence rule (no model sees another's
output; `contracts/` never carries a prior answer) is enforced mechanically by
`runner/qwen_extract.py`.

**STRUCTURE (2026-08-26): migrated to PREPARATION_CHARTER.md §23.** The charter is the
governing artifact and lives at the repo root. Tree is now
`evidence/ extraction/ ontology/ resolution/ verification/ cases/{inputs,gold,claude,codex}
open_model_test/{inputs,qwen_outputs,evaluations}` — NOT the old `contracts/`+`cases/outputs/`.
Open issues are tracked in `CURRENT_HANDOFF.md`, not in the charter.

⚠ **THREE CONFLICTING FUNCTION VOCABULARIES.** Charter §14 lists 11 (Identity/Title/
Capital/.../Cost/Value); `functions_vocab.py` `CANON` has 12; `FUNCTION_REGISTER.md` has 18.
The `ALIAS` table has ALREADY adjudicated `CAPITAL→DEBT` (105 claims, biggest drift),
`ASBUILT→PERMIT`, `OCCUPY→TENANCY` — so §14 would reintroduce settled drift. Start the
ontology from `CANON`. `COST`/`CONTEXT` are Derivation inputs no document evidences.

⚠ **TOKEN BUDGET IS THE REAL CONSTRAINT on the spec.** Measured: `FUNCTION_REGISTER.md`
= 3,131 tokens; `Bootcamp.md` = 562 KB ≈ 138,000 tokens (≈17× the 8192 window — it
CANNOT ship). After image (~450–900) and output (~500–1,500), the whole frozen spec gets
~5,800–7,200 tokens ≈ 700 per artifact. §23 is a compression problem, not a doc tree.

**Guard gap CLOSED:** the first guard blocked only `gold/`+`evaluations/`, leaving one
examiner able to read another's output. Now segment-matched and lab-relative, blocking
`cases/{gold,claude,codex}` + `open_model_test/{qwen_outputs,evaluations}`; writes allowed
only into an examiner's own output dir. Guards cannot detect an answer PASTED into a spec
file — that stays human.
