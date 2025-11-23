# LandingAI OCR Integration - API Reference

## Table of Contents

- [Overview](#overview)
- [OCR Provider Factory](#ocr-provider-factory)
- [OCR Providers](#ocr-providers)
- [Document Analyzer](#document-analyzer)
- [Layout Reconstructor](#layout-reconstructor)
- [Logging](#logging)
- [Error Handling](#error-handling)
- [Type Definitions](#type-definitions)

---

## Overview

This API reference documents the OCR integration architecture, including the provider factory pattern, individual providers, and supporting utilities.

### Module Structure

```
src/
├── ocr/
│   ├── __init__.py                 # Package exports
│   ├── base_provider.py            # Abstract base class
│   ├── ocr_factory.py              # Provider factory
│   ├── default_provider.py         # Tesseract implementation
│   ├── landing_ai_provider.py      # LandingAI implementation
│   └── example_usage.py            # Usage examples
├── document_analyzer.py            # Document type detection
└── utils/
    └── layout_reconstructor.py     # Layout preservation
```

---

## OCR Provider Factory

### OCRProviderFactory

Factory class for creating OCR provider instances based on configuration.

**Module**: `src.ocr.ocr_factory`

#### Class Attributes

```python
class OCRProviderFactory:
    VALID_PROVIDERS = {'default', 'landing_ai'}
```

**`VALID_PROVIDERS`**
- **Type**: `Set[str]`
- **Description**: Set of valid provider type names
- **Values**: `{'default', 'landing_ai'}`

#### Methods

##### `get_provider(config: Dict[str, Any]) -> BaseOCRProvider`

Get OCR provider instance based on configuration.

**Parameters:**
- `config` (Dict[str, Any]): Full application configuration dictionary

**Returns:**
- `BaseOCRProvider`: OCR provider instance (DefaultOCRProvider or LandingAIOCRProvider)

**Raises:**
- `ValueError`: If provider type is invalid

**Configuration Structure:**
```python
config = {
    'ocr': {
        'provider': 'default' | 'landing_ai',
        'landing_ai': {
            'api_key': str,
            'base_url': str,  # Optional
            'model': str,     # Optional
            # ... additional options
        }
    }
}
```

**Example Usage:**

```python
from src.ocr.ocr_factory import OCRProviderFactory
from src.config_loader import load_config

# Load configuration
config = load_config('credentials/config.dev.json')

# Get provider instance
provider = OCRProviderFactory.get_provider(config)

# Use provider
provider.process_document('input.pdf', 'output.docx')
```

**Automatic Fallback:**

If LandingAI is requested but API key is missing, automatically falls back to Tesseract:

```python
config = {
    'ocr': {
        'provider': 'landing_ai',
        'landing_ai': {
            'api_key': ''  # Empty!
        }
    }
}

# Returns DefaultOCRProvider instead of raising error
provider = OCRProviderFactory.get_provider(config)
assert isinstance(provider, DefaultOCRProvider)
```

**Error Handling:**

```python
try:
    provider = OCRProviderFactory.get_provider(config)
except ValueError as e:
    print(f"Invalid provider configuration: {e}")
    # Use default fallback
    provider = DefaultOCRProvider({})
```

##### `validate_config(config: Dict[str, Any]) -> bool`

Validate OCR configuration structure.

**Parameters:**
- `config` (Dict[str, Any]): Configuration dictionary to validate

**Returns:**
- `bool`: `True` if configuration is valid, `False` otherwise

**Example Usage:**

```python
config = {
    'ocr': {
        'provider': 'landing_ai',
        'landing_ai': {
            'api_key': 'land_sk_...'
        }
    }
}

if OCRProviderFactory.validate_config(config):
    provider = OCRProviderFactory.get_provider(config)
else:
    print("Invalid configuration")
```

**Validation Rules:**

1. `ocr` section must exist
2. `provider` value must be in `VALID_PROVIDERS`
3. For `landing_ai` provider, `api_key` must be present

**Edge Cases:**

```python
# Missing OCR section (valid - uses defaults)
OCRProviderFactory.validate_config({})  # False

# Invalid provider type
OCRProviderFactory.validate_config({
    'ocr': {'provider': 'invalid'}
})  # False

# LandingAI without API key
OCRProviderFactory.validate_config({
    'ocr': {
        'provider': 'landing_ai',
        'landing_ai': {}
    }
})  # False
```

---

## OCR Providers

### BaseOCRProvider (Abstract)

Abstract base class defining the OCR provider interface.

**Module**: `src.ocr.base_provider`

#### Abstract Methods

All providers must implement these methods:

##### `process_document(ocr_file: str, out_doc_file_path: str) -> None`

Process a document using OCR.

**Parameters:**
- `ocr_file` (str): Path to input file (PDF or image)
- `out_doc_file_path` (str): Path where DOCX output should be saved

**Raises:**
- `FileNotFoundError`: If input file doesn't exist
- `ValueError`: If file format is invalid
- `RuntimeError`: If OCR processing fails

**Contract:**
- Must handle PDF and image files
- Must create DOCX output at specified path
- Must raise appropriate exceptions on error
- Should log processing details

##### `is_pdf_searchable(pdf_path: str) -> bool`

Check if a PDF contains extractable text.

**Parameters:**
- `pdf_path` (str): Path to PDF file

**Returns:**
- `bool`: `True` if PDF contains text, `False` if image-based

**Raises:**
- `FileNotFoundError`: If PDF doesn't exist
- `ValueError`: If file is not a valid PDF
- `RuntimeError`: If PDF cannot be read

---

### DefaultOCRProvider

Tesseract-based OCR provider (local processing).

**Module**: `src.ocr.default_provider`

**Inherits**: `BaseOCRProvider`

#### Constructor

```python
DefaultOCRProvider(config: dict)
```

**Parameters:**
- `config` (dict): OCR configuration dictionary (currently unused, reserved for future)

**Example:**

```python
from src.ocr.default_provider import DefaultOCRProvider

provider = DefaultOCRProvider({})
```

#### Methods

##### `process_document(ocr_file: str, out_doc_file_path: str) -> None`

Process document using Tesseract OCR.

**Implementation Details:**
- Delegates to existing `ocr_pdf_image_to_doc()` function
- Supports PDF and image files
- Uses Tesseract for text extraction
- Converts output to DOCX format

**Example:**

```python
provider = DefaultOCRProvider({})
provider.process_document(
    ocr_file='scan.pdf',
    out_doc_file_path='output.docx'
)
```

**Performance:**
- Processing time: ~3-8 seconds per page
- Memory usage: Moderate
- CPU usage: High (local processing)

##### `is_pdf_searchable(pdf_path: str) -> bool`

Check if PDF is searchable.

**Implementation Details:**
- Delegates to existing `is_pdf_searchable_pypdf()` function
- Uses PyPDF2 for text extraction test

**Example:**

```python
provider = DefaultOCRProvider({})

if provider.is_pdf_searchable('document.pdf'):
    print("No OCR needed")
else:
    print("Requires OCR")
```

---

### LandingAIOCRProvider

LandingAI cloud-based OCR provider with layout preservation.

**Module**: `src.ocr.landing_ai_provider`

**Inherits**: `BaseOCRProvider`

#### Constructor

```python
LandingAIOCRProvider(config: dict)
```

**Parameters:**
- `config` (dict): LandingAI configuration

**Configuration Schema:**

```python
config = {
    # Required
    'api_key': str,              # LandingAI API key

    # API Configuration (Optional)
    'base_url': str,             # Default: 'https://api.va.landing.ai/v1'
    'model': str,                # Default: 'dpt-2-latest'
    'split_mode': str,           # Default: 'page'
    'preserve_layout': bool,     # Default: True

    # Chunk Processing (Optional)
    'chunk_processing': {
        'use_grounding': bool,       # Default: True
        'maintain_positions': bool   # Default: True
    },

    # Retry Logic (Optional)
    'retry': {
        'max_attempts': int,     # Default: 3
        'backoff_factor': int,   # Default: 2
        'timeout': int           # Default: 30 (seconds)
    }
}
```

**Raises:**
- `ValueError`: If `api_key` is missing

**Example:**

```python
from src.ocr.landing_ai_provider import LandingAIOCRProvider

config = {
    'api_key': 'land_sk_YOUR_KEY',
    'preserve_layout': True,
    'retry': {
        'max_attempts': 5,
        'timeout': 60
    }
}

provider = LandingAIOCRProvider(config)
```

#### Instance Attributes

```python
provider.api_key              # str: API key
provider.base_url             # str: API endpoint
provider.model                # str: Model name
provider.split_mode           # str: Split mode
provider.preserve_layout      # bool: Layout preservation flag
provider.use_grounding        # bool: Use grounding data
provider.maintain_positions   # bool: Maintain spatial positions
provider.max_attempts         # int: Max retry attempts
provider.backoff_factor       # int: Exponential backoff factor
provider.timeout              # int: Request timeout (seconds)
```

#### Methods

##### `process_document(ocr_file: str, out_doc_file_path: str) -> None`

Process document using LandingAI OCR with layout preservation.

**Processing Pipeline:**
1. Validate input file
2. Call LandingAI API with retry logic
3. Extract text using layout reconstruction
4. Convert to DOCX format
5. Clean up temporary files

**Example:**

```python
provider = LandingAIOCRProvider({'api_key': 'land_sk_...'})

provider.process_document(
    ocr_file='complex_table.pdf',
    out_doc_file_path='output.docx'
)
```

**Performance:**
- Processing time: ~2-5 seconds per page
- Network-dependent
- Minimal CPU usage (cloud processing)

**Error Handling:**

```python
try:
    provider.process_document('input.pdf', 'output.docx')
except FileNotFoundError as e:
    print(f"File not found: {e}")
except ValueError as e:
    print(f"Invalid file format: {e}")
except RuntimeError as e:
    print(f"OCR processing failed: {e}")
```

##### `is_pdf_searchable(pdf_path: str) -> bool`

Check if PDF is searchable (delegates to existing implementation).

**Example:**

```python
provider = LandingAIOCRProvider({'api_key': 'land_sk_...'})

if not provider.is_pdf_searchable('scan.pdf'):
    provider.process_document('scan.pdf', 'output.docx')
```

#### Private Methods

##### `_call_api_with_retry(file_path: str) -> Dict[str, Any]`

Call LandingAI API with exponential backoff retry logic.

**Parameters:**
- `file_path` (str): Path to document file

**Returns:**
- `Dict[str, Any]`: API response dictionary

**Raises:**
- `RuntimeError`: If all retry attempts fail or client error (4xx) occurs

**Retry Behavior:**

```python
# Attempt 1: Immediate
# Attempt 2: Wait 2^0 = 1 second
# Attempt 3: Wait 2^1 = 2 seconds
# Attempt 4: Wait 2^2 = 4 seconds
# etc.
```

**Example Response:**

```python
{
    'chunks': [
        {
            'text': 'Hello World',
            'grounding': {
                'page': 0,
                'box': {
                    'left': 0.1,
                    'top': 0.2,
                    'right': 0.5,
                    'bottom': 0.3
                }
            }
        }
    ]
}
```

##### `_extract_with_positions(api_response: Dict[str, Any]) -> str`

Extract text from API response using grounding data for layout preservation.

**Parameters:**
- `api_response` (Dict[str, Any]): LandingAI API response

**Returns:**
- `str`: Extracted text with preserved layout

**Layout Preservation:**
- If `use_grounding` and `maintain_positions` are `True`: Uses layout reconstructor
- Otherwise: Simple concatenation with newlines

**Example:**

```python
api_response = {
    'chunks': [
        {'text': 'Chunk 1', 'grounding': {...}},
        {'text': 'Chunk 2', 'grounding': {...}}
    ]
}

text = provider._extract_with_positions(api_response)
# Returns text with spatial layout preserved
```

##### `_save_as_docx(text: str, output_path: str) -> None`

Save extracted text as DOCX file.

**Parameters:**
- `text` (str): Extracted text content
- `output_path` (str): Path to save DOCX file

**Raises:**
- `RuntimeError`: If DOCX file creation fails

**Process:**
1. Create temporary text file
2. Convert to DOCX using `convert_txt_to_docx()`
3. Verify output file exists
4. Clean up temporary file

---

## Document Analyzer

Utilities for determining OCR requirements and document types.

**Module**: `src.document_analyzer`

### Type Definitions

#### DocumentType

Literal type representing document classifications:

```python
from typing import Literal

DocumentType = Literal[
    'pdf_searchable',      # PDF with extractable text
    'pdf_scanned',         # PDF without extractable text (image-based)
    'image',               # Image files (.jpg, .png, .tiff, etc.)
    'word_document',       # Word documents (.docx, .doc)
    'text_document',       # Text files (.txt, .rtf)
    'unknown'              # Unsupported or unrecognized format
]
```

### Functions

#### `requires_ocr(file_path: str) -> bool`

Determine if a document requires OCR processing.

**Parameters:**
- `file_path` (str): Absolute path to the document file

**Returns:**
- `bool`: `True` if document requires OCR, `False` otherwise

**Raises:**
- `FileNotFoundError`: If file doesn't exist

**Logic:**
- Returns `True` for: `pdf_scanned`, `image`
- Returns `False` for: `pdf_searchable`, `word_document`, `text_document`, `unknown`

**Example:**

```python
from src.document_analyzer import requires_ocr

if requires_ocr('document.pdf'):
    print("OCR needed")
    provider.process_document('document.pdf', 'output.docx')
else:
    print("No OCR needed - searchable document")
```

**Use Cases:**

```python
# Searchable PDF (no OCR)
requires_ocr('report.pdf')  # False

# Scanned PDF (needs OCR)
requires_ocr('scan.pdf')  # True

# Image file (needs OCR)
requires_ocr('photo.jpg')  # True

# Word document (no OCR)
requires_ocr('document.docx')  # False
```

#### `get_document_type(file_path: str) -> DocumentType`

Classify document type based on file extension and content.

**Parameters:**
- `file_path` (str): Path to the document

**Returns:**
- `DocumentType`: Document classification

**Classification Logic:**

1. **PDF Files**: Analyzes content to determine if searchable or scanned
2. **Image Files** (`.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`, `.gif`, `.bmp`): Returns `'image'`
3. **Word Files** (`.docx`, `.doc`): Returns `'word_document'`
4. **Text Files** (`.txt`, `.rtf`): Returns `'text_document'`
5. **Other**: Returns `'unknown'`

**Example:**

```python
from src.document_analyzer import get_document_type

doc_type = get_document_type('scan.pdf')
print(doc_type)  # 'pdf_scanned'

doc_type = get_document_type('image.jpg')
print(doc_type)  # 'image'
```

**Detailed Examples:**

```python
# Searchable PDF
get_document_type('text.pdf')
# Returns: 'pdf_searchable'

# Scanned PDF
get_document_type('scan.pdf')
# Returns: 'pdf_scanned'

# Image
get_document_type('photo.png')
# Returns: 'image'

# Word document
get_document_type('report.docx')
# Returns: 'word_document'

# Unknown
get_document_type('video.mp4')
# Returns: 'unknown'
```

#### `get_pdf_type(pdf_path: str) -> Literal['pdf_searchable', 'pdf_scanned']`

Determine if PDF is searchable or scanned.

**Parameters:**
- `pdf_path` (str): Path to PDF file

**Returns:**
- `'pdf_searchable'`: If text can be extracted
- `'pdf_scanned'`: If PDF is image-based

**Implementation:**
- Uses `is_pdf_searchable_pypdf()` to detect extractable text
- Defaults to `'pdf_scanned'` on error (safer to run OCR than skip it)

**Example:**

```python
from src.document_analyzer import get_pdf_type

pdf_type = get_pdf_type('document.pdf')

if pdf_type == 'pdf_searchable':
    print("Can extract text directly")
else:
    print("Needs OCR processing")
```

#### `is_image_based_pdf(pdf_path: str) -> bool`

Check if PDF is image-based (scanned document).

**Parameters:**
- `pdf_path` (str): Path to PDF file

**Returns:**
- `bool`: `True` if PDF is image-based/scanned, `False` if searchable

**Example:**

```python
from src.document_analyzer import is_image_based_pdf

if is_image_based_pdf('scan.pdf'):
    print("This is a scanned PDF - needs OCR")
```

**Convenience Function:**

This is equivalent to:
```python
get_pdf_type(pdf_path) == 'pdf_scanned'
```

#### `get_supported_extensions() -> dict[str, list[str]]`

Get dictionary of supported file extensions by category.

**Returns:**
- `dict[str, list[str]]`: Mapping of categories to extension lists

**Example:**

```python
from src.document_analyzer import get_supported_extensions

extensions = get_supported_extensions()

print(extensions)
# {
#     'pdf': ['.pdf'],
#     'images': ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.gif', '.bmp'],
#     'word': ['.docx', '.doc'],
#     'text': ['.txt', '.rtf']
# }

# Check if extension is an image
if '.png' in extensions['images']:
    print("PNG is supported")
```

#### `is_supported_format(file_path: str) -> bool`

Check if file format is supported for processing.

**Parameters:**
- `file_path` (str): Path to file

**Returns:**
- `bool`: `True` if file format is supported, `False` otherwise

**Example:**

```python
from src.document_analyzer import is_supported_format

# Supported formats
is_supported_format('document.pdf')   # True
is_supported_format('image.jpg')      # True
is_supported_format('text.docx')      # True

# Unsupported formats
is_supported_format('video.mp4')      # False
is_supported_format('audio.mp3')      # False
```

**Use Case:**

```python
if not is_supported_format(file_path):
    raise ValueError(f"Unsupported file format: {file_path}")
```

---

## Layout Reconstructor

Utilities for preserving document layout using LandingAI grounding data.

**Module**: `src.utils.layout_reconstructor`

### Data Classes

#### BoundingBox

Represents a bounding box with normalized coordinates (0-1).

```python
@dataclass
class BoundingBox:
    left: float
    top: float
    right: float
    bottom: float
```

**Properties:**

##### `width -> float`
Calculate bounding box width.

```python
box = BoundingBox(left=0.1, top=0.2, right=0.5, bottom=0.6)
print(box.width)  # 0.4
```

##### `height -> float`
Calculate bounding box height.

```python
print(box.height)  # 0.4
```

##### `center_x -> float`
Calculate horizontal center coordinate.

```python
print(box.center_x)  # 0.3
```

##### `center_y -> float`
Calculate vertical center coordinate.

```python
print(box.center_y)  # 0.4
```

#### TextChunk

Represents a text chunk with spatial information.

```python
@dataclass
class TextChunk:
    text: str
    page: int
    box: BoundingBox
```

**Example:**

```python
chunk = TextChunk(
    text="Hello World",
    page=0,
    box=BoundingBox(left=0.1, top=0.2, right=0.5, bottom=0.3)
)
```

### Functions

#### `reconstruct_layout(chunks: List[Dict[str, Any]]) -> str`

Reconstruct document layout using grounding data.

**Parameters:**
- `chunks` (List[Dict[str, Any]]): List of chunks from LandingAI API response

**Returns:**
- `str`: Text with preserved layout structure

**Process:**
1. Parse chunks into TextChunk objects
2. Group chunks by page number
3. For each page:
   - Sort chunks by vertical position
   - Detect column structure
   - Reconstruct layout
4. Combine pages with page breaks

**Example:**

```python
from src.utils.layout_reconstructor import reconstruct_layout

api_response = {
    'chunks': [
        {
            'text': 'Chapter 1',
            'grounding': {
                'page': 0,
                'box': {'left': 0.1, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
            }
        },
        {
            'text': 'Introduction text...',
            'grounding': {
                'page': 0,
                'box': {'left': 0.1, 'top': 0.25, 'right': 0.9, 'bottom': 0.35}
            }
        }
    ]
}

text = reconstruct_layout(api_response['chunks'])
print(text)
# Chapter 1
#
# Introduction text...
```

**Layout Features:**

1. **Vertical Ordering**: Chunks sorted top-to-bottom
2. **Paragraph Breaks**: Detected based on vertical gaps (>5% page height)
3. **Column Detection**: Multi-column layouts identified and preserved
4. **Page Breaks**: Inserted between pages with `--- Page Break ---`

**Multi-Column Example:**

```python
# Two-column layout
text = reconstruct_layout(chunks)
# Returns:
# Left column content
#
# [Column Break]
#
# Right column content
```

#### `apply_grounding_to_output(chunks: List[Dict[str, Any]]) -> Dict[str, Any]`

Apply grounding data to enhance output structure (metadata extraction).

**Parameters:**
- `chunks` (List[Dict[str, Any]]): API response chunks

**Returns:**
- `Dict[str, Any]`: Dictionary with structure metadata

**Response Structure:**

```python
{
    'total_pages': int,
    'total_chunks': int,
    'pages': {
        page_num: {
            'chunks': int,
            'columns': int,
            'has_multi_column': bool
        }
    }
}
```

**Example:**

```python
from src.utils.layout_reconstructor import apply_grounding_to_output

metadata = apply_grounding_to_output(chunks)

print(metadata)
# {
#     'total_pages': 3,
#     'total_chunks': 42,
#     'pages': {
#         0: {'chunks': 15, 'columns': 1, 'has_multi_column': False},
#         1: {'chunks': 18, 'columns': 2, 'has_multi_column': True},
#         2: {'chunks': 9, 'columns': 1, 'has_multi_column': False}
#     }
# }

# Use metadata for analytics
for page_num, page_info in metadata['pages'].items():
    if page_info['has_multi_column']:
        print(f"Page {page_num} has {page_info['columns']} columns")
```

### Algorithm Details

#### Column Detection

Detects columns based on horizontal positioning:

```python
COLUMN_GAP_THRESHOLD = 0.2  # 20% of page width

# If horizontal gap between chunks > threshold, new column
if abs(curr_x - prev_x) > COLUMN_GAP_THRESHOLD:
    start_new_column()
```

#### Paragraph Detection

Detects paragraph breaks based on vertical spacing:

```python
PARAGRAPH_GAP_THRESHOLD = 0.05  # 5% of page height

# If vertical gap > threshold, insert blank line
if vertical_gap > PARAGRAPH_GAP_THRESHOLD:
    insert_paragraph_break()
```

---

## Logging

### Available Loggers

The OCR integration uses hierarchical logging with the following logger names:

#### `EmailReader.OCR.Factory`
Provider selection and factory operations.

**Log Events:**
- Provider creation
- Configuration validation
- Fallback decisions

**Example Logs:**
```
INFO - Creating OCR provider: landing_ai
DEBUG - OCR configuration: {'provider': 'landing_ai', ...}
WARNING - LandingAI provider requested but API key not found. Falling back to default.
```

#### `EmailReader.OCR.Default`
Tesseract provider operations.

**Log Events:**
- Document processing
- OCR extraction
- Error handling

**Example Logs:**
```
INFO - Creating default Tesseract OCR provider
DEBUG - Processing document with Tesseract: input.pdf
INFO - Tesseract OCR completed: output.docx
```

#### `EmailReader.OCR.LandingAI`
LandingAI provider operations.

**Log Events:**
- API calls
- Retry attempts
- Layout processing
- Performance metrics

**Example Logs:**
```
INFO - Initialized LandingAIOCRProvider (model: dpt-2-latest, layout: True)
DEBUG - LandingAI API call attempt 1/3
INFO - LandingAI API call successful (attempt 1)
INFO - Received 42 chunks from API
INFO - LandingAI OCR completed in 3.45s: output.docx (15234 characters)
```

#### `EmailReader.DocumentAnalyzer`
Document type detection.

**Log Events:**
- File type detection
- OCR requirement determination
- PDF searchability checks

**Example Logs:**
```
DEBUG - Detected image file: photo.jpg
DEBUG - PDF type for scan.pdf: pdf_scanned
DEBUG - OCR required for scan.pdf: True (type: pdf_scanned)
```

#### `EmailReader.LayoutReconstructor`
Layout preservation operations.

**Log Events:**
- Layout reconstruction
- Column detection
- Page processing

**Example Logs:**
```
INFO - Reconstructing layout from 42 chunks
DEBUG - Detected 2 columns on page
DEBUG - Column break detected: prev_x=0.25, curr_x=0.65, gap=0.40
INFO - Layout reconstruction complete (3 pages, 15234 characters)
```

### Helper Functions

#### `get_logger(name: str) -> logging.Logger`

Get a logger instance for a given module.

**Parameters:**
- `name` (str): Logger name (e.g., `'EmailReader.OCR.LandingAI'`)

**Returns:**
- `logging.Logger`: Logger instance

**Example:**

```python
from src.ocr.landing_ai_provider import get_logger

logger = get_logger('EmailReader.OCR.MyModule')
logger.info("Processing started")
logger.debug("Debug information")
logger.error("Error occurred", exc_info=True)
```

### Log Configuration

**Default Configuration:**

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/email_reader.log'),
        logging.StreamHandler()
    ]
)
```

**Debug Mode:**

```python
# Enable debug logging
logging.getLogger('EmailReader.OCR').setLevel(logging.DEBUG)

# Enable only for specific provider
logging.getLogger('EmailReader.OCR.LandingAI').setLevel(logging.DEBUG)
```

### Filtering Logs

**View OCR-related logs only:**

```bash
tail -f logs/email_reader.log | grep "OCR"
```

**View LandingAI logs only:**

```bash
tail -f logs/email_reader.log | grep "LandingAI"
```

**View errors only:**

```bash
tail -f logs/email_reader.log | grep "ERROR"
```

---

## Error Handling

### Exception Hierarchy

```
Exception
├── FileNotFoundError    # Input file missing
├── ValueError           # Invalid configuration or file format
└── RuntimeError         # Processing failures
```

### Error Scenarios

#### File Not Found

```python
from src.ocr.ocr_factory import OCRProviderFactory

try:
    provider.process_document('nonexistent.pdf', 'output.docx')
except FileNotFoundError as e:
    logger.error(f"Input file not found: {e}")
    # Handle missing file
```

#### Invalid Configuration

```python
try:
    provider = OCRProviderFactory.get_provider({
        'ocr': {'provider': 'invalid'}
    })
except ValueError as e:
    logger.error(f"Invalid provider: {e}")
    # Use default fallback
    provider = DefaultOCRProvider({})
```

#### API Errors

```python
try:
    provider.process_document('input.pdf', 'output.docx')
except RuntimeError as e:
    logger.error(f"OCR processing failed: {e}")
    # Try fallback provider or retry
```

### Retry Logic

LandingAI provider implements exponential backoff retry:

```python
# Configuration
config = {
    'api_key': 'land_sk_...',
    'retry': {
        'max_attempts': 5,
        'backoff_factor': 2,
        'timeout': 30
    }
}

# Automatically retries on:
# - Timeout (requests.exceptions.Timeout)
# - Connection error (requests.exceptions.ConnectionError)
# - Server errors (5xx status codes)

# Does NOT retry on:
# - Client errors (4xx status codes)
# - Invalid API key (401)
# - Malformed request (400)
```

### Fallback Strategy

**Automatic Fallback Example:**

```python
from src.ocr.ocr_factory import OCRProviderFactory

# Request LandingAI but missing API key
config = {
    'ocr': {
        'provider': 'landing_ai',
        'landing_ai': {'api_key': ''}
    }
}

# Automatically falls back to Tesseract
provider = OCRProviderFactory.get_provider(config)
assert isinstance(provider, DefaultOCRProvider)
```

**Manual Fallback Example:**

```python
primary_provider = LandingAIOCRProvider({'api_key': 'land_sk_...'})
fallback_provider = DefaultOCRProvider({})

try:
    primary_provider.process_document('input.pdf', 'output.docx')
except RuntimeError as e:
    logger.warning(f"Primary provider failed: {e}. Using fallback.")
    fallback_provider.process_document('input.pdf', 'output.docx')
```

---

## Type Definitions

### Common Types

```python
from typing import Dict, List, Any, Literal

# Configuration dictionary
ConfigDict = Dict[str, Any]

# Document type literal
DocumentType = Literal[
    'pdf_searchable',
    'pdf_scanned',
    'image',
    'word_document',
    'text_document',
    'unknown'
]

# API response chunk
Chunk = Dict[str, Any]  # {'text': str, 'grounding': {...}}

# Grounding data
Grounding = Dict[str, Any]  # {'page': int, 'box': {...}}

# Bounding box data
BoxData = Dict[str, float]  # {'left': float, 'top': float, ...}
```

### Provider Types

```python
from src.ocr.base_provider import BaseOCRProvider
from src.ocr.default_provider import DefaultOCRProvider
from src.ocr.landing_ai_provider import LandingAIOCRProvider

# Type annotation for provider instances
Provider = BaseOCRProvider  # Union of all providers
```

---

## Summary

### Quick Reference

**Create Provider:**
```python
from src.ocr.ocr_factory import OCRProviderFactory
config = load_config('config.json')
provider = OCRProviderFactory.get_provider(config)
```

**Process Document:**
```python
provider.process_document('input.pdf', 'output.docx')
```

**Check if OCR Needed:**
```python
from src.document_analyzer import requires_ocr
if requires_ocr('document.pdf'):
    provider.process_document('document.pdf', 'output.docx')
```

**Layout Reconstruction:**
```python
from src.utils.layout_reconstructor import reconstruct_layout
text = reconstruct_layout(api_response['chunks'])
```

---

**Last Updated**: November 15, 2025
**Version**: 1.0.0
