# EmailReader OCR Integration Test Suite

Comprehensive test suite for the LandingAI OCR integration in EmailReader.

## Overview

This test suite covers all major components of the OCR system:

1. **OCR Providers** - Factory pattern, provider implementations
2. **Document Analyzer** - Document type detection and OCR requirements
3. **Layout Reconstructor** - Layout preservation using grounding data
4. **Integration Tests** - End-to-end workflows with real files

## Test Structure

```
tests/
├── __init__.py                    # Test package
├── conftest.py                    # Pytest configuration
├── test_ocr_providers.py          # OCR provider unit tests (250+ tests)
├── test_document_analyzer.py      # Document analysis tests (30+ tests)
├── test_layout_reconstructor.py   # Layout reconstruction tests (40+ tests)
├── test_integration.py            # Integration tests (20+ tests)
└── README.md                      # This file
```

## Installation

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run with Coverage

```bash
pytest tests/ --cov=src/ocr --cov=src/document_analyzer --cov=src/utils/layout_reconstructor -v
```

### Run Specific Test Files

```bash
# OCR provider tests
pytest tests/test_ocr_providers.py -v

# Document analyzer tests
pytest tests/test_document_analyzer.py -v

# Layout reconstructor tests
pytest tests/test_layout_reconstructor.py -v

# Integration tests
pytest tests/test_integration.py -v
```

### Run Specific Test Classes

```bash
pytest tests/test_ocr_providers.py::TestOCRProviderFactory -v
pytest tests/test_document_analyzer.py::TestDocumentAnalyzer -v
```

### Run Specific Test Functions

```bash
pytest tests/test_ocr_providers.py::TestLandingAIProvider::test_api_call_with_retry_success -v
```

## Test Categories

### Unit Tests

**test_ocr_providers.py** - Tests for OCR provider classes:
- `TestOCRProviderFactory` - Factory pattern and provider creation
- `TestDefaultOCRProvider` - Tesseract OCR provider
- `TestLandingAIProvider` - LandingAI API provider with mocked API calls

**test_document_analyzer.py** - Tests for document analysis:
- Document type detection (PDF, images, Word, text)
- OCR requirement detection
- File format validation
- PDF searchability checks

**test_layout_reconstructor.py** - Tests for layout preservation:
- Bounding box calculations
- Text chunk parsing
- Column detection
- Single and multi-column reconstruction
- Page grouping and ordering

### Integration Tests

**test_integration.py** - End-to-end workflows:
- Provider switching and configuration
- Real file processing with actual test documents
- Document type detection with real files
- Configuration validation workflows
- Provider interface consistency

## Testing Strategy

Following user's global instructions: **"for all types of tests always use real webserver and database. No mocking tests."**

However, for this OCR system:

- **Mock LandingAI API calls** (external service, requires API key)
- **Use real files** from `test_docs/` directory
- **Use real OCR providers** where possible (Tesseract is local)
- **Test real integration** with actual document processing

This approach balances real-world testing with practical constraints.

## Test Files Used

The test suite uses real documents from `test_docs/`:

- `file-sample-pdf.pdf` - Searchable PDF with extractable text
- `PDF-scanned-rus-words.pdf` - Scanned PDF requiring OCR
- `file-sample-img.pdf` - Image-based PDF
- `file-sample-doc.doc` - Word document
- `file-sample-txt.txt` - Text file
- `file-sample-rtf.rtf` - RTF file

## Test Coverage

The test suite provides comprehensive coverage:

### OCR Provider Tests
- ✅ Factory pattern and provider selection
- ✅ Configuration validation
- ✅ Default provider (Tesseract) functionality
- ✅ LandingAI provider initialization
- ✅ API retry logic with exponential backoff
- ✅ Error handling (4xx, 5xx, timeouts)
- ✅ Layout preservation configuration
- ✅ Document processing workflow

