# The Daily Loop

What you asked for: sit down, hit record, read, walk away, collect a finished
episode. This is how close that is.

---

## Setup — once, about five minutes

**1. Tell OBS which episode you're on.** In OBS:
`Settings → Output → Recording → Filename Formatting`, set it to:

```
EP01-%CCYY-%MM-%DD %hh-%mm-%ss
```

Change `EP01` when you move to episode 2. That one field is the only
housekeeping in the whole loop.

*Or* skip it and edit `CURRENT_EPISODE.txt` in this folder instead — it already
holds `1`. Autopilot checks the filename first, then that file.

**2. Start autopilot.** Double-click `AUTOPILOT.bat`. Leave the window open; it
checks for new recordings every 15 seconds.

It has been seeded with the 62 recordings already in your Videos folder, so it
will **ignore everything that exists today** and only act on new files.

---

## The loop — every time

1. Open the teleprompter for the episode (`05-teleprompter/PROMPTER-NN-*.html`).
2. Hit record in OBS.
3. Read the segment. Stop recording.
4. That's it. Walk away.

Autopilot picks the file up within 15 seconds and runs:

```
ZepCut      cuts dead air, filler words, normalises loudness, adds branding
transcribe  works out when you actually said each line
graphics    places this episode's assets on those lines
            -> C:\Users\YOUR_USER\Videos\FINISHED\EP01-....mp4
```

**Nothing is deleted.** Your original recording stays in `Videos\`. ZepCut's cut
stays in `Ready\` or `Review\`. The finished file is a new file.

---

## Record segment by segment

Your scripts are already split into 9–12 segments. Record one per take and hit
record again for the next. Each becomes its own finished file.

A flub 14 minutes into a continuous take costs you 14 minutes. In a 250-word
segment it costs you 90 seconds. This is the single biggest effort saver in the
whole process and it costs nothing.

---

## Are we actually there?

**Mostly. Two honest caveats.**

**1. The graphics stage has never run on real footage.** Every piece is built and
the logic is verified, but it has never seen your voice. Expect to tune the match
threshold (`MIN_RATIO` in `render.py`, currently 0.62) after the first episode.
Budget one session of fiddling, not a rewrite.

**2. Only Episode 1 places all of its assets.** Current coverage:

| | Placed | Unused |
|---|---|---|
| EP01 | 8 / 8 | 0 |
| EP05, EP13 | 5 | 1 |
| EP02, EP07, EP11 | 4–5 | 1–3 |
| the rest | 3–4 | 1–4 |
| EP09 | 1 / 2 | 1 |

The gap is trigger phrases in `cue_map.py`, not broken code. Each unplaced asset
needs one phrase added. Ten minutes per episode, and `plan-epNN.txt` tells you
exactly which assets went unused.

**Episode 1 is ready to shoot today.** The rest will place graphics, just fewer
of them, until you top up the triggers.

---

## B-roll: deliberately dropped

You said no second-unit footage, so `[B-ROLL]` cues are now excluded from
planning entirely — they no longer clutter the unmatched report. The series is a
locked-off talking head with full-frame graphic cutaways, which is a coherent
format, not a compromise. Plenty of very good video essays are exactly this.

---

## If something goes wrong

| Symptom | Cause / fix |
|---|---|
| `SKIP - cannot tell which episode` | Filename has no `EP01` and `CURRENT_EPISODE.txt` is unset |
| Routed to `Review\` | ZepCut wasn't confident — watch it before publishing |
| `no graphics output` | No anchors matched. ZepCut's cut is still usable as-is. |
| A graphic is missing | Run `python -I render.py N "<file>" --dry` — it prints the anchor it hunted for and its best score |
| Graphic on screen too long | Already clamped to the next cue; if still wrong, the next anchor matched late |

Run `python -I autopilot.py --once` to process a backlog and exit, rather than
watching.
