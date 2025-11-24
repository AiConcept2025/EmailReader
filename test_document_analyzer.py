"""
Unit tests for the document_analyzer module.

Run with:
    PYTHONPATH=/Users/vladimirdanishevsky/projects/EmailReader python test_document_analyzer.py

Or with pytest:
    PYTHONPATH=/Users/vladimirdanishevsky/projects/EmailReader pytest test_document_analyzer.py -v
"""

import os
import tempfile
from pathlib import Path

from src.document_analyzer import (
    requires_ocr,
    get_document_type,
    get_pdf_type,
    is_image_based_pdf,
    get_supported_extensions,
    is_supported_format,
)


def test_pdf_searchable():
    """Test detection of searchable PDF (text-based)."""
    pdf_path = 'test_docs/file-sample-pdf.pdf'
    assert os.path.exists(pdf_path), f"Test file not found: {pdf_path}"

    # Should be detected as searchable
    doc_type = get_document_type(pdf_path)
    assert doc_type == 'pdf_searchable', f"Expected 'pdf_searchable', got '{doc_type}'"

    # Should NOT require OCR
    needs_ocr = requires_ocr(pdf_path)
    assert needs_ocr is False, "Searchable PDF should not require OCR"

    # is_image_based_pdf should return False
    assert is_image_based_pdf(pdf_path) is False

    print(f"PASS: {pdf_path} - Searchable PDF detected correctly")


def test_pdf_scanned():
    """Test detection of scanned PDF (image-based)."""
    pdf_paths = [
        'test_docs/PDF-scanned-rus-words.pdf',
        'test_docs/file-sample-img.pdf',
    ]

    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            print(f"SKIP: {pdf_path} - File not found")
            continue

        # Should be detected as scanned
        doc_type = get_document_type(pdf_path)
        assert doc_type == 'pdf_scanned', f"Expected 'pdf_scanned', got '{doc_type}'"

        # Should require OCR
        needs_ocr = requires_ocr(pdf_path)
        assert needs_ocr is True, "Scanned PDF should require OCR"

        # is_image_based_pdf should return True
        assert is_image_based_pdf(pdf_path) is True

        print(f"PASS: {pdf_path} - Scanned PDF detected correctly")


def test_word_document():
    """Test detection of Word documents."""
    doc_path = 'test_docs/file-sample-doc.doc'
    assert os.path.exists(doc_path), f"Test file not found: {doc_path}"

    # Should be detected as Word document
    doc_type = get_document_type(doc_path)
    assert doc_type == 'word_document', f"Expected 'word_document', got '{doc_type}'"

    # Should NOT require OCR
    needs_ocr = requires_ocr(doc_path)
    assert needs_ocr is False, "Word documents should not require OCR"

    print(f"PASS: {doc_path} - Word document detected correctly")


def test_text_documents():
    """Test detection of text documents (.txt, .rtf)."""
    text_files = [
        'test_docs/file-sample-txt.txt',
        'test_docs/file-sample-rtf.rtf',
    ]

    for text_path in text_files:
        if not os.path.exists(text_path):
            print(f"SKIP: {text_path} - File not found")
            continue

        # Should be detected as text document
        doc_type = get_document_type(text_path)
        assert doc_type == 'text_document', f"Expected 'text_document', got '{doc_type}'"

        # Should NOT require OCR
        needs_ocr = requires_ocr(text_path)
        assert needs_ocr is False, "Text documents should not require OCR"

        print(f"PASS: {text_path} - Text document detected correctly")


def test_image_files():
    """Test detection of image files (hypothetical - we don't have image test files)."""
    # Create temporary image file for testing
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(b'fake image data')

    try:
        # Should be detected as image
        doc_type = get_document_type(tmp_path)
        assert doc_type == 'image', f"Expected 'image', got '{doc_type}'"

        # Should require OCR
        needs_ocr = requires_ocr(tmp_path)
        assert needs_ocr is True, "Image files should require OCR"

        print(f"PASS: Temporary .jpg - Image file detected correctly")
    finally:
        os.unlink(tmp_path)


def test_unknown_format():
    """Test detection of unknown/unsupported file formats."""
    # Create temporary file with unsupported extension
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(b'fake video data')

    try:
        # Should be detected as unknown
        doc_type = get_document_type(tmp_path)
        assert doc_type == 'unknown', f"Expected 'unknown', got '{doc_type}'"

        # Should NOT require OCR (unknown formats should not be processed)
        needs_ocr = requires_ocr(tmp_path)
        assert needs_ocr is False, "Unknown formats should not require OCR"

        print(f"PASS: Temporary .mp4 - Unknown format detected correctly")
    finally:
        os.unlink(tmp_path)


def test_file_not_found():
    """Test behavior with non-existent files."""
    non_existent = '/tmp/this_file_does_not_exist.pdf'

    # get_document_type should return 'unknown' for missing files
    doc_type = get_document_type(non_existent)
    assert doc_type == 'unknown', f"Expected 'unknown' for missing file, got '{doc_type}'"

    # requires_ocr should raise FileNotFoundError
    try:
        requires_ocr(non_existent)
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        print(f"PASS: FileNotFoundError raised correctly for missing file")


def test_supported_extensions():
    """Test get_supported_extensions function."""
    extensions = get_supported_extensions()

    assert 'pdf' in extensions
    assert 'images' in extensions
    assert 'word' in extensions
    assert 'text' in extensions

    assert '.pdf' in extensions['pdf']
    assert '.jpg' in extensions['images']
    assert '.jpeg' in extensions['images']
    assert '.png' in extensions['images']
    assert '.docx' in extensions['word']
    assert '.doc' in extensions['word']
    assert '.txt' in extensions['text']
    assert '.rtf' in extensions['text']

    print("PASS: get_supported_extensions returned correct structure")


def test_is_supported_format():
    """Test is_supported_format function."""
    # Supported formats
    assert is_supported_format('document.pdf') is True
    assert is_supported_format('image.jpg') is True
    assert is_supported_format('photo.png') is True
    assert is_supported_format('report.docx') is True
    assert is_supported_format('old_doc.doc') is True
    assert is_supported_format('notes.txt') is True
    assert is_supported_format('memo.rtf') is True

    # Unsupported formats
    assert is_supported_format('video.mp4') is False
    assert is_supported_format('audio.mp3') is False
    assert is_supported_format('data.csv') is False
    assert is_supported_format('code.py') is False

    print("PASS: is_supported_format correctly identifies supported/unsupported formats")


def run_all_tests():
    """Run all tests."""
    print("="*80)
    print("Running Document Analyzer Tests")
    print("="*80)

    tests = [
        test_pdf_searchable,
        test_pdf_scanned,
        test_word_document,
        test_text_documents,
        test_image_files,
        test_unknown_format,
        test_file_not_found,
        test_supported_extensions,
        test_is_supported_format,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            print(f"\n{test_func.__name__}:")
            print("-" * 80)
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {test_func.__name__} - {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {test_func.__name__} - {e}")
            failed += 1

    print("\n" + "="*80)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*80)

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
