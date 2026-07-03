"""Tests for jianpu JSON ↔ Token converter."""

import json
import unittest

from homr.jianpu.json_converter import (
    json_to_tokens,
    tokens_to_json,
    json_to_tokens_from_string,
    tokens_to_json_string,
)
from homr.jianpu.vocabulary import JianpuSymbol, JIANPU_KEY_PREFIX, JIANPU_TIME_PREFIX, nonote, empty


class TestJsonToTokens(unittest.TestCase):
    def test_basic_conversion(self) -> None:
        score = {
            "key": "C",
            "timeSignature": {"numerator": 4, "denominator": 4},
            "measures": [
                {
                    "notes": [
                        {"pitch": 1, "duration": 1, "lyric": "你"},
                        {"pitch": 2, "duration": 1, "lyric": "好"},
                    ],
                    "barline": "single",
                },
            ],
        }
        tokens = json_to_tokens(score)
        # key sig + time sig + 2 notes (barline is in the measure, may or may not be added)
        self.assertGreaterEqual(len(tokens), 4)
        self.assertTrue(tokens[0].is_key_signature())
        self.assertEqual(tokens[0].get_key_name(), "C")
        self.assertTrue(tokens[1].is_time_signature())
        self.assertEqual(tokens[1].get_time_signature(), (4, 4))

    def test_octave_conversion(self) -> None:
        score = {
            "key": "G",
            "timeSignature": {"numerator": 4, "denominator": 4},
            "measures": [
                {
                    "notes": [
                        {"pitch": 1, "octave": 1, "duration": 1},
                        {"pitch": 5, "octave": -1, "duration": 1},
                    ],
                },
            ],
        }
        tokens = json_to_tokens(score)
        notes = [t for t in tokens if t.is_note()]
        self.assertEqual(notes[0].get_octave_value(), 1)
        self.assertEqual(notes[1].get_octave_value(), -1)

    def test_accidental_conversion(self) -> None:
        score = {
            "key": "C",
            "timeSignature": {"numerator": 4, "denominator": 4},
            "measures": [
                {
                    "notes": [
                        {"pitch": 1, "accidental": "sharp", "duration": 1},
                        {"pitch": 3, "accidental": "flat", "duration": 1},
                        {"pitch": 5, "accidental": "natural", "duration": 1},
                    ],
                },
            ],
        }
        tokens = json_to_tokens(score)
        notes = [t for t in tokens if t.is_note()]
        self.assertEqual(notes[0].accidental, "#")
        self.assertEqual(notes[1].accidental, "b")
        self.assertEqual(notes[2].accidental, "N")

    def test_technique_conversion(self) -> None:
        score = {
            "key": "C",
            "timeSignature": {"numerator": 4, "denominator": 4},
            "measures": [
                {
                    "notes": [
                        {"pitch": 1, "duration": 1, "techniques": [{"type": "chanyin"}]},
                        {"pitch": 2, "duration": 1, "techniques": [{"type": "huayin", "slideDirection": "up"}]},
                        {"pitch": 3, "duration": 1, "techniques": [{"type": "huayin", "slideDirection": "down"}]},
                    ],
                },
            ],
        }
        tokens = json_to_tokens(score)
        notes = [t for t in tokens if t.is_note()]
        self.assertEqual(notes[0].technique, "chanyin")
        self.assertEqual(notes[1].technique, "huayin_up")
        self.assertEqual(notes[2].technique, "huayin_down")

    def test_dynamic_conversion(self) -> None:
        score = {
            "key": "C",
            "timeSignature": {"numerator": 4, "denominator": 4},
            "measures": [
                {
                    "notes": [
                        {"pitch": 1, "duration": 1, "dynamic": "mf"},
                        {"pitch": 2, "duration": 1, "dynamic": "ff"},
                    ],
                },
            ],
        }
        tokens = json_to_tokens(score)
        notes = [t for t in tokens if t.is_note()]
        self.assertEqual(notes[0].dynamic, "mf")
        self.assertEqual(notes[1].dynamic, "ff")

    def test_dash_conversion(self) -> None:
        score = {
            "key": "C",
            "timeSignature": {"numerator": 4, "denominator": 4},
            "measures": [
                {
                    "notes": [
                        {"pitch": 1, "duration": 2},
                        {"type": "dash", "duration": 1},
                    ],
                },
            ],
        }
        tokens = json_to_tokens(score)
        dashes = [t for t in tokens if t.is_dash()]
        self.assertEqual(len(dashes), 1)

    def test_rest_conversion(self) -> None:
        score = {
            "key": "C",
            "timeSignature": {"numerator": 4, "denominator": 4},
            "measures": [
                {
                    "notes": [
                        {"pitch": 0, "duration": 1},
                    ],
                },
            ],
        }
        tokens = json_to_tokens(score)
        rests = [t for t in tokens if t.is_rest()]
        self.assertEqual(len(rests), 1)

    def test_articulation_conversion(self) -> None:
        score = {
            "key": "C",
            "timeSignature": {"numerator": 4, "denominator": 4},
            "measures": [
                {
                    "notes": [
                        {"pitch": 1, "duration": 1, "accent": True},
                        {"pitch": 2, "duration": 1, "tenuto": True},
                        {"pitch": 3, "duration": 1, "fermata": True},
                    ],
                },
            ],
        }
        tokens = json_to_tokens(score)
        notes = [t for t in tokens if t.is_note()]
        self.assertEqual(notes[0].articulation, "accent")
        self.assertEqual(notes[1].articulation, "tenuto")
        self.assertEqual(notes[2].articulation, "fermata")

    def test_barline_conversion(self) -> None:
        score = {
            "key": "C",
            "timeSignature": {"numerator": 4, "denominator": 4},
            "measures": [
                {"notes": [{"pitch": 1, "duration": 1}], "barline": "repeat-start"},
                {"notes": [{"pitch": 2, "duration": 1}], "barline": "repeat-end"},
            ],
        }
        tokens = json_to_tokens(score)
        barlines = [t for t in tokens if t.is_barline() or "repeat" in t.rhythm]
        self.assertGreater(len(barlines), 0)
        self.assertIn("repeatStart", [t.rhythm for t in tokens])
        self.assertIn("repeatEnd", [t.rhythm for t in tokens])


