"""
Auto-labeled training data generator for jianpu (numbered notation).

Generates random jianpu melodies with full feature support:
- Notes, rests, dashes (augmentation lines)
- Octave dots, accidentals, augmentation dots
- Duration underlines (beamed groups)
- Dizi techniques (boyin, chanyin, dayin, etc.)
- Tie/slur/triplet group markers
- Dynamic markings (pp/p/mp/mf/f/ff)
- Force accents (sf/sfp/fp)
- Lyrics
- Barlines, repeats, key/time signatures

Also supports converting existing staff .tokens files to jianpu format.
"""

import os
import random

from homr.jianpu.constants import (
    DIZI_TECHNIQUE_TYPES,
    DYNAMIC_MARKS,
    FORCE_ACCENT_MARKS,
    SUPPORTED_KEYS,
)
from homr.jianpu.svg_renderer import render_jianpu_svg_to_file
from homr.jianpu.token_io import write_jianpu_tokens_to_file
from homr.jianpu.vocabulary import (
    JIANPU_KEY_PREFIX,
    JIANPU_TIME_PREFIX,
    JianpuSymbol,
    empty,
    nonote,
)


# Common rhythm patterns (durations in quarter-note units)
# Each entry is a list of durations
_RHYTHM_PATTERNS: list[list[float]] = [
    [1.0, 1.0, 1.0, 1.0],           # Four quarter notes
    [0.5, 0.5, 1.0, 0.5, 0.5],      # Eighth-eighth-quarter-eighth-eighth
    [1.5, 0.5, 1.0, 1.0],           # Dotted quarter, eighth, quarter, quarter
    [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],  # Eight eighth notes
    [2.0, 1.0, 1.0],                 # Half, quarter, quarter
    [1.0, 1.0, 2.0],                 # Quarter, quarter, half
    [0.75, 0.25, 1.0, 1.0],         # Dotted eighth, sixteenth, quarter, quarter
    [0.25, 0.25, 0.25, 0.25, 1.0, 1.0],  # Four sixteenths, two quarters
    [3.0, 1.0],                       # Dotted half, quarter
    [1.0, 0.5, 0.5, 1.0, 1.0],      # Quarter, two eighths, two quarters
]

# Common time signatures
_TIME_SIGNATURES: list[tuple[int, int]] = [
    (4, 4),
    (3, 4),
    (2, 4),
    (6, 8),
]

# Sample lyrics (Chinese characters from jianpu-renderer)
_LYRICS_POOL = "春夏秋冬风花雪月山水云雨星日天地人梦心光影灯火歌行路远近高深清静明亮暖凉红绿黄白青蓝" \
               "我爱你的大地飞雁想象远方"
_SAMPLE_LYRICS: list[str | None] = list(_LYRICS_POOL) + [None, None, None, None]


# Duration to kern mapping
def _duration_to_kern(duration: float, dot: int = 0) -> str:
    """Convert a duration (quarter-note units) to kern string."""
    if duration >= 4:
        base = "1"
    elif duration >= 2:
        base = "2"
    elif duration >= 1:
        base = "4"
    elif duration >= 0.5:
        base = "8"
    elif duration >= 0.25:
        base = "16"
    else:
        base = "32"
    return base + "." * dot


class GeneratorConfig:
    """Configuration for jianpu data generation."""

    def __init__(
        self,
        key: str = "C",
        time_signature: tuple[int, int] = (4, 4),
        num_measures: int = 4,
        with_lyrics: bool = True,
        with_accidentals: bool = False,
        with_techniques: bool = False,
        with_groups: bool = False,
        with_dynamics: bool = False,
        with_repeats: bool = False,
        with_rests: bool = True,
        octave_range: int = 1,
        seed: int | None = None,
    ) -> None:
        self.key = key
        self.time_signature = time_signature
        self.num_measures = num_measures
        self.with_lyrics = with_lyrics
        self.with_accidentals = with_accidentals
        self.with_techniques = with_techniques
        self.with_groups = with_groups
        self.with_dynamics = with_dynamics
        self.with_repeats = with_repeats
        self.with_rests = with_rests
        self.octave_range = octave_range
        self.seed = seed

        if seed is not None:
            random.seed(seed)


