"""Tests for jianpu bidirectional converter (jianpu↔MusicXML)."""

import os
import tempfile
import unittest

from homr.jianpu.jianpu_to_musicxml import (
    jianpu_to_encoded_symbols,
    jianpu_to_musicxml,
    jianpu_to_musicxml_file,
)
from homr.jianpu.musicxml_to_jianpu import parse_musicxml_to_jianpu
from homr.jianpu.vocabulary import JianpuSymbol, JIANPU_KEY_PREFIX, JIANPU_TIME_PREFIX, nonote, empty
from homr.transformer.vocabulary import EncodedSymbol


class TestJianpuToEncodedSymbols(unittest.TestCase):
    def test_convert_key_signature(self) -> None:
        symbols = [JianpuSymbol(f"{JIANPU_KEY_PREFIX}C")]
        encoded = jianpu_to_encoded_symbols(symbols)
        self.assertEqual(len(encoded), 1)
        self.assertEqual(encoded[0].rhythm, "keySignature_0")

    def test_convert_key_signature_g(self) -> None:
        symbols = [JianpuSymbol(f"{JIANPU_KEY_PREFIX}G")]
        encoded = jianpu_to_encoded_symbols(symbols)
        self.assertEqual(encoded[0].rhythm, "keySignature_1")

    def test_convert_time_signature(self) -> None:
        symbols = [JianpuSymbol(f"{JIANPU_TIME_PREFIX}4_4")]
        encoded = jianpu_to_encoded_symbols(symbols)
        self.assertEqual(encoded[0].rhythm, "timeSignature/4")

    def test_convert_barline(self) -> None:
        symbols = [JianpuSymbol("barline")]
        encoded = jianpu_to_encoded_symbols(symbols)
        self.assertEqual(encoded[0].rhythm, "barline")

    def test_convert_note_c_major_degree_1(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_4", "1", "0", empty, empty, nonote),
        ]
        encoded = jianpu_to_encoded_symbols(symbols)
        # After key sig, the note should be C4
        self.assertEqual(len(encoded), 2)
        self.assertEqual(encoded[1].rhythm, "note_4")
        self.assertEqual(encoded[1].pitch, "C4")

    def test_convert_note_c_major_degree_5(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_4", "5", "0", empty, empty, nonote),
        ]
        encoded = jianpu_to_encoded_symbols(symbols)
        self.assertEqual(encoded[1].pitch, "G4")

    def test_convert_note_g_major_degree_1(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}G"),
            JianpuSymbol("note_4", "1", "0", empty, empty, nonote),
        ]
        encoded = jianpu_to_encoded_symbols(symbols)
        self.assertEqual(encoded[1].pitch, "G4")

    def test_convert_rest(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("rest_4", "0", "0", empty, empty, nonote),
        ]
        encoded = jianpu_to_encoded_symbols(symbols)
        self.assertEqual(encoded[1].rhythm, "rest_4")

    def test_convert_chord(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_4", "1", "0", empty, empty, nonote),
            JianpuSymbol("chord"),
            JianpuSymbol("note_4", "3", "0", empty, empty, nonote),
        ]
        encoded = jianpu_to_encoded_symbols(symbols)
        # Key sig, note, chord marker, note
        self.assertEqual(len(encoded), 4)
        self.assertEqual(encoded[2].rhythm, "chord")


