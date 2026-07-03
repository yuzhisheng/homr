"""
JSON ↔ Token converter for jianpu (numbered musical notation).

Converts between jianpu-renderer's JSON Score format and homr's 9-branch
JianpuSymbol token format.

JSON Score format (from jianpu-renderer):
{
  "title": "...",
  "key": "C",
  "timeSignature": {"numerator": 4, "denominator": 4},
  "tempo": 120,
  "tempoText": "...",
  "measures": [
    {
      "notes": [
        {"pitch": 1, "octave": 0, "duration": 1, "dot": 0, ...},
        {"type": "dash", "duration": 1},
        ...
      ],
      "barline": "single",
      "repeatEnding": {"numbers": [1, 2]},
    },
    ...
  ]
}

Token format (9 branches):
rhythm degree octave accidental articulation technique group dynamic lyric
"""

import json
from fractions import Fraction
from typing import Any

from homr.jianpu.constants import (
    BARLINE_TYPE_MAP,
    json_technique_to_token,
    token_technique_to_json,
)
from homr.jianpu.vocabulary import (
    JIANPU_KEY_PREFIX,
    JIANPU_TIME_PREFIX,
    JianpuSymbol,
    empty,
    nonote,
)


# Duration (quarter-note units) to kern base mapping
# jianpu-renderer: 1=quarter, 0.5=eighth, 0.25=sixteenth, 2=half, 4=whole
def _duration_to_kern(duration: float, dot: int = 0) -> str:
    """Convert a jianpu-renderer duration to a kern string.

    Duration is in quarter-note units (1=quarter, 0.5=eighth, etc.)
    """
    if duration <= 0:
        return "4"

    # Find the base
    if duration >= 4:
        base = "1"
    elif duration >= 2:
        base = "2"
    elif duration >= 1:
        base = "4"
    elif duration >= 0.5:
        base = "8"
    elif duration >= 0.25:
        base = "16"
    else:
        base = "32"

    dots = "." * dot
    return base + dots


def _kern_to_duration(kern: str) -> tuple[float, int]:
    """Convert a kern string to (duration, dot_count).

    Returns duration in quarter-note units and dot count.
    """
    is_grace = "G" in kern
    if is_grace:
        kern = kern.replace("G", "")

    i = 0
    while i < len(kern) and kern[i].isdigit():
        i += 1
    base_str = kern[:i]
    rest = kern[i:]

    base = int(base_str) if base_str else 4
    dots = rest.count(".")

    dur_map = {1: 4.0, 2: 2.0, 4: 1.0, 8: 0.5, 16: 0.25, 32: 0.125, 64: 0.0625}
    dur = dur_map.get(base, 1.0)

    # Apply dots
    add = dur / 2
    for _ in range(dots):
        dur += add
        add /= 2

    return (dur, dots)


def _accidental_json_to_token(accidental: str | None) -> str:
    """Convert jianpu-renderer accidental to token."""
    if accidental is None:
        return empty
    mapping = {"sharp": "#", "flat": "b", "natural": "N"}
    return mapping.get(accidental, empty)


def _accidental_token_to_json(accidental: str) -> str | None:
    """Convert token accidental to jianpu-renderer format."""
    if accidental in (nonote, empty):
        return None
    mapping = {"#": "sharp", "b": "flat", "N": "natural", "##": "sharp", "bb": "flat"}
    return mapping.get(accidental)


def _barline_json_to_token(barline: str) -> str:
    """Convert jianpu-renderer barline type to token."""
    return BARLINE_TYPE_MAP.get(barline, "barline")


def _barline_token_to_json(rhythm: str) -> str:
    """Convert token barline to jianpu-renderer format."""
    reverse = {v: k for k, v in BARLINE_TYPE_MAP.items()}
    return reverse.get(rhythm, "single")


