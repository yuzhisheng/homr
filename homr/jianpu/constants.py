"""
Constants for jianpu (numbered musical notation) support.

Defines the mapping between scale degrees (1-7) and note names for all 12 major keys,
as well as the base octave convention.
"""



# In jianpu, octave 0 corresponds to scientific pitch octave 4 (the octave containing middle C4).
BASE_OCTAVE = 4

# The 12 major keys and their scale tones expressed as (note_name, semitone_offset_from_tonic).
# We store each key's diatonic scale using sharp-based spelling for sharp keys and
# flat-based spelling for flat keys, matching conventional music notation.
#
# Semitone offsets for a major scale: 0, 2, 4, 5, 7, 9, 11
_MAJOR_SCALE_SEMITONES = [0, 2, 4, 5, 7, 9, 11]

# Base note names indexed by semitone from C
_CHROMATIC_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_CHROMATIC_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# Keys that conventionally use flat spelling
_FLAT_KEYS = {"F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb"}

# Key name -> semitone offset of the tonic from C
_KEY_TO_TONIC_SEMITONE: dict[str, int] = {
    "C": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    "Cb": 11,
}

# Circle of fifths value -> canonical key name (for MusicXML fifths element)
# fifths: -7..-1 = flat keys, 0 = C, 1..7 = sharp keys
_FIFTHS_TO_KEY: dict[int, str] = {
    -7: "Cb",
    -6: "Gb",
    -5: "Db",
    -4: "Ab",
    -3: "Eb",
    -2: "Bb",
    -1: "F",
    0: "C",
    1: "G",
    2: "D",
    3: "A",
    4: "E",
    5: "B",
    6: "F#",
    7: "C#",
}

# Reverse: key name -> fifths value
_KEY_TO_FIFTHS: dict[str, int] = {v: k for k, v in _FIFTHS_TO_KEY.items()}


def _build_scale(key: str) -> list[str]:
    """Build the 7 diatonic note names for a major key."""
    tonic = _KEY_TO_TONIC_SEMITONE[key]
    use_flat = key in _FLAT_KEYS
    chromatic = _CHROMATIC_FLAT if use_flat else _CHROMATIC_SHARP
    return [chromatic[(tonic + interval) % 12] for interval in _MAJOR_SCALE_SEMITONES]


# Pre-compute scales for all supported keys
KEY_TO_SCALE: dict[str, list[str]] = {key: _build_scale(key) for key in _KEY_TO_TONIC_SEMITONE}


# Reverse lookup: (note_name_without_octave, key) -> (degree 1-7, accidental_adjustment)
def _apply_accidental_to_note(note: str, accidental: str) -> str:
    """Apply an accidental to a scale note, handling existing accidentals.

    E.g. F# with "b" -> F (remove the sharp), F# with "#" -> F## (double sharp),
    F with "b" -> Fb, F with "#" -> F#.
    """
    letter = note[0]
    existing = note[1:]

    if accidental in ("", "N", "_"):
        return note

    if accidental == "#":
        if existing == "#":
            return letter + "##"
        elif existing == "b":
            return letter
        else:
            return letter + "#"

    if accidental == "b":
        if existing == "#":
            return letter
        elif existing == "b":
            return letter + "bb"
        else:
            return letter + "b"

    if accidental == "##":
        if existing == "#":
            return letter + "###"
        elif existing == "b":
            return letter + "#"
        else:
            return letter + "##"

    if accidental == "bb":
        if existing == "#":
            return letter + "b"
        elif existing == "b":
            return letter + "bbb"
        else:
            return letter + "bb"

    return note


def _build_note_to_degree_maps() -> dict[str, dict[str, tuple[int, str]]]:
    """Build a reverse lookup map from note name to (degree, accidental) for each key.

    Uses the letter-based approach: for each scale degree, we register all
    accidental variants by prepending the accidental symbol to the scale note's letter.
    This ensures correct spelling (e.g. "F#" in C major maps to degree 4 with "#",
    not degree 5 with "b").
    """
    result: dict[str, dict[str, tuple[int, str]]] = {}

    for key, scale in KEY_TO_SCALE.items():
        note_map: dict[str, tuple[int, str]] = {}

        for degree_idx, scale_note in enumerate(scale, start=1):
            for accidental in ["", "#", "b", "##", "bb"]:
                note_name = _apply_accidental_to_note(scale_note, accidental)
                if note_name not in note_map:
                    note_map[note_name] = (degree_idx, accidental)

        result[key] = note_map

    return result


_NOTE_TO_DEGREE_MAPS = _build_note_to_degree_maps()


def fifths_to_key(fifths: int) -> str:
    """Convert a MusicXML fifths value (-7..7) to a key name."""
    if fifths not in _FIFTHS_TO_KEY:
        raise ValueError(f"Unsupported fifths value: {fifths}")
    return _FIFTHS_TO_KEY[fifths]


def key_to_fifths(key: str) -> int:
    """Convert a key name to a MusicXML fifths value (-7..7)."""
    if key not in _KEY_TO_FIFTHS:
        raise ValueError(f"Unsupported key: {key}")
    return _KEY_TO_FIFTHS[key]


