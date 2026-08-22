# Escalation crops — independent re-read

These are small image crops cut from NYC land records. Each one is a spot where
two independent readers (a vision model and an OCR engine) failed to agree, or
where only one of them saw anything at all.

**What we need:** an independent reading of each crop by a stronger model.

## Run it

```
python read_crops.py --url http://localhost:8080 --model <your-model-name>
```

Any OpenAI-compatible endpoint works — llama.cpp `llama-server`, vLLM, Ollama.
It resumes if interrupted, so you can stop and restart it.

Send back `answers.jsonl`. Nothing else is needed.

## Please do not

- **Do not tell the model what the other engines read.** Those readings are
  deliberately not in this folder. The whole value of this pass is that it is
  independent — a model shown two candidates picks the plausible one instead of
  reading the pixels, which is precisely the failure we are testing for.
- **Do not clean up, correct, or normalise the output.** If it reads
  `MORTGAGFE` we want `MORTGAGFE`.
- **Do not skip crops that look illegible.** `[ILLEGIBLE]` is a useful answer
  and an honest one. A guess is worse than a gap.

## What is in here

| file | what |
|---|---|
| `prompts.jsonl` | one row per crop: `item_id`, `crop`, `prompt` |
| `crops/` | the PNGs |
| `read_crops.py` | the runner |
| `answers.jsonl` | what you produce |