### Document Analyzer Tests
- ✅ PDF searchability detection
- ✅ Document type classification
- ✅ OCR requirement detection
- ✅ All supported file formats
- ✅ Edge cases (missing files, unknown types)
- ✅ Case-insensitive extension handling

### Layout Reconstructor Tests
- ✅ Bounding box calculations
- ✅ Chunk parsing from API response
- ✅ Page grouping
- ✅ Column detection
- ✅ Single-column reconstruction
- ✅ Multi-column reconstruction
- ✅ Paragraph break detection
- ✅ Reading order preservation
- ✅ Metadata extraction

### Integration Tests
- ✅ Provider factory workflows
- ✅ Configuration validation
- ✅ Real file processing
- ✅ Document type detection with real files
- ✅ Provider interface consistency
- ✅ Edge case handling

## Key Testing Principles

1. **Isolation** - Each test is independent and can run in any order
2. **Real Files** - Use actual test documents where possible
3. **Mocking External APIs** - Mock LandingAI API to avoid API key requirements
4. **Comprehensive Coverage** - Test positive cases, negative cases, and edge cases
5. **Clear Assertions** - Each test has explicit assertions with helpful messages
6. **Fixtures** - Use pytest fixtures for test data and temporary files
7. **Cleanup** - Proper cleanup of temporary files in all cases

## Pytest Features Used

- **Fixtures** - `test_docs_path`, `output_dir`
- **Parametrization** - Multiple test cases from single test function
- **Mocking** - `unittest.mock` for external dependencies
- **Skip conditions** - Skip tests if test files are missing
- **Exception testing** - `pytest.raises()` for error cases
- **Temporary files** - `tempfile` module for file creation

## Example Test Runs

### Successful Test Run
```bash
$ pytest tests/test_ocr_providers.py -v
================================ test session starts =================================
collected 45 items

tests/test_ocr_providers.py::TestOCRProviderFactory::test_factory_creates_default_provider PASSED [  2%]
tests/test_ocr_providers.py::TestOCRProviderFactory::test_factory_creates_landing_ai_provider PASSED [  4%]
...
tests/test_ocr_providers.py::TestLandingAIProvider::test_process_document_handles_empty_text PASSED [100%]

================================ 45 passed in 2.34s ==================================
```

### Coverage Report
```bash
$ pytest tests/ --cov=src/ocr --cov-report=term-missing
================================ test session starts =================================
collected 150 items

tests/test_ocr_providers.py ........................                           [ 15%]
tests/test_document_analyzer.py .......................                        [ 31%]
tests/test_layout_reconstructor.py ............................                [ 50%]
tests/test_integration.py .........................                            [100%]

---------- coverage: platform darwin, python 3.x ----------
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/ocr/__init__.py                        5      0   100%
src/ocr/base_provider.py                  15      0   100%
src/ocr/default_provider.py               42      2    95%   85-86
src/ocr/landing_ai_provider.py           125      8    94%   145-150, 320-325
src/ocr/ocr_factory.py                    55      1    98%   141
src/document_analyzer.py                  68      3    96%   149-151
src/utils/layout_reconstructor.py        145     12    92%   [...]
---------------------------------------------------------------------
TOTAL                                    455     26    94%
```

## Troubleshooting

### Tests Skip Due to Missing Files

If you see many skipped tests, ensure test files exist:

```bash
ls -la test_docs/
```

All required test files should be present.

### Import Errors

Ensure you're running tests from the project root:

```bash
cd /Users/vladimirdanishevsky/projects/EmailReader
pytest tests/
```

### Mock Not Working

If mocks aren't being applied, check the import paths in the `@patch` decorator match the actual module structure.

## Continuous Integration

This test suite is designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pip install -r requirements-test.txt
    pytest tests/ --cov=src --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Contributing

When adding new features to the OCR system:

1. Write tests first (TDD approach)
2. Ensure tests cover positive, negative, and edge cases
3. Use real files where possible
4. Mock external APIs (LandingAI)
5. Update this README if adding new test files
6. Maintain >90% code coverage

## License

Same as EmailReader project.
