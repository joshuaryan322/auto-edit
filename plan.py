"""
Stage 1 of the auto-edit: build a PLACEMENT PLAN.

Reads an episode script, finds every graphics cue, works out which rendered
asset answers it, and records the spoken line immediately before the cue as an
ANCHOR. The anchor is what stage 2 matches against the transcript of your actual
recording - which is how a graphic lands in the right place even after ZepCut has
cut dead air and filler words out from under it.

    python -I plan.py 1          # plan episode 1
    python -I plan.py all        # plan all 15

Writes plan-ep01.json plus a readable plan-ep01.txt for you to check.
Nothing is rendered here. Review the plan first.
"""
import os, re, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cue_map import (match, match_all, family, hold_mode, PLACEMENT,
                     NAME_ANCHORS, REUSE_ANCHORS)

ROOT    = r"C:\Users\YOUR_USER\Desktop\content production - claude"
SCRIPTS = r"C:\Users\YOUR_USER\Desktop\psych course\Scripts"
EPDIR   = os.path.join(ROOT, "EPISODES")
HERE    = os.path.dirname(os.path.abspath(__file__))

# B-ROLL is deliberately excluded: the series is shot as a single locked-off
# talking head with no second-unit footage, so those cues have no asset and
# would only be noise in the unmatched report.
CUE   = re.compile(r"^\s*\[(GRAPHIC|ON SCREEN|RESEARCH CARD|TITLE CARD|END CARD)"
                   r"\b(.*?)\]?\s*$", re.I)
DROP  = re.compile(r"^\s*(\[|#{1,6}\s|---+|\||\s*-\s|\*\*)", re.I)
SPEAK = re.compile(r"^\s*\[(HOST|VO)\b[^\]]*\]\s*", re.I)
INLINE= re.compile(r"\[[^\]]*\]")


def spoken(line):
    """Return the spoken text of a line, or '' if it is direction."""
    if CUE.match(line) or DROP.match(line.strip()[:2] if line.strip().startswith("[") else line):
        if not SPEAK.match(line):
            return ""
    t = SPEAK.sub("", line)
    if t.strip().startswith("["):
        return ""
    t = INLINE.sub("", t).replace("**", "").replace("*", "").strip()
    return t if len(t.split()) >= 3 else ""


def narration(line):
    """
    Word count of what is SAID on a line - used only to measure how long a
    concept is explained for.

    spoken() drops any line opening with **, because markdown emphasis is
    usually direction. Every DRILL step is written "**One.** Get an objective
    baseline...", so measuring with spoken() counted the drill as near
    silence: Episode 1's amygdala audit was credited with 67 words of
    explanation across a passage that actually runs 69 seconds, and the
    figure the viewer was being told to copy down left the screen with most
    of the drill still to come.
    """
    t = SPEAK.sub("", line)
    if CUE.match(line) or t.strip().startswith(("[", "#", "---", "|")):
        return ""
    return INLINE.sub("", t).replace("**", "").replace("*", "").strip()


def ep_paths(n):
    for d in os.listdir(EPDIR):
        if d.startswith(f"EP{n:02d}-"):
            return os.path.join(EPDIR, d, "graphics")
    return None


def script_for(n):
    for f in os.listdir(SCRIPTS):
        if f.startswith(f"{n:02d}_") and f.endswith(".md"):
            return os.path.join(SCRIPTS, f)
    return None


