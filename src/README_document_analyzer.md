# Document Analyzer Module

The `document_analyzer.py` module provides utilities for detecting document types and determining OCR requirements for the EmailReader project.

## Features

- Automatic detection of document types (PDF, Word, images, text files)
- PDF content analysis to distinguish searchable vs. scanned PDFs
- OCR requirement determination
- Format support validation
- Comprehensive error handling

## Quick Start

```python
from src.document_analyzer import requires_ocr, get_document_type

# Check if a document needs OCR
file_path = 'path/to/document.pdf'
if requires_ocr(file_path):
    print("This document needs OCR processing")
    # Call OCR function
else:
    print("This document has extractable text")
    # Call standard text extraction
```

## API Reference

### Main Functions

#### `requires_ocr(file_path: str) -> bool`

Determine if a document requires OCR processing.

**Parameters:**
- `file_path` (str): Absolute path to the document file

**Returns:**
- `bool`: True if document requires OCR, False otherwise

**Raises:**
- `FileNotFoundError`: If file doesn't exist

**Example:**
```python
from src.document_analyzer import requires_ocr

# Searchable PDF
requires_ocr('document.pdf')  # False

# Scanned PDF
requires_ocr('scan.pdf')  # True

# Image file
requires_ocr('photo.jpg')  # True

# Word document
requires_ocr('report.docx')  # False
```

---

#### `get_document_type(file_path: str) -> DocumentType`

Classify document type based on file extension and content.

**Parameters:**
- `file_path` (str): Path to the document

**Returns:**
- `DocumentType`: One of:
  - `'pdf_searchable'` - PDF with extractable text
  - `'pdf_scanned'` - PDF without extractable text (image-based)
  - `'image'` - Image files (.jpg, .png, .tiff, etc.)
  - `'word_document'` - Word documents (.docx, .doc)
  - `'text_document'` - Text files (.txt, .rtf)
  - `'unknown'` - Unsupported or unrecognized format

**Example:**
```python
from src.document_analyzer import get_document_type

doc_type = get_document_type('scan.pdf')
# Returns: 'pdf_scanned'

doc_type = get_document_type('image.jpg')
# Returns: 'image'
```

---

#### `get_pdf_type(pdf_path: str) -> Literal['pdf_searchable', 'pdf_scanned']`

Determine if PDF is searchable or scanned.

**Parameters:**
- `pdf_path` (str): Path to PDF file

**Returns:**
- `'pdf_searchable'` if text can be extracted
- `'pdf_scanned'` if PDF is image-based

**Example:**
```python
from src.document_analyzer import get_pdf_type

pdf_type = get_pdf_type('text.pdf')
# Returns: 'pdf_searchable'

pdf_type = get_pdf_type('scan.pdf')
# Returns: 'pdf_scanned'
```

---

#### `is_image_based_pdf(pdf_path: str) -> bool`

Check if PDF is image-based (scanned document).

**Parameters:**
- `pdf_path` (str): Path to PDF file

**Returns:**
- `bool`: True if PDF is image-based/scanned, False if searchable

**Example:**
```python
from src.document_analyzer import is_image_based_pdf

is_image_based_pdf('scan.pdf')  # True
is_image_based_pdf('text.pdf')  # False
```

---

#### `is_supported_format(file_path: str) -> bool`

Check if file format is supported for processing.

**Parameters:**
- `file_path` (str): Path to file

**Returns:**
- `bool`: True if file format is supported, False otherwise

**Example:**
```python
from src.document_analyzer import is_supported_format

is_supported_format('document.pdf')  # True
is_supported_format('video.mp4')     # False
```

---

#### `get_supported_extensions() -> dict[str, list[str]]`

Get dictionary of supported file extensions by category.

**Returns:**
- `dict[str, list[str]]`: Dictionary mapping categories to extension lists

**Example:**
```python
from src.document_analyzer import get_supported_extensions

ext = get_supported_extensions()
# Returns:
# {
#     'pdf': ['.pdf'],
#     'images': ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp'],
#     'word': ['.docx', '.doc'],
#     'text': ['.txt', '.rtf']
# }
```

## Document Types

The module recognizes the following document types:

| Type | Description | OCR Required | Extensions |
|------|-------------|--------------|------------|
| `pdf_searchable` | PDF with extractable text | No | `.pdf` |
| `pdf_scanned` | Image-based PDF | Yes | `.pdf` |
| `image` | Image files | Yes | `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`, `.gif`, `.bmp` |
| `word_document` | Word documents | No | `.docx`, `.doc` |
| `text_document` | Text files | No | `.txt`, `.rtf` |
| `unknown` | Unsupported format | No | All others |

## Usage in EmailReader Workflow

### Basic Document Processing

