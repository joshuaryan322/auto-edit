"""
AUTOPILOT - record, walk away, collect a finished episode.

Watches your OBS folder. When a new recording appears it runs the whole chain:

    new recording -> ZepCut (cut dead air, fillers, loudness, branding)
                  -> transcribe the cut
                  -> place this episode's graphics on the spoken anchors
                  -> finished MP4 in Videos\\FINISHED\\

    python -I autopilot.py            # watch forever
    python -I autopilot.py --once     # process the backlog and exit
    python -I autopilot.py --ep 1     # force the episode number

WHICH EPISODE IS THIS?
  Autopilot needs to know. In order of preference:
    1. the filename contains EP01 ... EP15  (set it once in OBS:
       Settings > Output > Recording > Filename Formatting -> EP01-%CCYY-%MM-%DD)
    2. CURRENT_EPISODE.txt in this folder holds a number
    3. --ep on the command line

Nothing is ever deleted. The original recording and ZepCut's own output both stay.
"""
import os, re, sys, time, json, shutil, subprocess

HERE    = os.path.dirname(os.path.abspath(__file__))
ZEPCUT  = r"C:\Users\YOUR_USER\Desktop\obs\zepcut\zepcut.py"
VIDEOS  = r"C:\Users\YOUR_USER\Videos"
READY   = os.path.join(VIDEOS, "Ready")
REVIEW  = os.path.join(VIDEOS, "Review")
FINISH  = os.path.join(VIDEOS, "FINISHED")
STATE   = os.path.join(HERE, ".autopilot-seen.json")
EPFILE  = os.path.join(HERE, "CURRENT_EPISODE.txt")
EXTS    = (".mp4", ".mkv")
SETTLE  = 10          # seconds of unchanged size before a file counts as finished


LOCK = os.path.join(HERE, ".autopilot.lock")


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def claim_singleton():
    """
    Refuse to start if another autopilot is already watching.

    Killing the cmd.exe window that hosts autopilot does NOT kill the python
    child. An orphaned watcher then keeps running invisibly, and when a
    recording appears BOTH instances launch ZepCut on it - two ffmpeg processes
    writing the same output file, which corrupts it and halves the speed.
    """
    import errno
    if os.path.exists(LOCK):
        try:
            pid = int(open(LOCK, encoding="utf-8").read().strip())
        except Exception:
            pid = None
        alive = False
        if pid:
            try:
                os.kill(pid, 0)          # signal 0 = existence check
                alive = True
            except OSError as e:
                alive = (e.errno == errno.EPERM)
        if alive:
            log(f"another autopilot is already running (pid {pid}) - exiting")
            log("close that window first, or delete .autopilot.lock if it is stale")
            return False
        log("found a stale lock from a dead instance - taking over")
    open(LOCK, "w", encoding="utf-8").write(str(os.getpid()))
    return True


def release_singleton():
    try:
        if os.path.exists(LOCK) and \
           open(LOCK, encoding="utf-8").read().strip() == str(os.getpid()):
            os.remove(LOCK)
    except Exception:
        pass


def seen():
    try:
        return set(json.load(open(STATE, encoding="utf-8")))
    except Exception:
        return set()


def mark(name):
    s = seen(); s.add(name)
    json.dump(sorted(s), open(STATE, "w", encoding="utf-8"), indent=1)


PROJECTS = r"C:\Users\YOUR_USER\Desktop\obs\zepcut\projects.json"


def _cfg():
    try:
        return json.load(open(PROJECTS, encoding="utf-8"))
    except Exception:
        return {}


def graphics_enabled():
    """The Graphics tab's toggle in ZepCut Studio. Off => ZepCut only."""
    return bool(_cfg().get("graphics_enabled", True))


def faceless_dir():
    """
    Faceless mode builds the whole picture from the script instead of
    overlaying graphics on footage. Returns the 07-faceless path, or None
    when the project is shot as a talking head.
    """
    d = _cfg()
    if d.get("mode") != "faceless":
        return None
    p = d.get("projects", {}).get(d.get("active"), {}).get("faceless")
    return p if p and os.path.isdir(p) else None


def finished_name(ep, stem):
    """
    Final filename. OBS already writes files starting with EP01, so blindly
    prefixing produced "EP01-EP01-2026-10-21...". Only add the prefix when the
    recording does not already carry one.
    """
    if re.match(rf"EP0?{ep}\b", stem, re.I):
        return os.path.join(FINISH, f"{stem}.mp4")
    return os.path.join(FINISH, f"EP{ep:02d}-{stem}.mp4")


def episode_of(path, forced=None):
    if forced:
        return forced
    m = re.search(r"EP(\d{1,2})", os.path.basename(path), re.I)
    if m:
        return int(m.group(1))
    if os.path.exists(EPFILE):
        try:
            return int(re.sub(r"\D", "", open(EPFILE, encoding="utf-8").read())[:2])
        except Exception:
            pass
    return None


def stable(path):
    try:
        a = os.path.getsize(path); time.sleep(SETTLE); b = os.path.getsize(path)
        return a == b and b > 0
    except OSError:
        return False