def build(n):
    sp, gdir = script_for(n), ep_paths(n)
    if not sp or not gdir:
        return None
    lines = open(sp, encoding="utf-8").read().splitlines()
    have  = {os.path.splitext(f)[0]: f for f in os.listdir(gdir) if f.endswith(".mp4")}

    events, unmatched, prev = [], [], []
    placed = set()                      # an asset is placed once, at its first cue

    # Cards generated straight from the scripts by cardgen.py. These bind by
    # LINE NUMBER, not by trigger phrase - the generator read the cue itself,
    # so there is nothing to infer and no chance of a phrase stealing another
    # asset's cue.
    gen = {}
    for fname, field in (("generated_cards.json", "cards"),
                         ("generated_figures.json", "figures"),
                         ("generated_bespoke.json", "figures"),
                         ("generated_final.json", "figures"),
                         ("generated_cards_frame.json", "figures")):
        gp = os.path.join(HERE, fname)
        if not os.path.exists(gp):
            continue
        for c in json.load(open(gp, encoding="utf-8")).get(field, []):
            if c["episode"] == n and have.get(c["key"]):
                gen[c["line"]] = c

    # Pass 1 - research cards bind to the first SPOKEN mention of the name,
    # because the scripts never cue them explicitly.
    for key, name in NAME_ANCHORS.items():
        # A T4 researcher plate SUPERSEDES the T1 card for the same person -
        # it says the same thing with their photograph. Where both exist the
        # card would otherwise fire a second time on the same sentence.
        # T4 is the photographic plate, T6 the typographic one for researchers
        # with no photograph. Either supersedes the T1 lower third.
        plate = (have.get(key.replace("T1_", "T4_"))
                 or have.get(key.replace("T1_", "T6_")))
        if plate:
            key = key.replace("T1_", "T4_" if "T4_" in plate else "T6_")
            fname = plate
        else:
            fname = have.get(key)
        if not fname:
            continue
        for i, line in enumerate(lines):
            s = spoken(line)
            names = [name] if isinstance(name, str) else name
            hit = next((nm for nm in names if s and nm in s.lower()), None)
            if hit:
                events.append({"line": i + 1,
                               "kind": "PLATE" if key.startswith("T4") else "RESEARCH CARD",
                               "asset": fname, "key": key,
                               "placement": PLACEMENT[family(key)],
                               "anchor": s, "cue": f"[first spoken mention of {hit}]"})
                placed.add(fname)
                break

    # Pass 1b - a returning figure usually has no cue of its own; the narrator
    # just refers back to it. Bind those to the spoken callback.
    for key, phrases in REUSE_ANCHORS.items():
        fname = have.get(key)
        if not fname or fname in placed:
            continue
        for i, line in enumerate(lines):
            s = spoken(line)
            if s and any(p in s.lower() for p in phrases):
                events.append({"line": i + 1, "kind": "CALLBACK", "asset": fname,
                               "key": key, "placement": PLACEMENT[family(key)],
                               "anchor": s, "cue": f"[spoken callback: {phrases[0]}]",
                               "explain_words": 0})
                placed.add(fname)
                break

    # Pass 2 - everything else binds to an explicit cue line.
    for i, line in enumerate(lines):
        m = CUE.match(line)
        if m:
            kind, body = m.group(1).upper(), m.group(2)
            # Build an anchor long enough to match on. "It's called myelin."
            # is three words once normalised, and compose.py refuses anchors
            # under four words - so Episode 2's myelin figure was silently
            # never placed. Reach back through the preceding lines until there
            # is enough text to identify the moment unambiguously.
            anchor = ""
            for back in reversed(prev[-3:]):
                anchor = (back + " " + anchor).strip() if anchor else back
                if len(anchor.split()) >= 8:
                    break
            g = gen.get(i + 1)
            if g and have[g["key"]] not in placed:
                events.append({
                    "line": i + 1,
                    "kind": "FIGURE" if g["key"].startswith("G_") else "CARD",
                    "asset": have[g["key"]],
                    "key": g["key"], "placement": "cutaway", "anchor": anchor,
                    "cue": line.strip()[:140], "explain_words": 0,
                    "hold": g.get("hold", "flash"),
                })
                placed.add(have[g["key"]])
                continue
            # Take the strongest candidate this episode actually has a file
            # for, not simply the strongest trigger.
            key = next((k for k in match_all(line)
                        if have.get(k) or have.get(k.replace("-REUSE", ""))
                        or have.get(k + "-REUSE")), match(line))
            if not key:
                unmatched.append({"line": i + 1, "kind": kind,
                                  "cue": line.strip()[:110], "anchor": anchor[:70]})
                continue
            base = key.replace("-REUSE", "")
            fname = have.get(key) or have.get(base) or have.get(base + "-REUSE")
            # A T1 research card may have been superseded by a photographic
            # plate (T4) or a typographic one (T6). Pass 1 knows that; this
            # pass did not, so an explicit "[RESEARCH CARD - T1: ...]" cue went
            # looking for a file that had been deliberately replaced and
            # reported it as missing art.
            if not fname and key.startswith("T1_"):
                for alt in ("T4_", "T6_"):
                    fname = have.get(key.replace("T1_", alt))
                    if fname:
                        key = key.replace("T1_", alt)
                        break
            # The already-placed test has to run on the RESOLVED filename. It
            # used to run on the key, which misses when the cue says
            # "competing pathway" (key F2_competing_pathway) and the only file
            # present is F2_competing_pathway-REUSE - the same asset lands on
            # the timeline twice.
            if fname and fname in placed:
                continue
            if not fname:
                unmatched.append({"line": i + 1, "kind": kind, "cue": line.strip()[:110],
                                  "anchor": anchor[:70], "note": f"no asset file for {key}"})
                continue
            events.append({
                "line": i + 1, "kind": kind, "asset": fname, "key": key,
                "placement": PLACEMENT[family(key)],
                "anchor": anchor,
                "cue": line.strip()[:140],
                # how many words you speak before the topic genuinely changes.
                # Filled in below once every cue line is known.
                "explain_words": 0,
            })
            placed.add(fname)
            continue
        s = spoken(line)
        if s:
            prev.append(s)
    events.sort(key=lambda e: e["line"])

    # How long is each concept actually explained for?
    #
    # The boundary is the next SEGMENT heading or the next FIGURE - NOT the
    # next [ON SCREEN] card. A card inside the span is almost always the payoff
    # of the concept being explained ("ALARM -> INTERPRETATION" belongs to the
    # two-roads diagram), so ending the hold there drops the figure right
    # before its punchline.
    SEGH = re.compile(r"^##\s+")
    FIGC = re.compile(r"^\s*\[GRAPHIC", re.I)
    hard = sorted({i for i, l in enumerate(lines, 1) if SEGH.match(l) or FIGC.match(l)})

    # An asset holds for as long as its IDEA is being explained, and the
    # script says where that ends: the next segment heading, or the next
    # [GRAPHIC] cue, because a new mechanism is a new idea. It does NOT end at
    # the next card - a card landing inside a figure's passage is a beat of
    # that same idea, not the start of a different one.
    #
    # This was previously clamped to "the next asset, whatever it is", to stop
    # a plan claiming a hold the next cutaway would truncate. That fixed the
    # reporting and broke the thing being reported: Episode 3's window of
    # tolerance - the whole point of the episode - held for 5.2 seconds,
    # because the Siegel card landed 5.2 seconds later. The real answer is for
    # the card to appear OVER the held figure rather than replace it, which is
    # what compose.py now does; so the span can go back to meaning what the
    # script says it means.
    starts = sorted(e["line"] for e in events)
    for e in events:
        idea_end = next((b for b in hard if b > e["line"]), len(lines))
        if hold_mode(e["key"]) == "flash":
            # A credibility stamp is not an idea. It ends at the next asset or
            # the idea boundary, whichever is sooner.
            nxt_ev = next((b for b in starts if b > e["line"]), len(lines))
            end = min(idea_end, nxt_ev)
        else:
            end = idea_end
        e["explain_words"] = sum(len(narration(lines[i - 1]).split())
                                 for i in range(e["line"] + 1, end))

    return {"episode": n, "script": sp, "graphics_dir": gdir,
            "events": events, "unmatched": unmatched,
            "assets_available": sorted(have)}


