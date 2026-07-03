"""
Degree↔Pitch mapper for jianpu notation.

Bridges jianpu scale degrees (1-7 with octave offsets) and absolute pitches
(C0-B9) used by the staff notation vocabulary. Handles key signature context
and accidental adjustments.
"""

import re

from homr.jianpu.constants import (
    BASE_OCTAVE,
    degree_to_note_name,
    note_to_degree,
)

# Note names for diatonic steps
_NOTE_NAMES = ["C", "D", "E", "F", "G", "A", "B"]

# Chromatic semitone offset for each note name (C=0, C#=1, D=2, ...)
_NOTE_SEMITONE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# Alteration value for accidentals
_ACCIDENTAL_ALTER = {
    "_": 0,
    "": 0,
    "#": 1,
    "##": 2,
    "b": -1,
    "bb": -2,
    "N": 0,
}


class DegreeMapper:
    """
    Maps between jianpu degrees and absolute pitches, given a key signature.

    In jianpu, octave 0 corresponds to scientific octave 4 (middle C4).
    Positive octave offsets raise the pitch; negative offsets lower it.
    """

    def __init__(self, key: str = "C") -> None:
        self.key = key

    def set_key(self, key: str) -> None:
        """Update the current key signature."""
        self.key = key

    def degree_to_pitch(
        self, degree: int, octave: int, accidental: str = "_"
    ) -> tuple[str, int]:
        """Convert a jianpu degree+octave to an absolute (note_name, octave) pair.

        Args:
            degree: Scale degree 1-7 (0 for rest)
            octave: Octave offset from base (0 = octave 4)
            accidental: Accidental token ("_", "#", "b", "N", "##", "bb")

        Returns:
            (note_name, octave_number) e.g. ("C", 4) for middle C
        """
        if degree == 0:
            return ("C", BASE_OCTAVE + octave)

        note_name = degree_to_note_name(degree, accidental, self.key)
        base_octave = BASE_OCTAVE + octave

        # Adjust octave for notes that wrap around (e.g., degree 4 in G major is C, which is
        # actually one octave higher than the tonic G)
        # The diatonic scale from the tonic: degrees 1-3 are in the same octave,
        # degree 4+ might be in the same or higher octave depending on the key.
        # For simplicity, we keep the octave as-is since the degree_to_note_name
        # already handles the correct note letter.
        # However, we need to handle the case where the note name's diatonic position
        # is lower than the tonic (indicating an octave wrap).
        tonic_note_letter = degree_to_note_name(1, "_", self.key)[0]
        note_letter = note_name[0]

        tonic_idx = _NOTE_NAMES.index(tonic_note_letter)
        note_idx = _NOTE_NAMES.index(note_letter)

        if note_idx < tonic_idx:
            # This note is in the next octave relative to the tonic
            base_octave += 1

        return (note_name, base_octave)

    def pitch_to_degree(
        self, note_name: str, octave: int, alter: int = 0
    ) -> tuple[int, int, str]:
        """Convert an absolute pitch to (degree, octave_offset, accidental).

        Args:
            note_name: Note name without octave, e.g. "C", "F#", "Bb"
            octave: Scientific octave number (e.g. 4 for C4)
            alter: Chromatic alteration (-2 to +2) from MusicXML <alter> element

        Returns:
            (degree 1-7, octave_offset, accidental_token)
        """
        # Apply alteration to get the actual note name
        if alter != 0:
            note_name = _apply_alter(note_name, alter)

        degree, base_accidental = note_to_degree(note_name, self.key)

        # Calculate octave offset
        # The degree_to_pitch function adds 1 to the octave when the note letter
        # is lower than the tonic. We reverse that here.
        tonic_note_letter = degree_to_note_name(1, "_", self.key)[0]
        tonic_idx = _NOTE_NAMES.index(tonic_note_letter)
        note_letter = note_name[0]
        note_idx = _NOTE_NAMES.index(note_letter)

        octave_offset = octave - BASE_OCTAVE
        if note_idx < tonic_idx:
            octave_offset -= 1

        accidental = base_accidental if base_accidental else "_"

        return (degree, octave_offset, accidental)

    def degree_to_staff_pitch(self, degree: int, octave: int, accidental: str = "_") -> str:
        """Convert a jianpu degree to a staff vocabulary pitch string (e.g. "C4", "F#5").

        Args:
            degree: Scale degree 1-7
            octave: Octave offset from base
            accidental: Accidental token

        Returns:
            Pitch string like "C4", "F#5", "Bb3"
        """
        note_name, abs_octave = self.degree_to_pitch(degree, octave, accidental)
        # Staff vocabulary uses letter+octave without the accidental in the pitch string
        # (accidental is a separate field). But the note_name may contain # or b.
        # We extract just the letter for the pitch.
        letter = note_name[0]
        return f"{letter}{abs_octave}"


def _apply_alter(note_name: str, alter: int) -> str:
    """Apply a chromatic alteration to a note name."""
    if alter == 0:
        return note_name

    # Get the base semitone
    letter = note_name[0]
    base_semitone = _NOTE_SEMITONE[letter]

    # Check for existing accidental in the note name
    existing_alter = 0
    if len(note_name) > 1:
        if "#" in note_name:
            existing_alter = note_name.count("#")
        elif "b" in note_name:
            existing_alter = -note_name.count("b")

    total_alter = existing_alter + alter
    final_semitone = (base_semitone + total_alter) % 12

    # Convert back to note name
    chromatic_sharp = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    chromatic_flat = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

    if alter > 0:
        return chromatic_sharp[final_semitone]
    else:
        return chromatic_flat[final_semitone]


def accidental_to_alter(accidental: str) -> int:
    """Convert an accidental token to a MusicXML alter value."""
    return _ACCIDENTAL_ALTER.get(accidental, 0)


def alter_to_accidental(alter: int) -> str:
    """Convert a MusicXML alter value to an accidental token."""
    if alter == 0:
        return "N"
    elif alter == 1:
        return "#"
    elif alter == 2:
        return "##"
    elif alter == -1:
        return "b"
    elif alter == -2:
        return "bb"
    return "_"
