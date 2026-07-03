"""
Converter from jianpu (numbered notation) to MusicXML.

Converts JianpuSymbol sequences to standard EncodedSymbol sequences
(by mapping degrees to absolute pitches via DegreeMapper), then calls
the existing generate_xml() to produce MusicXML output.
"""

import musicxml.xmlelement.xmlelement as mxl

from homr.jianpu.constants import key_to_fifths
from homr.jianpu.degree_mapper import DegreeMapper, accidental_to_alter
from homr.jianpu.vocabulary import JianpuSymbol, JIANPU_KEY_PREFIX, JIANPU_TIME_PREFIX, nonote, empty
from homr.music_xml_generator import XmlGeneratorArguments, generate_xml
from homr.transformer.vocabulary import EncodedSymbol


def jianpu_to_encoded_symbols(
    symbols: list[JianpuSymbol],
) -> list[EncodedSymbol]:
    """Convert a list of JianpuSymbols to EncodedSymbols (staff notation).

    The conversion maps jianpu degrees to absolute pitches using the key
    signature context found in the symbol sequence.

    Args:
        symbols: List of JianpuSymbol objects

    Returns:
        List of EncodedSymbol objects compatible with generate_xml()
    """
    mapper = DegreeMapper("C")  # Default to C major
    result: list[EncodedSymbol] = []

    for symbol in symbols:
        if symbol.rhythm == "chord":
            result.append(EncodedSymbol("chord"))
            continue

        if symbol.is_key_signature():
            key_name = symbol.get_key_name()
            mapper.set_key(key_name)
            # Convert to staff keySignature_<fifths>
            fifths = key_to_fifths(key_name)
            result.append(EncodedSymbol(f"keySignature_{fifths}"))
            continue

        if symbol.is_time_signature():
            beats, beat_type = symbol.get_time_signature()
            # Staff vocabulary uses timeSignature/<beat_type>
            result.append(EncodedSymbol(f"timeSignature/{beat_type}"))
            continue

        if symbol.is_barline() or symbol.rhythm in (
            "repeatStart", "repeatEnd", "repeatEndStart",
            "voltaStart", "voltaStop", "voltaDiscontinue",
            "newline",
        ):
            result.append(EncodedSymbol(symbol.rhythm))
            continue

        if symbol.is_note() or symbol.is_rest():
            encoded = _convert_note_or_rest(symbol, mapper)
            result.append(encoded)
            continue

        # Pass through any unrecognized tokens
        result.append(EncodedSymbol(symbol.rhythm))

    return result


def _convert_note_or_rest(symbol: JianpuSymbol, mapper: DegreeMapper) -> EncodedSymbol:
    """Convert a jianpu note or rest to an EncodedSymbol."""
    rhythm = symbol.rhythm

    # For rests, degree should be 0; no pitch info needed
    if symbol.is_rest():
        return EncodedSymbol(
            rhythm=rhythm,
            pitch=empty,
            lift=empty,
            articulation=symbol.articulation if symbol.articulation != nonote else empty,
            position="upper",
        )

    # For notes, map degree to absolute pitch
    degree = symbol.get_degree_value()
    if degree is None or degree == 0:
        # Rest-like note
        return EncodedSymbol(
            rhythm=rhythm,
            pitch=empty,
            lift=empty,
            articulation=symbol.articulation if symbol.articulation != nonote else empty,
            position="upper",
        )

    octave = symbol.get_octave_value()
    accidental = symbol.accidental if symbol.accidental not in (nonote,) else empty

    # Map degree+octave to staff pitch
    pitch = mapper.degree_to_staff_pitch(degree, octave, symbol.accidental)

    # Map accidental to lift vocabulary
    lift = symbol.accidental if symbol.accidental in ("#", "b", "N", "##", "bb", empty) else empty
    if lift == nonote:
        lift = empty

    # Map articulation
    articulation = symbol.articulation if symbol.articulation != nonote else empty

    # Map lyric (stored in slur field temporarily - will need special handling)
    # For now, lyrics are not passed through to MusicXML via EncodedSymbol
    # (they would need to be added as <lyric> elements in the XML)

    return EncodedSymbol(
        rhythm=rhythm,
        pitch=pitch,
        lift=lift,
        articulation=articulation,
        position="upper",
    )


def jianpu_to_musicxml(
    symbols: list[JianpuSymbol],
    title: str = "",
    large_page: bool = False,
    metronome: int | None = None,
    tempo: int | None = None,
) -> mxl.XMLElement:
    """Convert jianpu symbols to a MusicXML score.

    Args:
        symbols: List of JianpuSymbol objects
        title: Title of the piece
        large_page: Whether to use large page format
        metronome: Optional metronome BPM
        tempo: Optional tempo BPM

    Returns:
        MusicXML XMLElement root
    """
    encoded_symbols = jianpu_to_encoded_symbols(symbols)
    args = XmlGeneratorArguments(large_page, metronome, tempo)
    return generate_xml(args, [encoded_symbols], title)


def jianpu_to_musicxml_file(
    symbols: list[JianpuSymbol],
    output_path: str,
    title: str = "",
    large_page: bool = False,
    metronome: int | None = None,
    tempo: int | None = None,
) -> None:
    """Convert jianpu symbols to MusicXML and write to a file.

    Args:
        symbols: List of JianpuSymbol objects
        output_path: Path to write the .musicxml file
        title: Title of the piece
        large_page: Whether to use large page format
        metronome: Optional metronome BPM
        tempo: Optional tempo BPM
    """
    xml = jianpu_to_musicxml(symbols, title, large_page, metronome, tempo)
    xml.write(output_path)