def note_to_degree(note_name: str, key: str) -> tuple[int, str]:
    """Look up the (degree, accidental) for a note name in a given key.

    Args:
        note_name: Note name without octave, e.g. "C", "F#", "Bb"
        key: Key name, e.g. "C", "G", "Bb"

    Returns:
        (degree 1-7, accidental "" / "#" / "b")
    """
    key_map = _NOTE_TO_DEGREE_MAPS.get(key, _NOTE_TO_DEGREE_MAPS.get("C", {}))

    if note_name in key_map:
        return key_map[note_name]

    # Try enharmonic equivalent
    semitone = _note_name_to_semitone(note_name)
    if semitone is not None:
        for chromatic in [_CHROMATIC_SHARP, _CHROMATIC_FLAT]:
            alt_name = chromatic[semitone]
            if alt_name in key_map:
                return key_map[alt_name]

    raise ValueError(f"Cannot find degree for note {note_name} in key {key}")


def degree_to_note_name(degree: int, accidental: str, key: str) -> str:
    """Convert a scale degree + accidental to a note name in a given key.

    Args:
        degree: Scale degree 1-7
        accidental: "" / "#" / "b" / "N"
        key: Key name

    Returns:
        Note name without octave, e.g. "C", "F#", "Bb"
    """
    if key not in KEY_TO_SCALE:
        raise ValueError(f"Unsupported key: {key}")

    scale = KEY_TO_SCALE[key]
    if degree < 1 or degree > 7:
        raise ValueError(f"Degree must be 1-7, got {degree}")

    scale_note = scale[degree - 1]
    return _apply_accidental_to_note(scale_note, accidental if accidental else "_")


def _note_name_to_semitone(note_name: str) -> int | None:
    """Convert a note name to its semitone offset from C (0-11)."""
    # Try sharp spelling first
    if note_name in _CHROMATIC_SHARP:
        return _CHROMATIC_SHARP.index(note_name)
    if note_name in _CHROMATIC_FLAT:
        return _CHROMATIC_FLAT.index(note_name)
    return None


# Supported key names (for validation)
SUPPORTED_KEYS = sorted(_KEY_TO_TONIC_SEMITONE.keys())


# =============================================================================
# Dizi (bamboo flute) technique types — from jianpu-renderer DiziTechniqueType
# =============================================================================

DIZI_TECHNIQUE_TYPES: list[str] = [
    "zengyin",      # 赠音
    "dieyin",       # 叠音
    "liyin",        # 历音
    "huayin_up",    # 滑音（上滑）
    "huayin_down",  # 滑音（下滑）
    "dayin",        # 打音
    "yinyin",       # 倚音
    "chanyin",      # 颤音
    "qizhenyin",    # 气震音
    "tuyin",        # 吐音
    "huashe",       # 花舌
    "xunhuan",      # 循环换气
    "fanyin",       # 泛音
    "boyin",        # 波音
    "dunyin",       # 顿音
]

# Map from jianpu-renderer technique type to token technique value
# jianpu-renderer uses 'huayin' with slideDirection; we split into two
_TECHNIQUE_MAP_FROM_JSON: dict[str, str] = {
    "zengyin": "zengyin",
    "dieyin": "dieyin",
    "liyin": "liyin",
    "huayin": "huayin_up",  # default, overridden by slideDirection
    "dayin": "dayin",
    "yinyin": "yinyin",
    "chanyin": "chanyin",
    "qizhenyin": "qizhenyin",
    "tuyin": "tuyin",
    "huashe": "huashe",
    "xunhuan": "xunhuan",
    "fanyin": "fanyin",
    "boyin": "boyin",
    "dunyin": "dunyin",
}


def json_technique_to_token(tech_type: str, slide_direction: str | None = None) -> str:
    """Convert a jianpu-renderer JSON technique type to a token technique value.

    For huayin (滑音), the slideDirection determines huayin_up or huayin_down.
    """
    if tech_type == "huayin":
        return "huayin_down" if slide_direction == "down" else "huayin_up"
    return _TECHNIQUE_MAP_FROM_JSON.get(tech_type, tech_type)


def token_technique_to_json(technique: str) -> tuple[str, str | None]:
    """Convert a token technique value back to (json_type, slide_direction).

    Returns:
        (technique_type, slide_direction or None)
    """
    if technique == "huayin_up":
        return ("huayin", "up")
    if technique == "huayin_down":
        return ("huayin", "down")
    return (technique, None)


# =============================================================================
# Dynamic markings
# =============================================================================

DYNAMIC_MARKS: list[str] = ["pp", "p", "mp", "mf", "f", "ff"]

# Dynamic range markers: cresc_start/cresc_end, dim_start/dim_end
DYNAMIC_RANGE_MARKS: list[str] = [
    "cresc_start", "cresc_end",
    "dim_start", "dim_end",
]

# Force accent marks (sf, sfp, fp) — stored in articulation branch
FORCE_ACCENT_MARKS: list[str] = ["sf", "sfp", "fp"]


# =============================================================================
# Group markers (tie / slur / triplet) — start/end/cont pattern
# =============================================================================

GROUP_MARKS: list[str] = [
    "tie_start", "tie_end", "tie_cont",
    "slur_start", "slur_end", "slur_cont",
    "triplet_start", "triplet_end", "triplet_cont",
]


# =============================================================================
# Barline types from jianpu-renderer (mapped to rhythm tokens)
# =============================================================================

# jianpu-renderer BarlineType -> homr rhythm token
BARLINE_TYPE_MAP: dict[str, str] = {
    "single": "barline",
    "double": "doublebarline",
    "end": "bolddoublebarline",
    "repeat-start": "repeatStart",
    "repeat-end": "repeatEnd",
}
