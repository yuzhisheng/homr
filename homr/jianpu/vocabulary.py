"""
Jianpu (numbered musical notation) vocabulary and symbol definitions.

Defines the JianpuSymbol data class and the token validation logic.
The token format uses 9 space-separated fields:
    rhythm degree octave accidental articulation technique group dynamic lyric

Chords are joined with "&" (same as the existing staff notation).
"""

import copy
import itertools
import re
from fractions import Fraction

# Placeholder tokens (same convention as the staff vocabulary)
nonote = "."
empty = "_"

# Rhythm durations mapped to kern values (matching the staff vocabulary convention)
# The kern value is the denominator of the note duration: 4=quarter, 8=eighth, etc.
_KERN_DURATIONS = [0, 1, 2, 4, 8, 16, 32, 64]
_DOTS = ["", ".", ".."]
_GRACE = ["", "G"]

# Jianpu-specific rhythm tokens that don't exist in the staff vocabulary
# These are prefixed with "j_" to avoid collision with staff tokens
JIANPU_KEY_PREFIX = "jkey_"
JIANPU_TIME_PREFIX = "jtime_"
JIANPU_OCTAVE_PREFIX = "joct_"


def _build_rhythm_tokens() -> list[str]:
    """Build the list of valid rhythm tokens for jianpu."""
    tokens = []

    # Sequence control tokens
    tokens.extend(["PAD", "BOS", "EOS"])
    tokens.append("chord")

    # Bar lines
    tokens.extend(["barline", "doublebarline", "bolddoublebarline"])
    tokens.extend(["repeatStart", "repeatEnd", "repeatEndStart"])
    tokens.extend(["voltaStart", "voltaStop", "voltaDiscontinue"])

    # Key signatures: jkey_<keyname> e.g. jkey_C, jkey_G, jkey_Bb
    # Using jkey_ prefix to distinguish from staff keySignature_
    from homr.jianpu.constants import SUPPORTED_KEYS

    tokens.extend([f"{JIANPU_KEY_PREFIX}{k}" for k in SUPPORTED_KEYS])

    # Time signatures: jtime_beats_beattype e.g. jtime_4_4, jtime_3_4, jtime_6_8
    for beats in [2, 3, 4, 5, 6, 7, 9, 12]:
        for beat_type in [4, 8, 2, 16]:
            tokens.append(f"{JIANPU_TIME_PREFIX}{beats}_{beat_type}")

    # Octave markers (for rendering, not typically in tokens but kept for completeness)
    for o in range(-2, 3):
        tokens.append(f"{JIANPU_OCTAVE_PREFIX}{o}")

    # Notes and rests with kern-style durations
    kern_values = [f"{d}{g}{dot}" for d, g, dot in itertools.product(_KERN_DURATIONS, _GRACE, _DOTS)]
    tokens.extend([f"note_{d}" for d in kern_values])
    tokens.extend([f"rest_{d}" for d in kern_values])

    # Multi-rests
    tokens.extend([f"rest_{c}m" for c in range(2, 11)])

    # Dash (augmentation line — extends the previous note's duration)
    tokens.append("dash")

    # Newline (system break)
    tokens.append("newline")

    return tokens


def _build_degree_tokens() -> list[str]:
    """Valid degree values (scale degrees 1-7, 0 for rest/no-degree)."""
    return [nonote, empty, "0", "1", "2", "3", "4", "5", "6", "7"]


def _build_octave_tokens() -> list[str]:
    """Valid octave offset values."""
    return [nonote, empty, "-2", "-1", "0", "1", "2"]


def _build_accidental_tokens() -> list[str]:
    """Valid accidental tokens (same as staff lift vocabulary)."""
    return [nonote, empty, "#", "##", "N", "b", "bb"]


def _build_articulation_tokens() -> list[str]:
    """Valid articulation tokens (subset of staff articulation vocabulary + force accents)."""
    tokens = [nonote, empty]
    tokens.extend([
        "accent", "arpeggiate", "fermata", "staccato", "staccatissimo",
        "tenuto", "tremolo", "trill", "breathMark", "turn",
        "slurStart", "slurStop", "tieStart", "tieStop",
    ])
    # Force accent marks from jianpu-renderer (sf/sfp/fp)
    from homr.jianpu.constants import FORCE_ACCENT_MARKS
    tokens.extend(FORCE_ACCENT_MARKS)
    return tokens


