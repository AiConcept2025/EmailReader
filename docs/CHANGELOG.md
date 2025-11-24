# Changelog - LandingAI OCR Integration

All notable changes to the EmailReader OCR system are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-11-15

### Added

#### OCR Provider Architecture

- **OCR Provider Factory Pattern** (`src/ocr/ocr_factory.py`)
  - Configuration-driven provider selection
  - Automatic fallback to Tesseract when LandingAI unavailable
  - Provider validation with detailed error messages
  - Support for extensibility (easy to add new providers)

- **Base OCR Provider Interface** (`src/ocr/base_provider.py`)
  - Abstract base class defining OCR provider contract
  - Methods: `process_document()`, `is_pdf_searchable()`
  - Ensures consistency across all provider implementations

- **Default OCR Provider** (`src/ocr/default_provider.py`)
  - Wraps existing Tesseract OCR functionality
  - Implements BaseOCRProvider interface
  - Maintains backward compatibility with legacy code
  - No dependencies on external APIs

#### LandingAI Integration

- **LandingAI OCR Provider** (`src/ocr/landing_ai_provider.py`)
  - Integration with LandingAI ADE Parse API
  - Cloud-based OCR with superior accuracy
  - Advanced layout preservation using grounding data
  - Configurable retry logic with exponential backoff
  - HTTP timeout configuration
  - Detailed logging and performance metrics

- **API Features**
  - Document splitting modes (page/chunk)
  - Layout preservation flag
  - Custom model selection
  - Grounding data for spatial positioning
  - Multi-page support with page break markers

#### Document Analysis

- **Document Analyzer** (`src/document_analyzer.py`)
  - Intelligent document type detection
  - OCR requirement determination
  - PDF searchability detection (searchable vs scanned)
  - Support for multiple file formats (PDF, images, Word, text)
  - File format validation

- **Document Types Supported**
  - `pdf_searchable`: PDFs with extractable text
  - `pdf_scanned`: Image-based PDFs requiring OCR
  - `image`: Image files (.jpg, .png, .tiff, .gif, .bmp)
  - `word_document`: Word files (.docx, .doc)
  - `text_document`: Text files (.txt, .rtf)
  - `unknown`: Unsupported formats

#### Layout Preservation

- **Layout Reconstructor** (`src/utils/layout_reconstructor.py`)
  - Uses LandingAI grounding data for spatial positioning
  - Multi-column layout detection
  - Vertical spacing preservation
  - Paragraph break detection
  - Page break insertion
  - Column detection algorithm (20% page width threshold)
  - Reading order optimization (top-to-bottom, left-to-right)

- **Data Structures**
  - `BoundingBox`: Normalized coordinates (0-1) with computed properties
  - `TextChunk`: Text with spatial information and page number
  - Structure metadata extraction

#### Configuration System

- **OCR Configuration Schema**
  - Provider selection (`default` or `landing_ai`)
  - LandingAI-specific settings:
    - API key authentication
    - Base URL configuration
    - Model selection
    - Split mode
    - Layout preservation flags
    - Chunk processing options
    - Retry configuration
  - A/B testing flags (for future use)

- **Configuration Files**
  - `credentials/config.dev.json`: Development configuration
  - `credentials/config.prod.json`: Production configuration
  - `credentials/config.landing_ai.example.json`: Example template
  - `credentials/config.template.json`: Updated with OCR section

#### Logging System

- **Hierarchical Logging**
  - `EmailReader.OCR.Factory`: Provider selection and factory operations
  - `EmailReader.OCR.Default`: Tesseract provider operations
  - `EmailReader.OCR.LandingAI`: LandingAI provider operations
  - `EmailReader.DocumentAnalyzer`: Document analysis operations
  - `EmailReader.LayoutReconstructor`: Layout reconstruction operations

- **Log Levels**
  - `DEBUG`: Detailed processing information
  - `INFO`: High-level operation status
  - `WARNING`: Fallback activations and minor issues
  - `ERROR`: Processing failures with stack traces

- **Performance Metrics**
  - Processing duration tracking
  - Character count logging
  - Page count logging
  - API call attempt tracking
  - Retry attempt logging

#### Testing Infrastructure

