"""
Turn the scripts' [ON SCREEN] cues into renderable assets.

243 of these cues had no asset. They are not 243 design problems - the writer
already wrote the text and already said which treatment it gets:

    [ON SCREEN - large: "You are not fighting a malfunction."]
    [ON SCREEN: THESIS CARD - "You do not have a discipline problem."]
    [ON SCREEN: numbered list]

So this reads the cue, pulls the line, picks the variant, and emits a spec.
t5_statement.py renders the statements, t3_building_list.py renders the lists,
and plan.py binds them by LINE NUMBER - no trigger phrases, because we know
exactly which cue each one answers.

    python -I cardgen.py            # scan, classify, write the spec
    python -I cardgen.py --show     # print every card for review first

Review before you render. Statement cards are quoted verbatim and safe; LIST
items are derived from the sentences that follow the cue, and that derivation
is the only place this guesses.
"""
import json, os, re, sys, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan import script_for, spoken, CUE, SPEAK, INLINE                      # noqa: E402
from cue_map import match                                     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "generated_cards.json")

# The nine T3 lists that are hand-authored in data.py. Everything else named
# T3_* was generated here, so it does not own its cue against this script.
HAND_T3 = {"T3_ep01_amygdala_audit", "T3_ep05_elite_traits",
           "T3_ep08_five_phase", "T3_ep08_three_rings", "T3_ep11_pretrade",
           "T3_ep14_improvement", "T3_ep14_three_phases",
           "T3_ep15_circuit_breaker", "T3_ep15_three_layers"}

QUOTE = re.compile(r'["“”]([^"“”]{3,})["“”]')
ONSCR = re.compile(r"^\s*\[ON SCREEN\b(.*)\]\s*$", re.I)

# A cue's modifier picks the treatment. Longest match wins, so "the thesis,
# large" reads as a thesis card rather than a large one.
VARIANTS = [
    ("thesis card",  "thesis"),   ("the thesis",   "thesis"),
    ("callback bar", "callback"), ("callback",     "callback"),
    ("struck through", "strike"), ("crossed out",  "strike"),
    ("small, honest", "small"),   ("the required note", "small"),
    ("small",        "small"),    ("large",        "large"),
]

# Items in a built list are spoken, one per paragraph, opened by an ordinal.
ORDINAL = re.compile(r"^\**(One|Two|Three|Four|Five|Six|Seven)\b[\.—\-:,]*\**\s*",
                     re.I)
LISTCUE = re.compile(r"\b(numbered list|cards? in sequence|bullets?|"
                     r"appear in sequence|levers appear|list,? building|"
                     r"tools appearing|building line by line)\b", re.I)

# Cues that describe a DIAGRAM, not text. These stay unmatched and get reported
# - inventing a figure from a one-line description is exactly the guess that
# puts the wrong thing on screen.
FIGURE = re.compile(r"\b(chart|graph|curve|diagram|axis|quadrant|timeline|"
                    r"radar|waveform|scan)\b", re.I)


def slug(s, n=4):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    words = re.findall(r"[a-z0-9]+", s.lower())
    stop = {"the", "a", "an", "is", "are", "you", "your", "of", "to", "and",
            "it", "in", "that", "this", "not", "for", "on", "but", "with"}
    keep = [w for w in words if w not in stop] or words
    return "_".join(keep[:n])[:38] or "card"


def variant_of(mod):
    m = mod.lower()
    for needle, v in VARIANTS:
        if needle in m:
            return v
    return "statement"


def trim(item):
    """
    A list row is a label, not the sentence. These scripts front-load the
    point - "You replay it in slow motion, in writing. What was the exact
    cue?" - so the first clause IS the label, and anything past the first
    hard stop is the narration that goes with it.
    """
    t = ORDINAL.sub("", item).replace("**", "").replace("*", "").strip()
    t = re.split(r"(?<=[a-z\)\"])\s*[—\-–]\s+|\.\s+|\?\s+|:\s+", t)[0]
    t = t.strip(" .,;:—-")
    t = t.lstrip("\"“‘'")
    if len(t) > 54:
        cut = t[:54].rsplit(" ", 1)[0].rstrip(" ,;:")
        t = cut + "…"
    return t[:1].upper() + t[1:] if t else t


