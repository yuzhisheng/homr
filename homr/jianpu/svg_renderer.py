"""
SVG renderer for jianpu (numbered musical notation).

Renders JianpuSymbol sequences as SVG using the layout engine (layout.py)
and symbol path library (svg_symbols.py).

Supports:
- Numbers 1-7 for scale degrees, 0 for rests
- Octave dots above/below
- Duration underlines (beamed groups)
- Augmentation dots
- Barlines (single, double, repeat)
- Key/time signatures
- Lyrics
- Dizi techniques (symbols above notes)
- Tie/slur curves (quadratic Bézier)
- Dynamic markings
- Accents, tenuto, fermata
"""

import html
import math

from homr.jianpu.layout import (
    DEFAULT_CONFIG,
    LayoutConfig,
    NoteLayout,
    ScoreLayout,
    calculate_layout_from_symbols,
)
from homr.jianpu.svg_symbols import make_svg_path
from homr.jianpu.vocabulary import JianpuSymbol, nonote, empty

_FONT_FAMILY = "serif"


def _escape_text(text: str) -> str:
    """Escape text for XML/SVG output."""
    return html.escape(text, quote=True)


def _format_key_label(key_name: str) -> str:
    return f"1={key_name}"


def _format_time_label(beats: int, beat_type: int) -> str:
    return f"{beats}/{beat_type}"


def _draw_bezier_curve(
    x1: float, y1: float, x2: float, y2: float,
    height: float, color: str, stroke_width: float = 1.2,
) -> str:
    """Draw a quadratic Bézier curve (for tie/slur) as an SVG path."""
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2 - height
    return (
        f'<path d="M {x1:.2f},{y1:.2f} Q {mid_x:.2f},{mid_y:.2f} {x2:.2f},{y2:.2f}" '
        f'stroke="{color}" stroke-width="{stroke_width}" fill="none" '
        f'stroke-linecap="round"/>'
    )


def _render_title(layout: ScoreLayout, cfg: LayoutConfig) -> list[str]:
    """Render the title element."""
    if layout.titlePosition is None:
        return []
    tp = layout.titlePosition
    return [
        f'<text x="{tp.x + tp.width / 2:.2f}" y="{tp.y + cfg.titleFontSize:.2f}" '
        f'font-family="{_FONT_FAMILY}" font-size="{cfg.noteFontSize}" '
        f'font-weight="bold" text-anchor="middle" fill="black">'
        f'</text>'
    ]


def _render_header(layout: ScoreLayout, cfg: LayoutConfig) -> list[str]:
    """Render the key/time/tempo header."""
    parts: list[str] = []

    if layout.keyPosition is not None:
        kp = layout.keyPosition
        # Extract key name from the position — we store the full "1=X" text
        # We'll use the key text directly
        parts.append(
            f'<text x="{kp.x:.2f}" y="{kp.y + cfg.metaFontSize:.2f}" '
            f'font-family="{_FONT_FAMILY}" font-size="{cfg.metaFontSize}" '
            f'fill="black">{_escape_text(_format_key_label(_extract_key_from_layout(layout)))}</text>'
        )

    if layout.timeSignaturePosition is not None:
        tp = layout.timeSignaturePosition
        beats, beat_type = _extract_time_from_layout(layout)
        # Draw as two stacked numbers with a line between
        digit_y = tp.y + cfg.metaFontSize
        parts.append(
            f'<text x="{tp.x + tp.width / 2:.2f}" y="{digit_y:.2f}" '
            f'font-family="{_FONT_FAMILY}" font-size="{cfg.metaFontSize}" '
            f'text-anchor="middle" fill="black">{beats}</text>'
        )
        parts.append(
            f'<line x1="{tp.x:.2f}" y1="{digit_y + 2:.2f}" '
            f'x2="{tp.x + tp.width:.2f}" y2="{digit_y + 2:.2f}" '
            f'stroke="black" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{tp.x + tp.width / 2:.2f}" y="{digit_y + cfg.metaFontSize + 4:.2f}" '
            f'font-family="{_FONT_FAMILY}" font-size="{cfg.metaFontSize}" '
            f'text-anchor="middle" fill="black">{beat_type}</text>'
        )

    if layout.tempoPosition is not None and layout.tempoText:
        tp = layout.tempoPosition
        parts.append(
            f'<text x="{tp.x:.2f}" y="{tp.y + cfg.metaFontSize:.2f}" '
            f'font-family="{_FONT_FAMILY}" font-size="{cfg.metaFontSize}" '
            f'fill="black">{_escape_text(layout.tempoText)}</text>'
        )

    return parts