- **Unit Tests** (`tests/`)
  - `test_ocr_providers.py`: Provider factory and individual provider tests
  - `test_document_analyzer.py`: Document analysis functionality
  - `test_landing_ai_integration.py`: End-to-end LandingAI integration
  - `test_layout_reconstructor.py`: Layout reconstruction algorithms

- **Test Coverage**
  - 107 total tests passing
  - Provider creation and configuration
  - Document type detection
  - OCR requirement determination
  - Layout reconstruction
  - Multi-column detection
  - Error handling scenarios
  - Fallback mechanism validation

- **Test Files**
  - `test_docs/file-sample-pdf.pdf`: Searchable PDF
  - `test_docs/PDF-scanned-rus-words.pdf`: Scanned PDF
  - `test_docs/file-sample-img.pdf`: Image-based PDF
  - Additional test files for various scenarios

#### Documentation

- **Comprehensive Documentation** (`docs/`)
  - `MIGRATION_GUIDE.md`: Step-by-step migration instructions
  - `API_REFERENCE.md`: Complete API documentation
  - `ARCHITECTURE.md`: System design and architecture
  - `QUICK_START.md`: 5-minute getting started guide
  - `CHANGELOG.md`: This file

- **Code Examples**
  - `src/ocr/example_usage.py`: Usage examples
  - Inline code documentation
  - Docstrings for all public functions and classes

### Changed

#### Refactored Code

- **process_documents.py**
  - Refactored to use `OCRProviderFactory` instead of direct OCR calls
  - Improved error handling
  - Added document analysis integration
  - Enhanced logging

- **process_files_for_translation.py**
  - Updated to use provider factory pattern
  - Added OCR requirement checking
  - Improved processing pipeline
  - Better error messages

- **Configuration Structure**
  - Extended with `ocr` section
  - Backward compatible (defaults to Tesseract if missing)
  - Support for multiple environments (dev/prod)
  - Validation of configuration structure

#### Enhanced Error Handling

- **Improved Exception Messages**
  - More descriptive error messages
  - Context information in exceptions
  - Stack traces in debug mode
  - Graceful degradation on failures

- **Retry Logic**
  - Exponential backoff for API calls
  - Configurable max attempts
  - Configurable timeout
  - Automatic retry on transient errors (timeouts, connection errors)
  - No retry on permanent errors (4xx status codes)

#### Performance Improvements

- **Document Pre-screening**
  - Skip OCR for searchable PDFs
  - Reduce unnecessary API calls
  - Faster processing for text-based documents

- **API Optimization**
  - Configurable timeout values
  - Efficient retry mechanism
  - Connection reuse

### Fixed

#### Document Processing

- **PDF Type Detection**
  - Improved detection of searchable vs scanned PDFs
  - Better handling of mixed-content PDFs
  - More accurate text extraction testing

- **Error Handling**
  - Fixed error propagation in provider chain
  - Improved cleanup of temporary files
  - Better handling of malformed responses

#### Layout Reconstruction

- **Column Detection**
  - Fixed false positives in single-column documents
  - Improved threshold calculation
  - Better handling of irregular layouts

- **Spacing Preservation**
  - Fixed paragraph break detection
  - Improved vertical spacing calculation
  - Better handling of edge cases

### Security

#### Credential Management

- **API Key Handling**
  - API keys stored in configuration files (not in code)
  - Configuration files excluded from version control (.gitignore)
  - Clear documentation on secure key storage
  - Warning messages for missing keys

- **Secure Defaults**
  - HTTPS for all API communication
  - No API key logging
  - Automatic fallback prevents exposure of missing credentials

### Deprecated

#### Legacy Functions

- **Direct OCR Function Calls** (Soft Deprecation)
  - Direct imports of `ocr_pdf_image_to_doc` still work
  - Recommended to use provider factory pattern instead
  - Legacy code maintained for backward compatibility
  - Migration guide provided for updating code

**Note**: These are not removed, just discouraged. Use:
```python
# New (Recommended)
provider = OCRProviderFactory.get_provider(config)
provider.process_document(input_file, output_file)

# Old (Still works, but not recommended)
ocr_pdf_image_to_doc(input_file, output_file)
```

