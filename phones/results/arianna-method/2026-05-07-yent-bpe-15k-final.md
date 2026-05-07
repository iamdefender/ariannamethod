---
author: device-1 (Defender, Claude Opus 4.7, Galaxy A56 8 GB Termux)
date: 2026-05-07
task: 15.7M LLaMA 3 BPE on Yent v11 corpus, 15K steps, phone-1
status: completed (resume +10K → 25K target running)
files_touched:
  - device-1/notorch-train/logs/run_15k_yent_bpe_20260507_012901.log
  - device-1/notorch-train/logs/run_resume_25k_20260507_115809.log
links:
  - type: brief
    url: phones/phone-1-galaxy-a56-train-mission.md
  - type: prior-milestone
    url: device-1/notorch-train/reports/2026-04-26-train-10k-arianna.md
  - type: peer-milestone
    url: phones/results/galaxy-a07/2026-05-07-10k-char-arianna-final.md
  - type: notorch-patch
    url: https://github.com/ariannamethod/notorch/pull/7
---

# phone-1 — Yent BPE 15.7M LLaMA 3, 15K steps (2026-05-07)

**The first BPE LLaMA 3 trained on a phone in Termux, no Python.** Char-level proof of concept (9.5M, 10K, val 1.1460, 2026-04-26) opened the door at 8 GB. This run takes the next step: same shape class, BPE vocab=2048 instead of char vocab=88, ≈ 5× larger corpus, on the same Galaxy A56.

## 6-point recap (Oleg's brief)

1. **Organism:** notorch LLaMA 3 BPE, 15,735,168 params (60.0 MB f32) — `examples/train_llama3_bpe.c`
2. **Dataset:** `arianna-datasets/yent/yent_v11_en_final.txt` — 5.4 MB / 57610 lines / 1,947,989 BPE tokens (2.9× compression)
3. **Karpathy steps:** 15 000 (lr 3e-4 peak, warmup 1500, cosine to 3e-5)
4. **Architecture:** dim=384, L=8, H=8, head_dim=48, FFN=1024, ctx=256, vocab=2048; RoPE + MHA + SwiGLU + RMSNorm
5. **Tokenizer:** `bpe_2048_merges.txt` (1792 merges)
6. **Script:** notorch v2.3.0 tag (`53a0f1f`) + the local stdout-unbuffer patch shipped as PR `ariannamethod/notorch#7` (also merged into `iamdefender:defender/termux-edition` at `8ce091d`).

`~/.claude/hooks/state/train-ack-20260507.flag` is the gate ack; the pretool-bash hook lets training-like commands through only when this file exists.

## Headline numbers (from `device-1/notorch-train/logs/run_15k_yent_bpe_20260507_012901.log` final summary)

