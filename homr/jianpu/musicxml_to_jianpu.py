"""
Converter from MusicXML to jianpu (numbered notation).

Parses a MusicXML file, extracts notes, pitches, keys, time signatures,
and lyrics, then converts them to JianpuSymbol sequences using DegreeMapper.
"""

import re
import xml.etree.ElementTree as ET
from fractions import Fraction

from homr.jianpu.constants import fifths_to_key
from homr.jianpu.degree_mapper import DegreeMapper, alter_to_accidental
from homr.jianpu.vocabulary import JianpuSymbol, JIANPU_KEY_PREFIX, JIANPU_TIME_PREFIX, nonote, empty

# MusicXML namespace (most files don't use namespaces, but handle it just in case)
_MUSICXML_NS = "{http://www.musicxml.org/ns/musicxml}"


def _strip_ns(tag: str) -> str:
    """Remove XML namespace prefix from a tag name."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1] if "}" in tag else tag
    return tag


def _find_text(element: ET.Element, tag: str) -> str | None:
    """Find a child element by tag name (namespace-agnostic) and return its text."""
    for child in element:
        if _strip_ns(child.tag) == tag:
            return child.text
    return None


def _find_all(element: ET.Element, tag: str) -> list[ET.Element]:
    """Find all child elements by tag name (namespace-agnostic)."""
    return [child for child in element if _strip_ns(child.tag) == tag]


def _duration_to_kern(duration: int, divisions: int) -> str:
    """Convert a MusicXML duration (in divisions) to a kern duration string.

    Args:
        duration: Duration value from MusicXML <duration> element
        divisions: Divisions per quarter note from <divisions> element

    Returns:
        Kern-style duration string like "4", "8.", "16.."
    """
    if divisions <= 0:
        return "4"

    # Duration as fraction of a whole note
    # divisions = divisions per quarter, so whole note = 4 * divisions
    whole_note_divisions = 4 * divisions
    fraction = Fraction(duration, whole_note_divisions)

    # Convert to kern: find the base duration (1/fraction = denominator)
    if fraction <= 0:
        return "4"

    # Get the reciprocal as the kern base
    kern_base = float(1 / fraction)

    # Find the closest power of two
    base = 1
    while base < kern_base:
        base *= 2
    if base > kern_base * 1.5:
        base //= 2

    # Calculate dots
    remaining = fraction - Fraction(1, base)
    dots = 0
    add = Fraction(1, base * 2)
    while remaining > 0 and dots < 3:
        if remaining >= add:
            remaining -= add
            dots += 1
        else:
            add /= 2
            if add < Fraction(1, base * 16):
                break

    return str(base) + "." * dots


def parse_musicxml_to_jianpu(xml_content: str | bytes) -> list[JianpuSymbol]:
    """Parse MusicXML content and convert to jianpu symbols.

    Args:
        xml_content: MusicXML file content as string or bytes

    Returns:
        List of JianpuSymbol objects
    """
    root = ET.fromstring(xml_content)

    # Find all parts
    parts = _find_all(root, "part")

    if not parts:
        return []

    # Process the first part (for simplicity, single-part conversion)
    part = parts[0]

    # Get divisions from the first measure
    measures = _find_all(part, "measure")
    if not measures:
        return []

    first_measure = measures[0]
    divisions = _get_divisions(first_measure)
    mapper = DegreeMapper("C")  # Default to C major
    current_key = "C"

    symbols: list[JianpuSymbol] = []

    for measure in measures:
        measure_symbols = _parse_measure(measure, divisions, mapper, current_key)
        # Update key if changed
        for sym in measure_symbols:
            if sym.is_key_signature():
                current_key = sym.get_key_name()
                mapper.set_key(current_key)
        symbols.extend(measure_symbols)

        # Add barline at end of measure (if not already present)
        if measure_symbols and not measure_symbols[-1].is_barline():
            symbols.append(JianpuSymbol("barline"))

    return symbols


def _get_divisions(measure: ET.Element) -> int:
    """Extract the divisions value from a measure's attributes."""
    attributes = _find_all(measure, "attributes")
    if not attributes:
        return 16  # Default: 16 divisions per quarter

    divisions = _find_text(attributes[0], "divisions")
    if divisions:
        return int(divisions)
    return 16


def _parse_measure(
    measure: ET.Element,
    divisions: int,
    mapper: DegreeMapper,
    current_key: str,
) -> list[JianpuSymbol]:
    """Parse a single MusicXML measure into jianpu symbols."""
    symbols: list[JianpuSymbol] = []
    chord_notes: list[JianpuSymbol] = []

    for child in measure:
        tag = _strip_ns(child.tag)

        if tag == "attributes":
            sym = _parse_attributes(child, mapper)
            if sym:
                symbols.extend(sym)

        elif tag == "note":
            note_sym = _parse_note(child, divisions, mapper)
            if note_sym is not None:
                # Check if this is a chord note
                is_chord = _find_all(child, "chord")
                if is_chord:
                    chord_notes.append(note_sym)
                else:
                    # Flush any pending chord notes
                    if chord_notes:
                        for i, cn in enumerate(chord_notes):
                            if i > 0:
                                symbols.append(JianpuSymbol("chord"))
                            symbols.append(cn)
                        chord_notes = []
                        symbols.append(JianpuSymbol("chord"))
                    symbols.append(note_sym)

        elif tag == "backup":
            # Handle backup (time movement backward)
            pass

        elif tag == "forward":
            # Handle forward (time movement forward)
            pass

    # Flush remaining chord notes
    if chord_notes:
        for i, cn in enumerate(chord_notes):
            if i > 0:
                symbols.append(JianpuSymbol("chord"))
            symbols.append(cn)
        chord_notes = []

    return symbols


