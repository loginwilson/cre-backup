"""WHICH DEVICE IS ACTUALLY RUNNING THE VISION ENCODER — the question never asked.

⚠ THE WHOLE PROJECT HAS BEEN RUNNING AN ACCIDENTAL HYBRID. Every invocation passes
`-ngl 0` and every note in this repo describes the VLM as "CPU". But `-ngl 0` governs the
LANGUAGE MODEL only; llama.cpp offloads the multimodal projector separately and
`--mmproj-offload` DEFAULTS TO ENABLED. This build has Vulkan compiled in and sees
`Vulkan0: Intel Arc 140V GPU (9176 MiB, 8461 MiB free)`. So the vision tower — the one
component that touches the image — has been on the iGPU the entire time.

That reframes every failure blamed on "the encoder": `ggml_vulkan: device lost` was never
a mystery, it was the vision encoder crashing on the GPU we did not know we were using.
Login, 2026-08-17: "I think we keep running gpu instead of cpu." Correct.

⚠ AND IT INVALIDATES MY OWN "RAM WALL" READING. I read the timing curve (11s -> 89s ->
timeout across 1.6x pixels) as system memory pressure on 16 GB. With the encoder on an
iGPU carving 8 GB out of that same 16 GB, VRAM pressure produces the identical curve.
The two are not distinguishable without changing the device, which is what this does.

Three configurations, same images, same prompt:
    hybrid   -ngl 0                          LLM on CPU, vision on GPU   <- today
    cpu      -ngl 0 --no-mmproj-offload      everything on CPU
    gpu      -ngl 99                         everything on GPU (4.7 GB model, 8.4 GB free)

⚠ SCORED, NOT JUST SURVIVED. Each rung reports the ANSWER, because a config that runs
fast and reads the number wrong is worse than one that refuses. And the truth here is
itself uncertain — 732441 is unread by every channel (OCR drops a digit, the VLM flips
one), so `agreement` is reported rather than `correct`: what matters is whether a device
config changes the reading at all.
"""
from __future__ import annotations

import pathlib, subprocess, sys, time, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
from hand_test import ask, MODELS, SRV, MODEL, MMPROJ, URL, server_up

SIZES = [900, 1568, 2560]
CONFIGS = [
    ("hybrid  (today)", ["-ngl", "0"]),
    ("cpu-only", ["-ngl", "0", "--no-mmproj-offload"]),
    ("gpu-all", ["-ngl", "99"]),
]
PROMPT = ("There is a handwritten number in this image. Reply with that number's digits "
          "only, no other text. If no handwritten number is legible, reply NONE.")


def kill():
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-Process llama-server -ErrorAction SilentlyContinue | "
                    "Stop-Process -Force"], capture_output=True)
    time.sleep(3)


def start(extra, ctx=8192):
    kill()
    log = HERE / "_dev_server.log"
    fh = open(log, "wb")
    subprocess.Popen([str(SRV), "-m", str(MODELS / MODEL), "--mmproj",
                      str(MODELS / MMPROJ), "-c", str(ctx), "-np", "1",
                      "--host", "127.0.0.1", "--port", "8080", "-fa", "off"] + extra,
                     stdout=fh, stderr=fh)
    return server_up(300)


def main():
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    page = Image.open(HERE / "pages" / "FT_1680008647768" / "p010.png").convert("RGB")
    base = page.crop((300, 1430, 830, 1640))

    print(f"  base crop {base.size} · Qwen3-VL-4B Q4_K_M · ctx 8192")
    print(f"  ⚠ 732441 is unread by every channel; watch whether the DEVICE moves it\n")
    print(f"  {'config':<18}{'width':>7}{'~tok':>7}  {'answer':<16}{'sec':>8}")
    print("  " + "-" * 60)

    for name, extra in CONFIGS:
        if not start(extra):
            print(f"  {name:<18}{'—':>7}{'—':>7}  {'SERVER WOULD NOT START':<16}")
            continue
        for w in SIZES:
            img = base.resize((w, max(1, round(base.height * w / base.width))),
                              Image.LANCZOS)
            p = HERE / f"_dev_{w}.png"
            img.save(p)
            tok = (img.width * img.height) // 784
            t = time.time()
            try:
                a = ask(p, PROMPT, ntok=60, timeout=420).strip()[:14]
            except Exception as e:
                a = type(e).__name__
                # ⚠ a crash kills the slot for every later size, so restart before
                # continuing or the rest of the ladder measures this one failure
                if not start(extra):
                    print(f"  {name:<18}{w:>7}{tok:>7}  {'DEAD AFTER CRASH':<16}")
                    break
            print(f"  {name:<18}{w:>7}{tok:>7}  {a:<16}{time.time()-t:>8.1f}")
        # what the server itself says about devices
        try:
            log = (HERE / "_dev_server.log").read_text(errors="replace")
            for ln in log.splitlines():
                if any(k in ln for k in ("Vulkan", "offload", "buffer size", "using device")):
                    print(f"       | {ln.strip()[:96]}")
                    break
        except Exception:
            pass
        print()
    kill()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
