"""Tests for jianpu layout engine."""

import unittest

from homr.jianpu.layout import (
    DEFAULT_CONFIG,
    LayoutConfig,
    ScoreLayout,
    calculate_layout_from_symbols,
)
from homr.jianpu.vocabulary import (
    JIANPU_KEY_PREFIX,
    JIANPU_TIME_PREFIX,
    JianpuSymbol,
    empty,
    nonote,
)


class TestLayoutEngine(unittest.TestCase):
    def test_empty_symbols(self) -> None:
        layout = calculate_layout_from_symbols([])
        self.assertIsInstance(layout, ScoreLayout)
        self.assertGreater(layout.width, 0)
        self.assertGreater(layout.height, 0)

    def test_basic_layout(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol(f"{JIANPU_TIME_PREFIX}4_4"),
            JianpuSymbol("note_4", "1", "0", empty, empty, nonote),
            JianpuSymbol("note_4", "2", "0", empty, empty, nonote),
            JianpuSymbol("barline"),
        ]
        layout = calculate_layout_from_symbols(symbols)
        self.assertGreater(layout.height, 0)
        self.assertEqual(len(layout.rows), 1)
        self.assertGreater(len(layout.rows[0].measures), 0)

    def test_multiple_measures(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol(f"{JIANPU_TIME_PREFIX}4_4"),
        ]
        for _ in range(4):
            symbols.append(JianpuSymbol("note_4", "1", "0", empty, empty, nonote))
            symbols.append(JianpuSymbol("barline"))
        layout = calculate_layout_from_symbols(symbols)
        # Should have at least 1 measure
        self.assertGreater(len(layout.rows), 0)
        total_measures = sum(len(r.measures) for r in layout.rows)
        self.assertGreaterEqual(total_measures, 1)

    def test_octave_dots(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_4", "1", "1", empty, empty, nonote),  # Octave up
            JianpuSymbol("note_4", "2", "-1", empty, empty, nonote),  # Octave down
        ]
        layout = calculate_layout_from_symbols(symbols)
        for row in layout.rows:
            for ml in row.measures:
                for nl in ml.notes:
                    if nl.symbol.get_octave_value() == 1:
                        self.assertGreater(len(nl.upperDotPositions), 0)
                    elif nl.symbol.get_octave_value() == -1:
                        self.assertGreater(len(nl.lowerDotPositions), 0)

    def test_underlines(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol(f"{JIANPU_TIME_PREFIX}4_4"),
            JianpuSymbol("note_8", "1", "0", empty, empty, nonote),
            JianpuSymbol("note_8", "2", "0", empty, empty, nonote),
            JianpuSymbol("note_8", "3", "0", empty, empty, nonote),
            JianpuSymbol("note_8", "4", "0", empty, empty, nonote),
            JianpuSymbol("barline"),
        ]
        layout = calculate_layout_from_symbols(symbols)
        has_underline = False
        for row in layout.rows:
            for ml in row.measures:
                for nl in ml.notes:
                    if nl.underlines:
                        has_underline = True
                        break
        self.assertTrue(has_underline)

    def test_dashes(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol(f"{JIANPU_TIME_PREFIX}4_4"),
            JianpuSymbol("note_2", "1", "0", empty, empty, nonote),
            JianpuSymbol("dash"),
            JianpuSymbol("barline"),
        ]
        layout = calculate_layout_from_symbols(symbols)
        for row in layout.rows:
            for ml in row.measures:
                for nl in ml.notes:
                    if nl.item_type == "dash":
                        # Dashes should exist
                        return
        # If we get here, no dash was found
        self.fail("No dash found in layout")

    def test_custom_config(self) -> None:
        config = LayoutConfig(canvasWidth=400, noteFontSize=24)
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_4", "1", "0", empty, empty, nonote),
        ]
        layout = calculate_layout_from_symbols(symbols, config)
        self.assertEqual(layout.width, 400)

    def test_row_wrapping(self) -> None:
        """Test that many measures wrap to multiple rows."""
        config = LayoutConfig(canvasWidth=200)  # Narrow canvas
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol(f"{JIANPU_TIME_PREFIX}4_4"),
        ]
        for _ in range(8):
            for _ in range(4):
                symbols.append(JianpuSymbol("note_4", "1", "0", empty, empty, nonote))
            symbols.append(JianpuSymbol("barline"))
        layout = calculate_layout_from_symbols(symbols, config)
        self.assertGreater(len(layout.rows), 1)

    def test_technique_layout(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_4", "1", "0", empty, empty, nonote, technique="chanyin"),
        ]
        layout = calculate_layout_from_symbols(symbols)
        for row in layout.rows:
            for ml in row.measures:
                for nl in ml.notes:
                    if nl.symbol.technique == "chanyin":
                        self.assertGreater(len(nl.techniquePositions), 0)
                        return
        self.fail("No technique found in layout")

    def test_dynamic_layout(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_4", "1", "0", empty, empty, nonote, dynamic="mf"),
        ]
        layout = calculate_layout_from_symbols(symbols)
        for row in layout.rows:
            for ml in row.measures:
                for nl in ml.notes:
                    if nl.symbol.dynamic == "mf":
                        self.assertIsNotNone(nl.dynamicPosition)
                        return
        self.fail("No dynamic found in layout")


if __name__ == "__main__":
    unittest.main()
