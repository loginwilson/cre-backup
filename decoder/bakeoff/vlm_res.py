"""WHAT RESOLUTION DOES THE VLM ACTUALLY WANT — measured, not inherited.

⚠ 900 PX WAS NEVER A MEASUREMENT. It entered the project as a crash workaround: a page
at 1400 hung the encoder, 900 did not, and it has been the default ever since. Login,
2026-08-17: "setting the vlm at 900 when it may need a different config is poor practice."
Correct. A ceiling picked by the first value that stopped crashing is not a configuration.

⚠ AND TWO DIFFERENT FAILURES HAVE BEEN CONFLATED. `ggml_vulkan: device lost` was measured
on GPU OFFLOAD. Today's ConnectionResetError happened at 3600 px on the CPU path with
-ngl 0, where the Vulkan backend is not loaded at all. So "Vulkan cannot handle it" may
be the wrong diagnosis for the ceiling we actually keep hitting; a 3600 px image on a
16 GB shared-memory box is an ordinary allocation blow-up. This script separates them by
running the CPU path ONLY and walking the size up until it breaks.

⚠ SCORED ON A KNOWN ANSWER, NOT ON SURVIVAL. "It returned 200" is not success. Each size
is asked to read `732441` — the one artifact OCR cannot get and the VLM demonstrably can
— so every row reports whether the answer was RIGHT, not merely present. A size that
survives and reads it wrong is worse than one that crashes honestly.

⚠ AND EACH SIZE GETS A FRESH SERVER. A wedged slot poisons every later request on this
build (`-np 1` = one slot), so a size that fails would make all larger sizes look like
they failed too. Restart between sizes or the ladder measures the first failure repeatedly.
"""
from __future__ import annotations

import json, pathlib, subprocess, sys, time, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import hand_test
from hand_test import ask, URL

TRUTH = "732441"
SIZES = [900, 1200, 1568, 2000, 2560]
CTX = int(sys.argv[1]) if len(sys.argv) > 1 else 8192
PROMPT = ("There is a handwritten number in this image. Reply with that number's digits "
          "only, no other text. If no handwritten number is legible, reply NONE.")


def kill():
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-Process llama-server -ErrorAction SilentlyContinue | "
                    "Stop-Process -Force"], capture_output=True)
    time.sleep(3)


def main():
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    page = Image.open(HERE / "pages" / "FT_1680008647768" / "p010.png").convert("RGB")
    # the region carrying the handwritten number, cropped once and then scaled
    base = page.crop((300, 1430, 830, 1640))
    print(f"  base crop {base.size} · truth {TRUTH!r} · ctx={CTX}")
    print(f"\n  {'width':>7}{'px':>12}{'~tokens':>9}  {'answer':<22}{'verdict':<9}{'sec':>7}")
    print("  " + "-" * 70)

    for w in SIZES:
        sc = w / base.width
        img = base.resize((w, max(1, round(base.height * sc))), Image.LANCZOS)
        p = HERE / f"_res_{w}.png"
        img.save(p)
        px = img.width * img.height
        # Qwen-VL packs 28x28 px per token after the 2x2 patch merge
        tok = px // (28 * 28)

        kill()
        if not hand_test.start(CTX):
            print(f"  {w:>7}{px:>12,}{tok:>9}  {'server would not start':<22}{'DEAD':<9}")
            continue
        t = time.time()
        try:
            a = ask(p, PROMPT, ntok=60, timeout=420).strip()
            el = time.time() - t
            clean = "".join(ch for ch in a if ch.isdigit())
            verdict = ("RIGHT" if clean == TRUTH
                       else "refused" if "none" in a.lower()
                       else "WRONG")
        except Exception as e:
            el = time.time() - t
            a = f"{type(e).__name__}"
            verdict = "CRASH"
        print(f"  {w:>7}{px:>12,}{tok:>9}  {a[:20]!r:<22}{verdict:<9}{el:>7.1f}")

    kill()
    print("\n  ⚠ a RIGHT at a larger size means 900 was leaving accuracy on the table;")
    print("    a CRASH names the real ceiling, which is what should be configured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