def _parse_attributes(
    attributes: ET.Element, mapper: DegreeMapper
) -> list[JianpuSymbol]:
    """Parse attributes element for key/time signatures."""
    symbols: list[JianpuSymbol] = []

    # Key signature
    key = _find_all(attributes, "key")
    if key:
        fifths_text = _find_text(key[0], "fifths")
        if fifths_text:
            fifths = int(fifths_text)
            key_name = fifths_to_key(fifths)
            mapper.set_key(key_name)
            symbols.append(JianpuSymbol(
                rhythm=f"{JIANPU_KEY_PREFIX}{key_name}",
                degree=nonote, octave=nonote, accidental=nonote,
                articulation=nonote, lyric=nonote,
            ))

    # Time signature
    time = _find_all(attributes, "time")
    if time:
        beats_text = _find_text(time[0], "beats")
        beat_type_text = _find_text(time[0], "beat-type")
        if beats_text and beat_type_text:
            beats = int(beats_text)
            beat_type = int(beat_type_text)
            symbols.append(JianpuSymbol(
                rhythm=f"{JIANPU_TIME_PREFIX}{beats}_{beat_type}",
                degree=nonote, octave=nonote, accidental=nonote,
                articulation=nonote, lyric=nonote,
            ))

    return symbols


def _parse_note(
    note: ET.Element, divisions: int, mapper: DegreeMapper
) -> JianpuSymbol | None:
    """Parse a MusicXML note element into a jianpu symbol."""
    # Check for rest
    rest = _find_all(note, "rest")
    if rest:
        duration_text = _find_text(note, "duration")
        if duration_text:
            kern = _duration_to_kern(int(duration_text), divisions)
            return JianpuSymbol(
                rhythm=f"rest_{kern}",
                degree="0", octave="0", accidental=empty,
                articulation=empty, lyric=_extract_lyric(note),
            )
        return JianpuSymbol(
            rhythm="rest_4",
            degree="0", octave="0", accidental=empty,
            articulation=empty, lyric=nonote,
        )

    # Get pitch
    pitch = _find_all(note, "pitch")
    if not pitch:
        return None

    step = _find_text(pitch[0], "step")
    octave_text = _find_text(pitch[0], "octave")
    alter_text = _find_text(pitch[0], "alter")

    if not step or not octave_text:
        return None

    octave = int(octave_text)
    alter = int(alter_text) if alter_text else 0

    # Build note name with alteration
    note_name = step
    if alter == 1:
        note_name = step + "#"
    elif alter == -1:
        note_name = step + "b"
    elif alter == 2:
        note_name = step + "##"
    elif alter == -2:
        note_name = step + "bb"

    # Convert to degree
    degree, octave_offset, accidental = mapper.pitch_to_degree(note_name, octave, alter)

    # Get duration
    duration_text = _find_text(note, "duration")
    if duration_text:
        kern = _duration_to_kern(int(duration_text), divisions)
    else:
        kern = "4"

    # Check for grace note
    grace = _find_all(note, "grace")
    if grace:
        kern = kern + "G"

    # Extract articulations from notations
    articulation = _extract_articulation(note)

    # Extract lyric
    lyric = _extract_lyric(note)

    return JianpuSymbol(
        rhythm=f"note_{kern}",
        degree=str(degree),
        octave=str(octave_offset),
        accidental=accidental,
        articulation=articulation,
        lyric=lyric,
    )


def _extract_lyric(note: ET.Element) -> str:
    """Extract lyric text from a note element."""
    lyrics = _find_all(note, "lyric")
    if not lyrics:
        return nonote

    text = _find_text(lyrics[0], "text")
    if text:
        return text.strip()
    return empty


def _extract_articulation(note: ET.Element) -> str:
    """Extract articulation from a note's notations element."""
    notations = _find_all(note, "notations")
    if not notations:
        return empty

    articulations_found: list[str] = []

    notations_elem = notations[0]
    for child in notations_elem:
        tag = _strip_ns(child.tag)
        if tag == "articulations":
            for art in child:
                art_tag = _strip_ns(art.tag)
                if art_tag in ("accent", "staccato", "staccatissimo", "tenuto"):
                    articulations_found.append(art_tag)
        elif tag == "ornaments":
            for orn in child:
                orn_tag = _strip_ns(orn.tag)
                if orn_tag in ("trill-mark", "turn"):
                    articulations_found.append(
                        "trill" if orn_tag == "trill-mark" else "turn"
                    )
        elif tag == "fermata":
            articulations_found.append("fermata")
        elif tag == "slur":
            slur_type = child.get("type", "")
            if slur_type == "start":
                articulations_found.append("slurStart")
            elif slur_type == "stop":
                articulations_found.append("slurStop")

    if not articulations_found:
        return empty

    return "_".join(articulations_found)


def parse_musicxml_file_to_jianpu(filepath: str) -> list[JianpuSymbol]:
    """Read a MusicXML file and convert to jianpu symbols.

    Args:
        filepath: Path to the .musicxml file

    Returns:
        List of JianpuSymbol objects
    """
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    return parse_musicxml_to_jianpu(content)
