"""IS THE NPU FASTER THAN THE CPU FOR OCR? Measured, on the same pages.

    python npu_bench.py [n_pages]

⚠ WHY IT IS WORTH 20 MINUTES. The Arc 140V iGPU is already DISPROVEN for this
workload — devr_sweep.py records 6.65 s/pg and 3,230 chars against the CPU's
2.02 s/pg and 7,438 chars, because OCR is thousands of small variable-shape
inferences and that is the worst case for an iGPU. The NPU has never been tried.
It may lose for the same reason — NPUs want STATIC shapes — but "probably the
same reason" is a guess, and this project does not ship guesses.

⚠ SPEED ALONE IS NOT THE ANSWER. The iGPU was not merely slower, it read HALF
the characters. A device that is faster and blinder is worse than no device, so
every run reports chars alongside seconds, on identical pages, and a device that
reads materially less is REJECTED however fast it is.

⚠ AND A FAILURE TO COMPILE IS A RESULT, NOT AN ERROR TO HIDE. If the NPU refuses
a dynamic-shape model that is the finding, reported as such.
"""
from __future__ import annotations

import pathlib, statistics, sys, time, types

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

N = int(sys.argv[1]) if len(sys.argv) > 1 else 8


def reader(device, threads=4):
    """A RapidOCR bound to one device. Returns (reader, note) or raises."""
    import openvino
    shim = types.ModuleType("openvino.runtime")
    for n in dir(openvino):
        setattr(shim, n, getattr(openvino, n))
    sys.modules["openvino.runtime"] = shim

    import rapidocr_openvino.utils.infer_engine as IE
    from openvino import Core

    def patched(self, config):
        core = Core()
        self._verify_model(config["model_path"])
        m = core.read_model(config["model_path"])
        if device == "CPU":
            core.set_property("CPU", {"INFERENCE_NUM_THREADS": str(threads)})
        self.session = core.compile_model(
            model=m, device_name=device).create_infer_request()

    IE.OpenVINOInferSession.__init__ = patched
    from rapidocr_openvino import RapidOCR
    return RapidOCR()


def pages(n):
    """The same real pages for every device — a bench on different inputs is not
    a bench."""
    out = []
    for d in ("sample_pages", "devr_pages", "pages_out"):
        p = HERE / d
        if not p.exists():
            continue
        for doc in sorted(p.iterdir()):
            if not doc.is_dir():
                continue
            for t in sorted(doc.glob("p*.tif")):
                out.append(t)
                if len(out) >= n:
                    return out
    return out


def run(device, tifs):
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    t0 = time.time()
    try:
        ocr = reader(device)
    except Exception as e:
        return None, f"COMPILE FAILED: {type(e).__name__}: {str(e)[:120]}"
    setup = time.time() - t0

    import numpy as np
    times, chars = [], []
    for t in tifs:
        g = Image.open(t).convert("L")
        a = np.array(g)
        s = time.time()
        try:
            res, _ = ocr(a)
        except Exception as e:
            return None, f"INFERENCE FAILED on {t.name}: {type(e).__name__}: {str(e)[:100]}"
        times.append(time.time() - s)
        chars.append(sum(len(r[1]) for r in (res or [])))
    return {"setup_s": setup, "s_per_page": statistics.mean(times),
            "median_s": statistics.median(times),
            "chars": int(statistics.mean(chars)),
            "total_chars": sum(chars), "n": len(times)}, None


def main():
    tifs = pages(N)
    if not tifs:
        print("  no pages on disk")
        return 1
    print(f"BENCH — {len(tifs)} identical pages per device\n")
    import openvino as ov
    avail = ov.Core().available_devices
    print(f"  devices: {avail}\n")

    base = None
    for dev in ("CPU", "NPU", "GPU"):
        if dev not in avail:
            print(f"  {dev:<5} not present")
            continue
        print(f"  {dev} …", flush=True)
        r, err = run(dev, tifs)
        if err:
            # ⚠ A REFUSAL IS THE RESULT.
            print(f"  {dev:<5} ⚠ {err}\n")
            continue
        if dev == "CPU":
            base = r
        rel = f"{base['s_per_page']/r['s_per_page']:.2f}x" if base and r["s_per_page"] else "—"
        chr_rel = f"{100*r['chars']/base['chars']:.0f}%" if base and base["chars"] else "—"
        print(f"  {dev:<5} {r['s_per_page']:.2f} s/page (median {r['median_s']:.2f}) · "
              f"{r['chars']:,} chars/page · setup {r['setup_s']:.1f}s")
        print(f"        vs CPU: speed {rel} · characters {chr_rel}")
        if base and dev != "CPU":
            faster = r["s_per_page"] < base["s_per_page"]
            blind = r["chars"] < 0.9 * base["chars"]
            verdict = ("REJECT — reads materially less" if blind else
                       ("USE" if faster else "REJECT — slower"))
            print(f"        VERDICT: {verdict}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
