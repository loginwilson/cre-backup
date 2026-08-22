"""EVERY ENGINE AT ITS OWN MAXIMUM. Anything less is not a comparison.

⚠ THE UNFAIRNESS THIS FIXES WAS REAL AND IT WAS MINE. Tesseract was measured
running 8 parallel processes (4.4 pages/s) while Qwen was measured one image at
a time through a CLI that loads the model, encodes, generates, and exits — per
page. That is a 176x gap partly manufactured by how I invoked them. An engine
compared at its worst configuration against another at its best has not been
compared; it has been sandbagged.

So each engine here gets the parallelism its architecture actually supports:

    tesseract   8 OS processes            CPU-bound, scales on cores
    paddleocr   process pool              heavy init, so init ONCE per worker
    rapidocr    process pool              same
    qwen        llama-server -np 4 -cb    ONE model resident, continuous
                                          batching across slots — the GPU
                                          equivalent of 8 processes

⚠ AND THE MODEL STAYS RESIDENT, WHICH IS THE REAL FIX. The CLI paid ~25s of
model load on EVERY page. A server pays it once. That alone is most of the gap,
and it is an artefact of measurement rather than a property of the model.

⚠ WALL-CLOCK FOR THE WHOLE SET IS THE NUMBER. Per-page timings mislead when
requests overlap: four pages finishing in 60s each, concurrently, is 15s/page
of throughput, not 60.

    python bench_all.py tesseract|paddle|rapid|qwen [workers]
"""
import base64
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ⚠ THE BENCH DIRECTORY IS A PARAMETER because the set that matters changed:
# render/bench2 came out of sample_pages, which is the same material every psm
# mode, render width and frame list was tuned against all session. render/live
# is fetched fresh from the endpoint by map-selected document ids and has never
# been seen. Measuring on what you tuned on measures the tuning.
BENCH = pathlib.Path(os.environ.get("BENCH_DIR", "render/live"))
TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SERVER = "http://127.0.0.1:8080/v1/chat/completions"
CORES = os.cpu_count()

PROMPT = ("Transcribe every word of text visible in this scanned document page, "
          "exactly as printed. Include reel and page stamps, document numbers, "
          "names, dollar amounts and dates. Do not summarize.")


def pages():
    man = json.loads((BENCH / "manifest.json").read_text(encoding="utf-8"))
    return man, [BENCH / m["file"] for m in man]