def generate_random_melody(config: GeneratorConfig) -> list[JianpuSymbol]:
    """Generate a random jianpu melody with full feature support.

    Args:
        config: Generator configuration

    Returns:
        List of JianpuSymbol objects representing a complete melody
    """
    if config.seed is not None:
        random.seed(config.seed)

    symbols: list[JianpuSymbol] = []

    # Key signature
    symbols.append(JianpuSymbol(rhythm=f"{JIANPU_KEY_PREFIX}{config.key}"))

    # Time signature
    beats, beat_type = config.time_signature
    symbols.append(JianpuSymbol(rhythm=f"{JIANPU_TIME_PREFIX}{beats}_{beat_type}"))

    # Generate measures
    for measure_idx in range(config.num_measures):
        measure_symbols = _generate_measure(config, measure_idx)
        symbols.extend(measure_symbols)

        # Add barline (except after the last measure, unless repeats are on)
        if measure_idx < config.num_measures - 1:
            if config.with_repeats and measure_idx == 0 and random.random() < 0.2:
                symbols.append(JianpuSymbol("repeatStart"))
            elif config.with_repeats and measure_idx == config.num_measures - 2 and random.random() < 0.2:
                symbols.append(JianpuSymbol("repeatEnd"))
            else:
                symbols.append(JianpuSymbol("barline"))

    return symbols


def _generate_measure(config: GeneratorConfig, measure_idx: int) -> list[JianpuSymbol]:
    """Generate a single measure of random jianpu notes."""
    beats, beat_type = config.time_signature
    beats_per_measure = beats
    beat_duration = 4.0 / beat_type  # Duration of one beat in quarter units

    symbols: list[JianpuSymbol] = []
    prev_degree = random.randint(1, 7)
    total_duration = 0.0
    max_duration = beats_per_measure * beat_duration

    # Track active groups for this measure
    tie_active = False
    slur_active = False

    while total_duration < max_duration - 0.01:
        remaining = max_duration - total_duration

        # Pick a duration that fits
        choices: list[float] = []
        if remaining >= 2.0:
            choices.extend([2.0, 1.0, 1.0])
        if remaining >= 1.5:
            choices.append(1.5)
        if remaining >= 1.0:
            choices.extend([1.0, 1.0, 1.0])
        if remaining >= 0.75:
            choices.append(0.75)
        if remaining >= 0.5:
            choices.extend([0.5, 0.5])
        if remaining >= 0.25:
            choices.extend([0.25, 0.25])

        if not choices:
            break

        duration = random.choice(choices)
        total_duration += duration

        # Rest?
        if config.with_rests and random.random() < 0.08 and duration >= 0.5:
            kern = _duration_to_kern(duration)
            symbols.append(JianpuSymbol(
                rhythm=f"rest_{kern}",
                degree="0",
                octave="0",
                accidental=empty,
                articulation=empty,
                lyric=nonote,
            ))
            continue

        # Random walk on the scale
        step = random.choice([-2, -1, -1, 0, 1, 1, 2])
        degree = max(1, min(7, prev_degree + step))
        prev_degree = degree

        # Octave
        octave = 0
        if config.octave_range > 0 and random.random() < 0.1:
            octave = random.choice([-1, 1])

        # Accidental
        accidental = empty
        if config.with_accidentals and random.random() < 0.05:
            accidental = random.choice(["#", "b", "N"])

        # Dots
        dot = 0
        if random.random() < 0.1 and duration >= 0.5:
            dot = 1

        kern = _duration_to_kern(duration, dot)

        # Articulation
        articulation = nonote
        if random.random() < 0.05:
            articulation = random.choice(["accent", "tenuto", "fermata", "staccato"])
        elif random.random() < 0.02:
            articulation = random.choice(FORCE_ACCENT_MARKS)

        # Technique
        technique = nonote
        if config.with_techniques and random.random() < 0.1:
            technique = random.choice(DIZI_TECHNIQUE_TYPES)

        # Group (tie/slur/triplet)
        group = nonote
        if config.with_groups:
            if random.random() < 0.1 and not tie_active:
                group = "tie_start"
                tie_active = True
            elif random.random() < 0.15 and not slur_active:
                group = "slur_start"
                slur_active = True
            elif tie_active and random.random() < 0.3:
                group = "tie_end"
                tie_active = False
            elif slur_active and random.random() < 0.3:
                group = "slur_end"
                slur_active = False

        # Dynamic
        dynamic = nonote
        if config.with_dynamics and random.random() < 0.06:
            dynamic = random.choice(DYNAMIC_MARKS)

        # Lyric
        lyric = nonote
        if config.with_lyrics:
            lyric_choice = random.choice(_SAMPLE_LYRICS)
            if lyric_choice is not None:
                lyric = lyric_choice

        symbols.append(JianpuSymbol(
            rhythm=f"note_{kern}",
            degree=str(degree),
            octave=str(octave),
            accidental=accidental,
            articulation=articulation,
            lyric=lyric,
            technique=technique,
            group=group,
            dynamic=dynamic,
        ))

    # End any active groups at measure boundary
    if tie_active and symbols:
        last = symbols[-1]
        if last.group == "tie_start" or last.group == nonote:
            last.group = "tie_end"
    if slur_active and symbols:
        last = symbols[-1]
        if last.group == "slur_start" or last.group == nonote:
            last.group = "slur_end"

    # Add dashes for remaining time (if under-filled)
    while total_duration < max_duration - 0.01:
        symbols.append(JianpuSymbol(
            rhythm="dash",
            degree=nonote,
            octave=nonote,
            accidental=nonote,
            articulation=nonote,
            lyric=nonote,
        ))
        total_duration += 1.0

    return symbols


