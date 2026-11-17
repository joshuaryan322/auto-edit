"""
Which rendered asset answers which script cue.

The script describes graphics in prose ("animate the low road and high road").
The assets are named by key (F1_two_roads). This table bridges them.

Matching is keyword-based and deliberately conservative: a cue only binds to an
asset when a trigger phrase appears. Anything unmatched is reported, never
guessed - a wrong graphic on screen is worse than no graphic.

Add a trigger here when the planner reports an unmatched cue.
"""

# asset key -> trigger phrases (lowercase, substring match against the cue text)
TRIGGERS = {
    # ---- figures
    "F1_two_roads":           ["low road", "high road", "thalamus", "two roads"],
    # NB: "extinction" is deliberately NOT a trigger here - it also appears in
    # the T2 suppression/extinction card and in plain text cards, and the
    # broader word was stealing both.
    "F2_competing_pathway":   ["two pathways", "old and worn", "new and being drawn",
                               "competing pathway"],
    "F3_prefrontal_dimming":  ["prefrontal cortex highlighted", "visibly dimming",
                               "prefrontal", "dimming"],
    "F4_yerkes_dodson":       ["yerkes", "arousal on the x-axis", "inverted u"],
    "F5_window_of_tolerance": ["window of tolerance", "three-zone", "three zone",
                               "window visibly widening"],
    "F6_construction_curve":  ["weekend seminar", "construction project",
                               "progress curve"],
    "F7_mindset_pyramid":     ["mindset pyramid", "pyramid"],
    "F8_habit_loop":          ["habit loop", "cue → routine", "cue - routine",
                               "routine crossed out"],
    "F9_value_function":      ["value function", "s-shaped curve", "prospect theory",
                               "concave", "convex"],
    "F10_five_phases":        ["five-phase", "five phase", "morning prime"],
    "F11_sizing_curve":       ["sizing curve", "as size rises"],
    "F12_90day_phases":       ["three-phase overview", "gates at weeks",
                               "foundation (wk", "90-day", "90 day"],

    # ---- T1 research cards: the researcher's name is the trigger
    "T1_ep01_ledoux":      ["ledoux"],
    "T1_ep01_sapolsky":    ["sapolsky"],
    "T1_ep02_hebb":        ["hebb"],
    "T1_ep02_maguire":     ["maguire"],
    "T1_ep02_coyle":       ["coyle"],
    "T1_ep02_lally":       ["lally"],
    "T1_ep03_yerkes":      ["yerkes-dodson", "yerkes &"],
    "T1_ep03_siegel":      ["siegel"],
    "T1_ep04_dawson":      ["dawson"],
    "T1_ep04_williamson":  ["williamson"],
    "T1_ep04_walker":      ["walker"],
    "T1_ep05_bandura":     ["bandura"],
    "T1_ep05_ericsson":    ["ericsson"],
    "T1_ep06_damasio":     ["damasio"],
    "T1_ep06_kahneman":    ["kahneman", "tversky"],
    "T1_ep07_duhigg":      ["duhigg"],
    "T1_ep07_fogg":        ["fogg"],
    "T1_ep10_thaler":      ["thaler"],
    "T1_ep10_slovic":      ["slovic"],
    "T1_ep11_beilock":     ["beilock"],
    "T1_ep11_csik":        ["csikszentmihalyi"],
    "T1_ep12_meichenbaum": ["meichenbaum"],
    "T1_ep12_driskell":    ["driskell", "johnston"],
    "T1_ep13_pascual":     ["pascual-leone", "pascual"],
    "T1_ep13_pennebaker":  ["pennebaker"],
    "T1_ep13_davidson":    ["davidson"],
    "T1_ep13_lazar":       ["lazar"],

    # ---- T2 comparisons
    "T2_ep01_detect_feel":   ["detection", "feeling"],
    "T2_ep01_supp_ext":      ["suppression", "extinction"],
    "T2_ep02_seminar_build": ["weekend seminar", "construction project"],
    "T2_ep05_conf_eff":      ["confidence: diffuse", "self-efficacy"],
    "T2_ep05_comfort_edge":  ["comfortable path", "the edge"],
    "T2_ep06_supp_reg":      ["suppression: feel nothing", "regulation"],
    "T2_ep07_out_proc":      ["two foundations", "outcomes", "process"],
    "T2_ep10_profit_cap":    ["profit", "capital"],
    "T2_ep11_motiv_instr":   ["motivational", "instructional"],
    "T2_ep12_proc_out_fail": ["process failure", "outcome failure"],
    "T2_ep13_log_journal":   ["trade log", "psychological journal"],

    # ---- T3 building lists
    "T3_ep01_amygdala_audit": ["amygdala audit", "numbered list"],
    "T3_ep05_elite_traits":   ["four traits"],
    "T3_ep08_five_phase":     ["five-phase timeline", "five phase timeline"],
    "T3_ep08_three_rings":    ["concentric rings"],
    "T3_ep11_pretrade":       ["pre-trade decision flowchart", "pre-trade sequence"],
    "T3_ep14_improvement":    ["observe → analyse", "four-step loop"],
    "T3_ep14_three_phases":   ["three phases", "three-phase"],
    "T3_ep15_circuit_breaker": ["three levels", "warning / caution", "circuit breaker"],
    "T3_ep15_three_layers":   ["three layers"],

    # ---- callbacks: a figure debuts in one episode and returns in later ones,
    # but the later script describes it in its own words rather than repeating
    # the original cue. These are the phrases those callbacks actually use.
    "F1_two_roads-REUSE": [
        "f1/f3 head asset", "amygdala flaring", "hpa axis",
        "gap opening", "small gap opening", "fused with a thought"],
    "F3_prefrontal_dimming-REUSE": [
        "prefrontal connection", "visibly thinning", "three failure modes"],
    "F4_yerkes_dodson-REUSE": [
        "a dial — undersized", "a dial - undersized", "undersized (boredom)",
        "three dials"],
    "F5_window_of_tolerance-REUSE": [
        "in the window", "threshold line", "alert but not agitated",
        "hijack likely"],
    "F2_competing_pathway-REUSE": [
        "substitution", "same cue, same reward", "new routine"],
    "F7_mindset_pyramid-REUSE": [
        "pyramid, filling", "behavioural proof", "identity updates"],
    "F8_habit_loop-REUSE": ["keystone habits", "cue → routine", "habit loop"],
    "F9_value_function-REUSE": ["steeper in losses", "gains & losses"],
    "F12_90day_phases-REUSE": ["three phases", "week 1 —", "week-4 gate"],
    "F6_construction_curve-REUSE": ["flat-then-rising", "progress curve from episode"],
    "F10_five_phases-REUSE": ["five-phase day from episode", "every concept overlaid"],

    # ---- assets whose own episode cues were phrased differently
    "T2_ep02_seminar_build": ["66 days average", "up to 254"],
    "T3_ep05_elite_traits":  ["process absolutism", "adversarial comfort"],
    "T3_ep14_three_phases":  ["week 2 — awareness", "week 5 — visualisation",
                              "three prerequisites"],
}

