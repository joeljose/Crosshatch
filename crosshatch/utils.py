"""Utility functions for image processing and file operations."""

import os
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import requests
from PIL import Image


def download_file(url: str, dest_path: str | Path) -> None:
    """Download a file from a URL to a destination path.

    Args:
        url: URL to download from
        dest_path: Destination file path

    Raises:
        RuntimeError: If the download fails
    """
    dest_path = Path(dest_path)

    if dest_path.exists():
        print(f"File already exists: {dest_path}")
        return

    print(f"Downloading: {url} to {dest_path}")

    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Downloaded successfully: {dest_path}")
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download {url}: {e}") from e


def load_image(path: str | Path, grayscale: bool = False) -> np.ndarray:
    """Load an image from a file path.

    Args:
        path: Path to the image file
        grayscale: Whether to load as grayscale

    Returns:
        Image as numpy array

    Raises:
        FileNotFoundError: If the image file doesn't exist
        ValueError: If the image cannot be loaded
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    flags = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
    image = cv2.imread(str(path), flags)

    if image is None:
        raise ValueError(f"Failed to load image: {path}")

    return image


def save_image(image: np.ndarray, path: str | Path) -> None:
    """Save an image to a file path.

    Args:
        image: Image as numpy array
        path: Destination file path

    Raises:
        ValueError: If the image cannot be saved
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    success = cv2.imwrite(str(path), image)

    if not success:
        raise ValueError(f"Failed to save image: {path}")

    print(f"Saved image: {path}")


def resize_image(
    image: np.ndarray,
    width: int,
    height: int,
    interpolation: int = cv2.INTER_LANCZOS4
) -> np.ndarray:
    """Resize an image to specified dimensions.

    Args:
        image: Input image
        width: Target width
        height: Target height
        interpolation: Interpolation method

    Returns:
        Resized image
    """
    return cv2.resize(image, (width, height), interpolation=interpolation)


def calculate_resize_dimensions(
    original_width: int,
    original_height: int,
    max_dimension: int
) -> tuple[int, int]:
    """Calculate new dimensions while maintaining aspect ratio.

    Args:
        original_width: Original image width
        original_height: Original image height
        max_dimension: Maximum allowed dimension

    Returns:
        Tuple of (new_width, new_height)
    """
    max_current = max(original_width, original_height)
    ratio = max_dimension / max_current

    new_width = int(ratio * original_width)
    new_height = int(ratio * original_height)

    return new_width, new_height


def blend_images(images: list[np.ndarray]) -> np.ndarray:
    """Blend multiple images with equal weight.

    Args:
        images: List of images to blend (must be same shape)

    Returns:
        Blended image

    Raises:
        ValueError: If images list is empty or images have different shapes
    """
    if not images:
        raise ValueError("Images list cannot be empty")

    # Check all images have the same shape
    first_shape = images[0].shape
    if not all(img.shape == first_shape for img in images):
        raise ValueError("All images must have the same shape")

    equal_fraction = 1.0 / len(images)
    output = np.zeros_like(images[0], dtype=np.float32)

    for img in images:
        output += img.astype(np.float32) * equal_fraction

    return output.astype(np.uint8)


def create_binary_mask(
    segmentation_map: np.ndarray,
    target_label: int,
    foreground_value: int = 255,
    background_value: int = 0
) -> np.ndarray:
    """Create a binary mask from a segmentation map.

    Args:
        segmentation_map: Segmentation map with label values
        target_label: Label value to extract
        foreground_value: Value for target label pixels
        background_value: Value for other pixels

    Returns:
        Binary mask
    """
    mask = np.zeros(segmentation_map.shape, dtype=np.uint8)
    mask[segmentation_map == target_label] = foreground_value
    mask[segmentation_map != target_label] = background_value

    return mask
