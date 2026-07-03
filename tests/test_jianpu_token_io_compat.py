"""Tests for jianpu token I/O backward compatibility (6-field → 9-field)."""

import os
import tempfile
import unittest

from homr.jianpu.token_io import (
    read_jianpu_token_lines,
    read_jianpu_tokens,
    write_jianpu_tokens,
    write_jianpu_tokens_to_file,
)
from homr.jianpu.vocabulary import JianpuSymbol, nonote, empty


class TestLegacy6FieldCompat(unittest.TestCase):
    def test_read_legacy_6_field(self) -> None:
        """Old 6-field format should be readable and auto-padded to 9 fields."""
        legacy_lines = [
            "note_4 1 0 _ _ 我",
            "note_4 2 0 _ _ 爱",
            "barline . . . . .",
        ]
        symbols = read_jianpu_token_lines(legacy_lines)
        self.assertEqual(len(symbols), 3)

        # First note should have technique/group/dynamic as nonote
        self.assertEqual(symbols[0].technique, nonote)
        self.assertEqual(symbols[0].group, nonote)
        self.assertEqual(symbols[0].dynamic, nonote)

        # Original fields preserved
        self.assertEqual(symbols[0].rhythm, "note_4")
        self.assertEqual(symbols[0].degree, "1")
        self.assertEqual(symbols[0].lyric, "我")

    def test_write_always_9_fields(self) -> None:
        """Written files should always have 9 fields."""
        symbols = [
            JianpuSymbol("note_4", "1", "0", empty, empty, "你"),
            JianpuSymbol("barline"),
        ]
        content = write_jianpu_tokens(symbols)
        lines = [l for l in content.strip().split("\n") if l]
        for line in lines:
            parts = line.split()
            self.assertEqual(len(parts), 9, f"Expected 9 fields, got {len(parts)}: {line}")

    def test_roundtrip_9_field(self) -> None:
        """9-field format should roundtrip perfectly."""
        original = [
            JianpuSymbol(
                rhythm="note_4", degree="1", octave="0", accidental=empty,
                articulation="accent", lyric="你", technique="chanyin",
                group="tie_start", dynamic="mf",
            ),
            JianpuSymbol("barline"),
        ]
        content = write_jianpu_tokens(original)
        lines = content.strip().split("\n")
        parsed = read_jianpu_token_lines(lines)

        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0].rhythm, "note_4")
        self.assertEqual(parsed[0].technique, "chanyin")
        self.assertEqual(parsed[0].group, "tie_start")
        self.assertEqual(parsed[0].dynamic, "mf")

    def test_legacy_with_extra_fields(self) -> None:
        """Lines with more than 9 fields should merge excess into lyric."""
        lines = [
            "note_4 1 0 _ _ . . . 你 好 世界",
        ]
        symbols = read_jianpu_token_lines(lines)
        self.assertEqual(len(symbols), 1)
        self.assertIn("你", symbols[0].lyric)
        self.assertIn("世界", symbols[0].lyric)

    def test_read_short_line(self) -> None:
        """Very short lines should be padded to 9 fields."""
        lines = [
            "note_4",
            "barline",
        ]
        symbols = read_jianpu_token_lines(lines)
        self.assertEqual(len(symbols), 2)
        self.assertEqual(symbols[0].rhythm, "note_4")
        self.assertEqual(symbols[0].degree, nonote)
        self.assertEqual(symbols[0].technique, nonote)

    def test_file_roundtrip(self) -> None:
        """Write and read a file, ensure data is preserved."""
        symbols = [
            JianpuSymbol(
                rhythm="note_8", degree="3", octave="1", accidental="#",
                articulation="fermata", lyric="花", technique="dieyin",
                group="slur_start", dynamic="f",
            ),
            JianpuSymbol("barline"),
            JianpuSymbol(
                rhythm="note_4", degree="5", octave="0", accidental=empty,
                articulation=empty, lyric="开", technique=nonote,
                group=nonote, dynamic=nonote,
            ),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.jtokens")
            write_jianpu_tokens_to_file(symbols, path)

            read_symbols = read_jianpu_tokens(path)
            self.assertEqual(len(read_symbols), 3)
            self.assertEqual(read_symbols[0].technique, "dieyin")
            self.assertEqual(read_symbols[0].dynamic, "f")
            self.assertEqual(read_symbols[2].lyric, "开")

    def test_comment_lines(self) -> None:
        """Lines starting with # should be ignored."""
        lines = [
            "# This is a comment",
            "note_4 1 0 _ _ . . . 你",
            "# Another comment",
            "barline . . . . . . . . .",
        ]
        symbols = read_jianpu_token_lines(lines)
        self.assertEqual(len(symbols), 2)


if __name__ == "__main__":
    unittest.main()
