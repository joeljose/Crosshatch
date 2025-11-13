"""
Crosshatch: Modern implementation of crosshatching effect for portraits.

This package provides tools to create artistic crosshatch effects on images
using AI-powered segmentation and traditional hatching techniques.
"""

__version__ = "2.0.0"

from .crosshatch import CrosshatchProcessor
from .segmentation import SAM2Segmentor

__all__ = ["CrosshatchProcessor", "SAM2Segmentor"]