class TestJianpuToMusicXML(unittest.TestCase):
    def test_generate_xml_basic(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol(f"{JIANPU_TIME_PREFIX}4_4"),
            JianpuSymbol("note_4", "1", "0", empty, empty, nonote),
            JianpuSymbol("note_4", "2", "0", empty, empty, nonote),
            JianpuSymbol("note_4", "3", "0", empty, empty, nonote),
            JianpuSymbol("note_4", "4", "0", empty, empty, nonote),
            JianpuSymbol("barline"),
        ]
        xml = jianpu_to_musicxml(symbols, title="Test")
        self.assertIsNotNone(xml)

    def test_write_to_file(self) -> None:
        symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol("note_4", "1", "0", empty, empty, nonote),
            JianpuSymbol("barline"),
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.musicxml")
            jianpu_to_musicxml_file(symbols, path, title="Test")
            self.assertTrue(os.path.exists(path))
            with open(path, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("note", content.lower())


class TestMusicXMLToJianpu(unittest.TestCase):
    def test_parse_simple_musicxml(self) -> None:
        # Create a simple MusicXML string
        musicxml_str = """<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list>
    <score-part id="P1">
      <part-name>Voice</part-name>
    </score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>16</divisions>
        <key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
        <clef><sign>G</sign><line>2</line></clef>
      </attributes>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>16</duration>
        <type>quarter</type>
      </note>
      <note>
        <pitch><step>D</step><octave>4</octave></pitch>
        <duration>16</duration>
        <type>quarter</type>
      </note>
      <note>
        <pitch><step>E</step><octave>4</octave></pitch>
        <duration>16</duration>
        <type>quarter</type>
      </note>
      <note>
        <pitch><step>F</step><octave>4</octave></pitch>
        <duration>16</duration>
        <type>quarter</type>
      </note>
    </measure>
  </part>
</score-partwise>"""
        symbols = parse_musicxml_to_jianpu(musicxml_str)
        # Should have: key sig, time sig, 4 notes, barline
        self.assertGreater(len(symbols), 0)
        # Find key signature
        key_sigs = [s for s in symbols if s.is_key_signature()]
        self.assertEqual(len(key_sigs), 1)
        self.assertEqual(key_sigs[0].get_key_name(), "C")
        # Find notes
        notes = [s for s in symbols if s.is_note()]
        self.assertGreaterEqual(len(notes), 4)
        # First note should be degree 1 (C in C major)
        self.assertEqual(notes[0].get_degree_value(), 1)
        self.assertEqual(notes[1].get_degree_value(), 2)

    def test_parse_with_lyrics(self) -> None:
        musicxml_str = """<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list>
    <score-part id="P1"><part-name>Voice</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>16</divisions>
        <key><fifths>0</fifths></key>
      </attributes>
      <note>
        <pitch><step>C</step><octave>4</octave></pitch>
        <duration>16</duration>
        <lyric><text>你</text></lyric>
      </note>
    </measure>
  </part>
</score-partwise>"""
        symbols = parse_musicxml_to_jianpu(musicxml_str)
        notes = [s for s in symbols if s.is_note()]
        self.assertGreaterEqual(len(notes), 1)
        self.assertEqual(notes[0].lyric, "你")


class TestRoundtripConversion(unittest.TestCase):
    def test_jianpu_to_xml_to_jianpu(self) -> None:
        """Test that jianpu→MusicXML→jianpu preserves key info."""
        original_symbols = [
            JianpuSymbol(f"{JIANPU_KEY_PREFIX}C"),
            JianpuSymbol(f"{JIANPU_TIME_PREFIX}4_4"),
            JianpuSymbol("note_4", "1", "0", empty, empty, nonote),
            JianpuSymbol("note_4", "2", "0", empty, empty, nonote),
            JianpuSymbol("barline"),
        ]

        # Convert to MusicXML
        xml = jianpu_to_musicxml(original_symbols, title="Roundtrip Test")

        # Write and read back
        with tempfile.TemporaryDirectory() as tmpdir:
            xml_path = os.path.join(tmpdir, "roundtrip.musicxml")
            xml.write(xml_path)
            with open(xml_path, encoding="utf-8") as f:
                xml_content = f.read()

            # Parse back
            result_symbols = parse_musicxml_to_jianpu(xml_content)

            # Check key signature is preserved
            key_sigs = [s for s in result_symbols if s.is_key_signature()]
            self.assertGreaterEqual(len(key_sigs), 1)
            self.assertEqual(key_sigs[0].get_key_name(), "C")

            # Check notes are preserved (degree 1 and 2)
            notes = [s for s in result_symbols if s.is_note()]
            self.assertGreaterEqual(len(notes), 2)
            self.assertEqual(notes[0].get_degree_value(), 1)
            self.assertEqual(notes[1].get_degree_value(), 2)


if __name__ == "__main__":
    unittest.main()
