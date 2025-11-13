"""Segmentation module using SAM2 (Segment Anything Model 2)."""

from typing import Optional

import numpy as np
import torch
from PIL import Image

from .config import SAM2Config


class SAM2Segmentor:
    """Wrapper for SAM2 model to perform person segmentation.

    This class provides a simplified interface to SAM2 for extracting
    persons from images.

    Attributes:
        config: SAM2 configuration
        predictor: SAM2 image predictor instance
    """

    def __init__(self, config: Optional[SAM2Config] = None):
        """Initialize the SAM2 segmentor.

        Args:
            config: SAM2 configuration. If None, uses default config.

        Raises:
            ImportError: If SAM2 is not installed
            RuntimeError: If model files are not found
        """
        self.config = config or SAM2Config()
        self.predictor = None
        self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize the SAM2 model.

        Raises:
            ImportError: If SAM2 is not installed
            RuntimeError: If model files are not found
        """
        try:
            from sam2.build_sam import build_sam2
            from sam2.sam2_image_predictor import SAM2ImagePredictor
        except ImportError as e:
            raise ImportError(
                "SAM2 is not installed. Please install it using:\n"
                "git clone https://github.com/facebookresearch/sam2.git && "
                "cd sam2 && pip install -e ."
            ) from e

        # Get checkpoint and config paths
        if self.config.checkpoint_path is None or self.config.config_path is None:
            checkpoint_path, config_path = self.config.get_default_paths()
        else:
            checkpoint_path = self.config.checkpoint_path
            config_path = self.config.config_path

        # Build and initialize the model
        try:
            model = build_sam2(config_path, checkpoint_path, device=self.config.device)
            self.predictor = SAM2ImagePredictor(model)
            print(f"SAM2 model loaded: {self.config.model_type}")
        except Exception as e:
            raise RuntimeError(
                f"Failed to load SAM2 model. Make sure checkpoint files are downloaded.\n"
                f"Run: cd sam2 && ./checkpoints/download_ckpts.sh\n"
                f"Error: {e}"
            ) from e

    def segment_person(
        self,
        image: np.ndarray,
        center_point: Optional[tuple[int, int]] = None
    ) -> np.ndarray:
        """Segment person from an image using SAM2.

        Args:
            image: Input image as numpy array (H, W, 3) in RGB format
            center_point: Optional point (x, y) on the person. If None,
                         uses image center.

        Returns:
            Binary segmentation mask (H, W) with 255 for person, 0 for background

        Raises:
            ValueError: If image is invalid
        """
        if image is None or image.size == 0:
            raise ValueError("Invalid input image")

        # Convert to RGB if grayscale
        if len(image.shape) == 2:
            image = np.stack([image] * 3, axis=-1)

        # Ensure RGB format (SAM2 expects RGB)
        if image.shape[2] == 3 and np.max(image) <= 1.0:
            image = (image * 255).astype(np.uint8)

        # Get image dimensions
        height, width = image.shape[:2]

        # Use center point if not provided
        if center_point is None:
            center_point = (width // 2, height // 2)

        # Set image for prediction
        with torch.inference_mode(), torch.autocast(
            self.config.device, dtype=torch.bfloat16
        ):
            self.predictor.set_image(image)

            # Predict with center point prompt
            masks, scores, _ = self.predictor.predict(
                point_coords=np.array([[center_point[0], center_point[1]]]),
                point_labels=np.array([1]),  # 1 = foreground point
                multimask_output=True  # Get multiple mask options
            )

        # Select the best mask (highest score)
        best_mask_idx = np.argmax(scores)
        mask = masks[best_mask_idx]

        # Convert to binary mask with 255/0 values
        binary_mask = (mask * 255).astype(np.uint8)

        return binary_mask

    def segment_with_box(
        self,
        image: np.ndarray,
        box: tuple[int, int, int, int]
    ) -> np.ndarray:
        """Segment using a bounding box prompt.

        Args:
            image: Input image as numpy array (H, W, 3) in RGB format
            box: Bounding box as (x1, y1, x2, y2)

        Returns:
            Binary segmentation mask (H, W) with 255 for person, 0 for background

        Raises:
            ValueError: If image or box is invalid
        """
        if image is None or image.size == 0:
            raise ValueError("Invalid input image")

        # Convert to RGB if grayscale
        if len(image.shape) == 2:
            image = np.stack([image] * 3, axis=-1)

        # Set image for prediction
        with torch.inference_mode(), torch.autocast(
            self.config.device, dtype=torch.bfloat16
        ):
            self.predictor.set_image(image)

            # Predict with bounding box prompt
            masks, scores, _ = self.predictor.predict(
                box=np.array(box),
                multimask_output=True
            )

        # Select the best mask
        best_mask_idx = np.argmax(scores)
        mask = masks[best_mask_idx]

        # Convert to binary mask
        binary_mask = (mask * 255).astype(np.uint8)

        return binary_mask

    def reset(self) -> None:
        """Reset the predictor state."""
        if self.predictor is not None:
            self.predictor.reset_predictor()