# ── engines ──────────────────────────────────────────────────────────────
def do_tess(p):
    r = subprocess.run([TESS, str(p), "stdout", "--psm", "4"],
                       capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return " ".join(r.stdout.split())


def _texts(res):
    out = []
    for r in res or []:
        d = r.get("rec_texts") if isinstance(r, dict) else getattr(r, "rec_texts", None)
        if d:
            out += list(d)
    return " ".join(out)


def paddle_batch(files):
    """ONE process, ALL pages, threads = cores. The correct maximum for Paddle.

    ⚠ A PROCESS POOL IS THE WRONG SHAPE HERE AND WOULD HAVE SANDBAGGED IT. The
    pipeline costs ~15s to build, so 4 workers pay ~60s of startup on a 20-page
    run — more than the recognition itself. That would have been measured as
    "Paddle is slow" when it is really "I invoked it four times". The same
    mistake I made with Qwen, where a CLI reloaded 2.4 GB of weights per page.

    ⚠ AND DISABLING THE PREPROCESSORS IS PART OF THE CALIBRATION, NOT A HANDICAP.
    Orientation classification and unwarping are separate models run per page;
    on these scans they cost time and, measured earlier on film, blind geometric
    correction actively destroyed pages (70% -> 30% phrase recall).
    """
    from paddleocr import PaddleOCR
    kw = dict(lang="en")
    # ⚠ oneDNN MUST BE OFF OR PADDLE DOES NOT RUN AT ALL ON THIS BUILD. It dies
    # with `ConvertPirAttribute2RuntimeAttribute not support
    # [pir::ArrayAttribute<pir::DoubleAttribute>]` inside the oneDNN executor —
    # a PaddleX/oneDNN version mismatch, nothing to do with the documents.
    # Worth stating plainly: this is a SLOWER configuration, so Paddle's timing
    # below is a floor, not its best. It is not being sandbagged on purpose,
    # but it is not at its maximum either, and the table must say so.
    for extra in (dict(use_doc_orientation_classify=False, use_doc_unwarping=False,
                       use_textline_orientation=False, cpu_threads=CORES,
                       enable_mkldnn=False),
                  dict(use_doc_orientation_classify=False, use_doc_unwarping=False,
                       use_textline_orientation=False, enable_mkldnn=False),
                  dict(use_doc_orientation_classify=False, use_doc_unwarping=False,
                       use_textline_orientation=False, cpu_threads=CORES),
                  dict(use_doc_orientation_classify=False, use_doc_unwarping=False,
                       use_textline_orientation=False),
                  dict(use_angle_cls=False)):
        try:
            ocr = PaddleOCR(**kw, **extra)
            break
        except TypeError:
            continue
    else:
        ocr = PaddleOCR(lang="en")
    out = []
    for p in files:                      # predict() streams; one warm pipeline
        try:
            out.append(_texts(ocr.predict(str(p))))
        except AttributeError:
            res = ocr.ocr(str(p), cls=False)
            out.append(" ".join(l[1][0] for blk in (res or []) if blk for l in blk))
    return out


def rapid_batch(files):
    """ONE process, onnxruntime given every core. Same reasoning as Paddle."""
    from rapidocr_onnxruntime import RapidOCR
    try:
        eng = RapidOCR(intra_op_num_threads=CORES)
    except TypeError:
        eng = RapidOCR()
    out = []
    for p in files:
        r, _ = eng(str(p))
        out.append(" ".join(x[1] for x in (r or [])))
    return out


_RAPID = {}


def rapid_one(p):
    """RAPIDOCR ACROSS PROCESSES, one lightweight session per worker.

    ⚠ RAPID WAS THE ONLY ENGINE MEASURED AT ONE PROCESS, AND IT IS CURRENTLY
    WINNING. Reporting 0.072 pages/s as 'RapidOCR's speed' while Tesseract runs
    8-wide would repeat exactly the sandbagging this file was written to stop,
    only pointed at a different engine. onnxruntime's intra-op threads do not
    saturate 8 cores on images this size — the parallelism has to come from
    processes.

    ⚠ AND intra_op IS FORCED TO 1 HERE ON PURPOSE. 8 processes x 8 intra-op
    threads is 64 threads on 8 cores; they would fight for cache and run
    SLOWER, which would read as 'parallelism does not help Rapid'.
    """
    from rapidocr_onnxruntime import RapidOCR
    if "e" not in _RAPID:
        try:
            _RAPID["e"] = RapidOCR(intra_op_num_threads=1)
        except TypeError:
            _RAPID["e"] = RapidOCR()
    r, _ = _RAPID["e"](str(p))
    return " ".join(x[1] for x in (r or []))


ARTIFACT_PROMPT = (
    "From this scanned land-record page, list ONLY the following if present, "
    "one per line as FIELD: VALUE. Skip anything absent. Do not transcribe the "
    "page and do not explain.\n"
    "REEL / PAGE stamp; LIBER / PAGE; DOCUMENT ID; DOCUMENT TYPE; DOCUMENT DATE; "
    "RECORDED DATE; BLOCK; LOT; UNIT; ADDRESS; GRANTOR / PARTY ONE; "
    "GRANTEE / PARTY TWO; LENDER; BORROWER; DOLLAR AMOUNTS; SQUARE FEET; "
    "COUNTY / BOROUGH; PARTY WALL; EASEMENT.")


def do_qwenfast(p):
    """⚠ SPEED COMES FROM THE PROMPT, NOT THE HARDWARE.

    "Transcribe every word" makes the model GENERATE the page - 878 tokens on a
    dense page, ~98s of purely sequential decoding, and the pipeline throws the
    prose away. Naming the fields bounds output to ~150 tokens. Same model, same
    GPU, same pixels; the only change is how much it is asked to say.

    ⚠ AND IT IS DOWNSCALED TO 1000px because I raised the bench render to 1400
    mid-session and doubled the vision-token cost without noticing. The runs that
    looked fast earlier were 1000px.
    """
    import io as _io
    from PIL import Image as _Image
    im = _Image.open(p)
    if im.mode == "1":
        im = im.convert("L")
    if im.width != 1000:
        im = im.resize((1000, int(im.height * 1000 / im.width)), _Image.LANCZOS)
    buf = _io.BytesIO(); im.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    body = json.dumps({"messages": [{"role": "user", "content": [
        {"type": "text", "text": ARTIFACT_PROMPT},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
        "max_tokens": 320, "temperature": 0}).encode()
    req = urllib.request.Request(SERVER, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def do_qwen(p):
    """QWEN AS A PLAIN OCR: read the page, no field list, no structure.

    ⚠ THIS IS THE SLOWEST MODE THE MODEL HAS, AND THAT IS INHERENT. Cost here
    is per OUTPUT TOKEN, not per pixel. Tesseract reads a page in one pass;
    Qwen must emit every word sequentially at ~13.5 tok/s on this iGPU, so a
    1,000-word page is ~1,300 tokens ~= 96 seconds no matter how it is tuned.
    "No instructions, maximum speed" is a contradiction for a VLM: the reading
    IS the writing.

    ⚠ AND max_tokens MUST BE HIGH ENOUGH OR THE PAGE IS SILENTLY TRUNCATED,
    which would score as a reading failure that never happened. Dense pages hit
    878 tokens against the old 1100 cap. At 1000px the image is ~1,650 tokens
    of a 4,096 slot, so ~2,048 output is affordable.
    """
    import io as _io
    from PIL import Image as _Image
    im = _Image.open(p)
    if im.mode == "1":
        im = im.convert("L")
    if im.width != 1000:
        im = im.resize((1000, int(im.height * 1000 / im.width)), _Image.LANCZOS)
    buf = _io.BytesIO(); im.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    body = json.dumps({
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
        "max_tokens": 2048, "temperature": 0, "stream": False}).encode()
    req = urllib.request.Request(SERVER, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        d = json.load(r)
    return d["choices"][0]["message"]["content"]


# mode "batch" = the engine handles the whole list itself, warm, once.
ENGINES = {
    "tesseract": (do_tess, "thread", CORES),    # OS processes, scales on cores
    "paddle":    (paddle_batch, "batch", 1),    # one warm pipeline, cpu_threads=CORES
    "rapid":     (rapid_batch, "batch", 1),     # one session, intra-op = CORES
    "qwen":      (do_qwen, "thread", 4),        # concurrency = server slots
    "qwenfast":  (do_qwenfast, "thread", 1),    # artifact prompt, 1000px
    "rapidpool": (rapid_one, "process", CORES),  # 8 processes, intra-op 1 each
}


def main():
    name = sys.argv[1]
    fn, mode, default_w = ENGINES[name]
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else default_w
    man, files = pages()
    out = BENCH / name
    out.mkdir(exist_ok=True)

    print(f"  {name}   {len(files)} pages   {workers} {mode}s   "
          f"({CORES} cores available)\n")

    t0 = time.time()
    if mode == "batch":
        # ⚠ THE ENGINE OWNS ITS OWN PARALLELISM HERE. Wrapping a warm batched
        # pipeline in a process pool would re-pay its init per worker, which is
        # exactly the sandbagging this file exists to avoid.
        texts = fn(files)
    else:
        Pool = ThreadPoolExecutor if mode == "thread" else ProcessPoolExecutor
        with Pool(max_workers=workers) as ex:
            texts = list(ex.map(fn, files))
    el = time.time() - t0

    for m, p, t in zip(man, files, texts):
        (out / (p.name + ".txt")).write_text(t or "", encoding="utf-8")
        m[f"{name}_words"] = len((t or "").split())
    (BENCH / "manifest.json").write_text(json.dumps(man, indent=1), encoding="utf-8")

    # ⚠ THE TIME COLUMN WAS ALWAYS EMPTY BECAUSE NOTHING EVER WROTE IT. score.py
    # reads `<engine>_sec` off the manifest; this file only ever wrote
    # `<engine>_words`. So the accuracy/speed table — the entire deliverable —
    # had a permanent '-' where speed belonged, and I would have had to quote
    # timings from memory instead of from disk.
    tf = BENCH / "timings.json"
    tj = json.loads(tf.read_text(encoding="utf-8")) if tf.exists() else {}
    tj[name] = {"sec": round(el, 1), "pages": len(files),
                "pages_per_sec": round(len(files) / el, 4),
                "workers": workers, "mode": mode}
    tf.write_text(json.dumps(tj, indent=1), encoding="utf-8")

    tot = sum(len((t or "").split()) for t in texts)
    print(f"  {'page':<52}{'words':>7}")
    for m, t in zip(man, texts):
        print(f"  {m['file'][:51]:<52}{len((t or '').split()):>7}")
    print(f"\n  WALL CLOCK {el:>8.1f}s   {len(files)/el:>6.3f} pages/s   "
          f"{tot:,} words")
    print(f"  -> {out}")
    print(f"\n  ⚠ words are not a score. A model can emit 900 fluent words of")
    print(f"    hallucination; scoring is against pages read by hand.")


if __name__ == "__main__":
    main()
