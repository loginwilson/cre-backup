"""THE VLM DIRECTS THE READ — it places OCR lines, it does NOT transcribe them.

    python route.py --doc FT_1680008647768 --page p001
    python route.py --doc FT_1680008647768 --ocr ppbox --limit 3

⚠ THE INTERFACE IS THE GUARD. Measured this session: the VLM's real failure is a
DEGENERATE DECODE LOOP — q35-fair emitted the counter 92394…92644 (251 reps) on BK
p006, qwen35-2b emitted `david schum david schum` 273 times. Every one of those is
the model EMITTING CHARACTERS. So this pass never lets it emit characters at all.

It receives NUMBERED OCR lines and returns ASSIGNMENTS OF LINE NUMBERS to regions.
Invented text is then not "unlikely", it is UNREPRESENTABLE — there is no field it
could appear in. An invented line number is out of range, which is arithmetic, not
judgement. That converts the fabrication check from a statistical filter into a
property of the interface.

⚠ WHAT EACH CHANNEL IS FOR, MEASURED, NOT ASSUMED.
    OCR  characters + boxes. Never loops (rapidocr 21/21 pages clean) and cannot
         invent a phrase, but returns the page as ONE line — BK p004 came back as a
         single 7,566-char line from ppv6, ppbox AND tesseract.
    VLM  structure. The ONLY channel that produces any — 25 lines on that same page
         at the same character count. Loops on hard pages, which is why it is fenced.

⚠ REGIONS ARE A CLOSED SET AND `other` IS A REAL ANSWER. An open-ended label invites
the model to invent a taxonomy, which is the `**Document Title**` / `**Signature
Block**` failure in another costume — 9 of those 10 tokens were caught as unsupported
precisely because they were invented layout vocabulary.

⚠ AND UNPLACED IS REPORTED, NEVER SILENTLY DROPPED. A line the model did not assign
is UNREAD, which is a different finding from a line it assigned to `other`.
"""
from __future__ import annotations

import argparse, collections, json, pathlib, re, subprocess, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

import run_cli as R

REGIONS = ["recording_stamp", "parties", "granting_clause", "legal_description",
           "covenants", "amount", "signature", "notary", "schedule", "exhibit",
           "other"]

PROMPT = (
    "This is a scanned page from a New York property document. Below are numbered "
    "text lines an OCR engine read from THIS page.\n\n"
    "Label each line with the ONE region of the page it belongs to.\n"
    "Regions: " + ", ".join(REGIONS) + ".\n\n"
    "Return ONLY compact JSON on one line, keyed by line number:\n"
    "{\"0\":\"<region>\",\"1\":\"<region>\"}\n"
    "Rules: exactly one region per line number. Never repeat a line number. "
    # ⚠ SAID EXPLICITLY BECAUSE THE MODEL READ THE LIST AS A CHECKLIST: on
    # FT p001 it filled ALL ELEVEN regions rather than leave any empty, giving
    # `signature` and `notary` the same line and `schedule` and `exhibit`
    # another — 70 assignments for 44 lines.
    "MOST PAGES USE ONLY TWO OR THREE REGIONS — a region that is not on this "
    "page must simply not appear in your answer. Do not force one. "
    "Use \"other\" when no region fits. Do NOT transcribe, repeat, correct or "
    "invent any text; refer to lines only by number.\n\nLINES:\n")


def ocr_lines(doc, page, ocr, angle=0):
    """⚠ ONE LINE PER OCR ITEM, WITH ITS BOX. Items are what carry geometry; the
    concatenated .txt has none. Multi-angle runs repeat the page once per angle,
    so the angle travels with each line and de-duplication is the caller's
    decision, not a silent one here."""
    for name in (f"{page}.png.json", f"{page}.json"):
        f = HERE / "out" / ocr / doc / name
        if f.exists():
            items = json.loads(f.read_text(encoding="utf-8")).get("items") or []
            items = [i for i in items if (i.get("text") or "").strip()]
            # ⚠ ANGLE 0 BY DEFAULT, BECAUSE THE EXTRA ANGLES MEASURED +0.0%.
            # RapidOCR on film: a0 94.6%, a90 62.2%, a270 70.3%, union 94.6%
            # (n=37 CRITICAL artifacts, 4 pages). Feeding all three would triple
            # the line count with readings that add no artifact and would hand
            # the router two extra garbled copies of every line to place.
            if angle is not None:
                items = [i for i in items if i.get("angle", 0) == angle]
            return items
    return []


