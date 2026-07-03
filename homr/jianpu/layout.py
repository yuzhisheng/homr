"""
Layout engine for jianpu (numbered musical notation) SVG rendering.

Ported from jianpu-renderer's layout.ts. Computes the positions of all
jianpu symbols (notes, dots, underlines, barlines, techniques, etc.)
given a list of JianpuSymbol tokens and layout configuration.

Key algorithms:
  - analyzeUnderlineGroups: groups adjacent short notes (<=8th) within the
    same beat to share underline beams
  - fitMeasuresInRow: wraps measures across rows based on canvas width
  - layoutNote: computes all symbol positions for a single note
"""

from dataclasses import dataclass, field
from fractions import Fraction
from typing import NamedTuple

from homr.jianpu.vocabulary import (
    JIANPU_KEY_PREFIX,
    JIANPU_TIME_PREFIX,
    JianpuSymbol,
    empty,
    nonote,
)


class SymbolPosition(NamedTuple):
    """Position and size of a layout element."""

    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class LayoutConfig:
    """Configuration parameters for jianpu layout."""

    canvasWidth: float = 800
    paddingHorizontal: float = 24
    paddingVertical: float = 24
    noteFontSize: float = 18
    noteWidth: float = 22
    noteHeight: float = 22
    measureGap: float = 12
    rowGap: float = 14
    dotRadius: float = 1.5
    dotGap: float = 2
    accentDotRadius: float = 1.5
    underlineOffset: float = 2.5
    underlineGap: float = 2.5
    underlineThickness: float = 1
    dashThickness: float = 1.2
    barlineWidth: float = 1
    techniqueFontSize: float = 9
    titleFontSize: float = 14
    metaFontSize: float = 11
    tieCurveHeight: float = 6
    lyricFontSize: float = 9
    lyricOffset: float = 14


DEFAULT_CONFIG = LayoutConfig()


@dataclass
class UnderlineInfo:
    """Information about a single underline beam."""

    y: float
    width: float
    xOffset: float


@dataclass
class TechniqueLayout:
    """Layout for a technique symbol on a note."""

    technique: str
    position: SymbolPosition
    label: str = ""


@dataclass
class NoteLayout:
    """Layout information for a single note or dash."""

    item_type: str  # 'note' or 'dash'
    symbol: JianpuSymbol
    measureIndex: int
    noteIndex: int
    position: SymbolPosition
    upperDotPositions: list[SymbolPosition] = field(default_factory=list)
    lowerDotPositions: list[SymbolPosition] = field(default_factory=list)
    dotPositions: list[SymbolPosition] = field(default_factory=list)
    accidentalPosition: SymbolPosition | None = None
    underlines: list[UnderlineInfo] = field(default_factory=list)
    dashLinePositions: list[SymbolPosition] = field(default_factory=list)
    techniquePositions: list[TechniqueLayout] = field(default_factory=list)
    tieStart: bool = False
    tieEnd: bool = False
    slurStart: bool = False
    slurEnd: bool = False
    tripletStart: bool = False
    tripletEnd: bool = False
    accentPosition: SymbolPosition | None = None
    tenutoPosition: SymbolPosition | None = None
    fermataPosition: SymbolPosition | None = None
    staccatoPosition: SymbolPosition | None = None
    lyricPosition: SymbolPosition | None = None
    dynamicPosition: SymbolPosition | None = None
    # For tie/slur curves: the end x of the group
    tieEndX: float | None = None
    slurEndX: float | None = None


@dataclass
class MeasureLayout:
    """Layout for a single measure."""

    position: SymbolPosition
    barlinePosition: SymbolPosition | None = None
    barlineType: str = "single"
    notes: list[NoteLayout] = field(default_factory=list)
    repeatEndingPosition: SymbolPosition | None = None
    repeatEndingNumbers: list[int] = field(default_factory=list)


@dataclass
class RowLayout:
    """Layout for a single row of measures."""

    y: float
    height: float
    measures: list[MeasureLayout] = field(default_factory=list)


@dataclass
class ScoreLayout:
    """Complete layout for a jianpu score."""

    width: float
    height: float
    titlePosition: SymbolPosition | None = None
    keyPosition: SymbolPosition | None = None
    timeSignaturePosition: SymbolPosition | None = None
    tempoPosition: SymbolPosition | None = None
    tempoText: str | None = None
    rows: list[RowLayout] = field(default_factory=list)


# --- Duration helpers ---

