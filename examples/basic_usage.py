"""Basic usage example for the crosshatch package."""

from pathlib import Path
from crosshatch import CrosshatchProcessor
from crosshatch.config import CrosshatchConfig, SAM2Config


def main():
    """Demonstrate basic usage of the crosshatch package."""

    # Example 1: Quick process with defaults
    print("=" * 60)
    print("Example 1: Quick process (automatic texture download)")
    print("=" * 60)

    processor = CrosshatchProcessor()

    # This will automatically download hatch textures if needed
    output = processor.quick_process(
        image_path="path/to/your/image.jpg",
        output_path="output_quick.jpg",
        hatch_style="horizontal"  # or "vortex"
    )

    print(f"Output shape: {output.shape}")
    print()

    # Example 2: Custom configuration
    print("=" * 60)
    print("Example 2: Custom configuration")
    print("=" * 60)

    # Configure SAM2 model
    sam_config = SAM2Config(
        model_type="small",  # Options: "tiny", "small", "base_plus", "large"
        device="cuda"  # or "cpu"
    )

    # Configure crosshatch processing
    crosshatch_config = CrosshatchConfig(
        max_dimension=1500,  # Larger output
        threshold_percentiles=(0.2, 0.5, 0.8)  # Custom thresholds
    )

    # Create processor with custom config
    processor = CrosshatchProcessor(
        config=crosshatch_config
    )

    # Load hatch textures manually
    processor.load_hatch_textures(
        left_path="textures/leftx.png",
        right_path="textures/rightx.png",
        horizontal_path="textures/horizontalx.png",
        vortex_path="textures/vortexx.png"
    )

    # Process with specific center point for segmentation
    output = processor.process_image(
        image_path="path/to/your/image.jpg",
        output_path="output_custom.jpg",
        hatch_style="vortex",
        center_point=(500, 400)  # Optional: point on person
    )

    print(f"Output shape: {output.shape}")
    print()

    # Example 3: Batch processing
    print("=" * 60)
    print("Example 3: Batch processing multiple images")
    print("=" * 60)

    processor = CrosshatchProcessor()

    image_paths = [
        "image1.jpg",
        "image2.jpg",
        "image3.jpg",
    ]

    for i, img_path in enumerate(image_paths, 1):
        print(f"Processing image {i}/{len(image_paths)}: {img_path}")
        try:
            processor.quick_process(
                image_path=img_path,
                output_path=f"output_{i}.jpg"
            )
            print(f"  ✓ Success")
        except Exception as e:
            print(f"  ✗ Error: {e}")

        # Reset segmentor state between images
        processor.segmentor.reset()

    print("\nAll done!")


if __name__ == "__main__":
    main()