class TestTokensToJson(unittest.TestCase):
    def test_basic_roundtrip(self) -> None:
        tokens = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol(f"{JIANPU_TIME_PREFIX}4_4"),
            JianpuSymbol("note_4", "1", "0", empty, empty, "你"),
            JianpuSymbol("note_4", "2", "0", empty, empty, "好"),
            JianpuSymbol("barline"),
        ]
        score = tokens_to_json(tokens)
        self.assertEqual(score["key"], "C")
        self.assertEqual(score["timeSignature"], {"numerator": 4, "denominator": 4})
        self.assertGreater(len(score["measures"]), 0)

    def test_technique_roundtrip(self) -> None:
        tokens = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol(f"{JIANPU_TIME_PREFIX}4_4"),
            JianpuSymbol("note_4", "1", "0", empty, empty, nonote, technique="dieyin"),
            JianpuSymbol("barline"),
        ]
        score = tokens_to_json(tokens)
        notes = score["measures"][0]["notes"]
        self.assertEqual(len(notes[0].get("techniques", []), ), 1)
        self.assertEqual(notes[0]["techniques"][0]["type"], "dieyin")

    def test_dynamic_roundtrip(self) -> None:
        tokens = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}G"),
            JianpuSymbol(f"{JIANPU_TIME_PREFIX}3_4"),
            JianpuSymbol("note_4", "1", "0", empty, empty, nonote, dynamic="f"),
            JianpuSymbol("barline"),
        ]
        score = tokens_to_json(tokens)
        notes = score["measures"][0]["notes"]
        self.assertEqual(notes[0].get("dynamic"), "f")

    def test_dash_roundtrip(self) -> None:
        tokens = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol(f"{JIANPU_TIME_PREFIX}4_4"),
            JianpuSymbol("note_2", "1", "0", empty, empty, nonote),
            JianpuSymbol("dash"),
            JianpuSymbol("barline"),
        ]
        score = tokens_to_json(tokens)
        notes = score["measures"][0]["notes"]
        # Should have a note and a dash
        dash_notes = [n for n in notes if n.get("type") == "dash"]
        self.assertEqual(len(dash_notes), 1)


class TestRoundtripConversion(unittest.TestCase):
    def test_json_to_tokens_to_json(self) -> None:
        """Test that JSON → Tokens → JSON preserves key features."""
        original_json = {
            "key": "C",
            "timeSignature": {"numerator": 4, "denominator": 4},
            "measures": [
                {
                    "notes": [
                        {"pitch": 1, "duration": 1, "lyric": "你"},
                        {"pitch": 2, "duration": 1, "lyric": "好"},
                    ],
                    "barline": "single",
                },
            ],
        }
        tokens = json_to_tokens(original_json)
        result_json = tokens_to_json(tokens)
        self.assertEqual(result_json["key"], "C")
        self.assertEqual(result_json["timeSignature"], {"numerator": 4, "denominator": 4})
        self.assertGreater(len(result_json["measures"]), 0)

    def test_json_string_roundtrip(self) -> None:
        json_str = json.dumps({
            "key": "G",
            "timeSignature": {"numerator": 3, "denominator": 4},
            "measures": [
                {"notes": [{"pitch": 1, "duration": 1}]},
            ],
        })
        tokens = json_to_tokens_from_string(json_str)
        result_str = tokens_to_json_string(tokens)
        result = json.loads(result_str)
        self.assertEqual(result["key"], "G")
        self.assertEqual(result["timeSignature"], {"numerator": 3, "denominator": 4})


if __name__ == "__main__":
    unittest.main()
