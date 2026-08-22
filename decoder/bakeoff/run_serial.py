"""ONE VLM OVER THE KEYED PAGES, WITH THE SERVER RESTARTED UNDER IT.

    python run_serial.py qwen35-2b --model 35-2B-Q4_K_M.gguf --mmproj 35-2B-mmproj-F16.gguf
    python run_serial.py qwen35-2b --restart-every 4        # fewer restarts, more risk

⚠ WHY THIS EXISTS INSTEAD OF run.py. llama-server WEDGES on Qwen3.5-2B. Measured
2026-08-12 from the server's own log: two pages complete normally, then

    W find_slot: non-consecutive token position 43 after 42 for sequence 0
    W find_slot: non-consecutive token position 105 after 43 for sequence 0
    I launch_slot_: id 0 | task 984 | processing task

and the log ENDS. No "prompt processing" line ever follows, so it is stuck
BEFORE generation, inside image encoding. With `-np 1` that wedges the only
slot: /health stops answering, the client's socket timeout cannot fire because
the connection stays open, and every later request queues behind it forever.

⚠ IT IS THE SERVER, NOT THE MODEL, AND THAT WAS PROVEN NOT ASSUMED.
llama-mtmd-cli.exe reads the SAME page, at the SAME 1400px, with the SAME model
and mmproj, on the SAME GPU, and exits cleanly. One process per page has no slot
to corrupt. Three earlier hypotheses - context size, image width, thinking mode -
were all wrong, and two of them were "disconfirmed" by tests that were
themselves queued behind a wedge and therefore meaningless.

⚠ WHY NOT JUST USE THE CLI. The CLI in this build has no way to turn reasoning
off - no --chat-template-kwargs, no --reasoning-budget. Left on, Qwen3.5 narrates
("I will combine these into a single block of text") and reformats the page into
bulleted markdown, which is the same form-filler behaviour that scored 86%
against the generic prompt's 92%. The HTTP API can turn it off, so the API is
kept and the SERVER LIFETIME is what changes.

⚠ A RESTART IS NOT FREE AND IS NOT HIDDEN. ~25s per page of model loading, which
is why per-page wall time from this script is NOT a throughput measurement.
Startup and inference are timed separately and both are recorded.
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import run as R

HERE = pathlib.Path(__file__).parent
BIN = pathlib.Path(r"C:/Users/smile/llm/bin/llama-server.exe")
MODELS = pathlib.Path(r"C:/Users/smile/llm/models")
PORT = 8080
URL = f"http://127.0.0.1:{PORT}"


def ask_stream(url, b64, prompt, ntok, ttft, total, stall=60):
    """⚠ A WEDGE AND A SLOW PAGE ARE INDISTINGUISHABLE ON A BLOCKING CALL, AND
    TELLING THEM APART IS WORTH REAL TIME. A working page takes 35-45s; a wedged
    one never answers. With one blocking request the only way to catch the wedge
    is a timeout long enough to also cover the slowest legitimate page, so every
    hang cost 300s of nothing - roughly five minutes each, one page in three.

    Streaming separates them properly:
      - TIME TO FIRST TOKEN bounds the hang. The wedge happens BEFORE generation
        (the server log dies at "processing task", with no "prompt processing"
        line after it), so no first token inside `ttft` seconds means wedged.
      - The overall deadline stays generous, because a dense film page emitting
        4,096 tokens at ~22 tok/s legitimately needs three minutes and must NOT
        be killed for it.
    """
    body = {
        "model": "q",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
        "max_tokens": ntok, "temperature": 0, "stream": True,
        "cache_prompt": False,
        "chat_template_kwargs": {"enable_thinking": False},
        "reasoning_effort": "none"}
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    parts, first, fin, last = [], None, [None], [time.time()]
    with urllib.request.urlopen(req, timeout=ttft) as r:
        for raw in r:
            if time.time() - t0 > total:
                raise TimeoutError(f"exceeded {total}s overall")
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                j = json.loads(payload)
            except Exception:
                continue
            # ⚠ A SOCKET TIMEOUT RESETS ON EVERY BYTE, SO IT CANNOT BOUND A
            # STALL. Measured 2026-08-13: BK p005 ran 30,726s - EIGHT AND A HALF
            # HOURS - under a "300s timeout", because urlopen's timeout applies
            # per-recv and any keepalive byte restarts it, while the elapsed
            # check below only executes when a line actually arrives. If nothing
            # arrives, nothing checks. The deadline must be enforced OUTSIDE the
            # socket - see run_page().
            if first is not None and time.time() - last[0] > stall:
                raise TimeoutError(f"no token for {stall}s (stalled)")
            ch0 = (j.get("choices") or [{}])[0]
            # ⚠ MEASURE TRUNCATION, DO NOT INFER IT. "Ends without punctuation"
            # over-flags badly - `Page 2 of 5` and a document number are real
            # page endings, not cuts. finish_reason == "length" is the server
            # saying it hit max_tokens. The incumbent 4B run recorded nothing,
            # so its clipped film pages were only found by eyeballing text tails.
            if ch0.get("finish_reason"):
                fin[0] = ch0["finish_reason"]
            delta = ch0.get("delta") or {}
            c = delta.get("content")
            if c:
                if first is None:
                    first = time.time() - t0
                    if first > ttft:
                        raise TimeoutError(f"first token after {first:.0f}s")
                parts.append(c)
    txt = "".join(parts).strip()
    if not txt:
        raise R.EmptyReply("stream produced no content")
    return txt, first or 0.0, fin[0]


def run_page(url, b64, prompt, ntok, ttft, total, hard):
    """⚠ THE ONLY DEADLINE THAT CANNOT BE DEFEATED IS ONE OUTSIDE THE REQUEST.
    A worker thread does the HTTP; the parent waits `hard` seconds and gives up
    regardless of what the socket is doing. The thread is left daemonised - the
    caller kills the server next, which tears its connection down."""
    import threading
    box = {}

    def go():
        try:
            box["r"] = ask_stream(url, b64, prompt, ntok, ttft, total)
        except Exception as e:
            box["e"] = e

    t = threading.Thread(target=go, daemon=True)
    t.start()
    t.join(timeout=hard)
    if t.is_alive():
        raise TimeoutError(f"hard deadline {hard}s exceeded")
    if "e" in box:
        raise box["e"]
    return box["r"]


def kill():
    subprocess.run(["taskkill", "/F", "/IM", "llama-server.exe"],
                   capture_output=True)
    time.sleep(2)


def start(model, mmproj, ctx, log, imgtok=1024, batch=8192, ubatch=4096):
    """Returns seconds to become healthy, or raises.

    ⚠ --image-min/max-tokens IS WHAT MADE Qwen3.5 USABLE HERE, and llama.cpp
    prints the hint itself at load: "Qwen-VL models require at minimum 1024
    image tokens to function correctly". Uncapped, a 1400px page encoded to
    ~2,557 image tokens, time-to-first-token was 21-25s, and the vision encoder
    hung outright on roughly one page in three. Capped at 1024: TTFT 6s, and the
    page that wedged the server twice (BK p004) read 1,285 words in 72s.

    ⚠ IT IS A REAL TRADE, NOT A FREE WIN. Fewer image tokens means less visual
    detail reaching the model, and this corpus is faint microfilm and overlapping
    stamps. 1024 is llama.cpp's documented FLOOR, not a tuned value - if accuracy
    lands below the 4B, raising this cap is the first thing to test, before any
    conclusion about the model.
    """
    t = time.time()
    f = open(log, "ab")
    subprocess.Popen(
        [str(BIN), "-m", str(MODELS / model), "--mmproj", str(MODELS / mmproj),
         "-ngl", "99", "-c", str(ctx), "-np", "1", "-cb",
         # ⚠ THE MICRO-BATCH IS WHAT SPLITS THE IMAGE, AND THE SPLIT IS THE BUG.
         # Every hang warning reads "find_slot: non-consecutive token position
         # 43 after 43 for sequence 0 WITH 512 NEW TOKENS" - 512 is llama.cpp's
         # default n_ubatch. A 1400px page encodes to ~2,659 image tokens, so it
         # is chopped into six 512-token chunks and every chunk claims to start
         # at position 43 (where the text prompt ends) instead of advancing.
         # llama.cpp #22867 documents this exact warning as a slot-position
         # corruption on multimodal input that can retry until memory is gone;
         # #19929 documents Qwen3.5 vision misbehaving on particular -b/-ub
         # combinations. Sizing ubatch ABOVE the image token count sends the
         # embedding through in ONE piece, so there is no chunk boundary to
         # misalign.
         "-b", str(batch), "-ub", str(ubatch),
         "--image-min-tokens", str(imgtok), "--image-max-tokens", str(imgtok),
         "--host", "127.0.0.1", "--port", str(PORT)],
        stdout=f, stderr=f, creationflags=0x08000000)
    for _ in range(120):
        try:
            with urllib.request.urlopen(URL + "/health", timeout=5) as r:
                if r.status == 200:
                    return time.time() - t
        except Exception:
            time.sleep(1)
    raise RuntimeError("server never became healthy")


# ⚠ A VLM UNION IS NOT AN OCR UNION, AND CONCATENATING IS THE OBVIOUS WRONG MOVE.
# pp_book.py merges Paddle ITEMS - line boxes, so duplicates are visible and
# dropped by position. A VLM returns a whole-page blob per angle, so appending
# three passes writes the upright page THREE TIMES and every downstream token
# count, agreement rate and claim frequency inherits the triplication.
#
# The rotated passes exist for ONE reason: the backer, which is sideways and
# which no VLM run in this project has ever been shown upright. So a rotated
# pass is kept only when it read something genuinely NEW - measured as token
# overlap against the upright pass, the same test fuse.py uses to separate a
# real gap from an alignment artefact. A 90-degree pass that merely re-reads the
# upright text badly is discarded; one that returns the backer is appended.
NOVEL = 0.60   # keep a rotated pass when >60% of its tokens are absent upright


def union_passes(by_angle):
    """by_angle: {angle: text}. Returns (union_text, note)."""
    import re as _re
    base = (by_angle.get(0) or "").strip()
    tok = lambda t: {_re.sub(r"[^0-9a-z]", "", w.lower())
                     for w in t.split() if _re.sub(r"[^0-9a-z]", "", w.lower())}
    seen = tok(base)
    out, notes = [base] if base else [], []
    for ang in sorted(k for k in by_angle if k):
        t = (by_angle[ang] or "").strip()
        if not t:
            continue
        tt = tok(t)
        if not tt:
            continue
        novel = len(tt - seen) / len(tt)
        if novel >= NOVEL:
            out.append(t)
            seen |= tt
            notes.append(f"+{ang}({novel:.0%} new)")
        else:
            notes.append(f"-{ang}({novel:.0%} new, dropped as duplicate)")
    return "\n\n".join(out), " ".join(notes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--model", default="35-2B-Q4_K_M.gguf")
    ap.add_argument("--mmproj", default="35-2B-mmproj-F16.gguf")
    ap.add_argument("--ctx", type=int, default=16384)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--width", type=int, default=1400)
    ap.add_argument("--timeout", type=int, default=240,
                    help="overall deadline per page once tokens are flowing")
    ap.add_argument("--ttft", type=int, default=45,
                    help="seconds to FIRST token before calling it wedged")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--hard", type=int, default=420,
                    help="wall-clock ceiling per attempt, enforced outside the socket")
    ap.add_argument("--batch", type=int, default=8192)
    ap.add_argument("--ubatch", type=int, default=4096,
                    help="must EXCEED image tokens or the image gets chunked")
    ap.add_argument("--imgtok", type=int, default=1024,
                    help="image tokens per page (llama.cpp floor for Qwen-VL)")
    # ⚠ THE PROMPT IS PART OF THE CONFIG AND MUST BE RECORDED IN run.json.
    # An earlier head-to-head was declared invalid because run.json held no
    # config at all, so nobody could say what the losing arm had been given.
    ap.add_argument("--prompt-variant", default="baseline",
                    choices=sorted(R.PROMPTS),
                    help="baseline = the measured sentence; strict = adds the "
                         "no-invention clause. Changing this changes the arm.")
    ap.add_argument("--refresh-union", action="store_true",
                    help="rebuild pNNN.txt from the per-angle files on disk")
    ap.add_argument("--angles", default="0",
                    help="0 for upright; 0,90,270 for bound-book and film "
                         "pages whose backer is sideways")
    ap.add_argument("--doc", default=None,
                    help="restrict to one document (A/B on a subset)")
    ap.add_argument("--restart-every", type=int, default=1,
                    help="restart the server every N pages (1 = every page)")
    a = ap.parse_args()

    out = HERE / "out" / a.tag
    log = HERE / "out" / f"{a.tag}_server.log"
    jobs = [(d.name, p)
            for d in sorted(x for x in (HERE / "pages").iterdir() if x.is_dir())
            if (a.doc is None or d.name == a.doc)
            for p in sorted(d.glob("p*.png"))]
    if a.doc and not jobs:
        raise SystemExit(f"  no pages for --doc {a.doc}")
    PROMPT = R.PROMPTS[a.prompt_variant]
    angles = [int(x) for x in a.angles.split(",") if x.strip()]

    print(f"  {a.tag}: {a.model}   prompt={a.prompt_variant}")
    print(f"  {len(jobs)} pages × {len(angles)} angle(s) {angles} · ctx {a.ctx} · max_tokens {a.max_tokens} · "
          f"{a.width}px · restart every {a.restart_every}")
    print(f"  server log -> {log}\n", flush=True)

    kill()
    rows, since, boot, t0 = [], 10**9, 0.0, time.time()
    for i, (docn, pg) in enumerate(jobs, 1):
        d = out / docn
        d.mkdir(parents=True, exist_ok=True)
        f = d / (pg.stem + ".txt")
        if f.exists() and f.stat().st_size > 0 and not a.refresh_union:
            print(f"  {i:>2}/{len(jobs)} {docn[:14]:14}/{pg.name}  (on disk)",
                  flush=True)
            continue

        if since >= a.restart_every:
            kill()
            boot = start(a.model, a.mmproj, a.ctx, log, a.imgtok, a.batch, a.ubatch)
            since = 0

        t = time.time()
        status, txt, ttft, fin = "ok", None, 0.0, None
        by_angle, per_angle_status = {}, []
        for ang in angles:
            # ⚠ EACH ANGLE IS ITS OWN PAGE ON DISK. A crash mid-page must not
            # lose the passes already paid for, and a rotated pass that failed
            # must be distinguishable from one that returned nothing.
            af = d / f"{pg.stem}.a{ang}.txt"
            if af.exists() and af.stat().st_size > 0:
                by_angle[ang] = af.read_text(encoding="utf-8", errors="replace")
                per_angle_status.append(f"{ang}:disk")
                continue
            if since >= a.restart_every:
                kill()
                boot = start(a.model, a.mmproj, a.ctx, log, a.imgtok,
                             a.batch, a.ubatch)
                since = 0
            b64 = R.encode(pg, ang, a.width)
            atxt = None
            for attempt in range(a.retries + 1):
                try:
                    atxt, ttft, fin = run_page(URL, b64, PROMPT,
                                               a.max_tokens, a.ttft, a.timeout,
                                               a.hard)
                    break
                except Exception as e:
                    status = f"{type(e).__name__}"
                    # ⚠ A WEDGED SERVER STAYS WEDGED. Retrying against the same
                    # process burns another full deadline for nothing, so it is
                    # replaced before every retry.
                    if attempt < a.retries:
                        kill()
                        boot = start(a.model, a.mmproj, a.ctx, log, a.imgtok,
                                     a.batch, a.ubatch)
                        since = 0
                    else:
                        atxt = None
            since += 1
            if atxt:
                af.write_text(atxt, encoding="utf-8")
                by_angle[ang] = atxt
                per_angle_status.append(f"{ang}:{len(atxt.split())}w")
            else:
                per_angle_status.append(f"{ang}:FAILED")
        txt, note = union_passes(by_angle)
        status = ("ok" if len(by_angle) == len(angles)
                  else f"partial-{len(by_angle)}/{len(angles)}")
        if not by_angle:
            status = "FAILED:all-angles"
        el = time.time() - t

        if txt:
            f.write_text(txt, encoding="utf-8")
            print(f"  {i:>2}/{len(jobs)} {docn[:14]:14}/{pg.name}  "
                  f"{len(txt.split()):>5}w {el:>6.0f}s ttft {ttft:>4.0f}s  "
                  f"{status}{'  TRUNCATED' if fin=='length' else ''}", flush=True)
        else:
            # ⚠ NO FILE ON FAILURE. An empty .txt is indistinguishable from a
            # page the engine read and found nothing, and resume would treat it
            # as done forever.
            print(f"  {i:>2}/{len(jobs)} {docn[:14]:14}/{pg.name}  "
                  f"NO OUTPUT {el:>6.0f}s  {status}", flush=True)
        rows.append({"doc": docn, "page": pg.name, "sec": round(el, 1),
                     "boot": round(boot, 1), "ttft": round(ttft, 1),
                     "finish_reason": fin, "truncated": fin == "length",
                     "status": status,
                     "words": len(txt.split()) if txt else 0})

    kill()
    ok = [r for r in rows if r["status"].startswith("ok")]
    bad = [r for r in rows if not r["status"].startswith("ok")]
    (HERE / "out" / a.tag / "run.json").write_text(json.dumps(
        {"engine": a.tag, "model": a.model, "ctx": a.ctx,
         "max_tokens": a.max_tokens, "width": a.width,
         "restart_every": a.restart_every, "thinking": False,
         "prompt_variant": a.prompt_variant,
         "prompt": PROMPT,
         "imgtok": a.imgtok, "angles": angles,
         "pages": rows, "sec": round(time.time() - t0, 1),
         "note": "server restarted under the run; wall time includes model "
                 "loading and is NOT a throughput measurement"},
        indent=1), encoding="utf-8")

    inf = sum(r["sec"] for r in ok) / max(len(ok), 1)
    print(f"\n  {len(ok)}/{len(rows)} pages · {(time.time()-t0)/60:.1f} min total")
    print(f"  {inf:.0f}s per page INFERENCE ONLY (boot excluded)")
    for r in bad:
        print(f"    ⚠ {r['doc']}/{r['page']}: {r['status']} - no file, not zero")


if __name__ == "__main__":
    main()