def _extract_key_from_layout(layout: ScoreLayout) -> str:
    """Extract key name from layout key position."""
    # We don't store the key name in ScoreLayout directly, but it's implied
    # by the key text. For rendering, we need to reconstruct it.
    # Since we have the position but not the text, we use a fallback.
    # In practice, the key name is passed through the symbols.
    return "C"  # Fallback — will be overridden


def _extract_time_from_layout(layout: ScoreLayout) -> tuple[int, int]:
    """Extract time signature from layout."""
    return (4, 4)  # Fallback


def _render_note(nl: NoteLayout, cfg: LayoutConfig) -> list[str]:
    """Render a single note layout to SVG elements."""
    parts: list[str] = []
    sym = nl.symbol
    pos = nl.position

    cx = pos.x + pos.width / 2
    cy = pos.y + cfg.noteFontSize

    if nl.item_type == "dash":
        # Render dash as a horizontal line
        line_y = pos.y + cfg.noteHeight / 2
        parts.append(
            f'<line x1="{pos.x + 2:.2f}" y1="{line_y:.2f}" '
            f'x2="{pos.x + pos.width - 2:.2f}" y2="{line_y:.2f}" '
            f'stroke="black" stroke-width="{cfg.dashThickness}"/>'
        )
        return parts

    # Octave dots
    for dp in nl.upperDotPositions:
        parts.append(
            f'<circle cx="{dp.x + dp.width / 2:.2f}" cy="{dp.y + dp.height / 2:.2f}" '
            f'r="{cfg.dotRadius}" fill="black"/>'
        )
    for dp in nl.lowerDotPositions:
        parts.append(
            f'<circle cx="{dp.x + dp.width / 2:.2f}" cy="{dp.y + dp.height / 2:.2f}" '
            f'r="{cfg.dotRadius}" fill="black"/>'
        )

    # Accidental
    if nl.accidentalPosition is not None:
        ap = nl.accidentalPosition
        acc = sym.accidental
        sym_num = None
        if acc == "#":
            sym_num = 1
        elif acc == "b":
            sym_num = 2
        elif acc == "N":
            sym_num = 3
        elif acc == "##":
            sym_num = 1  # Approximate with sharp
        elif acc == "bb":
            sym_num = 2  # Approximate with flat

        if sym_num is not None:
            path_svg = make_svg_path(sym_num, ap.x + 8, ap.y + 8, 16, "black")
            if path_svg:
                parts.append(path_svg)
        else:
            acc_char = {"#": "♯", "b": "♭", "N": "♮", "##": "𝄪", "bb": "𝄫"}.get(acc, "")
            if acc_char:
                parts.append(
                    f'<text x="{ap.x:.2f}" y="{cy:.2f}" '
                    f'font-family="{_FONT_FAMILY}" font-size="{cfg.noteFontSize * 0.7}" '
                    f'fill="black">{_escape_text(acc_char)}</text>'
                )

    # Main number
    degree_val = sym.get_degree_value()
    if sym.is_rest() or degree_val == 0:
        display_text = "0"
    elif degree_val is not None:
        display_text = str(degree_val)
    else:
        display_text = "·"

    # Check for grace note (smaller, italic)
    kern = sym.get_kern()
    is_grace = "G" in kern
    font_size = cfg.noteFontSize * 0.7 if is_grace else cfg.noteFontSize
    font_style = ' font-style="italic"' if is_grace else ""

    parts.append(
        f'<text x="{cx:.2f}" y="{cy:.2f}" '
        f'font-family="{_FONT_FAMILY}" font-size="{font_size}" '
        f'text-anchor="middle" fill="black"{font_style}>'
        f'{_escape_text(display_text)}</text>'
    )

    # Augmentation dots
    for dp in nl.dotPositions:
        parts.append(
            f'<circle cx="{dp.x + dp.width / 2:.2f}" cy="{dp.y + dp.height / 2:.2f}" '
            f'r="{cfg.accentDotRadius}" fill="black"/>'
        )

    # Underlines (duration beams)
    for ul in nl.underlines:
        ux_start = pos.x + ul.xOffset
        ux_end = ux_start + ul.width
        if ul.width > 0:
            parts.append(
                f'<line x1="{ux_start:.2f}" y1="{ul.y:.2f}" '
                f'x2="{ux_end:.2f}" y2="{ul.y:.2f}" '
                f'stroke="black" stroke-width="{cfg.underlineThickness}"/>'
            )

    # Techniques
    for tl in nl.techniquePositions:
        tp = tl.position
        parts.append(
            f'<text x="{tp.x + tp.width / 2:.2f}" y="{tp.y + cfg.techniqueFontSize:.2f}" '
            f'font-family="{_FONT_FAMILY}" font-size="{cfg.techniqueFontSize}" '
            f'text-anchor="middle" fill="black">{_escape_text(tl.label)}</text>'
        )

    # Accent mark
    if nl.accentPosition is not None:
        ap = nl.accentPosition
        path_svg = make_svg_path(10, ap.x + ap.width / 2, ap.y + ap.height / 2, 8, "black")
        if path_svg:
            parts.append(path_svg)

    # Tenuto mark
    if nl.tenutoPosition is not None:
        tp = nl.tenutoPosition
        path_svg = make_svg_path(45, tp.x + tp.width / 2, tp.y + tp.height / 2, 10, "black")
        if path_svg:
            parts.append(path_svg)

    # Fermata
    if nl.fermataPosition is not None:
        fp = nl.fermataPosition
        path_svg = make_svg_path(8, fp.x + fp.width / 2, fp.y + fp.height / 2, 20, "black")
        if path_svg:
            parts.append(path_svg)

    # Staccato (顿音 ▼)
    if nl.staccatoPosition is not None:
        sp = nl.staccatoPosition
        path_svg = make_svg_path(11, sp.x + sp.width / 2, sp.y + sp.height / 2, 8, "black")
        if path_svg:
            parts.append(path_svg)

    # Force accent marks (sf/sfp/fp)
    if sym.articulation in ("sf", "sfp", "fp"):
        parts.append(
            f'<text x="{cx:.2f}" y="{pos.y - 4:.2f}" '
            f'font-family="{_FONT_FAMILY}" font-size="{cfg.techniqueFontSize}" '
            f'text-anchor="middle" fill="black" font-style="italic">'
            f'{_escape_text(sym.articulation)}</text>'
        )

    # Dynamic marking
    if nl.dynamicPosition is not None:
        dp = nl.dynamicPosition
        parts.append(
            f'<text x="{dp.x + dp.width / 2:.2f}" y="{dp.y + cfg.lyricFontSize:.2f}" '
            f'font-family="{_FONT_FAMILY}" font-size="{cfg.lyricFontSize}" '
            f'text-anchor="middle" fill="black" font-style="italic">'
            f'{_escape_text(sym.dynamic)}</text>'
        )

    # Lyric
    if nl.lyricPosition is not None:
        lp = nl.lyricPosition
        parts.append(
            f'<text x="{lp.x + lp.width / 2:.2f}" y="{lp.y:.2f}" '
            f'font-family="{_FONT_FAMILY}" font-size="{cfg.lyricFontSize}" '
            f'text-anchor="middle" fill="black">'
            f'{_escape_text(sym.lyric)}</text>'
        )

    return parts


