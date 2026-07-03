"""Tests for jianpu vocabulary and symbol definitions."""

import unittest

from homr.jianpu.vocabulary import (
    JianpuSymbol,
    JianpuVocabulary,
    default_jianpu_vocab,
    nonote,
    empty,
)


class TestJianpuSymbol(unittest.TestCase):
    def test_create_note(self) -> None:
        sym = JianpuSymbol(
            rhythm="note_4",
            degree="1",
            octave="0",
            accidental=empty,
            articulation=empty,
            lyric="我",
        )
        self.assertTrue(sym.is_note())
        self.assertFalse(sym.is_rest())
        self.assertEqual(sym.get_degree_value(), 1)
        self.assertEqual(sym.get_octave_value(), 0)
        self.assertTrue(sym.is_valid())

    def test_create_rest(self) -> None:
        sym = JianpuSymbol(
            rhythm="rest_4",
            degree="0",
            octave="0",
            accidental=empty,
            articulation=empty,
            lyric=nonote,
        )
        self.assertTrue(sym.is_rest())
        self.assertFalse(sym.is_note())
        self.assertEqual(sym.get_degree_value(), 0)
        self.assertTrue(sym.is_valid())

    def test_create_barline(self) -> None:
        sym = JianpuSymbol("barline")
        self.assertTrue(sym.is_barline())
        self.assertFalse(sym.is_note())
        self.assertFalse(sym.is_rest())
        self.assertTrue(sym.is_valid())

    def test_create_key_signature(self) -> None:
        sym = JianpuSymbol("jkey_C")
        self.assertTrue(sym.is_key_signature())
        self.assertEqual(sym.get_key_name(), "C")

    def test_create_time_signature(self) -> None:
        sym = JianpuSymbol("jtime_4_4")
        self.assertTrue(sym.is_time_signature())
        self.assertEqual(sym.get_time_signature(), (4, 4))

    def test_create_time_signature_3_8(self) -> None:
        sym = JianpuSymbol("jtime_3_8")
        self.assertEqual(sym.get_time_signature(), (3, 8))

    def test_invalid_note_no_degree(self) -> None:
        sym = JianpuSymbol(rhythm="note_4", degree=nonote)
        self.assertFalse(sym.is_valid())

    def test_equality(self) -> None:
        sym1 = JianpuSymbol("note_4", "1", "0", empty, empty, nonote)
        sym2 = JianpuSymbol("note_4", "1", "0", empty, empty, nonote)
        sym3 = JianpuSymbol("note_4", "2", "0", empty, empty, nonote)
        self.assertEqual(sym1, sym2)
        self.assertNotEqual(sym1, sym3)

    def test_str_representation(self) -> None:
        sym = JianpuSymbol("note_4", "1", "0", "_", "_", "我")
        self.assertEqual(str(sym), "note_4 1 0 _ _ . . . 我")

    def test_duration_fraction_quarter(self) -> None:
        sym = JianpuSymbol("note_4", "1", "0", "_", "_", "_")
        from fractions import Fraction
        self.assertEqual(sym.get_duration_fraction(), Fraction(1, 4))

    def test_duration_fraction_dotted(self) -> None:
        sym = JianpuSymbol("note_4.", "1", "0", "_", "_", "_")
        from fractions import Fraction
        self.assertEqual(sym.get_duration_fraction(), Fraction(3, 8))

    def test_duration_fraction_eighth(self) -> None:
        sym = JianpuSymbol("note_8", "1", "0", "_", "_", "_")
        from fractions import Fraction
        self.assertEqual(sym.get_duration_fraction(), Fraction(1, 8))


class TestJianpuVocabulary(unittest.TestCase):
    def test_vocab_has_rhythm_tokens(self) -> None:
        self.assertIn("note_4", default_jianpu_vocab.rhythm)
        self.assertIn("rest_8", default_jianpu_vocab.rhythm)
        self.assertIn("barline", default_jianpu_vocab.rhythm)
        self.assertIn("chord", default_jianpu_vocab.rhythm)

    def test_vocab_has_key_tokens(self) -> None:
        self.assertIn("jkey_C", default_jianpu_vocab.rhythm)
        self.assertIn("jkey_G", default_jianpu_vocab.rhythm)
        self.assertIn("jkey_Bb", default_jianpu_vocab.rhythm)

    def test_vocab_has_time_tokens(self) -> None:
        self.assertIn("jtime_4_4", default_jianpu_vocab.rhythm)
        self.assertIn("jtime_3_4", default_jianpu_vocab.rhythm)
        self.assertIn("jtime_6_8", default_jianpu_vocab.rhythm)

    def test_vocab_has_degree_tokens(self) -> None:
        for d in ["0", "1", "2", "3", "4", "5", "6", "7"]:
            self.assertIn(d, default_jianpu_vocab.degree)

    def test_vocab_has_octave_tokens(self) -> None:
        for o in ["-2", "-1", "0", "1", "2"]:
            self.assertIn(o, default_jianpu_vocab.octave)

    def test_vocab_has_accidental_tokens(self) -> None:
        for a in ["#", "b", "N", "##", "bb"]:
            self.assertIn(a, default_jianpu_vocab.accidental)

    def test_vocab_has_technique_tokens(self) -> None:
        for t in ["zengyin", "dieyin", "liyin", "huayin_up", "huayin_down",
                   "dayin", "yinyin", "chanyin", "qizhenyin", "tuyin",
                   "huashe", "xunhuan", "fanyin", "boyin", "dunyin"]:
            self.assertIn(t, default_jianpu_vocab.technique)

    def test_vocab_has_group_tokens(self) -> None:
        for g in ["tie_start", "tie_end", "tie_cont",
                   "slur_start", "slur_end", "slur_cont",
                   "triplet_start", "triplet_end", "triplet_cont"]:
            self.assertIn(g, default_jianpu_vocab.group)

    def test_vocab_has_dynamic_tokens(self) -> None:
        for d in ["pp", "p", "mp", "mf", "f", "ff",
                   "cresc_start", "cresc_end", "dim_start", "dim_end"]:
            self.assertIn(d, default_jianpu_vocab.dynamic)

    def test_vocab_has_dash_rhythm(self) -> None:
        self.assertIn("dash", default_jianpu_vocab.rhythm)

    def test_vocab_has_force_accent_tokens(self) -> None:
        for fa in ["sf", "sfp", "fp"]:
            self.assertIn(fa, default_jianpu_vocab.articulation)

    def test_symbol_with_technique(self) -> None:
        sym = JianpuSymbol(
            rhythm="note_4", degree="1", octave="0", accidental="_",
            articulation="_", lyric=".", technique="chanyin",
        )
        self.assertEqual(sym.technique, "chanyin")
        self.assertTrue(sym.is_note())

    def test_symbol_with_group(self) -> None:
        sym = JianpuSymbol(
            rhythm="note_4", degree="1", octave="0", accidental="_",
            articulation="_", lyric=".", group="tie_start",
        )
        self.assertEqual(sym.group, "tie_start")

    def test_symbol_with_dynamic(self) -> None:
        sym = JianpuSymbol(
            rhythm="note_4", degree="1", octave="0", accidental="_",
            articulation="_", lyric=".", dynamic="mf",
        )
        self.assertEqual(sym.dynamic, "mf")

    def test_dash_symbol(self) -> None:
        sym = JianpuSymbol("dash")
        self.assertTrue(sym.is_dash())
        self.assertFalse(sym.is_note())


if __name__ == "__main__":
    unittest.main()