def duration(body, variant):
    w = len(body.split())
    base = 2.0 + w * 0.26
    return round(min(max(base, 2.6), 7.5 if variant != "callback" else 5.5), 1)


COUNTWORD = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7}

# The narrator's run-up into a list is not a row of it. "Lock it in." and
# "Big one." are performance, not content, and they look absurd as item 1.
LEADIN = ("lock it in", "big one", "big episode", "let’s lock", "let's lock",
          "our biggest", "here’s", "here's", "sit with", "and here",
          "that pattern", "read before", "and now", "that’s the",
          "that's the", "and the whole thing", "lets lock")


def is_leadin(s):
    t = s.lower().lstrip("“‘\"' ")
    return any(t.startswith(p) for p in LEADIN)


def drill_spoken(line):
    """
    spoken() for list extraction only.

    plan.py's spoken() drops any line beginning with ** - markdown emphasis is
    normally direction, not narration. But every DRILL step in every episode is
    written "**One.** Get an objective baseline...", so that rule made all
    fourteen drills invisible to the extractor while the recaps, which happen
    to be written without bold, came through fine. The planner's anchors depend
    on spoken() behaving as it does, so this is a local relaxation rather than
    a change to it.
    """
    t = SPEAK.sub("", line)
    if CUE.match(line) or t.strip().startswith(("[", "#", "---", "|")):
        return ""
    t = INLINE.sub("", t).replace("**", "").replace("*", "").strip()
    return t if len(t.split()) >= 3 else ""


def list_items(lines, i, mod):
    """
    The rows of a built list, taken from the paragraphs the cue introduces.

    Two shapes appear in these scripts and both have to work:

      ordinal   "**One.** After every session - not at the end of the week..."
      parallel  "It degrades working memory - so you lose your grip..."
                "It amplifies confirmation bias - so you filter for..."

    The cue usually says how many to expect ("four bullets appear as host
    names them"), and that count is the most reliable signal there is, so it
    caps the run. Without one, stop at the first new cue or heading.
    """
    words = set(re.findall("[a-z]+", mod.lower()))
    want = next((v for k, v in COUNTWORD.items() if k in words), None)
    ordinals, plain = [], []
    for j in range(i + 1, min(i + 34, len(lines))):
        if re.match(r"^##\s+", lines[j]):
            break
        if CUE.match(lines[j]):
            if ordinals or plain:
                break
            continue
        raw = drill_spoken(lines[j]).strip()
        if not raw:
            continue
        if ORDINAL.match(raw):
            ordinals.append(trim(raw))
        elif not is_leadin(raw):
            plain.append(trim(raw))
        if want and len(ordinals) >= want:
            break
        if want and not ordinals and len(plain) >= want:
            break
    items = [it for it in (ordinals or plain) if len(it) > 12]
    if want:
        items = items[:want]
    return items if 3 <= len(items) <= 7 else []


def heading_for(lines, i):
    """Nearest preceding segment heading, as the list's title."""
    for j in range(i, max(-1, i - 60), -1):
        if re.match(r"^##\s+", lines[j]):
            h = re.sub(r"^#+\s*", "", lines[j])
            # "## Segment 6 - The Drill: The Baseline Audit [stopwatch] 15:00"
            # -> "The Drill: The Baseline Audit". The timing is a production
            # note and the segment number means nothing to a viewer.
            h = re.sub(r"[⏱⏰⌚].*$", "", h)
            h = re.sub(r"\s*\d{1,2}:\d{2}\s*$", "", h)
            h = re.sub(r"^Segment\s*\d+\s*[—\-–:]\s*", "", h, flags=re.I)
            h = h.strip(" —-:")
            return (h or "Recap")[:46]
    return "The Drill"