# How each asset family is placed on the timeline.
#   cutaway = replace the picture for the asset's duration, keep your audio
#   overlay = composite over your face (needs the alpha .mov, not the flat .mp4)
PLACEMENT = {
    "T1": "overlay",   # lower-third research card
    "T4": "cutaway",   # full-frame researcher plate - replaces T1 where a
                       # portrait exists, so the two never both appear
    "T5": "cutaway",   # statement card generated from the script's own text
    "T6": "cutaway",   # typographic plate - a cited researcher with no
                       # photograph; same frame as T4, monogram instead
    "T2": "cutaway",
    "T3": "cutaway",
    "F":  "cutaway",
}

# How long a graphic stays up once it has played.
#
# Measured on Episode 1: F1 (the two roads) plays for 7 seconds and is then
# EXPLAINED FOR 153. Cutting back to text while the narrator describes a
# diagram the viewer can no longer see is the worst thing a faceless explainer
# can do, so mechanism figures now hold.
#
#   flash         play once, then back to typography.  Credibility stamps.
#   hold          play, then freeze the last frame until the passage ends.
#   hold-caption  freeze, AND drop the typography to a caption underneath so
#                 the viewer keeps both the diagram and the words.
#
# Bounds stop a hold becoming a frozen slide: the gap to the next cue can be
# three minutes, which is as bad as no figure at all.
HOLD_MIN, HOLD_MAX = 6.0, 100.0   # cap is a backstop now, not the rule

HOLD = {
    "T1": "flash",          # a 4s research card is a stamp, not a subject
    "T4": "flash",          # same job as T1, with a face on it
    "T6": "flash",          # and the same again, with a monogram
    "T5": "flash",          # a statement card is read in one beat, unless the
                            # script said "held", which the generator records
    "T2": "hold",
    "T3": "hold",
    "F":  "hold-caption",   # mechanism diagrams are the point of the segment
}

# Per-asset overrides win over the family default.
HOLD_OVERRIDE = {
    "T3_ep01_amygdala_audit": "hold-caption",  # the drill - viewer copies it down
    "T3_ep11_pretrade":       "hold-caption",
    "T3_ep15_circuit_breaker":"hold-caption",
    "F12_90day_phases":       "hold-caption",
}


