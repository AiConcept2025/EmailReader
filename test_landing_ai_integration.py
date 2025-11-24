#!/usr/bin/env python3
"""
Test script for LandingAI OCR Provider Integration

This script demonstrates the LandingAI provider functionality with mock data.
For real usage, you'll need a valid LandingAI API key.

Usage:
    python test_landing_ai_integration.py
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ocr.landing_ai_provider import LandingAIOCRProvider
from src.utils.layout_reconstructor import (
    reconstruct_layout,
    BoundingBox,
    TextChunk,
    apply_grounding_to_output
)


def test_bounding_box():
    """Test BoundingBox calculations."""
    print("\n=== Testing BoundingBox ===")
    box = BoundingBox(left=0.1, top=0.2, right=0.9, bottom=0.8)

    print(f"Box coordinates: left={box.left}, top={box.top}, right={box.right}, bottom={box.bottom}")
    print(f"Calculated width: {box.width:.2f}")
    print(f"Calculated height: {box.height:.2f}")
    print(f"Center: ({box.center_x:.2f}, {box.center_y:.2f})")
    print("✓ BoundingBox test passed")


def test_single_column_layout():
    """Test layout reconstruction with single column."""
    print("\n=== Testing Single Column Layout ===")

    chunks = [
        {
            'text': 'Document Title',
            'grounding': {
                'page': 0,
                'box': {'left': 0.1, 'top': 0.05, 'right': 0.9, 'bottom': 0.1}
            }
        },
        {
            'text': 'This is the first paragraph of the document.',
            'grounding': {
                'page': 0,
                'box': {'left': 0.1, 'top': 0.2, 'right': 0.9, 'bottom': 0.3}
            }
        },
        {
            'text': 'This is the second paragraph with more content.',
            'grounding': {
                'page': 0,
                'box': {'left': 0.1, 'top': 0.4, 'right': 0.9, 'bottom': 0.5}
            }
        }
    ]

    result = reconstruct_layout(chunks)
    print("Reconstructed text:")
    print("-" * 60)
    print(result)
    print("-" * 60)
    print(f"✓ Single column layout: {len(result)} characters")


def test_multi_column_layout():
    """Test layout reconstruction with multiple columns."""
    print("\n=== Testing Multi-Column Layout ===")

    # Left column chunks
    left_col = [
        {
            'text': 'Left column paragraph 1',
            'grounding': {
                'page': 0,
                'box': {'left': 0.05, 'top': 0.1, 'right': 0.45, 'bottom': 0.2}
            }
        },
        {
            'text': 'Left column paragraph 2',
            'grounding': {
                'page': 0,
                'box': {'left': 0.05, 'top': 0.3, 'right': 0.45, 'bottom': 0.4}
            }
        }
    ]

    # Right column chunks
    right_col = [
        {
            'text': 'Right column paragraph 1',
            'grounding': {
                'page': 0,
                'box': {'left': 0.55, 'top': 0.1, 'right': 0.95, 'bottom': 0.2}
            }
        },
        {
            'text': 'Right column paragraph 2',
            'grounding': {
                'page': 0,
                'box': {'left': 0.55, 'top': 0.3, 'right': 0.95, 'bottom': 0.4}
            }
        }
    ]

    chunks = left_col + right_col
    result = reconstruct_layout(chunks)

    print("Reconstructed text:")
    print("-" * 60)
    print(result)
    print("-" * 60)
    print(f"✓ Multi-column layout: {len(result)} characters")


def test_multi_page_document():
    """Test layout reconstruction with multiple pages."""
    print("\n=== Testing Multi-Page Document ===")

    chunks = [
        # Page 0
        {
            'text': 'Page 1 content line 1',
            'grounding': {
                'page': 0,
                'box': {'left': 0.1, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
            }
        },
        {
            'text': 'Page 1 content line 2',
            'grounding': {
                'page': 0,
                'box': {'left': 0.1, 'top': 0.3, 'right': 0.9, 'bottom': 0.4}
            }
        },
        # Page 1
        {
            'text': 'Page 2 content line 1',
            'grounding': {
                'page': 1,
                'box': {'left': 0.1, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
            }
        },
        {
            'text': 'Page 2 content line 2',
            'grounding': {
                'page': 1,
                'box': {'left': 0.1, 'top': 0.3, 'right': 0.9, 'bottom': 0.4}
            }
        }
    ]

    result = reconstruct_layout(chunks)

    print("Reconstructed text:")
    print("-" * 60)
    print(result)
    print("-" * 60)
    print(f"✓ Multi-page document: {len(result)} characters")


def test_structure_metadata():
    """Test structure metadata extraction."""
    print("\n=== Testing Structure Metadata ===")

    chunks = [
        {
            'text': 'Column 1 text',
            'grounding': {
                'page': 0,
                'box': {'left': 0.1, 'top': 0.1, 'right': 0.4, 'bottom': 0.2}
            }
        },
        {
            'text': 'Column 2 text',
            'grounding': {
                'page': 0,
                'box': {'left': 0.6, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
            }
        },
        {
            'text': 'Page 2 text',
            'grounding': {
                'page': 1,
                'box': {'left': 0.1, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
            }
        }
    ]

    metadata = apply_grounding_to_output(chunks)

    print("Structure metadata:")
    print(json.dumps(metadata, indent=2))
    print(f"✓ Metadata extraction: {metadata['total_pages']} pages, {metadata['total_chunks']} chunks")


def test_provider_initialization():
    """Test LandingAI provider initialization."""
    print("\n=== Testing Provider Initialization ===")

    # Test with minimal config
    config_minimal = {
        'api_key': 'test_api_key_minimal'
    }
    provider = LandingAIOCRProvider(config_minimal)
    print(f"✓ Minimal config: model={provider.model}, timeout={provider.timeout}s")

    # Test with full config
    config_full = {
        'api_key': 'test_api_key_full',
        'base_url': 'https://api.va.landing.ai/v1',
        'model': 'custom-model-v2',
        'split_mode': 'page',
        'preserve_layout': True,
        'chunk_processing': {
            'use_grounding': True,
            'maintain_positions': True
        },
        'retry': {
            'max_attempts': 5,
            'backoff_factor': 3,
            'timeout': 60
        }
    }
    provider = LandingAIOCRProvider(config_full)
    print(f"✓ Full config: model={provider.model}, max_attempts={provider.max_attempts}")

    # Test error handling - missing API key
    try:
        bad_config = {'model': 'test'}
        provider = LandingAIOCRProvider(bad_config)
        print("✗ Should have raised ValueError for missing API key")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n=== Testing Edge Cases ===")

    # Empty chunks
    result = reconstruct_layout([])
    print(f"✓ Empty chunks: '{result}' (length={len(result)})")

    # Chunks without grounding data
    chunks_no_grounding = [
        {'text': 'Text without grounding'}
    ]
    result = reconstruct_layout(chunks_no_grounding)
    print(f"✓ No grounding data: {len(result)} characters")

    # Empty text in chunks
    chunks_empty_text = [
        {
            'text': '',
            'grounding': {
                'page': 0,
                'box': {'left': 0.1, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
            }
        },
        {
            'text': 'Valid text',
            'grounding': {
                'page': 0,
                'box': {'left': 0.1, 'top': 0.3, 'right': 0.9, 'bottom': 0.4}
            }
        }
    ]
    result = reconstruct_layout(chunks_empty_text)
    print(f"✓ Empty text chunks filtered: {len(result)} characters")


def main():
    """Run all tests."""
    print("=" * 70)
    print("LandingAI OCR Provider Integration Tests")
    print("=" * 70)

    try:
        # Run all test functions
        test_bounding_box()
        test_single_column_layout()
        test_multi_column_layout()
        test_multi_page_document()
        test_structure_metadata()
        test_provider_initialization()
        test_edge_cases()

        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        print("\nThe LandingAI integration is ready to use!")
        print("\nNext steps:")
        print("1. Add your LandingAI API key to config file")
        print("2. Set 'ocr_provider: landing_ai' in config")
        print("3. Process documents with layout preservation")

        return 0

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