def _build_technique_tokens() -> list[str]:
    """Valid technique tokens (dizi/bamboo flute techniques)."""
    tokens = [nonote, empty]
    from homr.jianpu.constants import DIZI_TECHNIQUE_TYPES
    tokens.extend(DIZI_TECHNIQUE_TYPES)
    return tokens


def _build_group_tokens() -> list[str]:
    """Valid group tokens (tie/slur/triplet connection markers)."""
    tokens = [nonote, empty]
    from homr.jianpu.constants import GROUP_MARKS
    tokens.extend(GROUP_MARKS)
    return tokens


def _build_dynamic_tokens() -> list[str]:
    """Valid dynamic tokens (dynamics + crescendo/diminuendo range markers)."""
    tokens = [nonote, empty]
    from homr.jianpu.constants import DYNAMIC_MARKS, DYNAMIC_RANGE_MARKS
    tokens.extend(DYNAMIC_MARKS)
    tokens.extend(DYNAMIC_RANGE_MARKS)
    return tokens


def _build_lyric_tokens() -> list[str]:
    """Valid lyric tokens."""
    return [nonote, empty, "-"]


class JianpuVocabulary:
    """Vocabulary for jianpu tokens, defining valid values for each of the 9 branches."""

    def __init__(self) -> None:
        self.rhythm = {t: i for i, t in enumerate(_build_rhythm_tokens())}
        self.degree = {t: i for i, t in enumerate(_build_degree_tokens())}
        self.octave = {t: i for i, t in enumerate(_build_octave_tokens())}
        self.accidental = {t: i for i, t in enumerate(_build_accidental_tokens())}
        self.articulation = {t: i for i, t in enumerate(_build_articulation_tokens())}
        self.technique = {t: i for i, t in enumerate(_build_technique_tokens())}
        self.group = {t: i for i, t in enumerate(_build_group_tokens())}
        self.dynamic = {t: i for i, t in enumerate(_build_dynamic_tokens())}
        self.lyric = {t: i for i, t in enumerate(_build_lyric_tokens())}


