"""Advanced usage examples for the crosshatch package."""

import numpy as np
from pathlib import Path
from crosshatch import CrosshatchProcessor, SAM2Segmentor
from crosshatch.config import CrosshatchConfig, SAM2Config
from crosshatch.utils import load_image, save_image
import cv2


def example_custom_segmentation():
    """Example: Use custom segmentation with bounding box."""
    print("=" * 60)
    print("Example: Custom segmentation with bounding box")
    print("=" * 60)

    # Create segmentor
    segmentor = SAM2Segmentor(
        config=SAM2Config(model_type="small", device="cuda")
    )

    # Load image
    image = load_image("path/to/image.jpg")
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Define bounding box around person (x1, y1, x2, y2)
    box = (100, 50, 400, 600)

    # Segment with box
    mask = segmentor.segment_with_box(image_rgb, box)

    # Save mask
    save_image(mask, "segmentation_mask.png")

    print("✓ Segmentation complete")
    print()


def example_compare_models():
    """Example: Compare different SAM2 model sizes."""
    print("=" * 60)
    print("Example: Compare SAM2 model sizes")
    print("=" * 60)

    import time

    models = ["tiny", "small", "base_plus", "large"]
    image_path = "path/to/image.jpg"

    for model_type in models:
        print(f"\nTesting {model_type} model...")

        config = SAM2Config(model_type=model_type, device="cuda")
        segmentor = SAM2Segmentor(config=config)

        image = load_image(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Time the segmentation
        start = time.time()
        mask = segmentor.segment_person(image_rgb)
        elapsed = time.time() - start

        print(f"  Time: {elapsed:.3f}s")
        print(f"  Mask shape: {mask.shape}")
        print(f"  Person pixels: {np.sum(mask == 255)}")

    print("\n✓ Model comparison complete")
    print()


def example_custom_hatch_textures():
    """Example: Create and use custom hatch textures."""
    print("=" * 60)
    print("Example: Create custom hatch textures")
    print("=" * 60)

    # Create custom hatch patterns programmatically
    def create_diagonal_hatch(size: int, spacing: int, angle: int) -> np.ndarray:
        """Create a diagonal hatch pattern."""
        hatch = np.ones((size, size), dtype=np.uint8) * 255

        # Draw diagonal lines
        for i in range(-size, size * 2, spacing):
            cv2.line(
                hatch,
                (i, 0),
                (i + size, size),
                0,
                thickness=2
            )

        # Rotate if needed
        if angle != 0:
            center = (size // 2, size // 2)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            hatch = cv2.warpAffine(hatch, matrix, (size, size))

        return hatch

    # Create custom textures
    size = 2100
    left_hatch = create_diagonal_hatch(size, 20, -45)
    right_hatch = create_diagonal_hatch(size, 20, 45)
    horizontal_hatch = create_diagonal_hatch(size, 20, 0)

    # Save custom textures
    Path("custom_textures").mkdir(exist_ok=True)
    save_image(left_hatch, "custom_textures/left.png")
    save_image(right_hatch, "custom_textures/right.png")
    save_image(horizontal_hatch, "custom_textures/horizontal.png")

    print("✓ Custom textures created")

    # Use custom textures
    processor = CrosshatchProcessor()
    processor.load_hatch_textures(
        left_path="custom_textures/left.png",
        right_path="custom_textures/right.png",
        horizontal_path="custom_textures/horizontal.png",
        vortex_path="textures/vortexx.png"  # Use default for vortex
    )

    print("✓ Custom textures loaded")
    print()


def example_adjust_parameters():
    """Example: Fine-tune crosshatch parameters."""
    print("=" * 60)
    print("Example: Fine-tune parameters")
    print("=" * 60)

    # Try different threshold percentiles
    percentile_sets = [
        (0.25, 0.50, 0.75),  # Default - balanced
        (0.20, 0.40, 0.60),  # More hatching (darker)
        (0.30, 0.60, 0.90),  # Less hatching (lighter)
    ]

    for i, percentiles in enumerate(percentile_sets, 1):
        print(f"\nTesting percentiles {percentiles}...")

        config = CrosshatchConfig(
            threshold_percentiles=percentiles,
            max_dimension=1200
        )

        processor = CrosshatchProcessor(config=config)

        processor.quick_process(
            image_path="path/to/image.jpg",
            output_path=f"output_params_{i}.jpg"
        )

        print(f"  ✓ Saved as output_params_{i}.jpg")

    print("\n✓ Parameter tuning complete")
    print()


if __name__ == "__main__":
    # Uncomment the examples you want to run
    # example_custom_segmentation()
    # example_compare_models()
    # example_custom_hatch_textures()
    # example_adjust_parameters()

    print("Examples ready to run!")
    print("Uncomment the examples you want to try.")
