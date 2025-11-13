"""Command-line interface for crosshatch package."""

import argparse
from pathlib import Path

from .crosshatch import CrosshatchProcessor
from .config import CrosshatchConfig, SAM2Config


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Create crosshatch artistic effects on images"
    )
    parser.add_argument(
        "input",
        type=str,
        help="Input image path"
    )
    parser.add_argument(
        "output",
        type=str,
        help="Output image path"
    )
    parser.add_argument(
        "--style",
        type=str,
        choices=["horizontal", "vortex"],
        default="horizontal",
        help="Hatch style for third layer (default: horizontal)"
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=["tiny", "small", "base_plus", "large"],
        default="small",
        help="SAM2 model size (default: small)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        help="Device to run on (default: cuda)"
    )
    parser.add_argument(
        "--max-dimension",
        type=int,
        default=1200,
        help="Maximum dimension for output (default: 1200)"
    )

    args = parser.parse_args()

    # Create configurations
    sam_config = SAM2Config(model_type=args.model, device=args.device)
    crosshatch_config = CrosshatchConfig(max_dimension=args.max_dimension)

    # Create processor
    print("Initializing crosshatch processor...")
    processor = CrosshatchProcessor(config=crosshatch_config)

    # Process image
    try:
        processor.quick_process(
            image_path=args.input,
            output_path=args.output,
            hatch_style=args.style
        )
        print(f"✓ Successfully created crosshatch image: {args.output}")
    except Exception as e:
        print(f"✗ Error processing image: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
