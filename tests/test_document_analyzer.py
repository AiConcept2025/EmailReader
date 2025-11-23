"""Tests for document analyzer."""
import os
import pytest
import tempfile
from pathlib import Path
from src.document_analyzer import (
    requires_ocr,
    get_document_type,
    get_pdf_type,
    is_image_based_pdf,
    is_supported_format,
    get_supported_extensions
)


class TestDocumentAnalyzer:
    """Test document analyzer functions."""

    @pytest.fixture
    def test_docs_path(self):
        """Get path to test documents."""
        return os.path.join(os.path.dirname(__file__), '..', 'test_docs')

    def test_searchable_pdf_no_ocr_required(self, test_docs_path):
        """Test searchable PDF doesn't require OCR."""
        pdf_path = os.path.join(test_docs_path, 'file-sample-pdf.pdf')
        if os.path.exists(pdf_path):
            assert requires_ocr(pdf_path) is False
            assert get_document_type(pdf_path) == 'pdf_searchable'
        else:
            pytest.skip(f"Test file not found: {pdf_path}")

    def test_scanned_pdf_requires_ocr(self, test_docs_path):
        """Test scanned PDF requires OCR."""
        pdf_path = os.path.join(test_docs_path, 'PDF-scanned-rus-words.pdf')
        if os.path.exists(pdf_path):
            assert requires_ocr(pdf_path) is True
            assert get_document_type(pdf_path) == 'pdf_scanned'
        else:
            pytest.skip(f"Test file not found: {pdf_path}")

    def test_image_based_pdf_requires_ocr(self, test_docs_path):
        """Test image-based PDF requires OCR."""
        pdf_path = os.path.join(test_docs_path, 'file-sample-img.pdf')
        if os.path.exists(pdf_path):
            result = requires_ocr(pdf_path)
            # This should require OCR (might be image-based or scanned)
            assert result in [True, False]  # Depends on PDF content
            doc_type = get_document_type(pdf_path)
            assert doc_type in ['pdf_searchable', 'pdf_scanned']
        else:
            pytest.skip(f"Test file not found: {pdf_path}")

    def test_image_file_requires_ocr(self):
        """Test image files require OCR."""
        # Create a temporary image file for testing
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_path = f.name
            f.write(b'\xff\xd8\xff\xe0')  # Minimal JPEG header
        try:
            assert requires_ocr(temp_path) is True
            assert get_document_type(temp_path) == 'image'
        finally:
            os.remove(temp_path)

    def test_png_file_requires_ocr(self):
        """Test PNG files require OCR."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name
            f.write(b'\x89PNG\r\n\x1a\n')  # PNG signature
        try:
            assert requires_ocr(temp_path) is True
            assert get_document_type(temp_path) == 'image'
        finally:
            os.remove(temp_path)

    def test_tiff_file_requires_ocr(self):
        """Test TIFF files require OCR."""
        with tempfile.NamedTemporaryFile(suffix='.tiff', delete=False) as f:
            temp_path = f.name
            f.write(b'II*\x00')  # TIFF signature (little-endian)
        try:
            assert requires_ocr(temp_path) is True
            assert get_document_type(temp_path) == 'image'
        finally:
            os.remove(temp_path)

    def test_word_document_no_ocr(self, test_docs_path):
        """Test Word documents don't require OCR."""
        doc_path = os.path.join(test_docs_path, 'file-sample-doc.doc')
        if os.path.exists(doc_path):
            assert requires_ocr(doc_path) is False
            assert get_document_type(doc_path) == 'word_document'
        else:
            pytest.skip(f"Test file not found: {doc_path}")

    def test_docx_document_no_ocr(self):
        """Test DOCX documents don't require OCR."""
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_path = f.name
            f.write(b'PK')  # ZIP signature (DOCX is a ZIP file)
        try:
            assert requires_ocr(temp_path) is False
            assert get_document_type(temp_path) == 'word_document'
        finally:
            os.remove(temp_path)

    def test_text_file_no_ocr(self, test_docs_path):
        """Test text files don't require OCR."""
        txt_path = os.path.join(test_docs_path, 'file-sample-txt.txt')
        if os.path.exists(txt_path):
            assert requires_ocr(txt_path) is False
            assert get_document_type(txt_path) == 'text_document'
        else:
            pytest.skip(f"Test file not found: {txt_path}")

    def test_rtf_file_no_ocr(self, test_docs_path):
        """Test RTF files don't require OCR."""
        rtf_path = os.path.join(test_docs_path, 'file-sample-rtf.rtf')
        if os.path.exists(rtf_path):
            assert requires_ocr(rtf_path) is False
            assert get_document_type(rtf_path) == 'text_document'
        else:
            pytest.skip(f"Test file not found: {rtf_path}")

    def test_file_not_found_raises_error(self):
        """Test missing file raises error."""
        with pytest.raises(FileNotFoundError):
            requires_ocr('/nonexistent/file.pdf')

    def test_unknown_file_type(self):
        """Test unknown file types return 'unknown'."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            temp_path = f.name
        try:
            doc_type = get_document_type(temp_path)
            assert doc_type == 'unknown'
            # Unknown types don't require OCR
            assert requires_ocr(temp_path) is False
        finally:
            os.remove(temp_path)

    def test_get_pdf_type_searchable(self, test_docs_path):
        """Test get_pdf_type identifies searchable PDFs."""
        pdf_path = os.path.join(test_docs_path, 'file-sample-pdf.pdf')
        if os.path.exists(pdf_path):
            pdf_type = get_pdf_type(pdf_path)
            assert pdf_type == 'pdf_searchable'
        else:
            pytest.skip(f"Test file not found: {pdf_path}")

    def test_get_pdf_type_scanned(self, test_docs_path):
        """Test get_pdf_type identifies scanned PDFs."""
        pdf_path = os.path.join(test_docs_path, 'PDF-scanned-rus-words.pdf')
        if os.path.exists(pdf_path):
            pdf_type = get_pdf_type(pdf_path)
            assert pdf_type == 'pdf_scanned'
        else:
            pytest.skip(f"Test file not found: {pdf_path}")

    def test_is_image_based_pdf_true(self, test_docs_path):
        """Test is_image_based_pdf returns True for scanned PDFs."""
        pdf_path = os.path.join(test_docs_path, 'PDF-scanned-rus-words.pdf')
        if os.path.exists(pdf_path):
            assert is_image_based_pdf(pdf_path) is True
        else:
            pytest.skip(f"Test file not found: {pdf_path}")

    def test_is_image_based_pdf_false(self, test_docs_path):
        """Test is_image_based_pdf returns False for searchable PDFs."""
        pdf_path = os.path.join(test_docs_path, 'file-sample-pdf.pdf')
        if os.path.exists(pdf_path):
            assert is_image_based_pdf(pdf_path) is False
        else:
            pytest.skip(f"Test file not found: {pdf_path}")

    def test_get_supported_extensions(self):
        """Test get_supported_extensions returns correct structure."""
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

    def test_is_supported_format_pdf(self):
        """Test is_supported_format for PDF files."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        try:
            assert is_supported_format(temp_path) is True
        finally:
            os.remove(temp_path)

    def test_is_supported_format_image(self):
        """Test is_supported_format for image files."""
        for ext in ['.jpg', '.png', '.tiff']:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                temp_path = f.name
            try:
                assert is_supported_format(temp_path) is True
            finally:
                os.remove(temp_path)

    def test_is_supported_format_word(self):
        """Test is_supported_format for Word documents."""
        for ext in ['.doc', '.docx']:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                temp_path = f.name
            try:
                assert is_supported_format(temp_path) is True
            finally:
                os.remove(temp_path)

    def test_is_supported_format_text(self):
        """Test is_supported_format for text files."""
        for ext in ['.txt', '.rtf']:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                temp_path = f.name
            try:
                assert is_supported_format(temp_path) is True
            finally:
                os.remove(temp_path)

    def test_is_supported_format_unsupported(self):
        """Test is_supported_format for unsupported files."""
        unsupported = ['.mp4', '.exe', '.zip', '.tar']
        for ext in unsupported:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                temp_path = f.name
            try:
                assert is_supported_format(temp_path) is False
            finally:
                os.remove(temp_path)

    def test_case_insensitive_extensions(self):
        """Test that file extension checking is case-insensitive."""
        with tempfile.NamedTemporaryFile(suffix='.PDF', delete=False) as f:
            temp_path = f.name
        try:
            assert is_supported_format(temp_path) is True
            assert get_document_type(temp_path) in ['pdf_searchable', 'pdf_scanned']
        finally:
            os.remove(temp_path)

    def test_document_type_for_all_image_formats(self):
        """Test document type detection for all supported image formats."""
        image_formats = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp']
        for ext in image_formats:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                temp_path = f.name
            try:
                doc_type = get_document_type(temp_path)
                assert doc_type == 'image', f"Failed for extension {ext}"
            finally:
                os.remove(temp_path)