```python
from src.document_analyzer import requires_ocr, is_supported_format
from src.pdf_image_ocr import ocr_pdf_image_to_doc

def process_document(file_path: str, output_path: str):
    """Process a document with automatic OCR detection."""

    # Step 1: Check if format is supported
    if not is_supported_format(file_path):
        raise ValueError(f"Unsupported file format: {file_path}")

    # Step 2: Determine if OCR is needed
    if requires_ocr(file_path):
        # Process with OCR
        ocr_pdf_image_to_doc(file_path, output_path)
    else:
        # Standard text extraction
        extract_text_standard(file_path, output_path)
```

### Batch Processing with Type Detection

```python
from pathlib import Path
from src.document_analyzer import get_document_type, requires_ocr

def batch_process_documents(input_dir: str):
    """Process multiple documents with type-based routing."""

    input_path = Path(input_dir)

    for file_path in input_path.glob('*'):
        if not file_path.is_file():
            continue

        # Classify document
        doc_type = get_document_type(str(file_path))

        print(f"Processing {file_path.name} (type: {doc_type})")

        # Route based on type
        if doc_type == 'pdf_scanned' or doc_type == 'image':
            process_with_ocr(str(file_path))
        elif doc_type == 'pdf_searchable':
            process_pdf_text(str(file_path))
        elif doc_type == 'word_document':
            process_word_doc(str(file_path))
        elif doc_type == 'text_document':
            process_text_file(str(file_path))
        else:
            print(f"Skipping unsupported format: {file_path.name}")
```

### PDF-Specific Analysis

```python
from src.document_analyzer import get_pdf_type, is_image_based_pdf

def analyze_pdf_collection(pdf_dir: str):
    """Analyze a collection of PDFs."""

    pdf_path = Path(pdf_dir)
    searchable_pdfs = []
    scanned_pdfs = []

    for pdf_file in pdf_path.glob('*.pdf'):
        if is_image_based_pdf(str(pdf_file)):
            scanned_pdfs.append(pdf_file)
        else:
            searchable_pdfs.append(pdf_file)

    print(f"Searchable PDFs: {len(searchable_pdfs)}")
    print(f"Scanned PDFs: {len(scanned_pdfs)}")

    return searchable_pdfs, scanned_pdfs
```

## Error Handling

The module provides comprehensive error handling:

```python
from src.document_analyzer import requires_ocr, get_document_type

# File not found
try:
    requires_ocr('/tmp/missing.pdf')
except FileNotFoundError as e:
    print(f"File not found: {e}")

# Unknown format (returns 'unknown' instead of raising error)
doc_type = get_document_type('video.mp4')
assert doc_type == 'unknown'

# PDF analysis errors (defaults to 'pdf_scanned' for safety)
# If PDF cannot be analyzed, assumes it needs OCR
```

## Testing

### Run the test suite:

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
PYTHONPATH=/Users/vladimirdanishevsky/projects/EmailReader python test_document_analyzer.py

# Run with pytest
PYTHONPATH=/Users/vladimirdanishevsky/projects/EmailReader pytest test_document_analyzer.py -v
```

### Run the demo:

```bash
source venv/bin/activate
PYTHONPATH=/Users/vladimirdanishevsky/projects/EmailReader python examples/document_analyzer_demo.py
```

### Run the module directly:

```bash
source venv/bin/activate
PYTHONPATH=/Users/vladimirdanishevsky/projects/EmailReader python src/document_analyzer.py
```

## Integration with Existing Code

The module leverages the existing `is_pdf_searchable_pypdf()` function from `src/pdf_image_ocr.py`:

```python
from src.pdf_image_ocr import is_pdf_searchable_pypdf

def get_pdf_type(pdf_path: str):
    """Use existing PDF analysis function."""
    is_searchable = is_pdf_searchable_pypdf(pdf_path)
    return 'pdf_searchable' if is_searchable else 'pdf_scanned'
```

## Logging

The module uses the EmailReader logging system:

```python
import logging

logger = logging.getLogger('EmailReader.DocumentAnalyzer')

# Logs are written to:
# - Console (INFO level and above)
# - File: logs/email_reader.log (DEBUG level and above)
```

## Dependencies

- `pypdf` - PDF text extraction (via `pdf_image_ocr.py`)
- Python 3.8+ (uses `dict[str, list[str]]` syntax)
- Standard library: `os`, `pathlib`, `logging`, `typing`

## Performance Considerations

- **PDF Analysis**: Fast for small PDFs, may take longer for large multi-page documents
- **Caching**: Consider caching results for repeated analysis of the same files
- **Error Recovery**: Defaults to OCR if PDF analysis fails (safe but slower)

## Future Enhancements

Potential improvements:

1. **Content-based detection**: Analyze actual file content, not just extensions
2. **Confidence scores**: Return confidence level for document type detection
3. **Partial OCR detection**: Detect mixed PDFs (some pages searchable, some scanned)
4. **Language detection**: Detect document language for better OCR configuration
5. **Metadata extraction**: Extract PDF metadata for better classification

## License

Part of the EmailReader project.
