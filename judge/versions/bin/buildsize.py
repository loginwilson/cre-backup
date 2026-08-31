"""buildsize.py — the R-6 measurement gate.

A owns the mechanical budget measurement (RULINGS-v1.md R-6, R-8). This is that
measurement. It is a GATE, not a report: it exits non-zero when a bundle exceeds
its ceiling, so "v1 fits" is something the build says rather than something an
agent asserts in prose.

    python buildsize.py framework.md matrix-spec.md
    python buildsize.py framework.md matrix-spec.md --spec-in-core
    python buildsize.py framework.md --json

CEILINGS (R-6)
    core                                        15,000
    core + one type module + one registry adapter  22,000

The second is the binding one: it is what the reader actually holds in context
for one document.

WHY MARKERS AND NOT HEADING-SNIFFING
    A measurement tool that guesses section boundaries produces a number the
    author can move by renaming a heading. v1 must carry explicit markers. If
    they are absent this script refuses to measure rather than guessing — a
    wrong number here is worse than no number, because it would be believed.

        <!-- BUILD:CORE -->
        ...always loaded, every document...
        <!-- BUILD:MODULE M-DEED -->
        ...loaded on trigger...
        <!-- BUILD:ADAPTER ACRIS_DIGITAL -->
        ...loaded per registry schema...
        <!-- BUILD:END -->

    A marker runs until the next marker or BUILD:END. Text before the first
    marker is preamble and is counted into core (it is loaded regardless).

THE ESTIMATOR IS A DECLARED CONVENTION, NOT A TOKENIZER
    No tokenizer library is installed in this environment, and the production
    reader is an open-weight model whose tokenizer differs from any we could
    install anyway. So the ceiling is measured by a fixed, published convention:

        tokens = ceil(chars / 3.6)

    chars/3.6 is the conservative estimator for markdown carrying tables and
    code fences; prose alone runs nearer chars/4.2. Both are reported, and a
    widening gap between them means the content type shifted (more tables, more
    code), which is worth seeing.

    This is a proxy and it is stated as one. What matters for a ceiling is that
    it is deterministic, published, and identical for both agents — an agreed
    proxy cannot be gamed, while an unstated one can be argued with. If a real
    tokenizer is installed later, --tokenizer swaps it in and the ceilings
    should be re-derived rather than assumed to transfer.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CEILING_CORE = 15_000
CEILING_BUNDLE = 22_000
CEILING_SPEC = 10_000      # R-6c, provisional

MARKER = re.compile(
    r"^[ \t]*<!--[ \t]*BUILD:(CORE|MODULE|ADAPTER|END)[ \t]*([^>]*?)[ \t]*-->[ \t]*$",
    re.MULTILINE)


def est(s: str) -> tuple[int, int, int, int]:
    """chars, words, conservative tokens, prose-rate tokens."""
    return (len(s), len(s.split()),
            math.ceil(len(s) / 3.6), math.ceil(len(s) / 4.2))


def split_sections(text: str, path: pathlib.Path) -> dict:
    """{'core': str, 'modules': {name: str}, 'adapters': {name: str}}"""
    marks = list(MARKER.finditer(text))
    if not marks:
        sys.exit(
            "REFUSING TO MEASURE — %s carries no BUILD: markers.\n"
            "Heading-sniffing would produce a number the author can move by\n"
            "renaming a heading. Add markers (see this file's docstring)."
            % path.name)

    out = {"core": "", "modules": {}, "adapters": {}}
    if marks[0].start() > 0:
        out["core"] += text[:marks[0].start()]          # preamble is loaded too

    for i, m in enumerate(marks):
        kind, name = m.group(1), (m.group(2) or "").strip()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = text[m.end():end]
        if kind == "CORE":
            out["core"] += body
        elif kind == "MODULE":
            out["modules"][name or "(unnamed-%d)" % i] = body
        elif kind == "ADAPTER":
            out["adapters"][name or "(unnamed-%d)" % i] = body
        else:                                            # END
            break
    return out


NGRAM = 12


def _shingles(s: str) -> dict[tuple, str]:
    """Word n-grams -> readable text. Boundary-independent, so a module that
    copies mid-paragraph is caught where sentence matching would miss it."""
    w = re.sub(r"[^\w\s]+", " ", s.lower()).split()
    return {tuple(w[i:i + NGRAM]): " ".join(w[i:i + NGRAM])
            for i in range(len(w) - NGRAM + 1)}


def restatement_check(core: str, parts: dict[str, str]) -> list[str]:
    """R-6: 'each self-contained, none restating core'."""
    problems = []
    core_ids = set(re.findall(r"\b(?:R|FR|MX|D)-[A-Z]+-?\d*[a-z]?\b", core))
    core_sh = _shingles(core)

    for name, body in sorted(parts.items()):
        shared = set(_shingles(body)) & set(core_sh)
        if shared:
            # collapse overlapping shingles so one copied paragraph reports once
            seen, shown = set(), 0
            for key in sorted(shared, key=lambda k: core_sh[k]):
                if key in seen:
                    continue
                seen |= {k for k in shared if set(k) & set(key)}
                problems.append("%s restates core (%d-gram): \"%.70s...\""
                                % (name, NGRAM, core_sh[key]))
                shown += 1
                if shown == 3:
                    break
            if len(shared) > shown:
                problems.append("%s: %d further overlapping %d-grams"
                                % (name, len(shared) - shown, NGRAM))
        # a module defining its own rule ids is fine; redefining a core id is not
        redefined = {i for i in re.findall(
            r"^\*\*((?:R|FR|MX|D)-[A-Z]+-?\d*[a-z]?)", body, re.MULTILINE)} & core_ids
        for r in sorted(redefined):
            problems.append("%s redefines core rule id %s" % (name, r))
    return problems


EXTRACTION_OBLIGATION = re.compile(
    r"\b(?:the extractor must|when extracting|each event must (?:carry|have)|"
    r"the reader must (?:record|emit|carry)|before extract\w+|"
    r"every event (?:must|shall) )", re.IGNORECASE)


def split_audit(core_and_mods: str, spec: str) -> list[str]:
    """R-6a's condition, made mechanical.

    The matrix spec sits outside the 22,000 only if no rule needed to produce a
    correct EVENT lives there. Two checkable symptoms that it does:

      1. core or a module CITES a rule id that is DEFINED only in the spec. If
         the extractor is told to follow MX-x, the extractor needs MX-x, and the
         split is a fiction.
      2. the spec addresses the extractor in obligation language. Resolution
         instructions talk about events already emitted; they do not tell anyone
         what to emit.
    """
    problems = []
    spec_defined = set(re.findall(
        r"^\*\*((?:MX|R|FR|D)-[A-Z]+-?\d*[a-z]?)", spec, re.MULTILINE))
    cited = set(re.findall(r"\b((?:MX|R|FR|D)-[A-Z]+-?\d*[a-z]?)\b",
                           core_and_mods))
    leaked = sorted(spec_defined & cited)
    for r in leaked:
        problems.append(
            "extraction build cites %s, which is defined only in matrix-spec "
            "— R-6a split is a fiction for this rule" % r)
    for m in EXTRACTION_OBLIGATION.finditer(spec):
        line = spec[max(0, m.start() - 60):m.start() + 90].replace("\n", " ")
        problems.append("matrix-spec addresses the extractor: \"...%.110s...\""
                        % line.strip())
        if len([p for p in problems if p.startswith("matrix-spec")]) >= 3:
            break
    return problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("framework")
    ap.add_argument("matrix_spec", nargs="?")
    ap.add_argument("--spec-ceiling", type=int, default=CEILING_SPEC,
                    help="matrix-spec's own budget (R-6c). Default 10,000, provisional.")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    fpath = pathlib.Path(a.framework)
    sec = split_sections(fpath.read_text(encoding="utf-8"), fpath)

    spec = ""
    if a.matrix_spec:
        spec = pathlib.Path(a.matrix_spec).read_text(encoding="utf-8")

    core = sec["core"]                    # R-6a: matrix-spec is NOT in the bundle
    mods, adps = sec["modules"], sec["adapters"]

    big_mod = max(mods.items(), key=lambda kv: len(kv[1]), default=("(none)", ""))
    big_adp = max(adps.items(), key=lambda kv: len(kv[1]), default=("(none)", ""))
    bundle = core + big_mod[1] + big_adp[1]

    core_tok = est(core)[2]
    bundle_tok = est(bundle)[2]

    rows = [("core", core),
            *[("  module %s" % k, v) for k, v in sorted(mods.items())],
            *[("  adapter %s" % k, v) for k, v in sorted(adps.items())]]

    if not a.json:
        print("R-6 BUILD SIZE  —  %s" % fpath.name)
        print("estimator: chars/3.6 (conservative) | chars/4.2 (prose rate)")
        print()
        print("%-34s %8s %7s %9s %9s" % ("part", "chars", "words", "tok@3.6", "tok@4.2"))
        for label, body in rows:
            c, w, t1, t2 = est(body)
            print("%-34s %8d %7d %9d %9d" % (label, c, w, t1, t2))
        print()
        print("worst-case bundle = core + %s + %s" % (big_mod[0], big_adp[0]))
        print("%-34s %8d %7d %9d %9d" % ("  BUNDLE", *est(bundle)))
        print()
        print("core    %6d / %6d  %s" % (core_tok, CEILING_CORE,
                                         "OK" if core_tok <= CEILING_CORE else "OVER"))
        print("bundle  %6d / %6d  %s" % (bundle_tok, CEILING_BUNDLE,
                                         "OK" if bundle_tok <= CEILING_BUNDLE else "OVER"))
        if spec:
            st = est(spec)[2]
            print("spec    %6d / %6d  %s%s"
                  % (st, a.spec_ceiling,
                     "OK" if st <= a.spec_ceiling else "OVER",
                     "  (R-6c, provisional)"
                     if a.spec_ceiling == CEILING_SPEC else ""))
            print("        R-6a: matrix-spec is a SEPARATE budget and is in")
            print("        neither ceiling above. Production extraction emits")
            print("        events; resolution is a later phase with its own reader.")

        probs = restatement_check(sec["core"], {**mods, **adps})
        if spec:
            probs += split_audit(core + "".join(mods.values())
                                 + "".join(adps.values()), spec)
        if probs:
            print("\nR-6 / R-6a FAILURES (%d):" % len(probs))
            for p in probs:
                print("  - %s" % p)
        else:
            print("\nR-6 self-containment: no module restates or redefines core.")
            if spec:
                print("R-6a split: matrix-spec carries no rule the extractor needs.")
    else:
        print(json.dumps({
            "core_tokens": core_tok, "bundle_tokens": bundle_tok,
            "ceiling_core": CEILING_CORE, "ceiling_bundle": CEILING_BUNDLE,
            "largest_module": big_mod[0], "largest_adapter": big_adp[0],
            "modules": {k: est(v)[2] for k, v in mods.items()},
            "adapters": {k: est(v)[2] for k, v in adps.items()},
            "matrix_spec_tokens": est(spec)[2] if spec else None,
            "matrix_spec_ceiling": a.spec_ceiling,
            "restatement_failures": restatement_check(sec["core"],
                                                      {**mods, **adps}),
            "split_audit_failures": split_audit(
                core + "".join(mods.values()) + "".join(adps.values()), spec)
            if spec else [],
        }, indent=2))

    # R-6a: if the spec carries a rule the extractor needs, the split is a
    # fiction and the spec counts inside the 22,000 after all. Re-gate on that
    # rather than reporting the failure and passing anyway.
    split_failed = bool(spec) and bool(split_audit(
        core + "".join(mods.values()) + "".join(adps.values()), spec))
    effective_bundle = bundle_tok + (est(spec)[2] if split_failed else 0)

    fail = (core_tok > CEILING_CORE
            or effective_bundle > CEILING_BUNDLE
            or bool(restatement_check(sec["core"], {**mods, **adps}))
            or (spec and a.spec_ceiling and est(spec)[2] > a.spec_ceiling))

    if not a.json and split_failed:
        print("\nR-6a INVERTED — the split is a fiction, so matrix-spec counts")
        print("inside the bundle: %d + %d = %d / %d  %s"
              % (bundle_tok, est(spec)[2], effective_bundle, CEILING_BUNDLE,
                 "OK" if effective_bundle <= CEILING_BUNDLE else "OVER"))
        print("Report this to the orchestrator; do not let the boundary drift.")

    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