_KERN_TO_DURATION: dict[int, Fraction] = {
    1: Fraction(4),   # whole
    2: Fraction(2),   # half
    4: Fraction(1),   # quarter
    8: Fraction(1, 2),   # eighth
    16: Fraction(1, 4),  # sixteenth
    32: Fraction(1, 8),  # thirty-second
    64: Fraction(1, 16),
}


def _parse_kern(kern: str) -> tuple[int, int, bool]:
    """Parse a kern duration string into (base, dots, is_grace)."""
    is_grace = "G" in kern
    if is_grace:
        kern = kern.replace("G", "")
    i = 0
    while i < len(kern) and kern[i].isdigit():
        i += 1
    base_str = kern[:i]
    rest = kern[i:]
    base = int(base_str) if base_str else 4
    dots = rest.count(".")
    return (base, dots, is_grace)


def _duration_fraction(base: int, dots: int) -> Fraction:
    """Compute the duration fraction from base and dot count."""
    if base == 0:
        return Fraction(1)
    if base in _KERN_TO_DURATION:
        dur = _KERN_TO_DURATION[base]
    elif base & (base - 1) == 0:
        dur = Fraction(1, base)
    else:
        # Tuplet
        from homr.transformer.vocabulary import prior_power_of_two
        normal = prior_power_of_two(base)
        dur = Fraction(1, normal) * Fraction(normal, base)

    add = dur / 2
    for _ in range(dots):
        dur += add
        add /= 2
    return dur


def _get_underline_level(duration: Fraction) -> int:
    """Determine underline level from duration (quarter-note units).

    - Duration >= 1 (quarter): level 0 (no underline)
    - Duration <= 0.5 (eighth): level 1
    - Duration <= 0.25 (sixteenth): level 2
    - Duration <= 0.125 (thirty-second): level 3
    """
    if duration <= Fraction(1, 8):
        return 3
    if duration <= Fraction(1, 4):
        return 2
    if duration <= Fraction(1, 2):
        return 1
    return 0


# --- Underline grouping ---

@dataclass
class _UnderlineGroup:
    startIndex: int
    endIndex: int
    level: int


def _analyze_underline_groups(
    notes: list[tuple[JianpuSymbol, Fraction, int, int]],
    beats_per_measure: int,
    beat_unit_duration: Fraction,
) -> list[_UnderlineGroup]:
    """Group adjacent short notes within the same beat.

    Args:
        notes: list of (symbol, duration, base, dots) tuples
        beats_per_measure: numerator of time signature
        beat_unit_duration: duration of one beat (e.g. 1 for 4/4, 1/2 for 6/8)

    Returns:
        List of underline groups with start/end indices and level
    """
    groups: list[_UnderlineGroup] = []
    i = 0
    beat_idx = 0

    while i < len(notes) and beat_idx < beats_per_measure:
        acc = Fraction(0)
        cur_start = -1
        cur_end = -1
        cur_level = 0

        while acc < beat_unit_duration - Fraction(1, 1000) and i < len(notes):
            sym, dur, base, dots = notes[i]

            if sym.is_dash():
                i += 1
                continue

            note_level = _get_underline_level(dur)

            if note_level > 0:
                if cur_start < 0:
                    cur_start = i
                cur_end = i
                if note_level > cur_level:
                    cur_level = note_level

            acc += dur
            i += 1

        if cur_start >= 0:
            groups.append(_UnderlineGroup(cur_start, cur_end, cur_level))
        beat_idx += 1

    # Handle remaining notes beyond all beats
    cur_start = -1
    cur_end = -1
    cur_level = 0
    while i < len(notes):
        sym, dur, base, dots = notes[i]
        if sym.is_dash():
            i += 1
            continue
        note_level = _get_underline_level(dur)
        if note_level > 0:
            if cur_start < 0:
                cur_start = i
            cur_end = i
            if note_level > cur_level:
                cur_level = note_level
        i += 1
    if cur_start >= 0:
        groups.append(_UnderlineGroup(cur_start, cur_end, cur_level))

    return groups


# --- Technique labels ---

_TECHNIQUE_LABELS: dict[str, str] = {
    "zengyin": "赠",
    "dieyin": "又",
    "liyin": "历",
    "huayin_up": "↗",
    "huayin_down": "↘",
    "dayin": "扌",
    "yinyin": "倚",
    "chanyin": "tr",
    "qizhenyin": "〰",
    "tuyin": "T",
    "huashe": "✱",
    "xunhuan": "↻",
    "fanyin": "o",
    "boyin": "波",
    "dunyin": "顿",
}