def ask(img, lines, model, mmproj, ntok, timeout, ngl=0, ctx=8192):
    """⚠ CPU, NOT THE iGPU, AND THAT IS MEASURED NOT PREFERRED. `-ngl 99` dies
    with `ggml_vulkan: device lost on Vulkan0` on this box — reproduced with the
    machine completely idle, so it is the Vulkan path and not contention (an
    earlier reading of mine blamed a concurrent Paddle run; that was wrong).

    ⚠ `-c` MUST BE PINNED. Without it the model's full default context is
    requested and llama.cpp fails with `failed to allocate buffer for kv cache`,
    exiting 1 with an EMPTY stdout — indistinguishable from a model that ran and
    answered nothing, which is the trap this project has already paid for once.
    """
    body = "\n".join(f"{i}. {l['text']}" for i, l in enumerate(lines))
    r = subprocess.run(
        [str(R.BIN), "-m", str(R.MODELS / model), "--mmproj", str(R.MODELS / mmproj),
         "--image", str(img), "-p", PROMPT + body,
         "-ngl", str(ngl), "-c", str(ctx), "--temp", "0", "-n", str(ntok),
         "--no-warmup"],
        capture_output=True, timeout=timeout)
    return r.stdout.decode("utf-8", "replace").strip()


def ask_http(img, lines, url, ntok, timeout):
    """THE SERVER PATH — the model is loaded ONCE, not per page.

    ⚠ WHY THIS AND NOT THE CLI. llama-mtmd-cli reloads 4.7 GB every page; on CPU
    that measured ~7 minutes per page and made iteration impossible. run_cli.py
    exists because llama-server WEDGES on Qwen3.5-2B — but the 4B was always
    measured through this HTTP path, which is also the only place thinking can
    be turned off.

    ⚠ cache_prompt MUST BE FALSE. Measured 2026-08-12: llama.cpp reuses the
    cached prefix, every request carries a DIFFERENT image, token positions go
    non-consecutive and the slot wedges FOREVER. With -np 1 that is the only
    slot, /health stops answering, and every later request queues behind it.

    ⚠ AND AN EMPTY REPLY IS DIAGNOSED, NOT RETURNED AS "". A 200 with no content
    means thinking ate the budget, which is a different finding from a blank page.
    """
    import base64, urllib.request
    b64 = base64.b64encode(pathlib.Path(img).read_bytes()).decode()
    body = {"model": "qwen", "messages": [{"role": "user", "content": [
                {"type": "text", "text": PROMPT + "\n".join(
                    f"{i}. {l['text']}" for i, l in enumerate(lines))},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
            "max_tokens": ntok, "temperature": 0, "cache_prompt": False,
            "chat_template_kwargs": {"enable_thinking": False},
            "reasoning_effort": "none"}
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        j = json.load(r)
    ch = j["choices"][0]
    txt = (ch["message"].get("content") or "").strip()
    if txt:
        return txt
    u = j.get("usage") or {}
    raise RuntimeError(f"empty content (finish_reason={ch.get('finish_reason')}, "
                       f"reasoning_chars={len(ch['message'].get('reasoning_content') or '')}, "
                       f"completion_tokens={u.get('completion_tokens')})")


SRV = pathlib.Path(r"C:/Users/smile/llm/bin/llama-server.exe")


def server_up(url, timeout=180):
    import urllib.request, urllib.error
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(url.rstrip("/") + "/health", timeout=3) as r:
                if b'"ok"' in r.read():
                    return True
        except Exception:
            pass
        time.sleep(3)
    return False


def restart_server(model, mmproj, url, ngl, ctx):
    """⚠ THE HANG IS PER-PROCESS, SO THE CURE IS A NEW PROCESS.

    llama-server's vision path hangs BEFORE generation roughly one page in three
    on a freshly started server: the log shows `launch_slot_: processing task`
    and then NO prompt-processing line ever follows — it is stuck in image
    ENCODING, not generating slowly, so no client-side timeout can shorten it and
    the slot never recovers. With -np 1 that is the only slot, and every later
    page queues behind it forever. Measured twice this session between two
    successes; run_cli.py exists because of exactly this.

    Restarting costs ~15 s of model load, against a page that would otherwise
    never return. A run that cannot do this cannot finish a document.
    """
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-Process llama-server -ErrorAction SilentlyContinue | "
                    "Stop-Process -Force -ErrorAction SilentlyContinue"],
                   capture_output=True)
    time.sleep(2)
    subprocess.Popen([str(SRV), "-m", str(R.MODELS / model),
                      "--mmproj", str(R.MODELS / mmproj), "-ngl", str(ngl),
                      "-c", str(ctx), "-np", "1", "--port", url.rsplit(":", 1)[-1],
                      "--host", "127.0.0.1"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return server_up(url)


def parse(raw, n):
    """⚠ EVERY DEVIATION IS COUNTED, NOT REPAIRED. A model that answers in the
    wrong shape is a measurement, and quietly coercing it would hide exactly the
    behaviour this run exists to observe.

    ⚠ ONE LABEL PER LINE, AND THAT IS WHY THE SHAPE CHANGED. The first interface
    asked for {region -> [lines]} and the 4B returned 70 assignments for 44 lines
    on FT p001: it filled ALL ELEVEN regions, giving `signature` and `notary` the
    same line 12, and `schedule` and `exhibit` the same line 20. It would not
    leave a region empty — it satisfied the region list instead of reading the
    page. That is fabrication in the only form left to a model that cannot emit
    text: an invented PLACEMENT.

    Keyed by LINE, a line physically cannot carry two regions — a duplicate key
    in a JSON object collapses to one. So the failure stops being detected and
    starts being impossible, which is the same move that stopped it inventing
    characters. An absent region simply never appears.
    """
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None, {"no_json": 1}
    try:
        j = json.loads(m.group(0))
    except Exception:
        return None, {"bad_json": 1}
    # ⚠ REFUSE THE OLD SHAPE RATHER THAN SILENTLY HALF-READING IT.
    if "regions" in j:
        return None, {"wrong_shape_region_keyed": 1}
    out, bad = collections.defaultdict(list), collections.Counter()
    for k, v in j.items():
        try:
            i = int(k)
        except (TypeError, ValueError):
            bad["non_numeric_key"] += 1
            continue
        if not (0 <= i < n):
            bad["out_of_range"] += 1        # a fabricated index — arithmetic
            continue
        if v not in REGIONS:
            bad["unknown_region"] += 1      # an invented label — closed set
            continue
        out[v].append(i)
    placed = sum(len(x) for x in out.values())
    bad["unplaced"] = n - placed            # UNREAD, not "other"
    # ⚠ DID IT EMIT PROSE? The one thing the interface forbids.
    stripped = re.sub(r"\{.*\}", "", raw, flags=re.S)
    bad["prose_words_outside_json"] = len(re.findall(r"[A-Za-z]{4,}", stripped))
    return dict(out), dict(bad)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--page", default=None)
    ap.add_argument("--ocr", default="ppv6ma")
    ap.add_argument("--model", default="4B-Qwen3-VL-4B-Instruct-Q4_K_M.gguf")
    ap.add_argument("--mmproj", default="4B-mmproj-F16.gguf")
    # ⚠ 900px, NOT run_cli's measured-best 1400. AT 1400 THE VULKAN VISION
    # ENCODER HANGS: p004 and p006 timed out at 170s each, twice, and the same
    # renders threw `ggml_vulkan: device lost` in the CLI. At 900 the SAME pages
    # complete in 47-65s, 3/3. Isolated — `-fa off` alone did NOT fix it, so it
    # is encoder work, not attention. 1400 remains best for TRANSCRIPTION; this
    # is a PLACEMENT task and the score is checked at 900 rather than assumed.
    ap.add_argument("--width", type=int, default=900)
    ap.add_argument("--ntok", type=int, default=2048)
    ap.add_argument("--url", default="http://127.0.0.1:8000",
                    help="llama-server; empty string forces the CLI path")
    ap.add_argument("--retries", type=int, default=2,
                    help="server restarts on a vision-path hang")
    ap.add_argument("--ngl", type=int, default=0)
    ap.add_argument("--ctx", type=int, default=8192)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--angle", type=int, default=0,
                    help="which OCR angle to route; -1 for all")
    a = ap.parse_args()
    if a.angle < 0:
        a.angle = None

    pgdir = HERE / "pages" / a.doc
    pages = ([a.page] if a.page else
             sorted(p.stem for p in pgdir.glob("p*.png")))
    if a.limit:
        pages = pages[:a.limit]

    outdir = HERE / "out" / "_route" / a.doc
    outdir.mkdir(parents=True, exist_ok=True)
    print(f"  ROUTING {a.doc} · ocr={a.ocr} · vlm={a.model}")
    print(f"  {len(pages)} page(s) — the VLM returns LINE NUMBERS, never text\n")

    for pg in pages:
        lines = ocr_lines(a.doc, pg, a.ocr, a.angle)
        if not lines:
            print(f"  {pg}  no OCR items — SKIPPED (run pp_doc.py first)")
            continue
        img = R.prep(pgdir / f"{pg}.png", a.width)
        t = time.time()
        raw, err = None, None
        for attempt in range(a.retries + 1):
            try:
                raw = (ask_http(img, lines, a.url, a.ntok, a.timeout) if a.url
                       else ask(img, lines, a.model, a.mmproj, a.ntok,
                                a.timeout, a.ngl, a.ctx))
                break
            except Exception as e:
                err = f"{type(e).__name__}: {str(e)[:90]}"
                if a.url and attempt < a.retries:
                    # ⚠ A HANG IS NOT A SLOW PAGE. Retrying against the SAME
                    # wedged slot queues forever; the process must be replaced.
                    print(f"  {pg}  hang/err ({err}) — restarting server "
                          f"[{attempt+1}/{a.retries}]", flush=True)
                    if not restart_server(a.model, a.mmproj, a.url, a.ngl, a.ctx):
                        print(f"  {pg}  ⚠ server did not come back up")
                        break
                    continue
                break
        if raw is None:
            # ⚠ NAMED, NOT SWALLOWED. A page the server never answered is UNREAD,
            # which is a different finding from a page with no regions on it.
            print(f"  {pg}  ⚠ UNREAD after {a.retries+1} attempt(s): {err}")
            continue
        el = time.time() - t
        placed, bad = parse(raw, len(lines))
        if placed is None:
            print(f"  {pg}  {el:.0f}s  ⚠ NO PARSEABLE JSON  {bad}")
            (outdir / f"{pg}.raw.txt").write_text(raw, encoding="utf-8")
            continue
        cover = 1 - bad["unplaced"] / len(lines)
        print(f"  {pg}  {el:>4.0f}s  {len(lines):>3} lines  "
              f"placed {cover:>5.1%}  regions {len(placed)}")
        print(f"      " + "  ".join(f"{k}:{len(v)}" for k, v in
                                    sorted(placed.items(), key=lambda kv: -len(kv[1]))))
        flags = {k: v for k, v in bad.items() if v}
        print(f"      integrity: {flags or 'clean'}")
        json.dump({"doc": a.doc, "page": pg, "ocr": a.ocr, "vlm": a.model,
                   "n_lines": len(lines), "seconds": round(el, 1),
                   "placed": placed, "integrity": bad,
                   "lines": [{"i": i, "text": l["text"], "box": l.get("box"),
                              "angle": l.get("angle")} for i, l in enumerate(lines)]},
                  open(outdir / f"{pg}.json", "w"), indent=1)
    print(f"\n  -> {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
