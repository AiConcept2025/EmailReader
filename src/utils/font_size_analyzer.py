"""
Font size analysis and calibration utilities for OCR text bounding boxes.

This module provides tools to analyze bounding box heights from OCR data
and calibrate font size inference to match real-world document fonts.
"""

import statistics
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger('EmailReader.FontSizeAnalyzer')


class FontSizeClassifier:
    """
    Classify text into categories (body, heading, title, small) based on font size.

    Uses statistical analysis of bounding box heights to determine appropriate
    font sizes that match real-world document conventions.
    """

    # Real-world font size ranges (in points)
    SMALL_TEXT_RANGE = (8.0, 10.0)      # Footnotes, captions
    BODY_TEXT_RANGE = (10.0, 13.0)      # Normal paragraph text
    HEADING_RANGE = (14.0, 18.0)        # Section headings
    SUBHEADING_RANGE = (18.0, 24.0)     # Subsection headings
    TITLE_RANGE = (24.0, 36.0)          # Document titles
    LARGE_TITLE_RANGE = (36.0, 48.0)    # Large titles/headers

    def __init__(self, calibration_factor: float = 400.0):
        """
        Initialize font size classifier.

        Args:
            calibration_factor: Multiplier to convert normalized height (0-1) to points.
                              Default 400 is calibrated from real document analysis.

        Calibration rationale:
        - Normalized height of 0.025 (2.5% of page) should be ~10pt body text
        - 0.025 * 400 = 10pt ✓
        - Normalized height of 0.05 (5% of page) should be ~20pt heading
        - 0.05 * 400 = 20pt ✓
        - Normalized height of 0.10 (10% of page) should be ~40pt title
        - 0.10 * 400 = 40pt ✓
        """
        self.calibration_factor = calibration_factor

    def classify_and_infer_size(
        self,
        height: float,
        base_size: float = 11.0,
        max_size: float = 48.0,
        min_size: float = 8.0
    ) -> Tuple[float, str]:
        """
        Infer font size and classify text type from bounding box height.

        Args:
            height: Normalized bounding box height (0.0 to 1.0)
            base_size: Default body text size in points
            max_size: Maximum allowed font size
            min_size: Minimum allowed font size

        Returns:
            Tuple of (font_size_in_points, classification)
            where classification is one of: 'small', 'body', 'heading',
            'subheading', 'title', 'large_title'
        """
        # Calculate raw size using calibrated factor
        raw_size = height * self.calibration_factor

        # Clamp to reasonable range
        font_size = max(min_size, min(raw_size, max_size))

        # Round to nearest 0.5pt for cleaner output
        font_size = round(font_size * 2) / 2

        # Classify based on size
        if font_size < self.SMALL_TEXT_RANGE[1]:
            classification = 'small'
        elif font_size < self.BODY_TEXT_RANGE[1]:
            classification = 'body'
        elif font_size < self.HEADING_RANGE[1]:
            classification = 'heading'
        elif font_size < self.SUBHEADING_RANGE[1]:
            classification = 'subheading'
        elif font_size < self.TITLE_RANGE[1]:
            classification = 'title'
        else:
            classification = 'large_title'

        return font_size, classification


def analyze_bounding_box_heights(chunks: List[Dict]) -> Dict[str, float]:
    """
    Analyze bounding box heights from OCR chunks to understand distribution.

    This function helps calibrate font size inference by providing statistical
    insights into the actual heights found in OCR data.

    Args:
        chunks: List of OCR chunks with grounding.box.height data

    Returns:
        Dictionary with statistical metrics:
        - min: Minimum height
        - max: Maximum height
        - mean: Average height
        - median: Median height
        - p25: 25th percentile (likely small text)
        - p75: 75th percentile (likely headings)
        - p90: 90th percentile (likely titles)
    """
    heights = []

    for chunk in chunks:
        grounding = chunk.get('grounding', {})
        box = grounding.get('box', {})

        if box:
            top = box.get('top', 0.0)
            bottom = box.get('bottom', 0.0)
            height = bottom - top

            if height > 0:
                heights.append(height)

    if not heights:
        logger.warning("No valid bounding box heights found in chunks")
        return {}

    heights.sort()

    stats = {
        'count': len(heights),
        'min': min(heights),
        'max': max(heights),
        'mean': statistics.mean(heights),
        'median': statistics.median(heights),
        'p25': heights[len(heights) // 4],
        'p75': heights[3 * len(heights) // 4],
        'p90': heights[9 * len(heights) // 10] if len(heights) >= 10 else max(heights)
    }

    logger.info(f"Bounding box height analysis (n={stats['count']}): "
                f"median={stats['median']:.4f}, "
                f"range=[{stats['min']:.4f}, {stats['max']:.4f}]")

    return stats


def suggest_calibration_factor(
    chunks: List[Dict],
    expected_body_text_pt: float = 11.0
) -> float:
    """
    Suggest a calibration factor based on actual document data.

    Assumes the median or p25 text is body text and calculates the
    factor needed to produce the expected font size.

    Args:
        chunks: List of OCR chunks
        expected_body_text_pt: Expected font size for body text in points

    Returns:
        Suggested calibration factor
    """
    stats = analyze_bounding_box_heights(chunks)

    if not stats:
        logger.warning("Cannot suggest calibration factor - no height data")
        return 400.0  # Default

    # Use 25th percentile as representative of body text
    # (median may include headings)
    body_text_height = stats.get('p25', stats.get('median', 0.03))

    if body_text_height == 0:
        logger.warning("Invalid body text height - using default calibration")
        return 400.0

    suggested_factor = expected_body_text_pt / body_text_height

    logger.info(
        f"Suggested calibration factor: {suggested_factor:.1f} "
        f"(body text height {body_text_height:.4f} → {expected_body_text_pt}pt)"
    )

    return suggested_factor
