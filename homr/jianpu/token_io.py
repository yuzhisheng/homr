"""
Token I/O for jianpu .jtokens files.

Handles serialization and deserialization of JianpuSymbol sequences.
Format: one symbol per line, 9 space-separated fields, chords joined with "&".

The 9 fields are:
    rhythm degree octave accidental articulation technique group dynamic lyric

Backward compatibility: when reading old 6-field files, technique/group/dynamic
are automatically filled with "." (nonote) default values.
"""

from homr.jianpu.vocabulary import JianpuSymbol, nonote

# Number of fields in the current token format
NUM_FIELDS = 9

# Number of fields in the legacy (pre-extension) format
LEGACY_NUM_FIELDS = 6


def read_jianpu_token_lines(lines: list[str]) -> list[JianpuSymbol]:
    """Parse lines from a .jtokens file into a flat list of JianpuSymbols.

    Each line represents one musical time position. Chord members are separated
    by "&"; all members after the first are preceded by the returned sequence
    by an explicit chord marker.

    Supports both the current 9-field format and the legacy 6-field format
    (automatically padding missing fields with defaults).

    Args:
        lines: Raw lines read from a token file.

    Returns:
        Flat sequence of jianpu symbols.
    """
    result: list[JianpuSymbol] = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        entries = line.split("&")
        for i, entry in enumerate(entries):
            parts = entry.strip().split()
            parts = _normalize_fields(parts)

            (
                rhythm, degree, octave, accidental, articulation,
                technique, group, dynamic, lyric,
            ) = parts

            symbol = JianpuSymbol(
                rhythm=rhythm,
                degree=degree,
                octave=octave,
                accidental=accidental,
                articulation=articulation,
                lyric=lyric,
                technique=technique,
                group=group,
                dynamic=dynamic,
            )

            if i > 0:
                result.append(JianpuSymbol("chord"))

            result.append(symbol)

    return result


def _normalize_fields(parts: list[str]) -> list[str]:
    """Normalize a list of token fields to exactly NUM_FIELDS elements.

    - If fewer than NUM_FIELDS: pad with nonote
    - If exactly LEGACY_NUM_FIELDS (6): insert technique/group/dynamic as nonote
    - If more than NUM_FIELDS: merge excess into lyric (last field)
    """
    if len(parts) < LEGACY_NUM_FIELDS:
        # Pad to 6 fields first
        parts = parts + [nonote] * (LEGACY_NUM_FIELDS - len(parts))

    if len(parts) == LEGACY_NUM_FIELDS:
        # Legacy 6-field format: insert technique, group, dynamic before lyric
        # Old order: rhythm degree octave accidental articulation lyric
        # New order: rhythm degree octave accidental articulation technique group dynamic lyric
        lyric = parts[5]
        return parts[:5] + [nonote, nonote, nonote, lyric]

    if len(parts) < NUM_FIELDS:
        # Between 7 and 8 fields — pad to 9
        parts = parts + [nonote] * (NUM_FIELDS - len(parts))
        return parts

    if len(parts) > NUM_FIELDS:
        # Extra fields: merge excess into lyric (last field)
        lyric_parts = parts[NUM_FIELDS - 1:]
        parts = parts[:NUM_FIELDS - 1] + [" ".join(lyric_parts)]

    return parts


def read_jianpu_tokens(filepath: str) -> list[JianpuSymbol]:
    """Read a .jtokens file and return a list of JianpuSymbols."""
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()
        return read_jianpu_token_lines(lines)


def _symbol_to_str(symbol: JianpuSymbol) -> str:
    """Convert a single JianpuSymbol to its string representation."""
    return str(symbol)


def write_jianpu_tokens(symbols: list[JianpuSymbol]) -> str:
    """Serialize a list of JianpuSymbols to a .jtokens string.

    Chord members are joined with "&" on the same line.
    """
    lines: list[str] = []
    current_chord: list[str] = []

    for symbol in symbols:
        if symbol.rhythm == "chord":
            # Next symbol is a chord member
            continue
        if current_chord and not symbol.rhythm.startswith("chord"):
            # Finish the previous chord line
            lines.append("&".join(current_chord))
            current_chord = []

        current_chord.append(_symbol_to_str(symbol))

    if current_chord:
        lines.append("&".join(current_chord))

    return "\n".join(lines) + "\n"


def write_jianpu_tokens_to_file(symbols: list[JianpuSymbol], filepath: str) -> None:
    """Write a list of JianpuSymbols to a .jtokens file."""
    content = write_jianpu_tokens(symbols)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