def generate_dataset(
    count: int,
    output_dir: str,
    config: GeneratorConfig | None = None,
    render_png: bool = False,
) -> list[str]:
    """Generate a batch of jianpu training data samples.

    For each sample, generates:
    - <name>.jtokens : jianpu token file
    - <name>.svg : SVG rendering
    - <name>.png : PNG rendering (optional, requires cairosvg)

    Args:
        count: Number of samples to generate
        output_dir: Directory to write output files
        config: Optional generator config (randomized if None)
        render_png: Whether to also render PNG files

    Returns:
        List of generated file base paths (without extension)
    """
    os.makedirs(output_dir, exist_ok=True)
    generated_files: list[str] = []

    for i in range(count):
        # Randomize config if not provided
        if config is None:
            key = random.choice(SUPPORTED_KEYS)
            time_sig = random.choice(_TIME_SIGNATURES)
            num_measures = random.choice([2, 4, 4, 8])
            with_lyrics = random.random() < 0.7
            with_techniques = random.random() < 0.4
            with_groups = random.random() < 0.5
            with_dynamics = random.random() < 0.3
            with_accidentals = random.random() < 0.3
            with_repeats = random.random() < 0.2

            gen_config = GeneratorConfig(
                key=key,
                time_signature=time_sig,
                num_measures=num_measures,
                with_lyrics=with_lyrics,
                with_accidentals=with_accidentals,
                with_techniques=with_techniques,
                with_groups=with_groups,
                with_dynamics=with_dynamics,
                with_repeats=with_repeats,
                seed=i,
            )
        else:
            gen_config = config

        # Generate melody
        symbols = generate_random_melody(gen_config)

        # File names
        base_name = f"jianpu_{i:04d}"
        base_path = os.path.join(output_dir, base_name)

        # Write .jtokens file
        tokens_path = base_path + ".jtokens"
        write_jianpu_tokens_to_file(symbols, tokens_path)

        # Write .svg file
        svg_path = base_path + ".svg"
        title = f"Sample {i + 1} - Key: {gen_config.key}"
        render_jianpu_svg_to_file(symbols, svg_path, title=title)

        # Write .png file (optional)
        if render_png:
            try:
                import cairosvg
                png_path = base_path + ".png"
                cairosvg.svg2png(url=svg_path, write_to=png_path)
            except ImportError:
                pass  # cairosvg not available

        generated_files.append(base_path)

    return generated_files


