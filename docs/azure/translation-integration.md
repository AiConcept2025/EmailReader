# Azure OCR + Google Translation Integration

Complete implementation of Azure Document Intelligence OCR with Google Cloud Translation API v3 for the EmailReader project.

## Overview

This integration provides a flexible, production-ready solution for OCR and translation:

- **OCR Providers**: Azure Document Intelligence, LandingAI, or Tesseract (default)
- **Translation Provider**: Google Cloud Translation API v3 (built-in)

## Architecture

### OCR Module (`src/ocr/`)

```
src/ocr/
├── __init__.py              # Module exports
├── base_provider.py         # Abstract OCR interface
├── ocr_factory.py           # Factory for creating OCR providers
├── default_provider.py      # Tesseract OCR wrapper
├── azure_provider.py        # Azure Document Intelligence
└── landing_ai_provider.py   # LandingAI provider (existing)
```

### Translation Module (`src/translation/`)

```
src/translation/
├── __init__.py              # Module exports
├── base_translator.py       # Abstract translator interface
├── translator_factory.py    # Factory for creating translators
└── google_doc_translator.py   # Google Cloud Translation API v3 (built-in)
```

## Setup

### 1. Install Dependencies

Dependencies are already in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Key dependencies:
- `azure-ai-formrecognizer>=3.3.0` - Azure Document Intelligence
- `google-cloud-translate>=3.11.0` - Google Translation API v3
- `pdfplumber>=0.10.0` - PDF page analysis
- `python-docx>=1.0.0` - DOCX file handling

### 2. Configure Azure Document Intelligence

Create an Azure Cognitive Services resource:

1. Go to [Azure Portal](https://portal.azure.com)
2. Create a "Document Intelligence" resource
3. Copy the endpoint and API key

### 3. Configure Google Cloud Translation

#### Option A: API v3 (Recommended)

1. Create a Google Cloud project
2. Enable the Cloud Translation API
3. Create a service account and download the JSON key
4. Set environment variables:

```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
export GOOGLE_TRANSLATION_LOCATION=us-central1  # optional
```

#### Option B: Subprocess (Legacy)

Uses the existing `translate_document` executable:

```bash
# Executable should exist at: ./translate_document
ls -la translate_document
```

### 4. Set Environment Variables

Copy the example environment file:

```bash
cp .env.azure.example .env.azure
```

Edit `.env.azure` with your credentials:

```bash
# Azure Configuration
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your-api-key

# Google Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GOOGLE_TRANSLATION_LOCATION=us-central1
```

Load environment:

```bash
source .env.azure
# or
export $(cat .env.azure | xargs)
```

## Usage

### Test Script

The `test_azure_translation.py` script provides a complete end-to-end test:

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
./venv/Scripts/activate   # Windows

# Run test
python test_azure_translation.py --input data/documents/PDF-scanned-rus-words.pdf --target en

# OCR only (skip translation)
python test_azure_translation.py --input test.pdf --ocr-only

# Verbose logging
python test_azure_translation.py --input test.pdf --target fr --verbose
```

### Using in Code

#### OCR Only

```python
from src.ocr.ocr_factory import OCRProviderFactory

# Configuration
config = {
    'ocr': {
        'provider': 'azure',  # or 'default', 'landing_ai'
        'azure': {
            'endpoint': 'https://your-resource.cognitiveservices.azure.com/',
            'api_key': 'your-api-key'
        }
    }
}

# Create OCR provider
ocr = OCRProviderFactory.get_provider(config)

# Process document
ocr.process_document('input.pdf', 'output.docx')
```

#### Translation Only

```python
from src.translation.translator_factory import TranslatorFactory

# Configuration for Google Cloud Translation API v3
config = {
    'translation': {
        'provider': 'google_doc',
        'google_doc': {
            'project_id': 'your-project-id',
            'location': 'us-central1'
        }
    }
}

# Create translator
translator = TranslatorFactory.get_translator(config)

# Translate document
translator.translate_document('input.docx', 'output.docx', target_lang='en')
```

#### Complete OCR + Translation Pipeline

```python
import os
from src.ocr.ocr_factory import OCRProviderFactory
from src.translation.translator_factory import TranslatorFactory

# Configuration
config = {
    'ocr': {
        'provider': 'azure',
        'azure': {
            'endpoint': os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'),
            'api_key': os.getenv('AZURE_DOCUMENT_INTELLIGENCE_API_KEY')
        }
    },
    'translation': {
        'provider': 'google_doc',
        'google_doc': {
            'project_id': os.getenv('GOOGLE_CLOUD_PROJECT'),
            'location': 'us-central1'
        }
    }
}

# Create providers
ocr = OCRProviderFactory.get_provider(config)
translator = TranslatorFactory.get_translator(config)

# Process document
ocr.process_document('scanned.pdf', 'ocr_output.docx')
translator.translate_document('ocr_output.docx', 'translated.docx', target_lang='en')
```

## Features

### Azure OCR Provider

- **Intelligent Page Detection**: Automatically detects searchable vs. scanned pages
- **Mixed Document Handling**: Extracts text from searchable pages, OCRs scanned pages
- **Layout Preservation**: Maintains document structure and formatting
- **Page Breaks**: Preserves page boundaries in output DOCX
- **Retry Logic**: Exponential backoff with 3 retry attempts
- **Detailed Logging**: Every API call logged with timing and size information

### Google Document Translator

- **Format Preservation**: Maintains DOCX formatting during translation
- **Multiple Languages**: Supports 100+ language pairs
- **Auto Language Detection**: Automatically detects source language
- **Production Ready**: Full error handling and logging
- **Async Support**: Handles long documents with polling

### Default OCR Provider (Tesseract)

- **Fallback Option**: Works when Azure credentials aren't available
- **Multi-language**: Supports eng, rus, aze, uzb, deu
- **High DPI**: 300 DPI for quality OCR
- **Text Extraction**: Direct text extraction for searchable PDFs

## Configuration Options

### OCR Configuration

```python
config = {
    'ocr': {
        'provider': 'azure',  # 'azure', 'landing_ai', 'default'
        'azure': {
            'endpoint': 'https://...',
            'api_key': 'xxx'
        },
        'landing_ai': {
            'api_key': 'xxx'
        },
        'default': {
            # Tesseract configuration (optional)
        }
    }
}
```

### Translation Configuration

```python
config = {
    'translation': {
        'provider': 'google_doc',  # Only google_doc is supported
        'google_doc': {
            'project_id': 'your-project',
            'location': 'us-central1'  # optional, default: us-central1
        }
    }
}
```

## Logging

All components use structured logging with the `EmailReader` logger hierarchy:

- `EmailReader.OCR` - Base OCR logging
- `EmailReader.OCR.Azure` - Azure-specific logging
- `EmailReader.OCR.Default` - Tesseract logging
- `EmailReader.Translation` - Base translation logging
- `EmailReader.Translation.GoogleDoc` - Google API v3 logging

### Log Levels

- **INFO**: Operation progress, success/failure
- **DEBUG**: Detailed timing, sizes, API parameters
- **ERROR**: Failures with stack traces

## Error Handling

All providers implement comprehensive error handling:

1. **Input Validation**: File existence, format validation
2. **API Errors**: Retry logic with exponential backoff
3. **Timeouts**: Configurable timeouts for long operations
4. **Cleanup**: Proper resource cleanup in finally blocks
5. **User-Friendly Messages**: Clear error messages with context

## Performance

### Azure OCR

- **Speed**: ~2-5 seconds per page
- **Accuracy**: 95%+ for clear scans
- **File Size Limit**: 50 MB per document
- **Page Limit**: 2000 pages per document

### Google Translation

- **Speed**: ~1-3 seconds per page
- **Quality**: Neural machine translation
- **Format Preservation**: Full DOCX formatting maintained
- **File Size Limit**: 100 MB per document

## Testing

### Manual Testing

```bash
# Test with sample PDF
python test_azure_translation.py --input data/documents/PDF-scanned-rus-words.pdf --target en

# Check outputs
ls -lh data/documents/PDF-scanned-rus-words_ocr_test_*.docx
ls -lh data/documents/PDF-scanned-rus-words_translated_test_*.docx
```

### Unit Tests

```bash
# Run tests (when created)
pytest tests/test_ocr_providers.py -v
pytest tests/test_translation_providers.py -v
```

## Troubleshooting

### Azure OCR Issues

**Error: "Invalid endpoint or API key"**
- Verify endpoint format: `https://your-resource.cognitiveservices.azure.com/`
- Check API key is correct
- Ensure resource is in correct region

**Error: "Document too large"**
- Azure limit: 50 MB per document
- Split large PDFs or compress images

### Google Translation Issues

**Error: "Permission denied"**
- Verify `GOOGLE_APPLICATION_CREDENTIALS` points to valid JSON key
- Check service account has Translation API permissions
- Ensure Translation API is enabled in project

**Error: "Project not found"**
- Verify `GOOGLE_CLOUD_PROJECT` is correct
- Check project exists and is active

### Import Errors

**Error: "No module named 'azure'"**
```bash
pip install azure-ai-formrecognizer
```

**Error: "No module named 'google.cloud.translate'"**
```bash
pip install google-cloud-translate
```

## Migration from Legacy Code

### OCR Migration

**Old code:**
```python
from src.pdf_image_ocr import is_pdf_searchable_pypdf, ocr_pdf_image_to_doc

if is_pdf_searchable_pypdf(pdf_path):
    convert_pdf_to_docx(pdf_path, output_path)
else:
    ocr_pdf_image_to_doc(pdf_path, output_path)
```

**New code:**
```python
from src.ocr.ocr_factory import OCRProviderFactory

config = {'ocr': {'provider': 'default'}}
ocr = OCRProviderFactory.get_provider(config)
ocr.process_document(pdf_path, output_path)
```

### Translation Migration

**Old code:**
```python
from src.utils import translate_document_to_english

translate_document_to_english(input_path, output_path)
```

**New code:**
```python
from src.translation.translator_factory import TranslatorFactory

config = {'translation': {'provider': 'google_doc', 'google_doc': {'project_id': 'your-project-id'}}}
translator = TranslatorFactory.get_translator(config)
translator.translate_document(input_path, output_path, target_lang='en')
```

## API Costs

### Azure Document Intelligence

- **Free Tier**: 500 pages/month
- **Standard**: $1.50 per 1000 pages (Read API)
- [Pricing Details](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/document-intelligence/)

### Google Cloud Translation

- **Free Tier**: $10/month credit (≈500,000 characters)
- **Standard**: $20 per 1 million characters
- **Advanced (Document)**: $80 per 1 million characters
- [Pricing Details](https://cloud.google.com/translate/pricing)

## Next Steps

1. **Integration**: Integrate with `process_documents.py`
2. **Configuration File**: Add OCR/translation config to `config.ini`
3. **Unit Tests**: Create comprehensive test suite
4. **Monitoring**: Add metrics and performance tracking
5. **Batch Processing**: Add support for batch document processing

## Support

For issues or questions:
1. Check logs in `logs/email_reader.log`
2. Enable verbose logging: `--verbose` flag
3. Review this documentation
4. Check Azure/Google Cloud console for API issues