def _get_technique_label(technique: str) -> str:
    return _TECHNIQUE_LABELS.get(technique, technique)


# --- Note layout ---

def _layout_note(
    symbol: JianpuSymbol,
    x: float,
    y: float,
    cfg: LayoutConfig,
    measure_idx: int,
    note_idx: int,
    group_info: dict | None,
) -> NoteLayout:
    """Compute the layout for a single note or dash."""
    pos = SymbolPosition(x, y, cfg.noteWidth, cfg.noteHeight)
    upper_dots: list[SymbolPosition] = []
    lower_dots: list[SymbolPosition] = []
    dot_positions: list[SymbolPosition] = []

    if symbol.is_dash():
        return NoteLayout(
            item_type="dash",
            symbol=symbol,
            measureIndex=measure_idx,
            noteIndex=note_idx,
            position=pos,
        )

    # Octave dots
    octave = symbol.get_octave_value()
    if octave > 0:
        for i in range(octave):
            dy = y - cfg.dotRadius + 2 - (cfg.dotGap * i if i > 0 else 0)
            upper_dots.append(SymbolPosition(
                x + cfg.noteWidth / 2 - cfg.dotRadius,
                dy,
                cfg.dotRadius * 2,
                cfg.dotRadius * 2,
            ))
    elif octave < 0:
        for i in range(-octave):
            dy = y + cfg.noteHeight - 3.5 + cfg.dotGap * i
            lower_dots.append(SymbolPosition(
                x + cfg.noteWidth / 2 - cfg.dotRadius,
                dy,
                cfg.dotRadius * 2,
                cfg.dotRadius * 2,
            ))

    # Augmentation dots
    kern = symbol.get_kern()
    _, dots, _ = _parse_kern(kern)
    for i in range(dots):
        dot_positions.append(SymbolPosition(
            x + cfg.noteWidth - 3 + i * (cfg.accentDotRadius * 2 + 3),
            y + cfg.noteHeight / 2 - cfg.accentDotRadius,
            cfg.accentDotRadius * 2,
            cfg.accentDotRadius * 2,
        ))

    # Accidental position
    accidental_pos = None
    if symbol.accidental not in (nonote, empty):
        accidental_pos = SymbolPosition(x - 2, y - 3, 16, 16)

    # Underlines
    underlines: list[UnderlineInfo] = []
    if group_info and group_info.get("underlineLevel", 0) > 0:
        level = group_info["underlineLevel"]
        group_start_x = group_info["groupStartX"]
        group_width = group_info["groupWidth"]
        for li in range(level):
            underlines.append(UnderlineInfo(
                y=y + cfg.noteHeight + cfg.underlineOffset + cfg.underlineGap * li,
                width=group_width,
                xOffset=group_start_x - x,
            ))
    elif group_info is None:
        dur = symbol.get_duration_fraction()
        levels = _get_underline_level(dur)
        for li in range(levels):
            underlines.append(UnderlineInfo(
                y=y + cfg.noteHeight + cfg.underlineOffset + cfg.underlineGap * li,
                width=cfg.noteWidth,
                xOffset=0,
            ))

    # Technique positions
    technique_positions: list[TechniqueLayout] = []
    if symbol.technique not in (nonote, empty):
        label = _get_technique_label(symbol.technique)
        tech_y_base = y - cfg.techniqueFontSize + 4
        width = len(label) * cfg.techniqueFontSize * 0.7
        technique_positions.append(TechniqueLayout(
            technique=symbol.technique,
            position=SymbolPosition(
                x + cfg.noteWidth / 2 - width / 2,
                tech_y_base,
                width,
                cfg.techniqueFontSize,
            ),
            label=label,
        ))

    has_techniques = len(technique_positions) > 0
    accent_y = (tech_y_base - cfg.techniqueFontSize - 2) if has_techniques else (y - 8)

    # Articulation positions
    accent_pos = None
    if symbol.articulation == "accent":
        accent_pos = SymbolPosition(x + cfg.noteWidth / 2 - 5, accent_y, 10, 8)

    tenuto_pos = None
    if symbol.articulation == "tenuto":
        tenuto_pos = SymbolPosition(x + cfg.noteWidth / 2 - 8, y - 8, 16, 3)

    fermata_pos = None
    if symbol.articulation == "fermata":
        fy = accent_y - 10 if has_techniques else y - 12
        fermata_pos = SymbolPosition(x + cfg.noteWidth / 2 - 10, fy, 20, 14)

    staccato_pos = None
    if symbol.articulation == "staccato":
        staccato_pos = SymbolPosition(x + cfg.noteWidth / 2 - 8, y - 6, 16, 8)

    # Lyric position
    lyric_pos = None
    if symbol.lyric not in (nonote, empty, "-"):
        lyric_text = symbol.lyric
        underline_level = group_info.get("underlineLevel", 0) if group_info else 0
        base_lyric_y = (
            y + cfg.noteHeight + cfg.lyricOffset
            + underline_level * cfg.underlineGap + cfg.underlineOffset
        )
        lyric_pos = SymbolPosition(
            x + cfg.noteWidth / 2 - len(lyric_text) * cfg.lyricFontSize * 0.5,
            base_lyric_y + cfg.lyricFontSize,
            len(lyric_text) * cfg.lyricFontSize,
            cfg.lyricFontSize,
        )

    # Dynamic position
    dynamic_pos = None
    if symbol.dynamic not in (nonote, empty):
        dyn_text = symbol.dynamic
        dynamic_pos = SymbolPosition(
            x + cfg.noteWidth / 2 - len(dyn_text) * cfg.lyricFontSize * 0.4,
            y + cfg.noteHeight + 11,
            len(dyn_text) * cfg.lyricFontSize,
            cfg.lyricFontSize,
        )

    # Group markers (tie/slur/triplet)
    tie_start = tie_end = slur_start = slur_end = triplet_start = triplet_end = False
    g = symbol.group
    if g == "tie_start":
        tie_start = True
    elif g == "tie_end":
        tie_end = True
    elif g == "slur_start":
        slur_start = True
    elif g == "slur_end":
        slur_end = True
    elif g == "triplet_start":
        triplet_start = True
    elif g == "triplet_end":
        triplet_end = True

    return NoteLayout(
        item_type="note",
        symbol=symbol,
        measureIndex=measure_idx,
        noteIndex=note_idx,
        position=pos,
        upperDotPositions=upper_dots,
        lowerDotPositions=lower_dots,
        dotPositions=dot_positions,
        accidentalPosition=accidental_pos,
        underlines=underlines,
        techniquePositions=technique_positions,
        tieStart=tie_start,
        tieEnd=tie_end,
        slurStart=slur_start,
        slurEnd=slur_end,
        tripletStart=triplet_start,
        tripletEnd=triplet_end,
        accentPosition=accent_pos,
        tenutoPosition=tenuto_pos,
        fermataPosition=fermata_pos,
        staccatoPosition=staccato_pos,
        lyricPosition=lyric_pos,
        dynamicPosition=dynamic_pos,
    )