# Generated cards carry their own hold, because the script said so: a cue
# written "[ON SCREEN - held: ...]" is an instruction to leave it up. Merged in
# at import so hold_mode() stays the single place that answers this question.
def _generated_holds():
    import json as _json
    import os as _os
    p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                      "generated_cards.json")
    try:
        return {c["key"]: c["hold"] for c in
                _json.load(open(p, encoding="utf-8"))["cards"] if c.get("hold")}
    except Exception:
        return {}


HOLD_OVERRIDE.update(_generated_holds())


def hold_mode(key):
    base = key.replace("-REUSE", "")
    if base in HOLD_OVERRIDE:
        return HOLD_OVERRIDE[base]
    return HOLD.get(family(key), "hold")


# A research card is not cued in the script - the writer just names the
# researcher mid-sentence. These bind to the first SPOKEN mention instead.
#
# A value may be a LIST where the researcher is never actually named aloud.
# Episode 2 tells Maguire's study in full - the Knowledge, the scans, the
# larger posterior hippocampus - and never says "Maguire"; the only instruction
# to credit her is a production note. Binding to the finding puts the plate
# where the claim is made, which is where it belongs anyway.
NAME_ANCHORS = {
    "T1_ep01_ledoux": "ledoux",            "T1_ep01_sapolsky": "sapolsky",
    "T1_ep02_hebb": "hebb",                "T1_ep02_maguire": ["maguire", "posterior hippocampus"],
    "T1_ep02_coyle": "coyle",              "T1_ep02_lally": "lally",
    "T1_ep03_yerkes": "yerkes",            "T1_ep03_siegel": "siegel",
    "T1_ep04_dawson": "dawson",            "T1_ep04_williamson": "williamson",
    "T1_ep04_walker": "walker",            "T1_ep05_bandura": "bandura",
    "T1_ep05_ericsson": "ericsson",        "T1_ep06_damasio": "damasio",
    "T1_ep06_kahneman": "kahneman",        "T1_ep07_duhigg": "duhigg",
    "T1_ep07_fogg": "fogg",                "T1_ep10_thaler": "thaler",
    "T1_ep10_slovic": "slovic",            "T1_ep11_beilock": "beilock",
    "T1_ep11_csik": "csikszentmihalyi",    "T1_ep12_meichenbaum": "meichenbaum",
    "T1_ep12_driskell": "driskell",        "T1_ep13_pascual": "pascual-leone",
    "T1_ep13_pennebaker": "pennebaker",    "T1_ep13_davidson": "davidson",
    "T1_ep13_lazar": "lazar",
}


# A returning figure is often not cued at all - the narrator simply refers to
# it ("the window of tolerance from Episode 3 does not widen by wishing").
# Like research cards, these bind to the first SPOKEN mention instead.
REUSE_ANCHORS = {
    "F1_two_roads-REUSE":           ["low road", "two roads", "two different routes"],
    "F3_prefrontal_dimming-REUSE":  ["prefrontal"],
    "F4_yerkes_dodson-REUSE":       ["yerkes", "inverted u"],
    "F5_window_of_tolerance-REUSE": ["window of tolerance"],
    "F2_competing_pathway-REUSE":   ["competing pathway", "extinction learning"],
    "F6_construction_curve-REUSE":  ["sixty-six days", "66 days"],
    "F7_mindset_pyramid-REUSE":     ["mindset pyramid"],
    "F8_habit_loop-REUSE":          ["cue, routine", "habit loop"],
    "F9_value_function-REUSE":      ["value function", "prospect theory"],
    "F10_five_phases-REUSE":        ["five-phase day", "five phase day"],
    "F12_90day_phases-REUSE":       ["ninety-day protocol", "90-day protocol"],
}


def family(key):
    return key.split("_")[0][:2] if key.startswith("T") else "F"


def match_all(cue_text):
    """
    Every asset key this cue could mean, strongest trigger first.

    A cue often names two assets: "reuse F1/F3 head asset - amygdala flaring,
    the prefrontal connection visibly thinning" trips both the F1 trigger and
    the F3 one, and on raw trigger length F3 wins - but only F1 was rendered
    for that episode, so the cue ended up matched to a file that does not
    exist and the F1 asset sat unused. Returning the ranking instead lets the
    caller take the strongest candidate that it actually HAS.
    """
    t = cue_text.lower()
    hits = {}
    for key, trigs in TRIGGERS.items():
        for tr in trigs:
            if tr in t:
                hits[key] = max(hits.get(key, 0), len(tr))
    return [k for k, _ in sorted(hits.items(), key=lambda kv: -kv[1])]


def match(cue_text):
    """Return the asset key for a cue, or None. Longest trigger wins."""
    c = match_all(cue_text)
    return c[0] if c else None
