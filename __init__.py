"""SpritePacker - Lightweight sprite atlas packer with MaxRects algorithm."""

from .packer import SpritePacker
from .algorithms import MaxRectsAlgorithm, Rect, PackingAlgorithm

__all__ = ['SpritePacker', 'MaxRectsAlgorithm', 'Rect', 'PackingAlgorithm']
