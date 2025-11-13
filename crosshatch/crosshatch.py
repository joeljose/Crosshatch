"""Core crosshatch processing module."""

from pathlib import Path
from typing import Literal, Optional

import cv2
import numpy as np
from PIL import Image

from .config import CrosshatchConfig
from .segmentation import SAM2Segmentor
from .utils import (
    blend_images,
    calculate_resize_dimensions,
    load_image,
    resize_image,
    save_image,
)


class CrosshatchProcessor:
    """Process images to create crosshatch artistic effects.

    This class handles the complete pipeline from segmentation to
    crosshatch effect generation.

    Attributes:
        config: Crosshatch configuration
        segmentor: SAM2 segmentor instance
        hatch_textures: Dictionary of loaded hatch texture images
    """

    def __init__(
        self,
        config: Optional[CrosshatchConfig] = None,
        segmentor: Optional[SAM2Segmentor] = None
    ):
        """Initialize the crosshatch processor.

        Args:
            config: Crosshatch configuration. If None, uses default.
            segmentor: SAM2 segmentor instance. If None, creates one.
        """
        self.config = config or CrosshatchConfig()
        self.segmentor = segmentor or SAM2Segmentor()
        self.hatch_textures: dict[str, np.ndarray] = {}

    def load_hatch_textures(
        self,
        left_path: str | Path,
        right_path: str | Path,
        horizontal_path: str | Path,
        vortex_path: str | Path
    ) -> None:
        """Load hatch texture images.

        Args:
            left_path: Path to left diagonal hatch texture
            right_path: Path to right diagonal hatch texture
            horizontal_path: Path to horizontal hatch texture
            vortex_path: Path to vortex hatch texture

        Raises:
            FileNotFoundError: If any texture file is not found
        """
        self.hatch_textures = {
            "left": load_image(left_path, grayscale=True),
            "right": load_image(right_path, grayscale=True),
            "horizontal": load_image(horizontal_path, grayscale=True),
            "vortex": load_image(vortex_path, grayscale=True),
        }
        print("Loaded all hatch textures")

    def _calculate_thresholds(
        self,
        image: np.ndarray,
        exclude_background: bool = True
    ) -> tuple[int, int, int]:
        """Calculate threshold values based on histogram.

        Args:
            image: Input grayscale image
            exclude_background: Whether to exclude white background (255)

        Returns:
            Tuple of three threshold values
        """
        # Calculate histogram
        counts, _ = np.histogram(image, bins=256, range=(0, 256))

        # Exclude background if requested
        max_val = 255 if exclude_background else 256
        total = np.sum(counts[:max_val])

        # Find thresholds at specified percentiles
        thresholds = []
        cum_sum = 0

        for percentile in self.config.threshold_percentiles:
            target = total * percentile

            for i in range(max_val):
                cum_sum += counts[i]
                if cum_sum > target:
                    thresholds.append(i)
                    break

        return tuple(thresholds)  # type: ignore

    def _crop_hatch_texture(
        self,
        texture: np.ndarray,
        target_width: int,
        target_height: int,
        center_crop: bool = False
    ) -> np.ndarray:
        """Crop hatch texture to target dimensions.

        Args:
            texture: Source hatch texture
            target_width: Target width
            target_height: Target height
            center_crop: Whether to crop from center (for vortex)

        Returns:
            Cropped texture

        Raises:
            ValueError: If texture is smaller than target dimensions
        """
        tex_height, tex_width = texture.shape[:2]

        if tex_height < target_height or tex_width < target_width:
            raise ValueError(
                f"Texture ({tex_width}x{tex_height}) is smaller than "
                f"target ({target_width}x{target_height})"
            )

        if center_crop:
            # Crop from center (for vortex effect)
            start_y = (tex_height - target_height) // 2
            start_x = (tex_width - target_width) // 2
            return texture[
                start_y:start_y + target_height,
                start_x:start_x + target_width
            ]
        else:
            # Crop from top-left
            return texture[:target_height, :target_width]

    def process_image(
        self,
        image_path: str | Path,
        output_path: str | Path,
        hatch_style: Literal["horizontal", "vortex"] = "horizontal",
        center_point: Optional[tuple[int, int]] = None
    ) -> np.ndarray:
        """Process an image to create crosshatch effect.

        Args:
            image_path: Path to input image
            output_path: Path to save output image
            hatch_style: Style of third hatch layer ("horizontal" or "vortex")
            center_point: Optional point on person for segmentation

        Returns:
            Processed image as numpy array

        Raises:
            ValueError: If hatch textures are not loaded
            FileNotFoundError: If input image is not found
        """
        if not self.hatch_textures:
            raise ValueError(
                "Hatch textures not loaded. Call load_hatch_textures() first."
            )

        print(f"Processing image: {image_path}")

        # Load image in color for segmentation
        image_color = load_image(image_path, grayscale=False)
        # Convert BGR to RGB for SAM2
        image_rgb = cv2.cvtColor(image_color, cv2.COLOR_BGR2RGB)

        # Load grayscale for processing
        image_gray = load_image(image_path, grayscale=True)
        original_height, original_width = image_gray.shape

        # Segment person using SAM2
        print("Segmenting person with SAM2...")
        segmentation_mask = self.segmentor.segment_person(image_rgb, center_point)

        # Calculate resize dimensions
        new_width, new_height = calculate_resize_dimensions(
            original_width,
            original_height,
            self.config.max_dimension
        )

        print(f"Resizing to {new_width}x{new_height}")

        # Resize image and mask
        image_resized = resize_image(image_gray, new_width, new_height)
        mask_resized = resize_image(segmentation_mask, new_width, new_height)

        # Create layered image (person on white background)
        background = np.ones_like(image_resized) * self.config.background_color
        layered_image = np.where(mask_resized == 255, image_resized, background)

        # Calculate thresholds
        print("Calculating thresholds...")
        thresh1, thresh2, thresh3 = self._calculate_thresholds(layered_image)
        print(f"Thresholds: {thresh1}, {thresh2}, {thresh3}")

        # Crop hatch textures to image size
        hatch_left = self._crop_hatch_texture(
            self.hatch_textures["left"], new_width, new_height
        )
        hatch_right = self._crop_hatch_texture(
            self.hatch_textures["right"], new_width, new_height
        )
        hatch_horizontal = self._crop_hatch_texture(
            self.hatch_textures["horizontal"], new_width, new_height
        )
        hatch_vortex = self._crop_hatch_texture(
            self.hatch_textures["vortex"], new_width, new_height, center_crop=True
        )

        # Select third hatch style
        hatch3_texture = hatch_vortex if hatch_style == "vortex" else hatch_horizontal

        # Create hatch layers based on thresholds
        print("Applying hatching...")
        hatch_layer1 = np.where(
            layered_image < thresh1,
            hatch_right,
            background
        )
        hatch_layer2 = np.where(
            layered_image < thresh2,
            hatch_left,
            background
        )
        hatch_layer3 = np.where(
            layered_image < thresh3,
            hatch3_texture,
            background
        )

        # Blend all hatch layers
        print("Blending layers...")
        output = blend_images([hatch_layer1, hatch_layer2, hatch_layer3])

        # Save output
        save_image(output, output_path)

        return output

    def quick_process(
        self,
        image_path: str | Path,
        output_path: str | Path,
        hatch_style: Literal["horizontal", "vortex"] = "horizontal"
    ) -> np.ndarray:
        """Quick process with automatic hatch texture download.

        This is a convenience method that downloads default hatch textures
        if they're not already present.

        Args:
            image_path: Path to input image
            output_path: Path to save output image
            hatch_style: Style of third hatch layer

        Returns:
            Processed image as numpy array
        """
        # Check if hatch textures are loaded
        if not self.hatch_textures:
            print("Downloading hatch textures...")
            from .utils import download_file

            # Create textures directory
            textures_dir = Path("textures")
            textures_dir.mkdir(exist_ok=True)

            # Download default textures
            base_url = "https://github.com/joeljose/assets/raw/master/crosshatch"
            textures = {
                "horizontal": "horizontalx.png",
                "left": "leftx.png",
                "right": "rightx.png",
                "vortex": "vortexx.png",
            }

            for name, filename in textures.items():
                dest = textures_dir / filename
                if not dest.exists():
                    download_file(f"{base_url}/{filename}", dest)

            # Load textures
            self.load_hatch_textures(
                left_path=textures_dir / "leftx.png",
                right_path=textures_dir / "rightx.png",
                horizontal_path=textures_dir / "horizontalx.png",
                vortex_path=textures_dir / "vortexx.png",
            )

        return self.process_image(image_path, output_path, hatch_style)
