"""Tests for jianpu SVG renderer."""

import os
import tempfile
import unittest

from homr.jianpu.svg_renderer import render_jianpu_svg, render_jianpu_svg_to_file
from homr.jianpu.vocabulary import JianpuSymbol, JIANPU_KEY_PREFIX, JIANPU_TIME_PREFIX, nonote, empty


class TestSvgRenderer(unittest.TestCase):
    def test_render_empty_symbols(self) -> None:
        svg = render_jianpu_svg([])
        self.assertIn("<svg", svg)
        self.assertIn("</svg>", svg)

    def test_render_with_title(self) -> None:
        svg = render_jianpu_svg([], title="My Song")
        self.assertIn("My Song", svg)

    def test_render_basic_notes(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol(f"{JIANPU_TIME_PREFIX}4_4"),
            JianpuSymbol("note_4", "1", "0", empty, empty, nonote),
            JianpuSymbol("note_4", "2", "0", empty, empty, nonote),
            JianpuSymbol("note_4", "3", "0", empty, empty, nonote),
            JianpuSymbol("barline"),
        ]
        svg = render_jianpu_svg(symbols, title="Test")
        self.assertIn("<svg", svg)
        self.assertIn("1=C", svg)
        # Check for note numbers
        self.assertIn(">1<", svg)
        self.assertIn(">2<", svg)
        self.assertIn(">3<", svg)

    def test_render_octave_dots(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_4", "1", "1", empty, empty, nonote),  # Octave up
            JianpuSymbol("note_4", "2", "-1", empty, empty, nonote),  # Octave down
        ]
        svg = render_jianpu_svg(symbols)
        self.assertIn("circle", svg)  # Should have octave dots

    def test_render_underlines(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_8", "1", "0", empty, empty, nonote),  # Eighth note: 1 underline
            JianpuSymbol("note_16", "2", "0", empty, empty, nonote),  # 16th note: 2 underlines
        ]
        svg = render_jianpu_svg(symbols)
        self.assertIn("line", svg)

    def test_render_lyrics(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_4", "1", "0", empty, empty, "你"),
            JianpuSymbol("note_4", "2", "0", empty, empty, "好"),
        ]
        svg = render_jianpu_svg(symbols)
        self.assertIn("你", svg)
        self.assertIn("好", svg)

    def test_render_rest(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("rest_4", "0", "0", empty, empty, nonote),
        ]
        svg = render_jianpu_svg(symbols)
        self.assertIn(">0<", svg)

    def test_render_dotted_note(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_4.", "1", "0", empty, empty, nonote),
        ]
        svg = render_jianpu_svg(symbols)
        self.assertIn("circle", svg)  # Augmentation dot

    def test_render_accidental(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_4", "1", "0", "#", empty, nonote),
        ]
        svg = render_jianpu_svg(symbols)
        # Sharp symbol is rendered as SVG path
        self.assertIn("path", svg)

    def test_render_to_file(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_4", "1", "0", empty, empty, nonote),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.svg")
            render_jianpu_svg_to_file(symbols, path, title="File Test")
            self.assertTrue(os.path.exists(path))
            with open(path, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("<svg", content)
            self.assertIn("File Test", content)

    def test_render_barline(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_4", "1", "0", empty, empty, nonote),
            JianpuSymbol("barline"),
            JianpuSymbol("note_4", "2", "0", empty, empty, nonote),
        ]
        svg = render_jianpu_svg(symbols)
        self.assertIn("line", svg)

    def test_render_grace_note(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_4G", "1", "0", empty, empty, nonote),
        ]
        svg = render_jianpu_svg(symbols)
        # Grace notes should have italic style
        self.assertIn("italic", svg)


if __name__ == "__main__":
    unittest.main()