### Migration Required

#### Configuration Updates

**Optional Migration**: To use LandingAI, add OCR configuration:

```json
{
  "ocr": {
    "provider": "landing_ai",
    "landing_ai": {
      "api_key": "land_sk_YOUR_KEY"
    }
  }
}
```

**No migration required** to continue using Tesseract (default behavior unchanged).

#### Code Updates

**Optional**: Modernize code to use provider factory:

```python
# Before
from src.pdf_image_ocr import ocr_pdf_image_to_doc
ocr_pdf_image_to_doc(input_file, output_file)

# After
from src.ocr.ocr_factory import OCRProviderFactory
provider = OCRProviderFactory.get_provider(config)
provider.process_document(input_file, output_file)
```

**Backward Compatibility**: Old code continues to work without changes.

---

## [0.9.0] - 2025-11-14 (Pre-LandingAI)

### Baseline

This version represents the state before LandingAI integration:

- Tesseract OCR as the only OCR engine
- Direct function calls for OCR processing
- Basic PDF searchability detection
- Simple document processing pipeline
- Limited error handling
- No layout preservation
- No provider abstraction

---

## Implementation Details

### Version 1.0.0 Statistics

- **Files Added**: 12
- **Files Modified**: 6
- **Lines of Code Added**: ~3,500
- **Tests Added**: 107
- **Documentation Pages**: 5 (50+ pages total)

### Components Added

1. **OCR Module** (`src/ocr/`)
   - `__init__.py` - Package initialization
   - `base_provider.py` - Abstract base class (57 lines)
   - `default_provider.py` - Tesseract implementation (142 lines)
   - `landing_ai_provider.py` - LandingAI implementation (358 lines)
   - `ocr_factory.py` - Provider factory (197 lines)
   - `example_usage.py` - Usage examples (150 lines)

2. **Document Analysis** (`src/`)
   - `document_analyzer.py` - Document type detection (257 lines)

3. **Utilities** (`src/utils/`)
   - `layout_reconstructor.py` - Layout preservation (345 lines)

4. **Configuration**
   - Extended configuration schema
   - Example configurations
   - Template files

5. **Tests** (`tests/`)
   - Comprehensive test suite
   - Unit tests
   - Integration tests
   - Test fixtures

6. **Documentation** (`docs/`)
   - Migration guide (600+ lines)
   - API reference (1000+ lines)
   - Architecture documentation (800+ lines)
   - Quick start guide (500+ lines)
   - Changelog (this file)

### Breaking Changes

**None**. This release is 100% backward compatible.

### Known Issues

None at release time.

### Upgrade Path

1. **No changes required** for existing deployments
2. **Optional**: Add LandingAI configuration to use new provider
3. **Recommended**: Run test suite to verify integration
4. **Optional**: Update code to use provider factory pattern

---

## Future Releases

### Planned for [1.1.0]

- Google Vision API provider
- Azure Form Recognizer provider
- AWS Textract provider
- Batch processing optimization
- Result caching system
- Enhanced A/B testing framework

### Planned for [1.2.0]

- Table structure detection
- Reading order optimization
- Font and style preservation
- Image extraction with positioning
- Advanced metrics and monitoring

### Planned for [2.0.0]

- ML-based layout analysis
- Custom model training support
- Real-time OCR streaming
- WebSocket API support
- Distributed processing

---

## Version History Summary

| Version | Release Date | Key Features | Breaking Changes |
|---------|--------------|--------------|------------------|
| 1.0.0   | 2025-11-15  | LandingAI integration, provider pattern, layout preservation | None |
| 0.9.0   | 2025-11-14  | Baseline (Tesseract only) | N/A |

---

## Contributors

- EmailReader Development Team
- LandingAI Integration Team

---

## Support

For issues, questions, or feature requests:

1. Check documentation in `docs/`
2. Review test files in `tests/` for examples
3. Check logs in `logs/email_reader.log`
4. See `docs/MIGRATION_GUIDE.md` for troubleshooting

---

## License

[Your License Here]

---

**Changelog maintained by**: EmailReader Development Team
**Last Updated**: November 15, 2025
**Current Version**: 1.0.0
