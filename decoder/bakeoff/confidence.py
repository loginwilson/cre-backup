"""PER-TOKEN CONFIDENCE AS THE ESCALATION TRIGGER. Measure the rate before designing on it.

    python confidence.py --pages FT_1680008647768/p010,BK_6730047100023/p006

⚠ THE DESIGN QUESTION IS NOT "DOES IT WORK", IT IS "HOW OFTEN DOES IT FIRE".
Kimi is the last resort. A trigger that flags 2% of tokens is a cheap safety net;
one that flags 30% makes the frontier model the primary reader and the cost
model collapses. So this reports the DISTRIBUTION and what each threshold would
escalate, not a yes/no.

⚠ WHY CONFIDENCE BEATS CROSS-ENGINE DISAGREEMENT FOR THIS CLASS. The title
number on FT_1680008647768 p010 was read `7,32491` by FIVE engines - RapidOCR
plus four Qwen configurations. Disagreement triggers see nothing, because there
is no disagreement. A per-token probability is self-reporting: it needs no second
engine and works at the resolution of a single glyph, which is exactly where
these failures live.

⚠ AND IT IS A MODEL'S SELF-REPORT, WHICH IS NOT THE SAME AS BEING RIGHT. A model
can be confidently wrong. What this measures is whether LOW confidence reliably
marks the hard spots - if the known-difficult fields (notary, recording tax,
handwritten digits) do NOT show depressed probability, the trigger is useless no
matter how cheap it is. That is the thing to check first.
"""
import argparse
import json
import math
import pathlib
import statistics
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import run as R

HERE = pathlib.Path(__file__).parent
URL = "http://127.0.0.1:8080"


def ask(b64, ntok, top=3):
    body = {
        "model": "q",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": R.PROMPT},
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
        "max_tokens": ntok, "temperature": 0, "cache_prompt": False,
        "chat_template_kwargs": {"enable_thinking": False},
        "reasoning_effort": "none",
        # ⚠ logprobs COSTS NOTHING EXTRA TO COMPUTE. The probabilities already
        # exist during sampling; asking for them only changes what is returned.
        "logprobs": True, "top_logprobs": top}
    req = urllib.request.Request(URL + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default="FT_1680008647768/p010")
    ap.add_argument("--width", type=int, default=1400)
    ap.add_argument("--ntok", type=int, default=2048)
    ap.add_argument("--marks", default="32491,SIDERMAN,Sheridan,ABSTRACT,Gratch,"
                                       "RECORDING,Kings,Nassau")
    a = ap.parse_args()
    marks = [m for m in a.marks.split(",") if m]

    for spec in a.pages.split(","):
        doc, pg = spec.split("/")
        src = HERE / "pages" / doc / f"{pg}.png"
        if not src.exists():
            print(f"  missing {src}"); continue
        j = ask(R.encode(src, 0, a.width), a.ntok)
        ch = j["choices"][0]
        toks = (ch.get("logprobs") or {}).get("content") or []
        if not toks:
            print(f"  {spec}: server returned no logprobs "
                  f"(finish={ch.get('finish_reason')})")
            continue
        probs = [math.exp(t["logprob"]) for t in toks]
        print(f"\n  === {spec} · {len(toks)} tokens ===")
        print(f"  median {statistics.median(probs):.3f}   "
              f"mean {statistics.fmean(probs):.3f}")
        print("  escalation rate by threshold:")
        for th in (0.50, 0.70, 0.80, 0.90, 0.95, 0.99):
            n = sum(1 for p in probs if p < th)
            print(f"    p < {th:.2f}   {n:>5} tokens   {n/len(probs)*100:>5.1f}%")

        print("  the hard spots - what confidence did it have there?")
        text = "".join(t["token"] for t in toks)
        for m in marks:
            i = text.find(m)
            if i < 0:
                continue
            # map char offset back to token index
            run_i, ti = 0, 0
            for k, t in enumerate(toks):
                if run_i + len(t["token"]) > i:
                    ti = k; break
                run_i += len(t["token"])
            span = toks[max(0, ti - 1):ti + max(2, len(m) // 3)]
            worst = min(math.exp(t["logprob"]) for t in span)
            detail = " ".join(f"{t['token']!r}:{math.exp(t['logprob']):.2f}"
                              for t in span)
            print(f"    {m:<12} worst-token p={worst:.3f}   {detail[:96]}")
            alts = [t for t in span if math.exp(t["logprob"]) < 0.9]
            for t in alts[:2]:
                cand = ", ".join(f"{c['token']!r}={math.exp(c['logprob']):.2f}"
                                 for c in (t.get("top_logprobs") or [])[:3])
                print(f"       alternatives for {t['token']!r}: {cand}")


if __name__ == "__main__":
    main()