def _render_barline(ml_barline_pos, barline_type: str, cfg: LayoutConfig) -> list[str]:
    """Render a barline."""
    parts: list[str] = []
    if ml_barline_pos is None:
        return parts

    bp = ml_barline_pos
    top = bp.y
    bottom = bp.y + bp.height

    if barline_type in ("doublebarline", "bolddoublebarline"):
        x1 = bp.x
        x2 = bp.x + 3
        parts.append(
            f'<line x1="{x1:.2f}" y1="{top:.2f}" x2="{x1:.2f}" y2="{bottom:.2f}" '
            f'stroke="black" stroke-width="{cfg.barlineWidth}"/>'
        )
        parts.append(
            f'<line x1="{x2:.2f}" y1="{top:.2f}" x2="{x2:.2f}" y2="{bottom:.2f}" '
            f'stroke="black" stroke-width="{cfg.barlineWidth}"/>'
        )
    elif barline_type in ("repeatStart", "repeatEnd"):
        # Draw repeat barline: thin + thick + dots
        dot_x = bp.x - 4 if barline_type == "repeatEnd" else bp.x + 6
        x1 = bp.x
        x2 = bp.x + 4
        parts.append(
            f'<line x1="{x1:.2f}" y1="{top:.2f}" x2="{x1:.2f}" y2="{bottom:.2f}" '
            f'stroke="black" stroke-width="1"/>'
        )
        parts.append(
            f'<line x1="{x2:.2f}" y1="{top:.2f}" x2="{x2:.2f}" y2="{bottom:.2f}" '
            f'stroke="black" stroke-width="3"/>'
        )
        mid_y = (top + bottom) / 2
        parts.append(
            f'<circle cx="{dot_x:.2f}" cy="{mid_y - 4:.2f}" r="1.5" fill="black"/>'
        )
        parts.append(
            f'<circle cx="{dot_x:.2f}" cy="{mid_y + 4:.2f}" r="1.5" fill="black"/>'
        )
    else:
        # Single barline
        parts.append(
            f'<line x1="{bp.x:.2f}" y1="{top:.2f}" x2="{bp.x:.2f}" y2="{bottom:.2f}" '
            f'stroke="black" stroke-width="{cfg.barlineWidth}"/>'
        )

    return parts