def convert_staff_tokens_to_jianpu(
    staff_tokens_path: str,
    output_jtokens_path: str,
    output_svg_path: str | None = None,
    key: str = "C",
) -> list[JianpuSymbol]:
    """Convert an existing staff .tokens file to jianpu format.

    Args:
        staff_tokens_path: Path to the existing .tokens file
        output_jtokens_path: Path to write the .jtokens file
        output_svg_path: Optional path to write an SVG rendering
        key: Key to use for degree conversion

    Returns:
        List of generated JianpuSymbol objects
    """
    from training.transformer.training_vocabulary import read_tokens

    # Read staff tokens
    staff_symbols = read_tokens(staff_tokens_path)

    # Convert to jianpu
    from homr.jianpu.degree_mapper import DegreeMapper
    mapper = DegreeMapper(key)
    jianpu_symbols: list[JianpuSymbol] = []

    # Add key signature at the start
    jianpu_symbols.append(JianpuSymbol(
        rhythm=f"{JIANPU_KEY_PREFIX}{key}",
    ))

    for symbol in staff_symbols:
        if symbol.rhythm == "chord":
            jianpu_symbols.append(JianpuSymbol("chord"))
            continue

        if symbol.rhythm == "newline":
            jianpu_symbols.append(JianpuSymbol("newline"))
            continue

        if symbol.rhythm.startswith("clef"):
            continue

        if symbol.rhythm.startswith("keySignature"):
            fifths_str = symbol.rhythm.split("_")[1]
            fifths = int(fifths_str)
            from homr.jianpu.constants import fifths_to_key
            key_name = fifths_to_key(fifths)
            mapper.set_key(key_name)
            jianpu_symbols.append(JianpuSymbol(
                rhythm=f"{JIANPU_KEY_PREFIX}{key_name}",
            ))
            continue

        if symbol.rhythm.startswith("timeSignature"):
            beat_type_str = symbol.rhythm.split("/")[1]
            beat_type = int(beat_type_str)
            beats_map = {4: 4, 8: 6, 2: 2}
            beats = beats_map.get(beat_type, 4)
            jianpu_symbols.append(JianpuSymbol(
                rhythm=f"{JIANPU_TIME_PREFIX}{beats}_{beat_type}",
            ))
            continue

        if symbol.rhythm.startswith("barline") or "repeat" in symbol.rhythm or "volta" in symbol.rhythm:
            jianpu_symbols.append(JianpuSymbol(symbol.rhythm))
            continue

        if symbol.rhythm.startswith("note") or symbol.rhythm.startswith("rest"):
            jianpu_sym = _convert_staff_note_to_jianpu(symbol, mapper)
            if jianpu_sym is not None:
                jianpu_symbols.append(jianpu_sym)
            continue

    # Write output files
    write_jianpu_tokens_to_file(jianpu_symbols, output_jtokens_path)
    if output_svg_path is not None:
        render_jianpu_svg_to_file(jianpu_symbols, output_svg_path)

    return jianpu_symbols


def _convert_staff_note_to_jianpu(
    staff_symbol: object, mapper: "DegreeMapper"
) -> JianpuSymbol | None:
    """Convert a single staff EncodedSymbol note to a jianpu symbol."""
    from homr.transformer.vocabulary import EncodedSymbol, nonote as staff_nonote, empty as staff_empty

    if not isinstance(staff_symbol, EncodedSymbol):
        return None

    rhythm = staff_symbol.rhythm

    # Extract kern duration from rhythm
    import re
    match = re.match(r"(note|rest)_(\d+[G\.]*)", rhythm)
    if not match:
        return None

    kern = match.group(2)

    # For rests
    if match.group(1) == "rest":
        return JianpuSymbol(
            rhythm=f"rest_{kern}",
            degree="0", octave="0", accidental=empty,
            articulation=staff_symbol.articulation if staff_symbol.articulation != staff_nonote else empty,
            lyric=nonote,
        )

    # For notes: convert pitch to degree
    pitch = staff_symbol.pitch
    if pitch in (staff_nonote, staff_empty):
        return JianpuSymbol(
            rhythm=f"note_{kern}",
            degree="0", octave="0", accidental=empty,
            articulation=empty, lyric=nonote,
        )

    # Parse pitch
    pitch_match = re.match(r"([A-G])([#b]*)(\d+)", pitch)
    if not pitch_match:
        return None

    letter = pitch_match.group(1)
    accidentals = pitch_match.group(2)
    octave = int(pitch_match.group(3))

    note_name = letter + accidentals

    alter = 0
    for c in accidentals:
        if c == "#":
            alter += 1
        elif c == "b":
            alter -= 1

    lift = staff_symbol.lift
    if lift == "#":
        alter += 1
    elif lift == "b":
        alter -= 1
    elif lift == "##":
        alter += 2
    elif lift == "bb":
        alter -= 2

    degree, octave_offset, accidental_token = mapper.pitch_to_degree(note_name, octave, alter)

    accidental_out = accidental_token if accidental_token else empty
    articulation_out = staff_symbol.articulation if staff_symbol.articulation != staff_nonote else empty

    return JianpuSymbol(
        rhythm=f"note_{kern}",
        degree=str(degree),
        octave=str(octave_offset),
        accidental=accidental_out,
        articulation=articulation_out,
        lyric=nonote,
    )
