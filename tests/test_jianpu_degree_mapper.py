"""Tests for jianpu degree↔pitch mapping."""

import unittest

from homr.jianpu.constants import (
    BASE_OCTAVE,
    KEY_TO_SCALE,
    SUPPORTED_KEYS,
    degree_to_note_name,
    fifths_to_key,
    key_to_fifths,
    note_to_degree,
)
from homr.jianpu.degree_mapper import DegreeMapper


class TestConstants(unittest.TestCase):
    def test_all_12_major_keys_supported(self) -> None:
        # All 15 major/minor key spellings (including enharmonic equivalents)
        expected_keys = {"C", "G", "D", "A", "E", "B", "F#", "C#",
                         "F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb"}
        for key in expected_keys:
            self.assertIn(key, KEY_TO_SCALE, f"Key {key} not in KEY_TO_SCALE")

    def test_c_major_scale(self) -> None:
        scale = KEY_TO_SCALE["C"]
        self.assertEqual(scale, ["C", "D", "E", "F", "G", "A", "B"])

    def test_g_major_scale(self) -> None:
        scale = KEY_TO_SCALE["G"]
        self.assertEqual(scale, ["G", "A", "B", "C", "D", "E", "F#"])

    def test_f_major_scale(self) -> None:
        scale = KEY_TO_SCALE["F"]
        self.assertEqual(scale, ["F", "G", "A", "Bb", "C", "D", "E"])

    def test_fifths_to_key(self) -> None:
        self.assertEqual(fifths_to_key(0), "C")
        self.assertEqual(fifths_to_key(1), "G")
        self.assertEqual(fifths_to_key(-1), "F")
        self.assertEqual(fifths_to_key(2), "D")
        self.assertEqual(fifths_to_key(-2), "Bb")

    def test_key_to_fifths(self) -> None:
        self.assertEqual(key_to_fifths("C"), 0)
        self.assertEqual(key_to_fifths("G"), 1)
        self.assertEqual(key_to_fifths("F"), -1)

    def test_degree_to_note_name_c_major(self) -> None:
        self.assertEqual(degree_to_note_name(1, "", "C"), "C")
        self.assertEqual(degree_to_note_name(2, "", "C"), "D")
        self.assertEqual(degree_to_note_name(7, "", "C"), "B")

    def test_degree_to_note_name_g_major(self) -> None:
        self.assertEqual(degree_to_note_name(1, "", "G"), "G")
        self.assertEqual(degree_to_note_name(7, "", "G"), "F#")

    def test_degree_to_note_name_with_sharp(self) -> None:
        self.assertEqual(degree_to_note_name(1, "#", "C"), "C#")
        self.assertEqual(degree_to_note_name(4, "#", "C"), "F#")

    def test_degree_to_note_name_with_flat(self) -> None:
        # Degree 1 in C major = C, flatted = Cb (correct spelling)
        self.assertEqual(degree_to_note_name(1, "b", "C"), "Cb")
        # Degree 3 in C major = E, flatted = Eb
        self.assertEqual(degree_to_note_name(3, "b", "C"), "Eb")

    def test_note_to_degree_c_major(self) -> None:
        degree, acc = note_to_degree("C", "C")
        self.assertEqual(degree, 1)
        self.assertEqual(acc, "")

        degree, acc = note_to_degree("F#", "C")
        self.assertEqual(degree, 4)
        self.assertEqual(acc, "#")

    def test_note_to_degree_g_major(self) -> None:
        # In G major, F# is degree 7 (natural, no accidental)
        degree, acc = note_to_degree("F#", "G")
        self.assertEqual(degree, 7)
        self.assertEqual(acc, "")

        # In G major, F natural is degree 7 with flat
        degree, acc = note_to_degree("F", "G")
        self.assertEqual(degree, 7)
        self.assertEqual(acc, "b")


class TestDegreeMapper(unittest.TestCase):
    def test_degree_to_pitch_c_major(self) -> None:
        mapper = DegreeMapper("C")
        note, octave = mapper.degree_to_pitch(1, 0, "_")
        self.assertEqual(note, "C")
        self.assertEqual(octave, BASE_OCTAVE)

        note, octave = mapper.degree_to_pitch(5, 0, "_")
        self.assertEqual(note, "G")
        self.assertEqual(octave, BASE_OCTAVE)

    def test_degree_to_pitch_octave_up(self) -> None:
        mapper = DegreeMapper("C")
        note, octave = mapper.degree_to_pitch(1, 1, "_")
        self.assertEqual(note, "C")
        self.assertEqual(octave, BASE_OCTAVE + 1)

    def test_degree_to_pitch_octave_down(self) -> None:
        mapper = DegreeMapper("C")
        note, octave = mapper.degree_to_pitch(1, -1, "_")
        self.assertEqual(note, "C")
        self.assertEqual(octave, BASE_OCTAVE - 1)

    def test_degree_to_pitch_g_major(self) -> None:
        mapper = DegreeMapper("G")
        note, octave = mapper.degree_to_pitch(1, 0, "_")
        self.assertEqual(note, "G")

        # Degree 4 in G major is C (one octave higher than tonic)
        note, octave = mapper.degree_to_pitch(4, 0, "_")
        self.assertEqual(note, "C")
        self.assertEqual(octave, BASE_OCTAVE + 1)

    def test_degree_to_pitch_with_sharp(self) -> None:
        mapper = DegreeMapper("C")
        note, octave = mapper.degree_to_pitch(1, 0, "#")
        self.assertEqual(note, "C#")

    def test_pitch_to_degree_c_major(self) -> None:
        mapper = DegreeMapper("C")
        degree, octave, acc = mapper.pitch_to_degree("C", 4, 0)
        self.assertEqual(degree, 1)
        self.assertEqual(octave, 0)
        self.assertEqual(acc, "_")

    def test_pitch_to_degree_g_major(self) -> None:
        mapper = DegreeMapper("G")
        degree, octave, acc = mapper.pitch_to_degree("G", 4, 0)
        self.assertEqual(degree, 1)
        self.assertEqual(octave, 0)

    def test_pitch_to_degree_with_alter(self) -> None:
        mapper = DegreeMapper("C")
        # C# in C major: degree 1 with sharp
        degree, octave, acc = mapper.pitch_to_degree("C", 4, 1)
        self.assertEqual(degree, 1)
        self.assertEqual(acc, "#")

    def test_roundtrip_c_major_all_degrees(self) -> None:
        mapper = DegreeMapper("C")
        for degree in range(1, 8):
            note, octave = mapper.degree_to_pitch(degree, 0, "_")
            result_degree, result_octave, result_acc = mapper.pitch_to_degree(note, octave, 0)
            self.assertEqual(degree, result_degree, f"Roundtrip failed for degree {degree}")

    def test_roundtrip_g_major(self) -> None:
        mapper = DegreeMapper("G")
        for degree in range(1, 8):
            note, octave = mapper.degree_to_pitch(degree, 0, "_")
            result_degree, result_octave, _ = mapper.pitch_to_degree(note, octave, 0)
            self.assertEqual(degree, result_degree, f"Roundtrip failed for degree {degree} in G major")

    def test_degree_to_staff_pitch(self) -> None:
        mapper = DegreeMapper("C")
        pitch = mapper.degree_to_staff_pitch(1, 0, "_")
        self.assertEqual(pitch, "C4")


if __name__ == "__main__":
    unittest.main()
