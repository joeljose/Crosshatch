"""Configuration constants for the crosshatch package."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class CrosshatchConfig:
    """Configuration for crosshatch processing.

    Attributes:
        max_dimension: Maximum dimension (width or height) for resizing images
        hatch_dimension: Dimension of the hatch texture images
        threshold_percentiles: Percentiles for threshold calculation (0.0 to 1.0)
        background_color: Background color value (0-255)
    """
    max_dimension: int = 1200
    hatch_dimension: int = 2100
    threshold_percentiles: tuple[float, float, float] = (0.25, 0.5, 0.75)
    background_color: int = 255


@dataclass
class SAM2Config:
    """Configuration for SAM2 segmentation.

    Attributes:
        model_type: Size of the SAM2 model to use
        checkpoint_path: Path to the model checkpoint file
        config_path: Path to the model configuration file
        device: Device to run inference on ('cuda' or 'cpu')
    """
    model_type: Literal["tiny", "small", "base_plus", "large"] = "small"
    checkpoint_path: str | None = None
    config_path: str | None = None
    device: str = "cuda"

    def get_default_paths(self) -> tuple[str, str]:
        """Get default checkpoint and config paths for the model type.

        Returns:
            Tuple of (checkpoint_path, config_path)
        """
        model_map = {
            "tiny": ("sam2.1_hiera_tiny.pt", "configs/sam2.1/sam2.1_hiera_t.yaml"),
            "small": ("sam2.1_hiera_small.pt", "configs/sam2.1/sam2.1_hiera_s.yaml"),
            "base_plus": ("sam2.1_hiera_base_plus.pt", "configs/sam2.1/sam2.1_hiera_b+.yaml"),
            "large": ("sam2.1_hiera_large.pt", "configs/sam2.1/sam2.1_hiera_l.yaml"),
        }

        ckpt_name, config_name = model_map[self.model_type]
        return f"checkpoints/{ckpt_name}", config_name