class JianpuSymbol:
    """
    A jianpu (numbered notation) symbol split into decoder branches.

    Fields:
        rhythm: note duration (note_4, rest_8, etc.), barline, key signature, time signature, dash
        degree: scale degree 1-7 (or 0 for rest), "." if not applicable
        octave: octave offset from base (-2 to 2), "." if not applicable
        accidental: sharp/flat/natural ("#", "b", "N", "_")
        articulation: articulation marks ("_", "accent", "staccato", "sf", etc.)
        technique: dizi technique ("_", "dieyin", "chanyin", etc.)
        group: tie/slur/triplet connection markers ("_", "tie_start", etc.)
        dynamic: dynamic markings ("_", "pp", "cresc_start", etc.)
        lyric: lyric syllable text, "_" for none, "-" for continuation
    """

    def __init__(
        self,
        rhythm: str,
        degree: str = nonote,
        octave: str = nonote,
        accidental: str = nonote,
        articulation: str = nonote,
        lyric: str = nonote,
        technique: str = nonote,
        group: str = nonote,
        dynamic: str = nonote,
    ) -> None:
        self.rhythm = rhythm
        self.degree = degree
        self.octave = octave
        self.accidental = accidental
        self.articulation = articulation
        self.lyric = lyric
        self.technique = technique
        self.group = group
        self.dynamic = dynamic

    def is_control_symbol(self) -> bool:
        return self.rhythm in ("BOS", "EOS", "PAD")

    def is_note(self) -> bool:
        return self.rhythm.startswith("note")

    def is_rest(self) -> bool:
        return self.rhythm.startswith("rest")

    def is_barline(self) -> bool:
        return "barline" in self.rhythm or "repeat" in self.rhythm

    def is_key_signature(self) -> bool:
        return self.rhythm.startswith(JIANPU_KEY_PREFIX)

    def is_time_signature(self) -> bool:
        return self.rhythm.startswith(JIANPU_TIME_PREFIX)

    def is_newline(self) -> bool:
        return self.rhythm == "newline"

    def is_dash(self) -> bool:
        """Check if this symbol is a dash (augmentation line)."""
        return self.rhythm == "dash"

    def get_key_name(self) -> str:
        """Extract the key name from a key signature token."""
        if not self.is_key_signature():
            raise ValueError(f"Symbol is not a key signature: {self.rhythm}")
        return self.rhythm[len(JIANPU_KEY_PREFIX):]

    def get_time_signature(self) -> tuple[int, int]:
        """Extract (beats, beat_type) from a time signature token."""
        if not self.is_time_signature():
            raise ValueError(f"Symbol is not a time signature: {self.rhythm}")
        parts = self.rhythm[len(JIANPU_TIME_PREFIX):].split("_")
        return int(parts[0]), int(parts[1])

    def get_degree_value(self) -> int | None:
        """Return the integer degree (0-7) or None if not a note/rest with degree."""
        if self.degree in (nonote, empty):
            return None
        return int(self.degree)

    def get_octave_value(self) -> int:
        """Return the octave offset (0 for central, positive for higher)."""
        if self.octave in (nonote, empty):
            return 0
        return int(self.octave)

    def get_kern(self) -> str:
        """Extract the kern duration string from the rhythm token."""
        match = re.match(r"(?:note|rest)_(\d+[G\.]*)", self.rhythm)
        if match:
            return match.group(1)
        return "4"

    def get_duration_fraction(self) -> Fraction:
        """Return the note duration as a Fraction of a whole note."""
        kern = self.get_kern()
        if kern.endswith("m"):
            # Multi-rest: whole measure
            return Fraction(1)

        # Extract numeric prefix
        i = 0
        while i < len(kern) and kern[i].isdigit():
            i += 1
        base_str = kern[:i]
        rest = kern[i:]

        base = int(base_str) if base_str else 4
        dots = rest.count(".")

        if "G" in kern:
            # Grace note: zero duration
            return Fraction(0)
        if base == 0:
            return Fraction(1)

        if base & (base - 1) == 0:
            # Power of two: normal note
            dur = Fraction(1, base)
        else:
            # Tuplet
            from homr.transformer.vocabulary import prior_power_of_two
            normal = prior_power_of_two(base)
            dur = Fraction(1, normal) * Fraction(normal, base)

        # Apply dots
        add = dur / 2
        for _ in range(dots):
            dur += add
            add /= 2

        return dur

    def is_valid(self) -> bool:
        """Check if this symbol has a valid combination of fields."""
        is_note_or_rest = self.is_note() or self.is_rest()
        has_degree = self.degree not in (nonote,)

        if is_note_or_rest:
            return has_degree
        else:
            # Non-note symbols should not have degree/octave/accidental
            return self.degree in (nonote,) and self.octave in (nonote,)

    def copy(self) -> "JianpuSymbol":
        return copy.copy(self)

    def __str__(self) -> str:
        return str.join(
            " ",
            (
                self.rhythm, self.degree, self.octave, self.accidental,
                self.articulation, self.technique, self.group, self.dynamic,
                self.lyric,
            ),
        )

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, JianpuSymbol):
            return False
        return (
            self.rhythm == other.rhythm
            and self.degree == other.degree
            and self.octave == other.octave
            and self.accidental == other.accidental
            and self.articulation == other.articulation
            and self.lyric == other.lyric
            and self.technique == other.technique
            and self.group == other.group
            and self.dynamic == other.dynamic
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.rhythm, self.degree, self.octave, self.accidental,
                self.articulation, self.lyric, self.technique, self.group,
                self.dynamic,
            )
        )


def has_jianpu_rhythm_position(rhythm: str) -> bool:
    """Check if a rhythm token represents a note, rest, dash, or clef (has position info)."""
    return rhythm.startswith(("note", "rest")) or rhythm == "dash"


# Default vocabulary instance
default_jianpu_vocab = JianpuVocabulary()