def json_to_tokens(score_json: dict[str, Any]) -> list[JianpuSymbol]:
    """Convert a jianpu-renderer JSON Score to a list of JianpuSymbol tokens.

    Args:
        score_json: Parsed JSON dict with 'key', 'timeSignature', 'measures', etc.

    Returns:
        List of JianpuSymbol objects
    """
    symbols: list[JianpuSymbol] = []

    # Key signature
    key = score_json.get("key", "C")
    symbols.append(JianpuSymbol(rhythm=f"{JIANPU_KEY_PREFIX}{key}"))

    # Time signature
    ts = score_json.get("timeSignature", {"numerator": 4, "denominator": 4})
    beats = ts.get("numerator", 4)
    beat_type = ts.get("denominator", 4)
    symbols.append(JianpuSymbol(rhythm=f"{JIANPU_TIME_PREFIX}{beats}_{beat_type}"))

    # Tempo
    tempo = score_json.get("tempo")
    if tempo:
        symbols.append(JianpuSymbol(rhythm=f"jtempo_{tempo}"))

    # Track tie/slur/triplet IDs for start/end marking
    tie_active = False
    slur_active = False
    triplet_active = False

    measures = score_json.get("measures", [])
    for m_idx, measure in enumerate(measures):
        notes = measure.get("notes", [])

        for n_idx, note in enumerate(notes):
            # Check if it's a dash
            if note.get("type") == "dash":
                symbols.append(JianpuSymbol(
                    rhythm="dash",
                    degree=nonote,
                    octave=nonote,
                    accidental=nonote,
                    articulation=nonote,
                    lyric=nonote,
                    technique=nonote,
                    group=nonote,
                    dynamic=nonote,
                ))
                continue

            # Regular note
            pitch = note.get("pitch", 0)
            octave = note.get("octave", 0)
            duration = note.get("duration", 1)
            dot = note.get("dot", 0)
            accidental = note.get("accidental")
            accidental_pos = note.get("accidentalPosition", "before")

            kern = _duration_to_kern(duration, dot)

            # Grace note check
            techniques = note.get("techniques", [])
            is_grace = any(t.get("type") == "yinyin" for t in techniques)
            if is_grace:
                kern = kern + "G"

            rhythm = f"note_{kern}" if pitch != 0 else f"rest_{kern}"

            # Accidental
            acc_token = _accidental_json_to_token(accidental)

            # Articulation
            articulation = nonote
            if note.get("accent"):
                articulation = "accent"
            elif note.get("tenuto"):
                articulation = "tenuto"
            elif note.get("fermata"):
                articulation = "fermata"
            elif note.get("staccato"):
                articulation = "staccato"

            force_accent = note.get("forceAccent")
            if force_accent:
                articulation = force_accent  # sf, sfp, fp

            # Technique (first technique only)
            technique = nonote
            if techniques:
                tech = techniques[0]
                tech_type = tech.get("type", "")
                slide_dir = tech.get("slideDirection")
                technique = json_technique_to_token(tech_type, slide_dir)

            # Group (tie/slur/triplet)
            group = nonote
            tie_id = note.get("tieId")
            slur_id = note.get("slurId")
            triplet_id = note.get("tripletId")

            if tie_id is not None:
                if not tie_active:
                    group = "tie_start"
                    tie_active = True
                else:
                    group = "tie_cont"

            if slur_id is not None:
                if not slur_active:
                    group = "slur_start"
                    slur_active = True
                else:
                    group = "slur_cont"

            if triplet_id is not None:
                if not triplet_active:
                    group = "triplet_start"
                    triplet_active = True
                else:
                    group = "triplet_cont"

            # Dynamic
            dynamic = nonote
            dyn = note.get("dynamic")
            if dyn:
                dynamic = dyn

            # Lyric
            lyric = nonote
            if note.get("lyric"):
                lyric = note["lyric"]
            elif note.get("lyrics") and len(note["lyrics"]) > 0:
                lyric = note["lyrics"][0]

            symbols.append(JianpuSymbol(
                rhythm=rhythm,
                degree=str(pitch),
                octave=str(octave),
                accidental=acc_token,
                articulation=articulation,
                lyric=lyric,
                technique=technique,
                group=group,
                dynamic=dynamic,
            ))

        # Handle tie/slur/triplet end at measure boundary
        # Check if any notes in the next measure have the same IDs
        if m_idx < len(measures) - 1:
            next_notes = measures[m_idx + 1].get("notes", [])
            next_tie_ids = set()
            next_slur_ids = set()
            next_triplet_ids = set()
            for n in next_notes:
                if n.get("type") == "dash":
                    continue
                if n.get("tieId"):
                    next_tie_ids.add(n["tieId"])
                if n.get("slurId"):
                    next_slur_ids.add(n["slurId"])
                if n.get("tripletId"):
                    next_triplet_ids.add(n["tripletId"])

            # If current tie/slur/triplet doesn't continue, mark end
            # (This is a simplification — we mark end on the last note of the group)
        else:
            # Last measure — end any active groups
            if tie_active:
                if symbols and symbols[-1].group == "tie_cont":
                    symbols[-1] = JianpuSymbol(
                        rhythm=symbols[-1].rhythm,
                        degree=symbols[-1].degree,
                        octave=symbols[-1].octave,
                        accidental=symbols[-1].accidental,
                        articulation=symbols[-1].articulation,
                        lyric=symbols[-1].lyric,
                        technique=symbols[-1].technique,
                        group="tie_end",
                        dynamic=symbols[-1].dynamic,
                    )
                tie_active = False
            if slur_active:
                if symbols and symbols[-1].group == "slur_cont":
                    symbols[-1] = JianpuSymbol(
                        rhythm=symbols[-1].rhythm,
                        degree=symbols[-1].degree,
                        octave=symbols[-1].octave,
                        accidental=symbols[-1].accidental,
                        articulation=symbols[-1].articulation,
                        lyric=symbols[-1].lyric,
                        technique=symbols[-1].technique,
                        group="slur_end",
                        dynamic=symbols[-1].dynamic,
                    )
                slur_active = False
            if triplet_active:
                if symbols and symbols[-1].group == "triplet_cont":
                    symbols[-1] = JianpuSymbol(
                        rhythm=symbols[-1].rhythm,
                        degree=symbols[-1].degree,
                        octave=symbols[-1].octave,
                        accidental=symbols[-1].accidental,
                        articulation=symbols[-1].articulation,
                        lyric=symbols[-1].lyric,
                        technique=symbols[-1].technique,
                        group="triplet_end",
                        dynamic=symbols[-1].dynamic,
                    )
                triplet_active = False

        # Barline
        barline = measure.get("barline", "single")
        barline_token = _barline_json_to_token(barline)
        if barline_token != "barline" or m_idx < len(measures) - 1:
            symbols.append(JianpuSymbol(rhythm=barline_token))

    return symbols


