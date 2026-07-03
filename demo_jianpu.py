"""Standalone demo: generate a random jianpu melody and render it to SVG."""

import os

from homr.jianpu.data_generator import (
    GeneratorConfig,
    generate_random_melody,
)
from homr.jianpu.svg_renderer import render_jianpu_svg_to_file
from homr.jianpu.token_io import write_jianpu_tokens_to_file


def main() -> None:
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_prefix = os.path.join(output_dir, "jianpu_demo")
    tokens_path = output_prefix + ".jtokens"
    svg_path = output_prefix + ".svg"

    config = GeneratorConfig(
        seed=42,
        num_measures=4,
        with_lyrics=True,
        with_accidentals=True,
        with_techniques=True,
        with_groups=True,
        with_dynamics=True,
        octave_range=1,
    )

    symbols = generate_random_melody(config)

    write_jianpu_tokens_to_file(symbols, tokens_path)
    render_jianpu_svg_to_file(symbols, svg_path, title="Random Jianpu Demo")

    print(f"Generated {len(symbols)} symbols")
    print(f"Tokens: {tokens_path}")
    print(f"SVG:    {svg_path}")

    print("\n--- Token preview ---")
    from homr.jianpu.token_io import write_jianpu_tokens
    print(write_jianpu_tokens(symbols))


if __name__ == "__main__":
    main()
