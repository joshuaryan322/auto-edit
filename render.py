"""
Stage 2 of the auto-edit: place the graphics onto your recording.

Takes the video ZepCut already cleaned, transcribes it, finds where each
plan anchor was actually spoken, and burns the graphics in at those points.

    python -I render.py 1 "C:\\Users\\YOUR_USER\\Videos\\Ready\\EP01.mp4"
    python -I render.py 1 "...\\EP01.mp4" --dry     # locate only, no encode

Why transcribe the EDITED file rather than the original: ZepCut has already
removed dead air and filler words, so every timestamp from before the cut is
wrong. Transcribing the output is the only way to know when a line is actually
spoken in the video you are going to publish.

Two placement modes, decided per asset family in cue_map.py:
  cutaway - the graphic replaces the picture for its duration, your audio continues
  overlay - the graphic composites over you (research cards; needs the alpha .mov)

Output: <name>-GRAPHICS.mp4, 1080p, H.264 CRF 18 - well above what YouTube needs.
"""
import os, sys, json, subprocess, difflib, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"C:\Users\YOUR_USER\Desktop\content production - claude"
MOVS = os.path.join(ROOT, "01-motion-graphics", "mograph", "out")
CRF  = "18"           # visually transparent; YouTube re-encodes anyway
MIN_RATIO = 0.62      # below this the anchor match is not trusted


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", s.lower()).split()


def transcribe(path):
    from faster_whisper import WhisperModel
    print("  transcribing (faster-whisper small, int8)…")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(path, word_timestamps=True, language="en")
    words = []
    for s in segs:
        for w in (s.words or []):
            words.append({"w": w.word.strip(), "t": w.start})
    print(f"  {len(words)} words")
    return words


def locate(anchor, words, used_until=0.0):
    """Find where `anchor` is spoken. Returns (time, ratio) or (None, best)."""
    target = norm(anchor)
    if len(target) < 4:
        return None, 0.0
    n = len(target)
    best_t, best_r = None, 0.0
    toks = [w["w"].lower() for w in words]
    for i in range(len(words) - 3):
        if words[i]["t"] < used_until:
            continue
        window = toks[i:i + n]
        r = difflib.SequenceMatcher(None, target, window).ratio()
        if r > best_r:
            best_r, best_t = r, words[i]["t"]
    return (best_t, best_r) if best_r >= MIN_RATIO else (None, best_r)


def dur(path):
    r = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "csv=p=0", path])
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def asset_path(ev):
    """Overlays need the alpha master; cutaways can use the flat mp4."""
    if ev["placement"] == "overlay":
        mov = os.path.join(MOVS, ev["key"] + "_light.mov")
        if os.path.exists(mov):
            return mov
    return os.path.join(os.path.dirname(ev["_gdir"]), "graphics", ev["asset"])


def main():
    if len(sys.argv) < 3:
        print(__doc__); return
    ep, video = int(sys.argv[1]), sys.argv[2]
    dry = "--dry" in sys.argv
    plan = json.load(open(os.path.join(HERE, f"plan-ep{ep:02d}.json"), encoding="utf-8"))
    if not os.path.exists(video):
        print("  video not found:", video); return

    words = transcribe(video)
    cursor, timed, missed = 0.0, [], []
    for ev in plan["events"]:
        ev["_gdir"] = plan["graphics_dir"]
        t, r = locate(ev["anchor"], words, cursor)
        if t is None:
            missed.append((ev, r)); continue
        src = asset_path(ev)
        if not os.path.exists(src):
            missed.append((ev, r)); continue
        d = dur(src)
        timed.append({**ev, "at": round(t, 2), "dur": round(d, 2),
                      "src": src, "conf": round(r, 2)})
        cursor = t + 0.5

    # ---- clamp each graphic so a fast delivery cannot leave it hanging over
    # the next point. If you reach the following cue before the asset has
    # finished, the asset is cut short there. Slow delivery is harmless - the
    # graphic simply ends and you are back on camera.
    GAP = 0.4
    for i, e in enumerate(timed):
        nxt = timed[i + 1]["at"] if i + 1 < len(timed) else None
        natural_end = e["at"] + e["dur"]
        if nxt is not None and natural_end > nxt - GAP:
            e["end"] = round(max(e["at"] + 1.2, nxt - GAP), 2)
            e["trimmed"] = round(natural_end - e["end"], 2)
        else:
            e["end"] = round(natural_end, 2)
            e["trimmed"] = 0.0

    # ---- pace report: what you actually did vs what the script assumed
    spoken_secs = words[-1]["t"] if words else 0
    est = plan.get("est_minutes")
    print(f"\n  PLACED {len(timed)} / {len(plan['events'])}")
    for e in timed:
        m, s = divmod(e["at"], 60)
        flag = f"  (trimmed {e['trimmed']}s - you moved on early)" if e["trimmed"] else ""
        print(f"    {int(m):>2}:{s:05.2f}  {e['placement']:<8} conf {e['conf']:.2f}  "
              f"{e['asset']}{flag}")
    wpm = len(words) / (spoken_secs / 60) if spoken_secs > 60 else 0
    if wpm:
        print(f"\n  your pace: {wpm:.0f} wpm over {spoken_secs/60:.1f} min "
              f"(script assumes 140)")
        if wpm > 165:
            print("  NOTE: well above 140 - several graphics will have been trimmed.")
        elif wpm < 118:
            print("  NOTE: below 140 - graphics will end before you finish each point.")
    for ev, r in missed:
        print(f"    --:--     NOT FOUND (best {r:.2f})  {ev['asset']}")
        print(f"              anchor: \"{ev['anchor'][:62]}\"")

    json.dump(timed, open(os.path.join(HERE, f"timed-ep{ep:02d}.json"), "w",
                          encoding="utf-8"), indent=2, ensure_ascii=False)
    if dry or not timed:
        print("\n  dry run - nothing encoded")
        return

    # ---- build the filter graph
    inputs, filt, last = ["-i", video], [], "0:v"
    for i, e in enumerate(timed, start=1):
        inputs += ["-i", e["src"]]
        a, b = e["at"], e["end"]          # end is clamped, not a+dur
        if e["placement"] == "cutaway":
            filt.append(f"[{i}:v]setpts=PTS-STARTPTS+{a}/TB,scale=1920:1080[g{i}]")
            filt.append(f"[{last}][g{i}]overlay=0:0:enable='between(t,{a},{b})'[v{i}]")
        else:
            filt.append(f"[{i}:v]setpts=PTS-STARTPTS+{a}/TB,format=yuva420p[g{i}]")
            filt.append(f"[{last}][g{i}]overlay=0:0:enable='between(t,{a},{b})'[v{i}]")
        last = f"v{i}"
    out = os.path.splitext(video)[0] + "-GRAPHICS.mp4"
    cmd = (["ffmpeg", "-y", "-loglevel", "error", "-stats"] + inputs +
           ["-filter_complex", ";".join(filt), "-map", f"[{last}]", "-map", "0:a:0",
            "-c:v", "libx264", "-preset", "slow", "-crf", CRF, "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", out])
    print(f"\n  encoding -> {os.path.basename(out)}")
    r = subprocess.run(cmd)
    print("  done" if r.returncode == 0 else "  FFMPEG FAILED")


if __name__ == "__main__":
    main()