def _render_ties_slurs(
    note_layouts: list[NoteLayout], cfg: LayoutConfig,
) -> list[str]:
    """Render tie and slur curves between notes."""
    parts: list[str] = []
    tie_height = cfg.tieCurveHeight

    # Ties
    i = 0
    while i < len(note_layouts):
        nl = note_layouts[i]
        if nl.tieStart:
            # Find the end of the tie
            for j in range(i + 1, len(note_layouts)):
                if note_layouts[j].tieEnd:
                    x1 = nl.position.x + nl.position.width / 2
                    y1 = nl.position.y + cfg.noteHeight + 2
                    x2 = note_layouts[j].position.x + note_layouts[j].position.width / 2
                    y2 = note_layouts[j].position.y + cfg.noteHeight + 2
                    parts.append(_draw_bezier_curve(x1, y1, x2, y2, tie_height, "black"))
                    break
        i += 1

    # Slurs
    i = 0
    while i < len(note_layouts):
        nl = note_layouts[i]
        if nl.slurStart:
            for j in range(i + 1, len(note_layouts)):
                if note_layouts[j].slurEnd:
                    x1 = nl.position.x + nl.position.width / 2
                    y1 = nl.position.y - 2
                    x2 = note_layouts[j].position.x + note_layouts[j].position.width / 2
                    y2 = note_layouts[j].position.y - 2
                    parts.append(_draw_bezier_curve(x1, y1, x2, y2, tie_height, "black"))
                    break
        i += 1

    return parts


