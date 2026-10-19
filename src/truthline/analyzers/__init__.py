"""Analyzer registry. Add a new analyzer by importing it and appending to REGISTRY."""

from .c2pa import C2PAAnalyzer
from .metadata import MetadataAnalyzer
from .screenshot import ScreenshotAnalyzer

REGISTRY = [
    C2PAAnalyzer(),
    MetadataAnalyzer(),
    ScreenshotAnalyzer(),
]

__all__ = ["REGISTRY", "C2PAAnalyzer", "MetadataAnalyzer", "ScreenshotAnalyzer"]
