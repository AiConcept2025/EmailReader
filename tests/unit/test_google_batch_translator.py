"""Unit tests for GoogleBatchTranslator.

Tests for paragraph-based batch translation using Google translate_text() API.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from typing import List
import tempfile
import os

from src.translation.google_batch_translator import GoogleBatchTranslator
from src.models.paragraph import Paragraph, TextSpan


class TestGoogleBatchTranslatorInitialization:
    """Test suite for GoogleBatchTranslator initialization."""

    @patch('src.translation.google_batch_translator.load_config')
    @patch('src.translation.google_batch_translator.service_account')
    @patch('src.translation.google_batch_translator.translate_v3.TranslationServiceClient')
    def test_initialization_with_valid_config(self, mock_client_class, mock_sa, mock_load_config):
        """Test successful initialization with valid project_id."""
        # Arrange
        mock_load_config.return_value = {
            'google_drive': {
                'service_account': {'type': 'service_account', 'project_id': 'test-project'}
            }
        }
        mock_credentials = Mock()
        mock_sa.Credentials.from_service_account_info.return_value = mock_credentials
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        config = {'project_id': 'test-project-123'}

        # Act
        translator = GoogleBatchTranslator(config)

        # Assert
        assert translator.project_id == 'test-project-123'
        assert translator.location == 'us-central1'
        assert translator.parent == 'projects/test-project-123/locations/us-central1'
        assert translator.BATCH_SIZE == 25
        mock_sa.Credentials.from_service_account_info.assert_called_once()
        mock_client_class.assert_called_once_with(credentials=mock_credentials)

    @patch('src.translation.google_batch_translator.load_config')
    @patch('src.translation.google_batch_translator.service_account')
    @patch('src.translation.google_batch_translator.translate_v3.TranslationServiceClient')
    def test_initialization_with_custom_location(self, mock_client_class, mock_sa, mock_load_config):
        """Test initialization with custom location."""
        # Arrange
        mock_load_config.return_value = {
            'google_drive': {
                'service_account': {'type': 'service_account'}
            }
        }
        mock_credentials = Mock()
        mock_sa.Credentials.from_service_account_info.return_value = mock_credentials
        mock_client_class.return_value = Mock()

        config = {'project_id': 'test-project', 'location': 'europe-west1'}

        # Act
        translator = GoogleBatchTranslator(config)

        # Assert
        assert translator.location == 'europe-west1'
        assert translator.parent == 'projects/test-project/locations/europe-west1'

    def test_initialization_missing_project_id(self):
        """Test that initialization fails without project_id."""
        # Arrange
        config = {}

        # Act & Assert
        with pytest.raises(ValueError, match="'project_id' in configuration"):
            GoogleBatchTranslator(config)

    @patch('src.translation.google_batch_translator.load_config')
    def test_initialization_missing_service_account(self, mock_load_config):
        """Test that initialization fails without service account in config."""
        # Arrange
        mock_load_config.return_value = {'google_drive': {}}
        config = {'project_id': 'test-project'}

        # Act & Assert
        with pytest.raises(ValueError, match="Service account credentials not found"):
            GoogleBatchTranslator(config)


class TestMapStyleToRole:
    """Test suite for _map_style_to_role method."""

    @patch('src.translation.google_batch_translator.load_config')
    @patch('src.translation.google_batch_translator.service_account')
    @patch('src.translation.google_batch_translator.translate_v3.TranslationServiceClient')
    def setup_translator(self, mock_client_class, mock_sa, mock_load_config):
        """Helper to create translator instance."""
        mock_load_config.return_value = {
            'google_drive': {'service_account': {'type': 'service_account'}}
        }
        mock_sa.Credentials.from_service_account_info.return_value = Mock()
        mock_client_class.return_value = Mock()
        return GoogleBatchTranslator({'project_id': 'test'})

    def test_map_title_style(self):
        """Test mapping 'Title' style to 'title' role."""
        translator = self.setup_translator()
        assert translator._map_style_to_role('Title') == 'title'

    def test_map_heading1_style(self):
        """Test mapping 'Heading 1' style to 'heading' role."""
        translator = self.setup_translator()
        assert translator._map_style_to_role('Heading 1') == 'heading'

    def test_map_heading2_style(self):
        """Test mapping 'Heading 2' style to 'heading' role."""
        translator = self.setup_translator()
        assert translator._map_style_to_role('Heading 2') == 'heading'

    def test_map_heading3_style(self):
        """Test mapping 'Heading 3' style to 'heading' role."""
        translator = self.setup_translator()
        assert translator._map_style_to_role('Heading 3') == 'heading'

    def test_map_list_paragraph_style(self):
        """Test mapping 'List Paragraph' style to 'listItem' role."""
        translator = self.setup_translator()
        assert translator._map_style_to_role('List Paragraph') == 'listItem'

    def test_map_default_style(self):
        """Test mapping unknown style to 'paragraph' role."""
        translator = self.setup_translator()
        assert translator._map_style_to_role('Normal') == 'paragraph'
        assert translator._map_style_to_role('Unknown Style') == 'paragraph'
        assert translator._map_style_to_role('') == 'paragraph'


class TestExtractRunsAsSpans:
    """Test suite for _extract_runs_as_spans method."""

    @patch('src.translation.google_batch_translator.load_config')
    @patch('src.translation.google_batch_translator.service_account')
    @patch('src.translation.google_batch_translator.translate_v3.TranslationServiceClient')
    def setup_translator(self, mock_client_class, mock_sa, mock_load_config):
        """Helper to create translator instance."""
        mock_load_config.return_value = {
            'google_drive': {'service_account': {'type': 'service_account'}}
        }
        mock_sa.Credentials.from_service_account_info.return_value = Mock()
        mock_client_class.return_value = Mock()
        return GoogleBatchTranslator({'project_id': 'test'})

    def test_extract_plain_run(self):
        """Test extracting a plain text run without formatting."""
        translator = self.setup_translator()

        mock_run = Mock()
        mock_run.text = "Plain text"
        mock_run.bold = None
        mock_run.italic = None
        mock_run.font.size = None

        spans = translator._extract_runs_as_spans([mock_run])

        assert len(spans) == 1
        assert spans[0].text == "Plain text"
        assert spans[0].is_bold is False
        assert spans[0].is_italic is False
        assert spans[0].font_size is None

    def test_extract_bold_run(self):
        """Test extracting a bold run."""
        translator = self.setup_translator()

        mock_run = Mock()
        mock_run.text = "Bold text"
        mock_run.bold = True
        mock_run.italic = None
        mock_run.font.size = None

        spans = translator._extract_runs_as_spans([mock_run])

        assert len(spans) == 1
        assert spans[0].text == "Bold text"
        assert spans[0].is_bold is True
        assert spans[0].is_italic is False

    def test_extract_italic_run(self):
        """Test extracting an italic run."""
        translator = self.setup_translator()

        mock_run = Mock()
        mock_run.text = "Italic text"
        mock_run.bold = None
        mock_run.italic = True
        mock_run.font.size = None

        spans = translator._extract_runs_as_spans([mock_run])

        assert len(spans) == 1
        assert spans[0].is_italic is True

    def test_extract_run_with_font_size(self):
        """Test extracting a run with font size."""
        translator = self.setup_translator()

        mock_run = Mock()
        mock_run.text = "Sized text"
        mock_run.bold = None
        mock_run.italic = None
        mock_font_size = Mock()
        mock_font_size.pt = 14.0
        mock_run.font.size = mock_font_size

        spans = translator._extract_runs_as_spans([mock_run])

        assert len(spans) == 1
        assert spans[0].font_size == 14.0

    def test_extract_multiple_runs(self):
        """Test extracting multiple runs with different formatting."""
        translator = self.setup_translator()

        run1 = Mock()
        run1.text = "Normal "
        run1.bold = None
        run1.italic = None
        run1.font.size = None

        run2 = Mock()
        run2.text = "bold "
        run2.bold = True
        run2.italic = None
        run2.font.size = None

        run3 = Mock()
        run3.text = "italic"
        run3.bold = None
        run3.italic = True
        run3.font.size = None

        spans = translator._extract_runs_as_spans([run1, run2, run3])

        assert len(spans) == 3
        assert spans[0].text == "Normal "
        assert spans[0].is_bold is False
        assert spans[1].text == "bold "
        assert spans[1].is_bold is True
        assert spans[2].text == "italic"
        assert spans[2].is_italic is True


class TestExtractParagraphsFromDocx:
    """Test suite for _extract_paragraphs_from_docx method."""

    @patch('src.translation.google_batch_translator.load_config')
    @patch('src.translation.google_batch_translator.service_account')
    @patch('src.translation.google_batch_translator.translate_v3.TranslationServiceClient')
    def setup_translator(self, mock_client_class, mock_sa, mock_load_config):
        """Helper to create translator instance."""
        mock_load_config.return_value = {
            'google_drive': {'service_account': {'type': 'service_account'}}
        }
        mock_sa.Credentials.from_service_account_info.return_value = Mock()
        mock_client_class.return_value = Mock()
        return GoogleBatchTranslator({'project_id': 'test'})

    @patch('src.translation.google_batch_translator.Document')
    def test_extract_paragraphs_from_simple_docx(self, mock_document_class):
        """Test extracting paragraphs from a simple DOCX file."""
        translator = self.setup_translator()

        # Mock document
        mock_para1 = Mock()
        mock_para1.text = "First paragraph"
        mock_para1.style.name = 'Normal'
        mock_run1 = Mock()
        mock_run1.text = "First paragraph"
        mock_run1.bold = None
        mock_run1.italic = None
        mock_run1.font.size = None
        mock_para1.runs = [mock_run1]

        mock_para2 = Mock()
        mock_para2.text = "Second paragraph"
        mock_para2.style.name = 'Normal'
        mock_run2 = Mock()
        mock_run2.text = "Second paragraph"
        mock_run2.bold = None
        mock_run2.italic = None
        mock_run2.font.size = None
        mock_para2.runs = [mock_run2]

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_document_class.return_value = mock_doc

        # Act
        paragraphs = translator._extract_paragraphs_from_docx('/fake/path.docx')

        # Assert
        assert len(paragraphs) == 2
        assert paragraphs[0].content == "First paragraph"
        assert paragraphs[0].page == 0
        assert paragraphs[0].role == 'paragraph'
        assert paragraphs[1].content == "Second paragraph"
        mock_document_class.assert_called_once_with('/fake/path.docx')

    @patch('src.translation.google_batch_translator.Document')
    def test_extract_paragraphs_with_different_roles(self, mock_document_class):
        """Test extracting paragraphs with different styles/roles."""
        translator = self.setup_translator()

        # Mock title paragraph
        mock_title = Mock()
        mock_title.text = "Document Title"
        mock_title.style.name = 'Title'
        mock_title.runs = []

        # Mock heading paragraph
        mock_heading = Mock()
        mock_heading.text = "Section Heading"
        mock_heading.style.name = 'Heading 1'
        mock_heading.runs = []

        # Mock list item
        mock_list = Mock()
        mock_list.text = "List item"
        mock_list.style.name = 'List Paragraph'
        mock_list.runs = []

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_title, mock_heading, mock_list]
        mock_document_class.return_value = mock_doc

        # Act
        paragraphs = translator._extract_paragraphs_from_docx('/fake/path.docx')

        # Assert
        assert len(paragraphs) == 3
        assert paragraphs[0].role == 'title'
        assert paragraphs[1].role == 'heading'
        assert paragraphs[2].role == 'listItem'


class TestTranslateBatch:
    """Test suite for _translate_batch method."""

    @patch('src.translation.google_batch_translator.load_config')
    @patch('src.translation.google_batch_translator.service_account')
    @patch('src.translation.google_batch_translator.translate_v3.TranslationServiceClient')
    def setup_translator(self, mock_client_class, mock_sa, mock_load_config):
        """Helper to create translator instance."""
        mock_load_config.return_value = {
            'google_drive': {'service_account': {'type': 'service_account'}}
        }
        mock_sa.Credentials.from_service_account_info.return_value = Mock()
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        translator = GoogleBatchTranslator({'project_id': 'test-project'})
        translator.client = mock_client
        return translator

    def test_translate_batch_success(self):
        """Test successful batch translation."""
        translator = self.setup_translator()

        # Mock API response
        mock_translation1 = Mock()
        mock_translation1.translated_text = "Translated text 1"
        mock_translation2 = Mock()
        mock_translation2.translated_text = "Translated text 2"
        mock_translation3 = Mock()
        mock_translation3.translated_text = "Translated text 3"

        mock_response = Mock()
        mock_response.translations = [mock_translation1, mock_translation2, mock_translation3]
        translator.client.translate_text.return_value = mock_response

        # Act
        texts = ["Text 1", "Text 2", "Text 3"]
        result = translator._translate_batch(texts, 'en')

        # Assert
        assert len(result) == 3
        assert result[0] == "Translated text 1"
        assert result[1] == "Translated text 2"
        assert result[2] == "Translated text 3"

        # Verify API call
        translator.client.translate_text.assert_called_once()
        call_args = translator.client.translate_text.call_args
        request = call_args.kwargs['request'] if 'request' in call_args.kwargs else call_args[0][0]
        assert request.parent == 'projects/test-project/locations/us-central1'
        assert request.contents == texts
        assert request.target_language_code == 'en'
        assert request.mime_type == 'text/plain'

    def test_translate_batch_with_different_target_language(self):
        """Test batch translation with different target language."""
        translator = self.setup_translator()

        mock_translation = Mock()
        mock_translation.translated_text = "Texte traduit"
        mock_response = Mock()
        mock_response.translations = [mock_translation]
        translator.client.translate_text.return_value = mock_response

        # Act
        result = translator._translate_batch(["Text"], 'fr')

        # Assert
        call_args = translator.client.translate_text.call_args
        request = call_args.kwargs['request'] if 'request' in call_args.kwargs else call_args[0][0]
        assert request.target_language_code == 'fr'

    def test_translate_batch_api_error(self):
        """Test batch translation handles GoogleAPIError."""
        translator = self.setup_translator()

        # Create a custom exception class that looks like GoogleAPIError
        class GoogleAPIError(Exception):
            pass

        # Mock API error
        mock_error = GoogleAPIError("API Error")
        translator.client.translate_text.side_effect = mock_error

        # Act & Assert
        with pytest.raises(RuntimeError, match="Translation API failed"):
            translator._translate_batch(["Text"], 'en')


class TestAssembleDocx:
    """Test suite for _assemble_docx method."""

    @patch('src.translation.google_batch_translator.load_config')
    @patch('src.translation.google_batch_translator.service_account')
    @patch('src.translation.google_batch_translator.translate_v3.TranslationServiceClient')
    def setup_translator(self, mock_client_class, mock_sa, mock_load_config):
        """Helper to create translator instance."""
        mock_load_config.return_value = {
            'google_drive': {'service_account': {'type': 'service_account'}}
        }
        mock_sa.Credentials.from_service_account_info.return_value = Mock()
        mock_client_class.return_value = Mock()
        return GoogleBatchTranslator({'project_id': 'test'})

    @patch('src.translation.google_batch_translator.Document')
    def test_assemble_simple_paragraphs(self, mock_document_class):
        """Test assembling simple paragraphs without formatting."""
        translator = self.setup_translator()

        mock_doc = Mock()
        mock_document_class.return_value = mock_doc

        paragraphs = [
            Paragraph(content="First paragraph", page=0, role='paragraph'),
            Paragraph(content="Second paragraph", page=0, role='paragraph')
        ]

        # Act
        translator._assemble_docx(paragraphs, '/fake/output.docx')

        # Assert
        assert mock_doc.add_paragraph.call_count == 2
        mock_doc.add_paragraph.assert_any_call('First paragraph')
        mock_doc.add_paragraph.assert_any_call('Second paragraph')
        mock_doc.save.assert_called_once_with('/fake/output.docx')

    @patch('src.translation.google_batch_translator.Document')
    def test_assemble_title_paragraph(self, mock_document_class):
        """Test assembling a title paragraph."""
        translator = self.setup_translator()

        mock_doc = Mock()
        mock_document_class.return_value = mock_doc

        paragraphs = [
            Paragraph(content="Document Title", page=0, role='title')
        ]

        # Act
        translator._assemble_docx(paragraphs, '/fake/output.docx')

        # Assert
        mock_doc.add_heading.assert_called_once_with('Document Title', level=0)

    @patch('src.translation.google_batch_translator.Document')
    def test_assemble_heading_paragraph(self, mock_document_class):
        """Test assembling a heading paragraph."""
        translator = self.setup_translator()

        mock_doc = Mock()
        mock_document_class.return_value = mock_doc

        paragraphs = [
            Paragraph(content="Section Heading", page=0, role='heading')
        ]

        # Act
        translator._assemble_docx(paragraphs, '/fake/output.docx')

        # Assert
        mock_doc.add_heading.assert_called_once_with('Section Heading', level=1)

    @patch('src.translation.google_batch_translator.Document')
    def test_assemble_list_item_paragraph(self, mock_document_class):
        """Test assembling a list item paragraph."""
        translator = self.setup_translator()

        mock_doc = Mock()
        mock_para = Mock()
        mock_doc.add_paragraph.return_value = mock_para
        mock_document_class.return_value = mock_doc

        paragraphs = [
            Paragraph(content="List item", page=0, role='listItem')
        ]

        # Act
        translator._assemble_docx(paragraphs, '/fake/output.docx')

        # Assert
        mock_doc.add_paragraph.assert_called_once()
        # Verify list marker was added
        call_args = mock_doc.add_paragraph.call_args[0][0]
        assert '•' in call_args or 'List item' in call_args

    @patch('src.translation.google_batch_translator.Document')
    @patch('src.translation.google_batch_translator.Pt')
    def test_assemble_paragraph_with_formatting_spans(self, mock_pt, mock_document_class):
        """Test assembling a paragraph with formatting spans."""
        translator = self.setup_translator()

        mock_doc = Mock()
        mock_para = Mock()
        mock_run1 = Mock()
        mock_run2 = Mock()
        mock_para.add_run.side_effect = [mock_run1, mock_run2]
        mock_doc.add_paragraph.return_value = mock_para
        mock_document_class.return_value = mock_doc

        paragraphs = [
            Paragraph(
                content="Normal bold text",
                page=0,
                role='paragraph',
                spans=[
                    TextSpan(text="Normal ", is_bold=False, font_size=12.0),
                    TextSpan(text="bold text", is_bold=True, font_size=14.0)
                ]
            )
        ]

        # Act
        translator._assemble_docx(paragraphs, '/fake/output.docx')

        # Assert
        assert mock_para.add_run.call_count == 2
        mock_para.add_run.assert_any_call("Normal ")
        mock_para.add_run.assert_any_call("bold text")
        assert mock_run2.bold is True


class TestTranslateDocument:
    """Test suite for translate_document method."""

    @patch('src.translation.google_batch_translator.load_config')
    @patch('src.translation.google_batch_translator.service_account')
    @patch('src.translation.google_batch_translator.translate_v3.TranslationServiceClient')
    def setup_translator(self, mock_client_class, mock_sa, mock_load_config):
        """Helper to create translator instance."""
        mock_load_config.return_value = {
            'google_drive': {'service_account': {'type': 'service_account'}}
        }
        mock_sa.Credentials.from_service_account_info.return_value = Mock()
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        translator = GoogleBatchTranslator({'project_id': 'test-project'})
        translator.client = mock_client
        return translator

    @patch('src.translation.google_batch_translator.os.path.exists')
    def test_translate_document_file_not_found(self, mock_exists):
        """Test translate_document raises error for missing input file."""
        translator = self.setup_translator()
        mock_exists.return_value = False

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            translator.translate_document('/fake/input.docx', '/fake/output.docx')

    @patch('src.translation.google_batch_translator.os.path.exists')
    @patch.object(GoogleBatchTranslator, '_extract_paragraphs_from_docx')
    @patch.object(GoogleBatchTranslator, '_translate_batch')
    @patch.object(GoogleBatchTranslator, '_assemble_docx')
    def test_translate_document_success(self, mock_assemble, mock_translate,
                                       mock_extract, mock_exists):
        """Test successful document translation workflow."""
        translator = self.setup_translator()
        mock_exists.return_value = True

        # Mock extracted paragraphs
        mock_extract.return_value = [
            Paragraph(content="Paragraph 1", page=0, role='paragraph'),
            Paragraph(content="Paragraph 2", page=0, role='paragraph')
        ]

        # Mock translation
        mock_translate.return_value = ["Translated 1", "Translated 2"]

        # Act
        translator.translate_document('/fake/input.docx', '/fake/output.docx', 'en')

        # Assert
        mock_extract.assert_called_once_with('/fake/input.docx')
        mock_translate.assert_called_once()
        mock_assemble.assert_called_once()

        # Verify translated paragraphs were assembled
        assembled_paragraphs = mock_assemble.call_args[0][0]
        assert len(assembled_paragraphs) == 2
        assert assembled_paragraphs[0].content == "Translated 1"
        assert assembled_paragraphs[1].content == "Translated 2"

    @patch('src.translation.google_batch_translator.os.path.exists')
    @patch.object(GoogleBatchTranslator, '_extract_paragraphs_from_docx')
    @patch.object(GoogleBatchTranslator, '_translate_batch')
    @patch.object(GoogleBatchTranslator, '_assemble_docx')
    def test_translate_document_batching(self, mock_assemble, mock_translate,
                                        mock_extract, mock_exists):
        """Test that document translation properly batches paragraphs."""
        translator = self.setup_translator()
        mock_exists.return_value = True

        # Create 60 paragraphs (should be split into 3 batches of 25, 25, 10)
        paragraphs = [
            Paragraph(content=f"Paragraph {i}", page=0, role='paragraph')
            for i in range(60)
        ]
        mock_extract.return_value = paragraphs

        # Mock translation returns
        def translate_side_effect(texts, lang):
            return [f"Translated {t}" for t in texts]

        mock_translate.side_effect = translate_side_effect

        # Act
        translator.translate_document('/fake/input.docx', '/fake/output.docx', 'en')

        # Assert
        # Should be called 3 times (3 batches)
        assert mock_translate.call_count == 3

        # Verify batch sizes
        call1_texts = mock_translate.call_args_list[0][0][0]
        call2_texts = mock_translate.call_args_list[1][0][0]
        call3_texts = mock_translate.call_args_list[2][0][0]

        assert len(call1_texts) == 25
        assert len(call2_texts) == 25
        assert len(call3_texts) == 10

        # Verify all 60 paragraphs were translated
        assembled_paragraphs = mock_assemble.call_args[0][0]
        assert len(assembled_paragraphs) == 60