def _fit_measures_in_row(
    measures: list[list[JianpuSymbol]],
    start_idx: int,
    avail_width: float,
    cfg: LayoutConfig,
) -> int:
    """Calculate how many measures fit in one row."""
    width = 0.0
    count = 0
    for i in range(start_idx, len(measures)):
        m = measures[i]
        m_width = 0.0
        for sym in m:
            if sym.rhythm == "chord":
                continue
            if sym.is_note() or sym.is_rest() or sym.is_dash():
                m_width += cfg.noteWidth
                kern = sym.get_kern() if (sym.is_note() or sym.is_rest()) else ""
                if kern:
                    _, dots, _ = _parse_kern(kern)
                    if dots > 0:
                        m_width += dots * (cfg.accentDotRadius * 2 + 10)
                if sym.accidental not in (nonote, empty):
                    m_width += 10
        m_width += cfg.barlineWidth
        if count > 0:
            m_width += cfg.measureGap
        if width + m_width > avail_width and count > 0:
            break
        width += m_width
        count += 1
    return max(count, 1)


def calculate_layout_from_symbols(
    symbols: list[JianpuSymbol],
    config: LayoutConfig = DEFAULT_CONFIG,
    title: str = "",
) -> ScoreLayout:
    """Calculate the layout for a list of JianpuSymbols.

    This is the Python equivalent of jianpu-renderer's calculateLayout().

    Args:
        symbols: List of JianpuSymbol tokens
        config: Layout configuration
        title: Optional score title

    Returns:
        ScoreLayout with all element positions
    """
    cfg = config
    content_width = cfg.canvasWidth - cfg.paddingHorizontal * 2
    current_y = cfg.paddingVertical

    # Parse metadata from symbols
    key_name = "C"
    time_sig = (4, 4)
    tempo: int | None = None

    # Extract key/time/tempo from the first few symbols
    for sym in symbols:
        if sym.is_key_signature():
            key_name = sym.get_key_name()
        elif sym.is_time_signature():
            time_sig = sym.get_time_signature()
        elif sym.rhythm.startswith("jtempo_"):
            tempo = int(sym.rhythm[len("jtempo_"):])

    # Title
    title_pos = None
    if title:
        title_pos = SymbolPosition(
            cfg.paddingHorizontal, current_y, content_width, cfg.titleFontSize + 8
        )
        current_y += title_pos.height + 8

    # Key/time/tempo
    meta_y = current_y
    key_text = f"1={key_name}"
    key_pos = SymbolPosition(
        cfg.paddingHorizontal, meta_y,
        len(key_text) * cfg.metaFontSize * 0.7,
        cfg.metaFontSize + 4,
    )
    ts_digit_width = cfg.metaFontSize * 0.65
    ts_line_width = ts_digit_width + 4
    ts_total_height = cfg.metaFontSize * 2 + 10
    key_center_y = meta_y + (cfg.metaFontSize + 4) / 2
    time_sig_pos = SymbolPosition(
        key_pos.x + key_pos.width + 6,
        key_center_y - ts_total_height / 2,
        ts_line_width,
        ts_total_height,
    )

    tempo_pos = None
    tempo_text = f"♩={tempo}" if tempo else None
    if tempo_text:
        tempo_pos = SymbolPosition(
            cfg.paddingHorizontal,
            meta_y + cfg.metaFontSize + 4 + 6,
            len(tempo_text) * cfg.metaFontSize * 0.6,
            cfg.metaFontSize + 4,
        )

    if tempo_pos:
        current_y = tempo_pos.y + tempo_pos.height + 4
    else:
        current_y = time_sig_pos.y + ts_total_height + 4
    current_y += 60  # Extra space for the score body

    # Split symbols into measures
    measures = _split_into_measures(symbols)

    # Calculate row layouts
    rows: list[RowLayout] = []
    measure_idx = 0

    while measure_idx < len(measures):
        fit_count = _fit_measures_in_row(measures, measure_idx, content_width, cfg)
        row_measures = measures[measure_idx:measure_idx + fit_count]

        measure_layouts: list[MeasureLayout] = []
        current_x = cfg.paddingHorizontal

        for mi, m_symbols in enumerate(row_measures):
            m_start_x = current_x

            # Parse note durations for underline grouping
            note_data: list[tuple[JianpuSymbol, Fraction, int, int]] = []
            for sym in m_symbols:
                if sym.rhythm == "chord":
                    continue
                if sym.is_note() or sym.is_rest():
                    kern = sym.get_kern()
                    base, dots, _ = _parse_kern(kern)
                    dur = _duration_fraction(base, dots)
                    note_data.append((sym, dur, base, dots))
                elif sym.is_dash():
                    note_data.append((sym, Fraction(1), 0, 0))

            beats_per_measure = time_sig[0]
            beat_unit_duration = Fraction(4, time_sig[1])
            groups = _analyze_underline_groups(note_data, beats_per_measure, beat_unit_duration)

            # Layout each note
            note_layouts: list[NoteLayout] = []
            note_x = m_start_x
            data_idx = 0

            for sym in m_symbols:
                if sym.rhythm == "chord":
                    continue
                if not (sym.is_note() or sym.is_rest() or sym.is_dash()):
                    continue

                # Check if this note is in an underline group
                group = None
                for g in groups:
                    if g.startIndex <= data_idx <= g.endIndex:
                        group = g
                        break

                group_info = None
                if group:
                    group_info = {
                        "underlineLevel": 0,
                        "groupStartX": 0,
                        "groupWidth": 0,
                    }

                nl = _layout_note(sym, note_x, current_y, cfg, measure_idx + mi, data_idx, group_info)
                note_layouts.append(nl)

                # Advance x
                advance_x = cfg.noteWidth
                if sym.is_note() or sym.is_rest():
                    kern = sym.get_kern()
                    _, dots, _ = _parse_kern(kern)
                    if dots > 0:
                        advance_x += dots * (cfg.accentDotRadius * 2 + 10)
                    if sym.accidental not in (nonote, empty):
                        advance_x += 10
                note_x += advance_x
                data_idx += 1

            # Fix up underline group widths based on actual positions
            for g in groups:
                if g.startIndex >= len(note_layouts):
                    continue
                first = note_layouts[g.startIndex]
                if g.endIndex >= len(note_layouts):
                    g.endIndex = len(note_layouts) - 1
                last = note_layouts[g.endIndex]
                if first is last:
                    continue

                arr: list[UnderlineInfo] = []
                for li in range(g.level):
                    required_level = li + 1
                    seg_start = -1
                    for ni in range(g.startIndex, g.endIndex + 1):
                        nl = note_layouts[ni]
                        sym = nl.symbol
                        dur = sym.get_duration_fraction() if (sym.is_note() or sym.is_rest()) else Fraction(1)
                        n_level = _get_underline_level(dur)
                        in_seg = n_level >= required_level
                        if in_seg and seg_start < 0:
                            seg_start = ni
                        is_last = ni == g.endIndex
                        if (not in_seg or is_last) and seg_start >= 0:
                            seg_end = ni if (in_seg and is_last) else ni - 1
                            s_first = note_layouts[seg_start]
                            s_last = note_layouts[seg_end]
                            f_center = s_first.position.x + s_first.position.width / 2
                            l_center = s_last.position.x + s_last.position.width / 2
                            arr.append(UnderlineInfo(
                                y=current_y + cfg.noteHeight + cfg.underlineOffset + cfg.underlineGap * li,
                                width=l_center - f_center,
                                xOffset=f_center - first.position.x,
                            ))
                            seg_start = -1

                first.underlines = arr
                for gi in range(g.startIndex + 1, g.endIndex + 1):
                    if gi < len(note_layouts):
                        note_layouts[gi].underlines = []

            # Barline
            note_x += 10
            barline_pos = SymbolPosition(
                note_x, current_y - 4, cfg.barlineWidth, cfg.noteHeight + 8
            )

            # Determine barline type
            barline_type = "single"
            for sym in m_symbols:
                if sym.is_barline():
                    barline_type = sym.rhythm
                    break

            measure_layouts.append(MeasureLayout(
                position=SymbolPosition(m_start_x, current_y, note_x - m_start_x, cfg.noteHeight),
                barlinePosition=barline_pos,
                barlineType=barline_type,
                notes=note_layouts,
            ))

            current_x = note_x + cfg.barlineWidth + 10

        # Calculate row height
        max_bottom = current_y + cfg.noteHeight
        for ml in measure_layouts:
            for nl in ml.notes:
                if nl.lowerDotPositions:
                    last_dot = nl.lowerDotPositions[-1]
                    max_bottom = max(max_bottom, last_dot.y + last_dot.height + 4)
                if nl.underlines:
                    last_line = nl.underlines[-1]
                    max_bottom = max(max_bottom, last_line.y + cfg.underlineThickness + 2)
                if nl.dynamicPosition:
                    max_bottom = max(max_bottom, nl.dynamicPosition.y + nl.dynamicPosition.height + 2)
                if nl.lyricPosition:
                    max_bottom = max(max_bottom, nl.lyricPosition.y + nl.lyricPosition.height + 2)

        row_height = max_bottom - current_y + 8
        rows.append(RowLayout(y=current_y, height=row_height, measures=measure_layouts))
        current_y += row_height + cfg.rowGap
        measure_idx += fit_count

    return ScoreLayout(
        width=cfg.canvasWidth,
        height=current_y + cfg.paddingVertical,
        titlePosition=title_pos,
        keyPosition=key_pos,
        timeSignaturePosition=time_sig_pos,
        tempoPosition=tempo_pos,
        tempoText=tempo_text,
        rows=rows,
    )


def _split_into_measures(symbols: list[JianpuSymbol]) -> list[list[JianpuSymbol]]:
    """Split a flat symbol list into measures (delimited by barlines).

    Key/time signatures at the start are included in the first measure.
    Newlines trigger a new measure boundary.
    """
    measures: list[list[JianpuSymbol]] = []
    current: list[JianpuSymbol] = []

    for sym in symbols:
        if sym.rhythm == "chord":
            current.append(sym)
            continue

        if sym.is_newline():
            if current:
                measures.append(current)
                current = []
            continue

        current.append(sym)

        if sym.is_barline() or "repeat" in sym.rhythm or "volta" in sym.rhythm:
            measures.append(current)
            current = []

    if current:
        measures.append(current)

    return measures if measures else [[]]
