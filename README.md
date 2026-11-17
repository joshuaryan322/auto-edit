# Auto-Edit — graphics placement on top of ZepCut

## The honest answer to "can ZepCut do this?"

**Not on its own.** ZepCut's own SPEC lists graphics and driving CapCut as
**non-goals**, and the code matches: it is audio-driven cutting only — silence,
filler words, loudness, intro/outro concat, confidence routing. All of that works
well; the log shows it handling a 21-minute take with 82 cuts at 85/100.

What it does give you is the thing that makes graphics placement possible:
**faster-whisper with word-level timestamps.** That's the hook. This folder is
the missing stage, bolted on after ZepCut rather than inside it.

```
record (teleprompter) → OBS → ZepCut (cut + clean) → THIS → finished episode
```

---

## Why it has to run after ZepCut, not before

ZepCut removes dead air and filler words. Every timestamp from the original
recording is therefore wrong by the time it finishes — a graphic cued at 4:12 in
the raw take might belong at 3:48 in the cut.

So stage 2 transcribes **the edited file**, finds where each line was actually
spoken in the video you are about to publish, and places from that. It is immune
to whatever ZepCut cut out.

---

## Two stages

### Stage 1 — plan (no recording needed, already run)

```bash
python -I plan.py 1          # one episode
python -I plan.py all        # all 15
```

Reads the script, finds every `[GRAPHIC]` / `[ON SCREEN]` cue, works out which
rendered asset answers it, and records the **spoken line immediately before** as
an anchor. Writes `plan-epNN.json` and a readable `plan-epNN.txt`.

Research cards are handled differently: the scripts never cue them, they just
name the researcher mid-sentence. So those bind to the **first spoken mention of
the name** instead. That's why LeDoux lands at the line where he's introduced.

**Episode 1 currently places 8 of 8 assets with none unused.** Other episodes
place fewer — see *Tuning* below.

### Stage 2 — render (needs your recording)

```bash
python -I render.py 1 "C:\Users\YOUR_USER\Videos\Ready\EP01.mp4" --dry   # locate only
python -I render.py 1 "C:\Users\YOUR_USER\Videos\Ready\EP01.mp4"         # encode
```

Transcribes, fuzzy-matches each anchor, reports a confidence per placement, then
burns the graphics in. **Always run `--dry` first** — it prints every placement
with its timecode and match confidence, and flags anything it could not find,
without spending an encode.

Output: `EP01-GRAPHICS.mp4`, 1080p, H.264 CRF 18, AAC 192k. Well above what
YouTube needs — it re-encodes on upload regardless, so the goal is to hand it a
clean high-bitrate master.

---

## How graphics are placed

| Family | Mode | Why |
|---|---|---|
| T1 research cards | **overlay** | lower third — you stay on screen. Uses the alpha `.mov`. |
| T2 comparisons | cutaway | full-frame design |
| T3 building lists | cutaway | full-frame design |
| Figures F1–F12 | cutaway | full-frame design |

A cutaway replaces the picture for the asset's duration while your audio
continues. That's the right look for a video essay and it's far more robust to
automate than keying graphics over a moving face.

---

## "What if I read faster than the script assumes?"

**Placement is unaffected.** Nothing here uses the script's ⏱ timecodes. Stage 2
transcribes what you actually said and matches the anchor *sentence*. Read 20%
faster and the graphic lands 20% earlier — which is correct. The ⏱ marks only
drive the teleprompter's ahead/behind readout.

**Graphic length adapts too.** Each graphic is clamped so it cannot run past the
next cue: if you reach the following point before the asset has finished, it is
cut short there (minimum 1.2 s so nothing flashes). The `--dry` run reports
every trim, plus your actual words-per-minute against the 140 the script assumes.

Reading *slower* is harmless — the graphic simply ends and you're back on camera.

### What does break it

| Situation | What happens |
|---|---|
| You **paraphrase** the anchor line | Match degrades. Below 0.62 it is reported as NOT FOUND, never placed wrong. |
| You **skip** a line entirely | Anchor missing → reported, graphic not placed. |
| You **repeat** a phrase later | Safe — matching only moves forward, never backward. |
| You **stumble** mid-anchor and ZepCut cuts the filler | Usually still matches; fuzzy, not exact. |
| You **ad-lib** a whole passage | That graphic won't place. Re-record, or place it by hand. |

The pattern: **it fails loudly, not silently.** Every miss is printed with the
anchor it was hunting for and its best score, so you can fix it or drop it.

If one anchor keeps failing, change the anchor rather than your delivery — the
anchor is just the line before the cue, and `plan-epNN.json` is editable.

### What is NOT automated yet

**B-roll.** The scripts carry 20 `[B-ROLL]` cues and no b-roll assets exist yet —
four need shooting (night screen, real red candles, messy desk vs clean station,
the instruments), the rest are stock. Once those files exist, they slot into the
same system: add them to `cue_map.py` with a trigger and they place like anything
else.

---

## Tuning

`cue_map.py` is the file you edit. It maps asset keys to trigger phrases found in
the script's cue text. Matching is **deliberately conservative** — a cue binds
only when a trigger appears, and an unmatched cue is reported rather than guessed.
A wrong graphic on screen is worse than no graphic.

When `plan-epNN.txt` reports a cue with no asset, either add a trigger or ignore
it. Most unmatched cues are plain `[ON SCREEN: "some text"]` cards that have no
rendered asset — there are ~269 of those across the series and they were never
built as individual files. If you want them, they're T3 template fills.

One trap already hit: `"extinction"` was a trigger on the F2 figure, and it stole
the T2 suppression/extinction card because the word appears in both. Keep triggers
specific.

---

## Status

- **Stage 1 is built and run.** All 15 plans exist in this folder.
- **Stage 2 is built but UNTESTED** — it needs a real recording to run against,
  and you don't have one yet. Expect to iterate on the first episode, especially
  the `MIN_RATIO` match threshold (currently 0.62).

The first recording is the test. Run `--dry` on it before anything else.

## Setup note

The scripts contain placeholder paths (`C:\Users\YOUR_USER\...`). Change them to your own folders before running. The script text and generated plan files are not included.
Built with an AI assistant (Claude); I set the requirements and checked the results.