def tokens_to_json(symbols: list[JianpuSymbol]) -> dict[str, Any]:
    """Convert a list of JianpuSymbol tokens to a jianpu-renderer JSON Score.

    Args:
        symbols: List of JianpuSymbol objects

    Returns:
        JSON-serializable dict in jianpu-renderer Score format
    """
    key = "C"
    time_sig = {"numerator": 4, "denominator": 4}
    tempo = None
    tempo_text = None

    # Parse header
    note_symbols: list[JianpuSymbol] = []
    for sym in symbols:
        if sym.rhythm == "chord":
            continue
        if sym.is_key_signature():
            key = sym.get_key_name()
        elif sym.is_time_signature():
            beats, beat_type = sym.get_time_signature()
            time_sig = {"numerator": beats, "denominator": beat_type}
        elif sym.rhythm.startswith("jtempo_"):
            tempo = int(sym.rhythm[len("jtempo_"):])
        else:
            note_symbols.append(sym)

    # Build measures
    measures: list[dict[str, Any]] = []
    current_measure_notes: list[dict[str, Any]] = []
    current_barline = "single"

    tie_counter = 0
    slur_counter = 0
    triplet_counter = 0
    current_tie_id = None
    current_slur_id = None
    current_triplet_id = None

    for sym in note_symbols:
        if sym.is_key_signature() or sym.is_time_signature():
            continue

        if sym.is_newline():
            continue

        # Barline -> end current measure
        if sym.is_barline() or "repeat" in sym.rhythm or "volta" in sym.rhythm:
            barline_json = _barline_token_to_json(sym.rhythm)
            if current_measure_notes:
                measures.append({
                    "notes": current_measure_notes,
                    "barline": barline_json,
                })
                current_measure_notes = []
            else:
                # Empty measure with just a barline
                measures.append({
                    "notes": [],
                    "barline": barline_json,
                })
            current_barline = barline_json
            continue

        if sym.is_dash():
            # Dash (augmentation line)
            current_measure_notes.append({
                "type": "dash",
                "duration": 1,
            })
            continue

        if not (sym.is_note() or sym.is_rest()):
            continue

        # Parse note
        degree = sym.get_degree_value()
        octave = sym.get_octave_value()
        kern = sym.get_kern()
        duration, dot = _kern_to_duration(kern)

        accidental = _accidental_token_to_json(sym.accidental)

        # Articulation
        note_dict: dict[str, Any] = {
            "pitch": degree if degree is not None else 0,
            "octave": octave,
            "duration": duration,
            "dot": dot,
        }

        if accidental:
            note_dict["accidental"] = accidental

        if sym.articulation == "accent":
            note_dict["accent"] = True
        elif sym.articulation == "tenuto":
            note_dict["tenuto"] = True
        elif sym.articulation == "fermata":
            note_dict["fermata"] = True
        elif sym.articulation == "staccato":
            note_dict["staccato"] = True
        elif sym.articulation in ("sf", "sfp", "fp"):
            note_dict["forceAccent"] = sym.articulation

        # Technique
        if sym.technique not in (nonote, empty):
            tech_type, slide_dir = token_technique_to_json(sym.technique)
            tech_dict: dict[str, Any] = {"type": tech_type}
            if slide_dir:
                tech_dict["slideDirection"] = slide_dir
            note_dict["techniques"] = [tech_dict]

        # Group (tie/slur/triplet)
        g = sym.group
        if g == "tie_start":
            tie_counter += 1
            current_tie_id = f"tie_{tie_counter}"
            note_dict["tieId"] = current_tie_id
        elif g == "tie_cont" and current_tie_id:
            note_dict["tieId"] = current_tie_id
        elif g == "tie_end" and current_tie_id:
            note_dict["tieId"] = current_tie_id
            current_tie_id = None
        elif g == "slur_start":
            slur_counter += 1
            current_slur_id = f"slur_{slur_counter}"
            note_dict["slurId"] = current_slur_id
        elif g == "slur_cont" and current_slur_id:
            note_dict["slurId"] = current_slur_id
        elif g == "slur_end" and current_slur_id:
            note_dict["slurId"] = current_slur_id
            current_slur_id = None
        elif g == "triplet_start":
            triplet_counter += 1
            current_triplet_id = f"triplet_{triplet_counter}"
            note_dict["tripletId"] = current_triplet_id
        elif g == "triplet_cont" and current_triplet_id:
            note_dict["tripletId"] = current_triplet_id
        elif g == "triplet_end" and current_triplet_id:
            note_dict["tripletId"] = current_triplet_id
            current_triplet_id = None

        # Dynamic
        if sym.dynamic not in (nonote, empty):
            note_dict["dynamic"] = sym.dynamic

        # Lyric
        if sym.lyric not in (nonote, empty, "-"):
            note_dict["lyric"] = sym.lyric

        current_measure_notes.append(note_dict)

    # Don't forget the last measure
    if current_measure_notes:
        measures.append({
            "notes": current_measure_notes,
            "barline": "single",
        })

    result: dict[str, Any] = {
        "key": key,
        "timeSignature": time_sig,
        "measures": measures,
    }

    if tempo:
        result["tempo"] = tempo
    if tempo_text:
        result["tempoText"] = tempo_text

    return result


def json_to_tokens_from_string(json_str: str) -> list[JianpuSymbol]:
    """Parse a JSON string and convert to tokens."""
    score_json = json.loads(json_str)
    return json_to_tokens(score_json)


def json_to_tokens_from_file(filepath: str) -> list[JianpuSymbol]:
    """Read a JSON file and convert to tokens."""
    with open(filepath, encoding="utf-8") as f:
        score_json = json.load(f)
    return json_to_tokens(score_json)


def tokens_to_json_string(symbols: list[JianpuSymbol]) -> str:
    """Convert tokens to a JSON string."""
    score_json = tokens_to_json(symbols)
    return json.dumps(score_json, ensure_ascii=False, indent=2)


def tokens_to_json_file(symbols: list[JianpuSymbol], filepath: str) -> None:
    """Convert tokens and write to a JSON file."""
    json_str = tokens_to_json_string(symbols)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(json_str)