def render_jianpu_svg(
    symbols: list[JianpuSymbol],
    title: str = "",
    width: int = 800,
    height: int | None = None,
    config: LayoutConfig | None = None,
) -> str:
    """Render a list of jianpu symbols as an SVG string.

    Args:
        symbols: List of JianpuSymbol objects
        title: Title to display at the top of the score
        width: SVG width in pixels
        height: Optional SVG height (auto-calculated if None)
        config: Optional layout configuration override

    Returns:
        SVG document as a string
    """
    cfg = config or DEFAULT_CONFIG
    if cfg.canvasWidth != width:
        # Create a config with the requested width
        cfg = LayoutConfig(
            canvasWidth=width,
            paddingHorizontal=cfg.paddingHorizontal,
            paddingVertical=cfg.paddingVertical,
            noteFontSize=cfg.noteFontSize,
            noteWidth=cfg.noteWidth,
            noteHeight=cfg.noteHeight,
            measureGap=cfg.measureGap,
            rowGap=cfg.rowGap,
            dotRadius=cfg.dotRadius,
            dotGap=cfg.dotGap,
            accentDotRadius=cfg.accentDotRadius,
            underlineOffset=cfg.underlineOffset,
            underlineGap=cfg.underlineGap,
            underlineThickness=cfg.underlineThickness,
            dashThickness=cfg.dashThickness,
            barlineWidth=cfg.barlineWidth,
            techniqueFontSize=cfg.techniqueFontSize,
            titleFontSize=cfg.titleFontSize,
            metaFontSize=cfg.metaFontSize,
            tieCurveHeight=cfg.tieCurveHeight,
            lyricFontSize=cfg.lyricFontSize,
            lyricOffset=cfg.lyricOffset,
        )

    layout = calculate_layout_from_symbols(symbols, cfg, title)

    svg_height = height if height is not None else int(layout.height)

    svg_parts: list[str] = []

    # SVG header
    svg_parts.append(
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{int(layout.width)}" height="{svg_height}" '
        f'viewBox="0 0 {int(layout.width)} {svg_height}">'
    )

    # Background
    svg_parts.append(
        f'<rect width="{int(layout.width)}" height="{svg_height}" fill="white"/>'
    )

    # Title
    if layout.titlePosition is not None:
        tp = layout.titlePosition
        svg_parts.append(
            f'<text x="{tp.x + tp.width / 2:.2f}" y="{tp.y + cfg.titleFontSize:.2f}" '
            f'font-family="{_FONT_FAMILY}" font-size="{cfg.titleFontSize}" '
            f'font-weight="bold" text-anchor="middle" fill="black">'
            f'{_escape_text(title)}</text>'
        )

    # Header (key/time/tempo)
    svg_parts.extend(_render_header_with_data(symbols, layout, cfg))

    # Render rows
    for row in layout.rows:
        for ml in row.measures:
            # Render notes
            for nl in ml.notes:
                svg_parts.extend(_render_note(nl, cfg))

            # Render barline
            if ml.barlinePosition is not None:
                svg_parts.extend(_render_barline(ml.barlinePosition, ml.barlineType, cfg))

            # Render ties/slurs within this measure
            svg_parts.extend(_render_ties_slurs(ml.notes, cfg))

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def _render_header_with_data(
    symbols: list[JianpuSymbol],
    layout: ScoreLayout,
    cfg: LayoutConfig,
) -> list[str]:
    """Render the header using data extracted from the symbol list."""
    parts: list[str] = []

    key_name = "C"
    time_sig = (4, 4)
    tempo: int | None = None

    for sym in symbols:
        if sym.is_key_signature():
            key_name = sym.get_key_name()
        elif sym.is_time_signature():
            time_sig = sym.get_time_signature()
        elif sym.rhythm.startswith("jtempo_"):
            tempo = int(sym.rhythm[len("jtempo_"):])

    # Key signature
    if layout.keyPosition is not None:
        kp = layout.keyPosition
        key_text = _format_key_label(key_name)
        parts.append(
            f'<text x="{kp.x:.2f}" y="{kp.y + cfg.metaFontSize:.2f}" '
            f'font-family="{_FONT_FAMILY}" font-size="{cfg.metaFontSize}" '
            f'fill="black">{_escape_text(key_text)}</text>'
        )

    # Time signature
    if layout.timeSignaturePosition is not None:
        tp = layout.timeSignaturePosition
        beats, beat_type = time_sig
        digit_y = tp.y + cfg.metaFontSize
        parts.append(
            f'<text x="{tp.x + tp.width / 2:.2f}" y="{digit_y:.2f}" '
            f'font-family="{_FONT_FAMILY}" font-size="{cfg.metaFontSize}" '
            f'text-anchor="middle" fill="black">{beats}</text>'
        )
        parts.append(
            f'<line x1="{tp.x:.2f}" y1="{digit_y + 2:.2f}" '
            f'x2="{tp.x + tp.width:.2f}" y2="{digit_y + 2:.2f}" '
            f'stroke="black" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{tp.x + tp.width / 2:.2f}" y="{digit_y + cfg.metaFontSize + 4:.2f}" '
            f'font-family="{_FONT_FAMILY}" font-size="{cfg.metaFontSize}" '
            f'text-anchor="middle" fill="black">{beat_type}</text>'
        )

    # Tempo
    if layout.tempoPosition is not None and tempo:
        tp = layout.tempoPosition
        tempo_text = f"♩={tempo}"
        parts.append(
            f'<text x="{tp.x:.2f}" y="{tp.y + cfg.metaFontSize:.2f}" '
            f'font-family="{_FONT_FAMILY}" font-size="{cfg.metaFontSize}" '
            f'fill="black">{_escape_text(tempo_text)}</text>'
        )

    return parts


def render_jianpu_svg_to_file(
    symbols: list[JianpuSymbol],
    output_path: str,
    title: str = "",
    width: int = 800,
    height: int | None = None,
    config: LayoutConfig | None = None,
) -> None:
    """Render jianpu symbols to an SVG file.

    Args:
        symbols: List of JianpuSymbol objects
        output_path: Path to write the .svg file
        title: Title to display
        width: SVG width
        height: Optional SVG height
        config: Optional layout configuration
    """
    svg_content = render_jianpu_svg(symbols, title, width, height, config)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