def write(plan):
    n = plan["episode"]
    json.dump(plan, open(os.path.join(HERE, f"plan-ep{n:02d}.json"), "w",
                         encoding="utf-8"), indent=2, ensure_ascii=False)
    L = [f"PLACEMENT PLAN - Episode {n:02d}", "=" * 64, "",
         f"script : {os.path.basename(plan['script'])}",
         f"assets : {len(plan['assets_available'])} available",
         f"placed : {len(plan['events'])}",
         f"unmatched cues : {len(plan['unmatched'])}", ""]
    L += ["PLACED", "-" * 64]
    for e in plan["events"]:
        L.append(f"  L{e['line']:<5} {e['placement']:<8} {e['asset']}")
        L.append(f"         cue    : {e['cue']}")
        L.append(f"         anchor : \"{e['anchor'][:78]}\"")
        L.append("")
    used = {e["asset"] for e in plan["events"]}
    unused = [a for a in plan["assets_available"] if a + ".mp4" not in used]
    if unused:
        L += ["ASSETS RENDERED BUT NOT PLACED", "-" * 64]
        L += [f"  {a}" for a in unused] + [""]
    if plan["unmatched"]:
        L += ["CUES WITH NO ASSET  (add a trigger in cue_map.py, or ignore)",
              "-" * 64]
        for u in plan["unmatched"]:
            L.append(f"  L{u['line']:<5} {u['kind']:<14} {u['cue']}")
            if u.get("note"):
                L.append(f"         {u['note']}")
        L.append("")
    open(os.path.join(HERE, f"plan-ep{n:02d}.txt"), "w", encoding="utf-8").write("\n".join(L))


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    eps = range(1, 16) if arg == "all" else [int(arg)]
    print(f"{'EP':<4} {'PLACED':>7} {'UNMATCHED':>10} {'ASSETS':>7} {'UNUSED':>7}")
    for n in eps:
        p = build(n)
        if not p:
            print(f"  {n:<4} -- script or graphics folder missing"); continue
        write(p)
        used = {e["asset"] for e in p["events"]}
        unused = len([a for a in p["assets_available"] if a + ".mp4" not in used])
        print(f"  {n:<4} {len(p['events']):>7} {len(p['unmatched']):>10} "
              f"{len(p['assets_available']):>7} {unused:>7}")
