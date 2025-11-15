"""
Demonstration of document_analyzer module usage.

This script shows practical examples of how to use the document analyzer
to determine OCR requirements for various document types.

Run with:
    PYTHONPATH=/Users/vladimirdanishevsky/projects/EmailReader python examples/document_analyzer_demo.py
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.document_analyzer import (
    requires_ocr,
    get_document_type,
    get_pdf_type,
    is_image_based_pdf,
    get_supported_extensions,
    is_supported_format,
)


def demo_basic_usage():
    """Demonstrate basic OCR detection."""
    print("="*80)
    print("DEMO 1: Basic OCR Detection")
    print("="*80)

    test_files = [
        'test_docs/file-sample-pdf.pdf',           # Searchable PDF
        'test_docs/PDF-scanned-rus-words.pdf',    # Scanned PDF
        'test_docs/file-sample-doc.doc',          # Word document
    ]

    for file_path in test_files:
        if os.path.exists(file_path):
            needs_ocr = requires_ocr(file_path)
            print(f"\nFile: {Path(file_path).name}")
            print(f"  Requires OCR: {needs_ocr}")
        else:
            print(f"\nFile: {Path(file_path).name} - NOT FOUND")


def demo_document_classification():
    """Demonstrate document type classification."""
    print("\n" + "="*80)
    print("DEMO 2: Document Type Classification")
    print("="*80)

    test_files = [
        'test_docs/file-sample-pdf.pdf',
        'test_docs/PDF-scanned-rus-words.pdf',
        'test_docs/file-sample-img.pdf',
        'test_docs/file-sample-doc.doc',
        'test_docs/file-sample-txt.txt',
        'test_docs/file-sample-rtf.rtf',
    ]

    for file_path in test_files:
        if os.path.exists(file_path):
            doc_type = get_document_type(file_path)
            print(f"\nFile: {Path(file_path).name}")
            print(f"  Document Type: {doc_type}")
        else:
            print(f"\nFile: {Path(file_path).name} - NOT FOUND")


def demo_pdf_analysis():
    """Demonstrate PDF-specific analysis."""
    print("\n" + "="*80)
    print("DEMO 3: PDF-Specific Analysis")
    print("="*80)

    pdf_files = [
        'test_docs/file-sample-pdf.pdf',
        'test_docs/PDF-scanned-rus-words.pdf',
        'test_docs/file-sample-img.pdf',
    ]

    for pdf_path in pdf_files:
        if os.path.exists(pdf_path):
            pdf_type = get_pdf_type(pdf_path)
            is_scanned = is_image_based_pdf(pdf_path)

            print(f"\nPDF: {Path(pdf_path).name}")
            print(f"  PDF Type: {pdf_type}")
            print(f"  Is Scanned: {is_scanned}")
            print(f"  Requires OCR: {requires_ocr(pdf_path)}")
        else:
            print(f"\nPDF: {Path(pdf_path).name} - NOT FOUND")


def demo_format_support():
    """Demonstrate format support checking."""
    print("\n" + "="*80)
    print("DEMO 4: Format Support Checking")
    print("="*80)

    test_extensions = [
        'document.pdf',
        'image.jpg',
        'photo.png',
        'report.docx',
        'notes.txt',
        'video.mp4',
        'audio.mp3',
        'data.csv',
    ]

    print("\nChecking format support for various file types:")
    for filename in test_extensions:
        supported = is_supported_format(filename)
        status = "SUPPORTED" if supported else "NOT SUPPORTED"
        print(f"  {filename:20} - {status}")


def demo_supported_extensions():
    """Demonstrate listing supported extensions."""
    print("\n" + "="*80)
    print("DEMO 5: Supported Extensions by Category")
    print("="*80)

    extensions = get_supported_extensions()

    for category, ext_list in extensions.items():
        print(f"\n{category.upper()}:")
        print(f"  {', '.join(ext_list)}")


def demo_workflow_simulation():
    """Demonstrate a typical document processing workflow."""
    print("\n" + "="*80)
    print("DEMO 6: Document Processing Workflow Simulation")
    print("="*80)

    files = [
        'test_docs/file-sample-pdf.pdf',
        'test_docs/PDF-scanned-rus-words.pdf',
        'test_docs/file-sample-doc.doc',
    ]

    print("\nSimulating document processing pipeline:\n")

    for file_path in files:
        if not os.path.exists(file_path):
            continue

        filename = Path(file_path).name
        print(f"Processing: {filename}")
        print(f"  Step 1: Check if format is supported...")

        if not is_supported_format(file_path):
            print(f"    SKIP - Unsupported format")
            continue

        print(f"    OK - Format is supported")
        print(f"  Step 2: Determine document type...")

        doc_type = get_document_type(file_path)
        print(f"    Detected: {doc_type}")

        print(f"  Step 3: Check if OCR is needed...")
        needs_ocr = requires_ocr(file_path)

        if needs_ocr:
            print(f"    ACTION - Run OCR processing")
            print(f"    (Would call: ocr_pdf_image_to_doc())")
        else:
            print(f"    SKIP - OCR not needed")
            print(f"    (Would call: standard text extraction)")

        print()


def demo_error_handling():
    """Demonstrate error handling."""
    print("\n" + "="*80)
    print("DEMO 7: Error Handling")
    print("="*80)

    print("\n1. Testing with non-existent file:")
    try:
        requires_ocr('/tmp/nonexistent_file.pdf')
        print("   No error raised (unexpected!)")
    except FileNotFoundError as e:
        print(f"   Caught FileNotFoundError: {e}")

    print("\n2. Testing with unknown format:")
    # Create a temp file with unknown extension
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        doc_type = get_document_type(tmp_path)
        print(f"   Document type: {doc_type}")
        needs_ocr = requires_ocr(tmp_path)
        print(f"   Requires OCR: {needs_ocr}")
        print("   (Unknown formats return 'unknown' type and don't require OCR)")
    finally:
        os.unlink(tmp_path)


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*20 + "Document Analyzer Module Demo" + " "*29 + "║")
    print("╚" + "═"*78 + "╝")

    demos = [
        demo_basic_usage,
        demo_document_classification,
        demo_pdf_analysis,
        demo_format_support,
        demo_supported_extensions,
        demo_workflow_simulation,
        demo_error_handling,
    ]

    for demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\nError in {demo_func.__name__}: {e}")

    print("\n" + "="*80)
    print("Demo Complete!")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