def scan(n):
    sp = script_for(n)
    if not sp:
        return []
    lines = open(sp, encoding="utf-8").read().splitlines()
    # Lines already answered by a HAND-BUILT asset. A line answered by a card
    # this script generated on a previous run is not a conflict - it is this
    # script's own output, and counting it collapsed the whole spec to a
    # handful of entries the moment the plans were rebuilt.
    # Decided by key prefix, NOT by reading the previous spec file. Reading the
    # spec made the guard self-referential: one bad run overwrote the file,
    # and every later run then had no record of its own output and collapsed
    # the spec to a handful of entries. A rule that cannot be corrupted by its
    # own output is worth more here than a precise one.
    #
    # T5 exists only because this script makes it. Everything below is
    # hand-built or comes from another generator, and owns its cue.
    HANDBUILT = ("T1_", "T2_", "T4_", "F", "G_", "H_")
    pf = os.path.join(HERE, f"plan-ep{n:02d}.json")
    placed_lines = set()
    if os.path.exists(pf):
        placed_lines = {e["line"] for e in
                        json.load(open(pf, encoding="utf-8"))["events"]
                        if e["key"].startswith(HANDBUILT)
                        or e["key"] in HAND_T3}
    out, used = [], {}
    for i, line in enumerate(lines):
        m = ONSCR.match(line)
        if not m:
            continue
        # A cue the planner has already answered has a hand-built asset, and a
        # text card on the same line would put two things on one sentence.
        # Checked against the PLAN, not against cue_map.match: match() is a
        # substring test, so a card quoting "suppression" collides with the
        # suppression/extinction comparison in a different episode entirely.
        if (i + 1) in placed_lines:
            continue
        mod = m.group(1)
        q = QUOTE.search(line)
        if q:
            body = q.group(1).strip()
            v = variant_of(mod.replace(body, ""))
            key = f"T5_ep{n:02d}_{slug(body)}"
            used[key] = used.get(key, 0) + 1
            if used[key] > 1:
                key = f"{key}_{used[key]}"
            out.append({"episode": n, "line": i + 1, "template": "T5", "key": key,
                        "variant": v, "body": body, "dur": duration(body, v),
                        "hold": "hold" if "held" in mod.lower() else "flash",
                        "cue": line.strip()[:140]})
        elif LISTCUE.search(mod):
            items = list_items(lines, i, mod)
            if len(items) < 2:
                continue               # nothing to build - leave it unmatched
            key = f"T3_ep{n:02d}_{slug(items[0], 3)}"
            used[key] = used.get(key, 0) + 1
            if used[key] > 1:
                key = f"{key}_{used[key]}"
            out.append({"episode": n, "line": i + 1, "template": "T3", "key": key,
                        "heading": heading_for(lines, i), "items": items,
                        "ordered": bool(re.search(r"numbered", mod, re.I)),
                        "dur": round(2.6 + 1.15 * len(items), 1),
                        "hold": "hold", "cue": line.strip()[:140]})
        elif FIGURE.search(mod):
            out.append({"episode": n, "line": i + 1, "template": "FIGURE-NEEDED",
                        "key": None, "cue": line.strip()[:140]})
    return out


def main(show=False):
    cards, figs = [], []
    for n in range(1, 16):
        for c in scan(n):
            (figs if c["template"] == "FIGURE-NEEDED" else cards).append(c)
    spec = {"cards": [c for c in cards], "needs_figure": figs}
    json.dump(spec, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    t5 = [c for c in cards if c["template"] == "T5"]
    t3 = [c for c in cards if c["template"] == "T3"]
    print(f"  {len(t5)} statement cards, {len(t3)} built lists, "
          f"{len(figs)} cues that want a diagram and are left alone")
    byv = {}
    for c in t5:
        byv[c["variant"]] = byv.get(c["variant"], 0) + 1
    print("  variants: " + ", ".join(f"{k} {v}" for k, v in sorted(byv.items())))
    print(f"  spec -> {OUT}")
    if show:
        sys.stdout.reconfigure(encoding="utf-8")
        for c in cards:
            if c["template"] == "T5":
                print(f"\n  ep{c['episode']:02d} L{c['line']:<5} {c['variant']:<10}"
                      f"{c['dur']:>5}s {c['hold']}\n      {c['body'][:118]}")
            else:
                print(f"\n  ep{c['episode']:02d} L{c['line']:<5} LIST "
                      f"'{c['heading']}' ordered={c['ordered']}")
                for it in c["items"]:
                    print(f"      - {it}")


if __name__ == "__main__":
    main(show="--show" in sys.argv)
