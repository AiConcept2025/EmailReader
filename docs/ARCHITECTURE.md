# LandingAI OCR Integration - Architecture

## Table of Contents

- [Overview](#overview)
- [Provider Pattern](#provider-pattern)
- [Component Details](#component-details)
- [Integration Points](#integration-points)
- [Testing Strategy](#testing-strategy)
- [Future Enhancements](#future-enhancements)

---

## Overview

### High-Level Architecture

The LandingAI OCR integration implements a **provider pattern** architecture that allows pluggable OCR engines while maintaining a consistent interface for document processing.

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (process_documents.py, process_files_for_translation.py)   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Configuration Layer                        │
│                (config.dev.json, config.prod.json)          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 OCRProviderFactory                           │
│        (Selects provider based on configuration)            │
└───────────┬──────────────────────────┬──────────────────────┘
            │                          │
            ▼                          ▼
┌────────────────────┐      ┌──────────────────────┐
│ DefaultOCRProvider │      │ LandingAIOCRProvider │
│   (Tesseract)      │      │   (Cloud API)        │
└────────────────────┘      └──────────────────────┘
            │                          │
            │                          ▼
            │               ┌──────────────────────┐
            │               │ Layout Reconstructor │
            │               │ (Grounding Data)     │
            │               └──────────────────────┘
            │                          │
            ▼                          ▼
┌─────────────────────────────────────────────────────────────┐
│               Document Analyzer                              │
│         (Determines OCR requirements)                        │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Output Layer                                │
│              (DOCX files, logs)                              │
└─────────────────────────────────────────────────────────────┘
```

### Component Relationships

```
┌──────────────────────┐
│  BaseOCRProvider     │  (Abstract)
│  (Interface)         │
└──────────┬───────────┘
           │
           │ implements
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌──────────┐  ┌──────────────┐
│ Default  │  │ LandingAI    │
│ Provider │  │ Provider     │
└──────────┘  └───────┬──────┘
                      │
                      │ uses
                      ▼
              ┌───────────────┐
              │ Layout        │
              │ Reconstructor │
              └───────────────┘

┌──────────────────────┐
│ OCRProviderFactory   │
│ (Creates providers)  │
└──────────┬───────────┘
           │
           │ creates
           ▼
      [Providers]

┌──────────────────────┐
│ Document Analyzer    │
│ (Determines OCR need)│
└──────────────────────┘
```

### Data Flow

**Document Processing Flow:**

```
1. Input File (PDF/Image)
   │
   ▼
2. Document Analyzer
   ├─ Check file type
   ├─ Analyze PDF content (if PDF)
   └─ Determine if OCR needed
   │
   ▼
3. OCR Provider Factory
   ├─ Load configuration
   ├─ Select provider
   └─ Create provider instance
   │
   ▼
4. OCR Provider (Default or LandingAI)
   ├─ Process document
   ├─ Extract text
   └─ (LandingAI: Preserve layout)
   │
   ▼
5. Layout Reconstructor (LandingAI only)
   ├─ Parse grounding data
   ├─ Detect columns
   ├─ Preserve structure
   └─ Reconstruct layout
   │
   ▼
6. DOCX Conversion
   ├─ Create DOCX from text
   └─ Save output file
   │
   ▼
7. Output DOCX File
```

---

## Provider Pattern

### Why Provider Pattern?

The provider pattern was chosen for this architecture for several key reasons:

#### 1. **Extensibility**

New OCR engines can be added without modifying existing code:

```python
# Adding a new provider (e.g., Google Vision API)
class GoogleVisionProvider(BaseOCRProvider):
    def process_document(self, ocr_file, out_doc_file_path):
        # Implementation
        pass

# Register in factory
class OCRProviderFactory:
    VALID_PROVIDERS = {'default', 'landing_ai', 'google_vision'}
```

#### 2. **Configuration-Driven**

Provider selection happens at runtime based on configuration:

```json
// Development: Use free Tesseract
{
  "ocr": {"provider": "default"}
}

// Production: Use premium LandingAI
{
  "ocr": {"provider": "landing_ai"}
}
```

No code changes required to switch providers.

#### 3. **Testability**

Mock providers can be easily created for testing:

```python
class MockOCRProvider(BaseOCRProvider):
    def process_document(self, ocr_file, out_doc_file_path):
        # Mock implementation for testing
        with open(out_doc_file_path, 'w') as f:
            f.write("Mock OCR output")
```

#### 4. **Separation of Concerns**

Each provider handles its own:
- API communication
- Error handling
- Retry logic
- Output formatting

#### 5. **Fallback Mechanism**

Automatic fallback when primary provider is unavailable:

```python
# Configuration requests LandingAI
config = {'ocr': {'provider': 'landing_ai', 'landing_ai': {}}}

# Factory detects missing API key, falls back to Tesseract
provider = OCRProviderFactory.get_provider(config)
# Returns: DefaultOCRProvider
```

### Benefits and Trade-offs

**Benefits:**
- Clean abstraction
- Easy to extend
- Configuration-driven
- Testable
- Maintainable

**Trade-offs:**
- Slight performance overhead (negligible)
- Additional abstraction layer
- More files to maintain

**Alternative Approaches Considered:**

1. **Direct Implementation**: Call OCR APIs directly
   - ❌ Hard to switch providers
   - ❌ Difficult to test
   - ❌ Code duplication

2. **Strategy Pattern**: Similar to provider pattern
   - ✅ Same benefits
   - ⚖️ More complex for simple use case

3. **Plugin System**: Dynamic loading of providers
   - ✅ Most flexible
   - ❌ Over-engineering for current needs

**Conclusion**: Provider pattern offers the best balance of simplicity and flexibility.

### Extension Points

The architecture provides several extension points:

#### 1. **New OCR Providers**

```python
# Extend BaseOCRProvider
class NewOCRProvider(BaseOCRProvider):
    def __init__(self, config: dict):
        self.config = config
        # Initialize provider

    def process_document(self, ocr_file: str, out_doc_file_path: str):
        # Implement OCR processing
        pass

    def is_pdf_searchable(self, pdf_path: str) -> bool:
        # Implement PDF check
        pass
```

#### 2. **Custom Document Analyzers**

```python
# Add new document types
DocumentType = Literal[
    'pdf_searchable',
    'pdf_scanned',
    'image',
    'word_document',
    'text_document',
    'spreadsheet',  # New type
    'presentation'  # New type
]
```

#### 3. **Layout Algorithms**

```python
# Custom layout reconstruction
def reconstruct_layout_advanced(chunks):
    # Advanced algorithm with ML-based column detection
    pass
```

#### 4. **Configuration Sources**

```python
# Load config from database, API, etc.
class ConfigLoader:
    @staticmethod
    def load_from_database():
        # Load from DB
        pass
```

---

## Component Details

### OCR Provider Factory

**Responsibility:**
- Create OCR provider instances based on configuration
- Validate configuration
- Handle fallback logic

**Design Decisions:**

1. **Static Methods**: Factory methods are static (no state needed)
2. **Validation**: Separate validation method for configuration checking
3. **Logging**: Detailed logging for debugging provider selection
4. **Fallback**: Automatic fallback when API key missing

**Key Code:**

```python
class OCRProviderFactory:
    VALID_PROVIDERS = {'default', 'landing_ai'}

    @staticmethod
    def get_provider(config: Dict[str, Any]) -> BaseOCRProvider:
        provider_type = config.get('ocr', {}).get('provider', 'default')

        if provider_type == 'landing_ai':
            api_key = config.get('ocr', {}).get('landing_ai', {}).get('api_key')
            if not api_key:
                # Automatic fallback
                return DefaultOCRProvider({})
            return LandingAIOCRProvider(config['ocr']['landing_ai'])

        return DefaultOCRProvider(config.get('ocr', {}))
```

### Document Analyzer

**Purpose:**
- Determine if documents need OCR
- Classify document types
- Optimize processing pipeline

**Detection Logic:**

```python
def requires_ocr(file_path: str) -> bool:
    doc_type = get_document_type(file_path)

    # Only scanned PDFs and images need OCR
    return doc_type in ('pdf_scanned', 'image')
```

**Benefits:**
- Avoids unnecessary OCR on searchable PDFs
- Faster processing
- Cost savings (API calls)

**Integration:**

```python
# Before processing
if requires_ocr(file_path):
    provider.process_document(file_path, output_path)
else:
    # Direct extraction or skip OCR
    extract_text_directly(file_path, output_path)
```

### Layout Reconstructor

**Grounding Data Usage:**

LandingAI API returns spatial positioning for each text chunk:

```json
{
  "text": "Hello World",
  "grounding": {
    "page": 0,
    "box": {
      "left": 0.1,    // Normalized coordinates (0-1)
      "top": 0.2,
      "right": 0.5,
      "bottom": 0.3
    }
  }
}
```

**Column Detection Algorithm:**

```python
def _detect_columns(chunks: List[TextChunk]) -> List[List[TextChunk]]:
    # Sort by horizontal position
    h_sorted = sorted(chunks, key=lambda c: c.box.center_x)

    columns = []
    current_column = [h_sorted[0]]

    COLUMN_GAP_THRESHOLD = 0.2  # 20% of page width

    for chunk in h_sorted[1:]:
        # Calculate horizontal gap
        gap = abs(chunk.box.center_x - current_column[0].box.center_x)

        if gap > COLUMN_GAP_THRESHOLD:
            # New column detected
            columns.append(current_column)
            current_column = [chunk]
        else:
            current_column.append(chunk)

    columns.append(current_column)
    return columns
```

**Why This Approach:**

1. **Spatial Awareness**: Uses actual positions instead of text patterns
2. **Robust**: Works with any language or character set
3. **Configurable**: Threshold can be adjusted
4. **Simple**: Easy to understand and debug

**Multi-Page Handling:**

```python
def reconstruct_layout(chunks: List[Dict[str, Any]]) -> str:
    # Group by page
    pages = _group_by_page(text_chunks)

    # Process each page
    page_texts = []
    for page_num in sorted(pages.keys()):
        page_text = _reconstruct_page(pages[page_num])
        page_texts.append(page_text)

    # Combine with page breaks
    return '\n\n--- Page Break ---\n\n'.join(page_texts)
```

---

## Integration Points

### How Providers Integrate with Existing Code

**Before Integration (Original Code):**

```python
# Direct call to OCR function
from src.pdf_image_ocr import ocr_pdf_image_to_doc

def process_document(file_path, output_path):
    ocr_pdf_image_to_doc(file_path, output_path)
```

**After Integration (Provider Pattern):**

```python
# Use provider factory
from src.ocr.ocr_factory import OCRProviderFactory

def process_document(file_path, output_path, config):
    provider = OCRProviderFactory.get_provider(config)
    provider.process_document(file_path, output_path)
```

**Migration Path:**

1. Create `BaseOCRProvider` interface
2. Wrap existing `ocr_pdf_image_to_doc` in `DefaultOCRProvider`
3. Add `LandingAIOCRProvider` with new API
4. Update calling code to use factory
5. Maintain backward compatibility

### Fallback Mechanism

**Multi-Layer Fallback:**

```
Configuration Level:
├─ LandingAI requested but no API key
└─ Factory returns DefaultOCRProvider

Runtime Level:
├─ LandingAI API call fails (network error)
├─ Provider raises RuntimeError
└─ Application catches and retries with Tesseract

Retry Level:
├─ LandingAI temporary failure
├─ Exponential backoff retry
└─ Success or final failure
```

**Implementation:**

```python
def process_with_fallback(file_path, output_path, config):
    # Try primary provider
    primary = OCRProviderFactory.get_provider(config)

    try:
        primary.process_document(file_path, output_path)
    except RuntimeError as e:
        logger.warning(f"Primary provider failed: {e}")

        # Fall back to Tesseract
        fallback = DefaultOCRProvider({})
        fallback.process_document(file_path, output_path)
```

### Error Handling Strategy

**Three-Tier Error Handling:**

1. **Provider Level**: Retry logic, API errors
2. **Factory Level**: Configuration validation
3. **Application Level**: Final error handling

**Error Flow:**

```
Application Call
    │
    ▼
Factory.get_provider()
    ├─ ValueError: Invalid provider
    └─ Returns provider
    │
    ▼
Provider.process_document()
    ├─ FileNotFoundError: File missing
    ├─ ValueError: Invalid file format
    ├─ RuntimeError: OCR processing failed
    │   └─ (Retry logic inside)
    └─ Success
    │
    ▼
Application Success Handler
```

**Logging at Each Level:**

```python
# Factory level
logger.info(f"Creating OCR provider: {provider_type}")
logger.warning("Falling back to default provider")

# Provider level
logger.debug("LandingAI API call attempt 1/3")
logger.error("OCR processing failed", exc_info=True)

# Application level
logger.info("Document processing completed")
```

---

## Testing Strategy

### Unit Tests

**Provider Tests:**

```python
# tests/test_ocr_providers.py

class TestOCRProviderFactory:
    def test_factory_creates_default_provider(self):
        config = {'ocr': {'provider': 'default'}}
        provider = OCRProviderFactory.get_provider(config)
        assert isinstance(provider, DefaultOCRProvider)

    def test_factory_creates_landing_ai_provider(self):
        config = {
            'ocr': {
                'provider': 'landing_ai',
                'landing_ai': {'api_key': 'land_sk_test'}
            }
        }
        provider = OCRProviderFactory.get_provider(config)
        assert isinstance(provider, LandingAIOCRProvider)

    def test_factory_falls_back_when_api_key_missing(self):
        config = {
            'ocr': {
                'provider': 'landing_ai',
                'landing_ai': {'api_key': ''}
            }
        }
        provider = OCRProviderFactory.get_provider(config)
        assert isinstance(provider, DefaultOCRProvider)
```

**Document Analyzer Tests:**

```python
# tests/test_document_analyzer.py

class TestDocumentAnalyzer:
    def test_requires_ocr_for_scanned_pdf(self):
        assert requires_ocr('test_docs/scan.pdf') == True

    def test_no_ocr_for_searchable_pdf(self):
        assert requires_ocr('test_docs/text.pdf') == False

    def test_requires_ocr_for_image(self):
        assert requires_ocr('test_docs/image.jpg') == True
```

**Layout Reconstructor Tests:**

```python
# tests/test_layout_reconstructor.py

class TestLayoutReconstructor:
    def test_reconstruct_single_column(self):
        chunks = [
            {'text': 'Line 1', 'grounding': {'page': 0, 'box': {...}}},
            {'text': 'Line 2', 'grounding': {'page': 0, 'box': {...}}}
        ]
        result = reconstruct_layout(chunks)
        assert 'Line 1' in result
        assert 'Line 2' in result

    def test_detect_multi_column(self):
        # Chunks in two columns
        chunks = create_two_column_chunks()
        result = reconstruct_layout(chunks)
        assert '[Column Break]' in result
```

### Integration Tests

**End-to-End OCR Tests:**

```python
# tests/test_landing_ai_integration.py

class TestLandingAIIntegration:
    def test_process_real_document(self):
        config = load_test_config()
        provider = OCRProviderFactory.get_provider(config)

        input_file = 'test_docs/sample.pdf'
        output_file = 'output_temp/result.docx'

        provider.process_document(input_file, output_file)

        assert os.path.exists(output_file)
        assert os.path.getsize(output_file) > 0
```

### Performance Tests

**Benchmarking:**

```python
import time

def benchmark_providers():
    test_files = ['scan1.pdf', 'scan2.pdf', 'scan3.pdf']

    # Test Tesseract
    tesseract = DefaultOCRProvider({})
    start = time.time()
    for f in test_files:
        tesseract.process_document(f, f.replace('.pdf', '_tess.docx'))
    tesseract_time = time.time() - start

    # Test LandingAI
    landing_ai = LandingAIOCRProvider({'api_key': 'land_sk_...'})
    start = time.time()
    for f in test_files:
        landing_ai.process_document(f, f.replace('.pdf', '_lai.docx'))
    landing_ai_time = time.time() - start

    print(f"Tesseract: {tesseract_time:.2f}s")
    print(f"LandingAI: {landing_ai_time:.2f}s")
```

### Test File Usage

**Test Document Categories:**

1. **Searchable PDFs**: `file-sample-pdf.pdf`
   - Text can be extracted directly
   - No OCR needed

2. **Scanned PDFs**: `PDF-scanned-rus-words.pdf`
   - Image-based PDF
   - Requires OCR

3. **Image Files**: `file-sample-img.pdf`
   - JPEG, PNG, etc.
   - Always requires OCR

4. **Multi-column**: Custom test files
   - Tests layout preservation
   - Verifies column detection

5. **Tables**: Custom test files
   - Tests structure preservation
   - Verifies grounding accuracy

---

## Future Enhancements

### Additional Providers

**Planned Integrations:**

1. **Google Vision API**
   ```python
   class GoogleVisionProvider(BaseOCRProvider):
       def process_document(self, ocr_file, out_doc_file_path):
           # Use Google Cloud Vision API
           pass
   ```

2. **Azure Form Recognizer**
   ```python
   class AzureFormRecognizerProvider(BaseOCRProvider):
       def process_document(self, ocr_file, out_doc_file_path):
           # Use Azure Form Recognizer
           pass
   ```

3. **AWS Textract**
   ```python
   class AWSTextractProvider(BaseOCRProvider):
       def process_document(self, ocr_file, out_doc_file_path):
           # Use AWS Textract
           pass
   ```

**Configuration:**

```json
{
  "ocr": {
    "provider": "google_vision",
    "google_vision": {
      "credentials": "/path/to/credentials.json"
    }
  }
}
```

### Advanced Layout Features

**1. Table Detection**

```python
def detect_tables(chunks: List[TextChunk]) -> List[Table]:
    # Detect grid-like patterns in grounding data
    # Return structured table objects
    pass
```

**2. Reading Order Optimization**

```python
def optimize_reading_order(chunks: List[TextChunk]) -> List[TextChunk]:
    # Use ML to determine natural reading order
    # Handle complex layouts (zigzag, etc.)
    pass
```

**3. Font and Style Preservation**

```python
@dataclass
class StyledTextChunk(TextChunk):
    font_size: float
    font_family: str
    is_bold: bool
    is_italic: bool
```

**4. Image Extraction**

```python
def extract_images_with_positions(chunks):
    # Extract embedded images
    # Preserve their positions relative to text
    pass
```

### Performance Optimizations

**1. Batch Processing**

```python
class BatchOCRProvider(BaseOCRProvider):
    def process_documents_batch(self, files: List[str]) -> List[str]:
        # Process multiple documents in single API call
        # Reduce overhead
        pass
```

**2. Caching**

```python
class CachedOCRProvider(BaseOCRProvider):
    def __init__(self, wrapped_provider: BaseOCRProvider):
        self.provider = wrapped_provider
        self.cache = {}

    def process_document(self, ocr_file, out_doc_file_path):
        file_hash = compute_hash(ocr_file)
        if file_hash in self.cache:
            # Use cached result
            return self.cache[file_hash]

        result = self.provider.process_document(ocr_file, out_doc_file_path)
        self.cache[file_hash] = result
        return result
```

**3. Parallel Processing**

```python
from concurrent.futures import ThreadPoolExecutor

def process_documents_parallel(files: List[str], provider):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(provider.process_document, f, f + '.docx')
            for f in files
        ]
        results = [f.result() for f in futures]
    return results
```

**4. Streaming for Large Files**

```python
class StreamingOCRProvider(BaseOCRProvider):
    def process_document_streaming(self, ocr_file, out_doc_file_path):
        # Process page by page
        # Stream results incrementally
        pass
```

### A/B Testing Framework

**Configuration:**

```json
{
  "ocr": {
    "enable_ab_test": true,
    "ab_test_percentage": 10,
    "providers": {
      "control": "default",
      "treatment": "landing_ai"
    }
  }
}
```

**Implementation:**

```python
class ABTestOCRFactory:
    @staticmethod
    def get_provider(config):
        if not config.get('ocr', {}).get('enable_ab_test'):
            return OCRProviderFactory.get_provider(config)

        # Random assignment
        percentage = config['ocr']['ab_test_percentage']
        if random.randint(1, 100) <= percentage:
            # Treatment group
            provider_type = config['ocr']['providers']['treatment']
        else:
            # Control group
            provider_type = config['ocr']['providers']['control']

        # Log assignment
        logger.info(f"A/B Test assignment: {provider_type}")

        return create_provider(provider_type, config)
```

### Monitoring and Analytics

**1. Performance Metrics**

```python
class MetricsCollector:
    @staticmethod
    def log_performance_metric(
        provider: str,
        duration: float,
        file_size: int,
        page_count: int
    ):
        # Log to metrics system (Prometheus, CloudWatch, etc.)
        metrics.histogram('ocr_duration', duration, labels={'provider': provider})
        metrics.counter('ocr_pages', page_count, labels={'provider': provider})
```

**2. Quality Metrics**

```python
def calculate_ocr_quality(original: str, ocr_output: str) -> float:
    # Calculate character accuracy
    # Use edit distance or other metrics
    pass
```

**3. Cost Tracking**

```python
class CostTracker:
    @staticmethod
    def track_api_call(provider: str, pages: int):
        # Track API usage
        # Calculate costs
        # Alert on budget thresholds
        pass
```

---

## Summary

### Architecture Highlights

1. **Clean Separation**: Factory, providers, and utilities are decoupled
2. **Extensible**: Easy to add new providers or features
3. **Configurable**: Behavior changes via configuration, not code
4. **Testable**: Each component can be tested independently
5. **Maintainable**: Clear responsibilities and interfaces

### Design Principles Applied

- **Single Responsibility**: Each class has one clear purpose
- **Open/Closed**: Open for extension, closed for modification
- **Dependency Inversion**: Depend on abstractions (BaseOCRProvider), not concretions
- **Interface Segregation**: Minimal interface in BaseOCRProvider
- **Don't Repeat Yourself**: Shared utilities (logging, layout reconstruction)

### Key Takeaways

- Provider pattern enables easy OCR engine switching
- Configuration-driven approach minimizes code changes
- Layout reconstruction uses spatial data for accuracy
- Comprehensive testing ensures reliability
- Architecture supports future enhancements

---

**Last Updated**: November 15, 2025
**Version**: 1.0.0
**Architecture Pattern**: Provider Pattern with Factory