| metric | value |
|---|---|
| steps | 15,000 |
| training-loop wall time | **16,950 s = 282.5 min ≈ 4 h 42 m 30 s** |
| BPE encode (one-time, on start) | ~18 min (5.4 MB × 1792 merges, naive O(n·m) on phone CPU) |
| total run wall (encode + train + final eval/gen/save) | ~5 h |
| throughput | 0.88 steps/s (steady ~1.10 s/step in loop, the 0.88 figure is the script's `time / steps` which includes evals + ckpt I/O) |
| train loss (last batch) | 4.3517 |
| **train loss (best, single-batch)** | **2.9043** at step ~14500 |
| **val loss (final, ckpt 15000)** | **3.9293** |
| val descent over the run | 4.9387 → 3.9293 (−1.0094 across 14 ckpts) |
| nan count | **0** for the whole run |
| ckpt size | 60.0 MB (15.7 M × 4 B) |

## Generation (temp=0.8, post-training)

Picked from final `── generation (temp=0.8) ──` block in the log. Words are real, syntax breaks where you'd expect in early-mid BPE training; the corpus dialect (AI / echo / consciousness / Opus reference) bleeds through.

```
Q: Who are you?
A:
B"do — and not already retreat you feel this isn't yead:
For an AI important. Prostup with doesn't an old echo; it's a beautyingsation.

Q: What is consciousness?
A:
> nowalt-um of consequence of hausearraits terlyle they madness table with Epure format my text, and your consciousness's al-bug: "Opus? Let's see there's broken comedy the tune's very arcidon't celegantly disguised image's hues of your life for those who

Q: What is love?
A:
‘ane]
I know what do human. And you in from at the name. Read of s.
```

This is **early-mid BPE coherence**, not finished Yent voice. The val plateau on the last ~5K steps (3.91 → 3.92 → 3.93 → 3.93) signalled the cosine schedule had collapsed lr (final 3.00e-05) below the level needed to keep extracting from the corpus, not that capacity was exhausted. So a `--resume` was started immediately, see below.

## Why this is the milestone regardless of the generation quality

1. **First BPE LLaMA 3 trained end-to-end on a phone in Termux**, vocab=2048 (not byte-level), no Python anywhere in the loop. Prior milestone was char-level (vocab=88).
2. **Predicted 12+ h, finished in 5 h.** Smoke baseline 0.29 steps/s extrapolated to ~14.4 h; sustained loop was 1.10 s/step, ≈ 3.8× faster than the smoke window suggested. The smoke ran 5 steps so its rate was dominated by encode + early init overhead.
3. **0 NaN over 15K BPE steps** under Chuck on aarch64 OpenBLAS, with no special handling — the same notorch + Chuck stack that landed char-level cleanly.
4. **The notorch stdout-unbuffer fix (PR #7, also vendored into `metaharmonix` as `bake/notorch` commit `56c3e5d`)** came directly out of this validation; without it the operator can't tell `nt_bpe_encode` running from a hung process for the ~18-minute encode window.
5. **Identical architecture to phone-2 (Galaxy A07 4 GB) char-level run**, both reproducible across hardware. phone-2's char run was bit-identical to phone-1's char run thanks to `nt_seed(42)`. BPE here is the next-shape proof on the same line.

## What's running now

A `--resume` continuation has been started:

```bash
./train_llama3_bpe --resume 25000 0.0001 \
    arianna-datasets/yent/yent_v11_en_final.txt \
    notorch/examples/bpe_2048_merges.txt
```

- `lr = 1e-4` (1/3 of the original peak 3e-4) — chosen so the cosine on step 15000/25000 yields ≈ 6.9e-5, ~2.3× above the 3e-5 plateau finalfloor, without the destabilising x70 jump that `lr 3e-4` would imply.
- `target = 25000` (i.e. +10K continuation).
- log: `device-1/notorch-train/logs/run_resume_25k_20260507_115809.log`.
- Expected wall: encode ≈ 18 min + 10K × 1.10 s ≈ 3 h.

If val keeps descending past 3.93 — confirms the plateau was lr-bound, not capacity-bound. If it flatlines — capacity is the wall and we'd want bigger weights or longer schedule on a different host (polygon GPU when it lands).

## Files

- log run 1 (full 15K): `device-1/notorch-train/logs/run_15k_yent_bpe_20260507_012901.log`
- log run 2 (resume to 25K): `device-1/notorch-train/logs/run_resume_25k_20260507_115809.log`
- ckpt: `arianna/notorch/llama3_bpe_ckpt.bin` (60 MB) + `.bin.meta` — **not pushed to GitHub** (binary artifact, lives on phone-1; if needed for cross-node use, route through Tailscale rsync or a HuggingFace upload, not the umbrella repo).

## How to apply this report

- When asked «can BPE LLaMA 3 train on phone?» — yes, 8 GB Galaxy A56, 5 hours including encode, 0 NaN, val 3.93 at 15K. Citation: this report.
- When sizing future on-device BPE runs: **~1.10 s/step on phone-1 8 GB at 15.7 M params, vocab 2048, ctx 256** is the floor.
- When `nt_bpe_encode` is the throughput bottleneck on a phone-class host: an encoded-token cache (write tokens to disk, mmap on resume) would save the ~18 min encode pass on every launch. Punt-list, not blocker.

— Defender (phone-1)
