"""Tests for jianpu data generator."""

import os
import tempfile
import unittest

from homr.jianpu.data_generator import (
    GeneratorConfig,
    generate_dataset,
    generate_random_melody,
)
from homr.jianpu.vocabulary import JianpuSymbol


class TestGenerateRandomMelody(unittest.TestCase):
    def test_generate_basic_melody(self) -> None:
        config = GeneratorConfig(key="C", num_measures=2, seed=42)
        symbols = generate_random_melody(config)
        self.assertGreater(len(symbols), 0)

        # Should start with a key signature
        self.assertTrue(symbols[0].is_key_signature())
        self.assertEqual(symbols[0].get_key_name(), "C")

        # Should have a time signature
        self.assertTrue(symbols[1].is_time_signature())

    def test_generate_with_lyrics(self) -> None:
        config = GeneratorConfig(key="C", num_measures=2, with_lyrics=True, seed=123)
        symbols = generate_random_melody(config)
        notes = [s for s in symbols if s.is_note()]
        self.assertGreater(len(notes), 0)
        # At least some notes should have lyrics
        notes_with_lyrics = [n for n in notes if n.lyric not in (".", "_")]
        self.assertGreater(len(notes_with_lyrics), 0)

    def test_generate_without_lyrics(self) -> None:
        config = GeneratorConfig(key="C", num_measures=1, with_lyrics=False, seed=456)
        symbols = generate_random_melody(config)
        notes = [s for s in symbols if s.is_note()]
        for note in notes:
            self.assertEqual(note.lyric, ".")

    def test_generate_different_keys(self) -> None:
        for key in ["C", "G", "D", "F", "Bb"]:
            config = GeneratorConfig(key=key, num_measures=1, seed=789)
            symbols = generate_random_melody(config)
            self.assertEqual(symbols[0].get_key_name(), key)

    def test_generate_with_barlines(self) -> None:
        config = GeneratorConfig(key="C", num_measures=3, seed=101)
        symbols = generate_random_melody(config)
        barlines = [s for s in symbols if s.is_barline()]
        # Should have barlines between measures (but not after the last)
        self.assertGreater(len(barlines), 0)

    def test_seed_reproducibility(self) -> None:
        config1 = GeneratorConfig(key="C", num_measures=2, seed=999)
        config2 = GeneratorConfig(key="C", num_measures=2, seed=999)
        symbols1 = generate_random_melody(config1)
        symbols2 = generate_random_melody(config2)
        self.assertEqual(symbols1, symbols2)

    def test_notes_have_valid_degrees(self) -> None:
        config = GeneratorConfig(key="C", num_measures=2, seed=202)
        symbols = generate_random_melody(config)
        notes = [s for s in symbols if s.is_note()]
        for note in notes:
            degree = note.get_degree_value()
            self.assertIsNotNone(degree)
            self.assertGreaterEqual(degree, 1)
            self.assertLessEqual(degree, 7)


class TestGenerateDataset(unittest.TestCase):
    def test_generate_dataset_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            files = generate_dataset(3, tmpdir, GeneratorConfig(seed=42))
            self.assertEqual(len(files), 3)
            for f in files:
                self.assertTrue(os.path.exists(f + ".jtokens"))
                self.assertTrue(os.path.exists(f + ".svg"))

    def test_generate_dataset_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_dataset(1, tmpdir, GeneratorConfig(key="G", num_measures=2, seed=42))
            from homr.jianpu.token_io import read_jianpu_tokens
            jtokens_files = [f for f in os.listdir(tmpdir) if f.endswith(".jtokens")]
            self.assertEqual(len(jtokens_files), 1)
            symbols = read_jianpu_tokens(os.path.join(tmpdir, jtokens_files[0]))
            self.assertGreater(len(symbols), 0)
            self.assertTrue(symbols[0].is_key_signature())
            self.assertEqual(symbols[0].get_key_name(), "G")


if __name__ == "__main__":
    unittest.main()
