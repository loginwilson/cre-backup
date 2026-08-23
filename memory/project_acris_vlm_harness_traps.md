---
name: project_acris_vlm_harness_traps
description: "How a local VLM run silently produces fake results — HTTP 200 with empty content, a wedged single slot that poisons every later test, and thinking mode eating the token budget"
metadata: 
  node_type: memory
  type: project
  originSessionId: 7c5a3ccb-a88e-40cd-a587-cc575cf7a400
  modified: 2026-08-12T23:07:51.590Z
---

Measured 2026-08-12 benchmarking **Qwen3.5-2B (Q4_K_M) on llama-server** for the Design B
slot. Every trap below produced a result that LOOKED like a measurement.

## ⚠ HTTP 200 CARRYING AN EMPTY STRING IS A FAILURE, NOT A TRANSCRIPTION

5 of 8 pages wrote a **zero-byte .txt in ~85s each** while 3 read cleanly. The calls all
succeeded, so `run.py`'s `except` guard never fired — the harness only refused to write on an
*exception*. Cause: **thinking mode is ON by default in Qwen3.x** and the model spent the
whole budget narrating before emitting content.

Fixes now in `bakeoff/run.py`: `chat_template_kwargs={"enable_thinking":false}` +
`reasoning_effort:"none"` (both spellings — llama.cpp and vLLM honour different ones); an
empty reply raises `EmptyReply` naming `finish_reason` / `reasoning_chars` /
`completion_tokens`; a zero-byte sweep runs at startup. **After the fix: 12/12 pages had
content, 0 zero-byte.** Transcription is not a reasoning task — thinking actively breaks it.

## ⚠ AND IT IS A RESUME TRAP

Resume skips any page whose `.txt` EXISTS. A zero-byte file is therefore permanently "done"
and never retried. `exists()` is not the test; `exists() and st_size > 0` is.

## ⚠ A WEDGED SLOT POISONS EVERY TEST THAT FOLLOWS — this wasted the most time

Server runs `-np 1` (one slot). When a page hangs it, the request keeps the slot forever;
`/slots` and `/health` stop answering. **Every subsequent request queues behind it and times
out**, so each new "test" reports failure regardless of what it changes. Two hypotheses got
falsely disconfirmed this way before it was spotted. **Restart the server before every
diagnostic, or the result means nothing.** Killing the client does NOT free the slot.

Also: killing a client mid-run leaves its queued requests server-side — the next run inherits
a backlog and its first page reads as pathologically slow.

## What is actually known about the hang (UNRESOLVED)

`BK_6730047100023 p004` wedges a **freshly restarted** server at both `-c 8192` and
`-c 16384`, at 1400px. Digital pages 9/9 fine (~33s); book p001–p003 fine. **1000px on a
clean server is the one clean test never run** — the 1000px attempt was queued behind a wedge
and is invalid. Do that first. Denser page (0.8 MB vs 0.4 MB) is the only obvious difference.

## ⚠ THE 2026-08-12 SCOREBOARD COMPARING Qwen3-VL-4B TO Qwen3.5-2B IS INVALID

**7 of 10 film pages from the incumbent 4B run END MID-SENTENCE** (p006 stops at "and that
the"). It was hitting a max_tokens cap, so its film score is a FLOOR set by the harness, not
its capability — and 6 of its 20 CRITICAL misses sit on p006, the single longest output.

Worse, `out/qwen/run.json` records **no configuration at all** — only
`model: "incumbent (2025 gen, local)"`. No max_tokens, width, prompt, or thinking flag. The
run is unreproducible, so its 96.2% cannot be defended or repeated.

Qwen3.5-2B was measured through `run_serial.py` with everything recorded (imgtok 2560,
max_tokens 2048/4096, 1400px, thinking off). **Comparing the two measures two harnesses, not
two models.** Before quoting any VLM head-to-head again, re-run the 4B through the SAME
script with the SAME settings.

**Checks that would have caught it, and are now mandatory:** does the output end mid-sentence
(cheap truncation test, run it on every engine); does run.json record every setting; do the
two runs share one harness.

## ⚠ NEVER RUN CPU OCR WHILE THE VLM IS RUNNING — made this mistake TWICE in one day

The iGPU (Intel Arc 140V, Vulkan) has NO memory of its own; it takes system RAM. So
llama-server and PaddleOCR compete for both cores AND the same 15.7 GB. Measured
2026-08-12: with PP-OCR on only 3 threads alongside the VLM, CPU hit 99% and free RAM fell to
0.3 GB, Windows began paging, and VLM pages went **40-70s → 361s → 754s**. It reads exactly
like a new model bug and it is pure contention. Killing the OCR job restored 3.7 GB free and
70% CPU instantly.

**Diagnose a "stall" by checking free RAM and what else is running BEFORE theorising about the
model.** Serialise: OCR runs, then the VLM runs. Also `-c 16384` → `-c 8192` freed ~0.5 GB and
costs nothing, because a page needs ~2,560 image + ~2,048 output ≈ 4,600 tokens.

## Laptop is not the measurement rig

Fans maxed under PP-OCR (4 threads × 3 rotations) alongside llama-server. Thermal throttling
also invalidates any pages/second figure taken here. Speed belongs on Torch/HPC; this box
measures ACCURACY only. See [[project_acris_ocr_stack]], [[feedback_bkrea_scale_failure]].