def zepcut_output(stem):
    for d in (READY, REVIEW):
        p = os.path.join(d, stem + ".mp4")
        if os.path.exists(p):
            return p, os.path.basename(d)
    return None, None


def process(raw, forced=None):
    name = os.path.basename(raw)
    ep = episode_of(raw, forced)
    if ep is None:
        log(f"SKIP {name} - cannot tell which episode. "
            f"Put EP01 in the filename or set CURRENT_EPISODE.txt")
        return False
    plan = os.path.join(HERE, f"plan-ep{ep:02d}.json")
    if not os.path.exists(plan):
        log(f"SKIP {name} - no plan for episode {ep}. Run: python -I plan.py {ep}")
        return False

    log(f"EP{ep:02d}  {name}")
    log("  1/3 ZepCut - cutting dead air, fillers, loudness…")
    r = subprocess.run([sys.executable, "-I", ZEPCUT, "edit", raw],
                       capture_output=True, text=True)
    if r.returncode not in (0, 2):
        log(f"  ZepCut failed:\n{r.stdout[-800:]}{r.stderr[-400:]}")
        return False

    stem = os.path.splitext(name)[0]
    cut, route = zepcut_output(stem)
    if not cut:
        log("  ZepCut produced no output (too short, or silent). Stopping.")
        return False
    log(f"  ZepCut -> {route}/{os.path.basename(cut)}")
    if route == "Review":
        log("  NOTE: routed to Review - ZepCut was not confident. "
            "Watch the result before publishing.")

    if not graphics_enabled():
        log("  graphics stage is switched OFF in ZepCut Studio (Graphics tab)")
        log(f"  DONE -> {route}/{os.path.basename(cut)}  (cut only, no graphics)")
        return True

    fl = faceless_dir()
    if fl and _cfg().get("segmented"):
        # Segmented recording: each take is cleaned but NOT composed. Composing
        # every take would produce one video per take, each with its own title
        # card. assemble.py joins them and composes once.
        log(f"  segmented mode - take cleaned and held in {route}/")
        log(f"  when all takes are recorded, run:")
        log(f"      python \"{os.path.join(fl, 'assemble.py')}\" {ep}")
        return True

    if fl:
        log("  2/3 building the picture from the script (faceless)…")
        r = subprocess.run([sys.executable, os.path.join(fl, "compose.py"),
                            str(ep), cut], capture_output=True, text=True, cwd=fl)
        print("\n".join("      " + l for l in r.stdout.splitlines() if l.strip()))
        if r.returncode != 0:
            log(f"  compose failed:\n{r.stderr[-700:]}")
            return False
        final = os.path.join(fl, f"EP{ep:02d}-FACELESS.mp4")
        if not os.path.exists(final):
            log("  compose produced no output")
            return False
        os.makedirs(FINISH, exist_ok=True)
        shutil.move(final, finished_name(ep, stem))
        log(f"  3/3 DONE -> FINISHED\\{os.path.basename(finished_name(ep, stem))}")
        return True

    log("  2/3 placing graphics on the spoken anchors…")
    r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "render.py"),
                        str(ep), cut], capture_output=True, text=True)
    print("\n".join("      " + l for l in r.stdout.splitlines() if l.strip()))
    if r.returncode != 0:
        log(f"  graphics stage failed:\n{r.stderr[-600:]}")
        return False

    final = os.path.splitext(cut)[0] + "-GRAPHICS.mp4"
    if not os.path.exists(final):
        log("  no graphics output - nothing placed. ZepCut's cut is still in "
            f"{route}/ and is usable as-is.")
        return False

    os.makedirs(FINISH, exist_ok=True)
    dest = os.path.join(FINISH, f"EP{ep:02d}-{stem}.mp4")
    shutil.move(final, dest)
    log(f"  3/3 DONE -> FINISHED\\{os.path.basename(dest)}")
    return True


def scan(forced=None, once=False):
    os.makedirs(FINISH, exist_ok=True)
    done = seen()
    found = 0
    for f in sorted(os.listdir(VIDEOS)):
        if not f.lower().endswith(EXTS) or f in done:
            continue
        p = os.path.join(VIDEOS, f)
        if not os.path.isfile(p):
            continue
        if not stable(p):
            log(f"  {f} still being written - leaving for next pass")
            continue
        found += 1
        try:
            process(p, forced)
        except Exception as exc:
            log(f"  ERROR on {f}: {exc}")
        mark(f)
    return found


def main():
    forced = None
    if "--ep" in sys.argv:
        forced = int(sys.argv[sys.argv.index("--ep") + 1])
    once = "--once" in sys.argv
    if not claim_singleton():
        return
    import atexit
    atexit.register(release_singleton)
    log(f"autopilot watching {VIDEOS}")
    log(f"finished episodes -> {FINISH}")
    if forced:
        log(f"episode forced to EP{forced:02d}")
    if once:
        n = scan(forced, once=True)
        log(f"backlog done ({n} file(s))")
        return
    try:
        while True:
            scan(forced)
            time.sleep(15)
    except KeyboardInterrupt:
        log("stopped")


if __name__ == "__main__":
    main()
