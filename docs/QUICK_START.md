# LandingAI OCR Integration - Quick Start

## 5-Minute Setup

Get up and running with LandingAI OCR integration in under 5 minutes.

---

## Option 1: Use Default (Tesseract)

**No changes needed!** The default Tesseract OCR provider is already configured and ready to use.

### Verify It Works

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\activate   # Windows

# Run a quick test
python -c "
from src.ocr.ocr_factory import OCRProviderFactory
config = {'ocr': {'provider': 'default'}}
provider = OCRProviderFactory.get_provider(config)
print(f'Active provider: {provider.__class__.__name__}')
"
```

Expected output:
```
Active provider: DefaultOCRProvider
```

**Done!** You're using Tesseract OCR.

---

## Option 2: Enable LandingAI

### Step 1: Get API Key (2 minutes)

1. Visit [https://landing.ai](https://landing.ai)
2. Sign up or log in
3. Navigate to **Settings** → **API Keys**
4. Click **Create New API Key**
5. Copy the key (starts with `land_sk_`)

### Step 2: Update Configuration (1 minute)

Edit your configuration file:

```bash
# Development environment
vim credentials/config.dev.json

# Production environment
vim credentials/config.prod.json
```

Add this configuration:

```json
{
  "ocr": {
    "provider": "landing_ai",
    "landing_ai": {
      "api_key": "land_sk_YOUR_KEY_HERE"
    }
  }
}
```

**Security Note:** Replace `land_sk_YOUR_KEY_HERE` with your actual API key.

### Step 3: Test (2 minutes)

```bash
# Run OCR provider test
python -m pytest tests/test_ocr_providers.py::test_factory_creates_landing_ai_provider -v
```

Expected output:
```
tests/test_ocr_providers.py::test_factory_creates_landing_ai_provider PASSED
```

### Step 4: Done!

You're now using LandingAI OCR with layout preservation!

---

## Common Tasks

### Test OCR Integration

#### Quick Test

```bash
python -c "
from src.ocr.ocr_factory import OCRProviderFactory
from src.config_loader import load_config

config = load_config('credentials/config.dev.json')
provider = OCRProviderFactory.get_provider(config)

print(f'Provider: {provider.__class__.__name__}')
print(f'Ready to process documents!')
"
```

#### Test with Sample Document

```bash
python -c "
from src.ocr.ocr_factory import OCRProviderFactory
from src.config_loader import load_config
import os

config = load_config('credentials/config.dev.json')
provider = OCRProviderFactory.get_provider(config)

# Process test file
input_file = 'test_docs/file-sample-pdf.pdf'
output_file = 'output_test.docx'

if os.path.exists(input_file):
    provider.process_document(input_file, output_file)
    print(f'✓ OCR completed: {output_file}')
else:
    print(f'✗ Test file not found: {input_file}')
"
```

#### Run Full Test Suite

```bash
# All OCR tests
python -m pytest tests/test_ocr_providers.py -v

# All tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ -v --cov=src/ocr --cov=src/document_analyzer
```

### Check Which Provider is Active

#### Method 1: Python Code

```python
from src.ocr.ocr_factory import OCRProviderFactory
from src.config_loader import load_config

config = load_config('credentials/config.dev.json')
provider = OCRProviderFactory.get_provider(config)

print(f'Active provider: {provider.__class__.__name__}')
# Output: LandingAIOCRProvider or DefaultOCRProvider

if hasattr(provider, 'api_key'):
    print(f'API key configured: Yes')
    print(f'Model: {provider.model}')
    print(f'Layout preservation: {provider.preserve_layout}')
else:
    print('Using local Tesseract OCR')
```

#### Method 2: Check Logs

```bash
# View recent provider selections
tail -f logs/email_reader.log | grep "Creating OCR provider"
```

Output will show:
```
INFO - Creating OCR provider: landing_ai
INFO - Creating LandingAI OCR provider
```

or

```
INFO - Creating OCR provider: default
INFO - Creating default Tesseract OCR provider
```

### View OCR Logs

#### Real-time Monitoring

```bash
# All OCR activity
tail -f logs/email_reader.log | grep "OCR"

# LandingAI only
tail -f logs/email_reader.log | grep "LandingAI"

# Errors only
tail -f logs/email_reader.log | grep "ERROR"

# Performance metrics
tail -f logs/email_reader.log | grep "completed in"
```

#### View Historical Logs

```bash
# Last 50 OCR operations
grep "OCR" logs/email_reader.log | tail -50

# Count provider usage today
grep "$(date +%Y-%m-%d)" logs/email_reader.log | grep "Creating OCR provider" | wc -l

# Performance summary
grep "completed in" logs/email_reader.log | tail -20
```

### Switch Providers

#### Switch to LandingAI

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

#### Switch to Tesseract

```json
{
  "ocr": {
    "provider": "default"
  }
}
```

#### Or Simply Remove OCR Section

If no `ocr` section is present, defaults to Tesseract:

```json
{
  "google_drive": {...},
  "email": {...}
  // No ocr section = uses Tesseract
}
```

**Apply Changes:**

```bash
# Restart the application
sudo systemctl restart emailreader

# Or if running manually
pkill -f index.py
python index.py
```

---

## Code Examples

### Basic Usage

#### Example 1: Process a Document

```python
from src.ocr.ocr_factory import OCRProviderFactory
from src.config_loader import load_config

# Load configuration
config = load_config('credentials/config.dev.json')

# Get provider
provider = OCRProviderFactory.get_provider(config)

# Process document
provider.process_document(
    ocr_file='documents/scan.pdf',
    out_doc_file_path='documents/scan_ocr.docx'
)

print("OCR processing completed!")
```

#### Example 2: Check if Document Needs OCR

```python
from src.document_analyzer import requires_ocr
from src.ocr.ocr_factory import OCRProviderFactory
from src.config_loader import load_config

config = load_config('credentials/config.dev.json')
provider = OCRProviderFactory.get_provider(config)

file_path = 'documents/document.pdf'

if requires_ocr(file_path):
    print(f"{file_path} requires OCR")
    provider.process_document(file_path, file_path.replace('.pdf', '.docx'))
else:
    print(f"{file_path} is searchable - no OCR needed")
```

#### Example 3: Batch Processing

```python
import os
from pathlib import Path
from src.ocr.ocr_factory import OCRProviderFactory
from src.document_analyzer import requires_ocr
from src.config_loader import load_config

# Setup
config = load_config('credentials/config.dev.json')
provider = OCRProviderFactory.get_provider(config)

# Process all PDFs in directory
input_dir = Path('documents/inbox')
output_dir = Path('documents/processed')
output_dir.mkdir(exist_ok=True)

for pdf_file in input_dir.glob('*.pdf'):
    if requires_ocr(str(pdf_file)):
        output_file = output_dir / f"{pdf_file.stem}_ocr.docx"
        print(f"Processing {pdf_file.name}...")

        provider.process_document(str(pdf_file), str(output_file))
        print(f"✓ Saved to {output_file.name}")
    else:
        print(f"⊘ Skipped {pdf_file.name} (already searchable)")

print("Batch processing completed!")
```

### Advanced Usage

#### Example 4: Provider Comparison

```python
import time
from src.ocr.ocr_factory import OCRProviderFactory
from src.ocr.default_provider import DefaultOCRProvider

# Test file
test_file = 'test_docs/scan.pdf'

# Test Tesseract
tesseract = DefaultOCRProvider({})
start = time.time()
tesseract.process_document(test_file, 'output_tesseract.docx')
tesseract_time = time.time() - start

# Test LandingAI
config = {
    'ocr': {
        'provider': 'landing_ai',
        'landing_ai': {'api_key': 'land_sk_...'}
    }
}
landing_ai = OCRProviderFactory.get_provider(config)
start = time.time()
landing_ai.process_document(test_file, 'output_landing_ai.docx')
landing_ai_time = time.time() - start

print(f"Tesseract: {tesseract_time:.2f}s")
print(f"LandingAI: {landing_ai_time:.2f}s")
print(f"Speedup: {tesseract_time / landing_ai_time:.1f}x")
```

#### Example 5: Custom Configuration

```python
from src.ocr.landing_ai_provider import LandingAIOCRProvider

# Custom LandingAI configuration
config = {
    'api_key': 'land_sk_YOUR_KEY',
    'model': 'dpt-2-latest',
    'split_mode': 'page',
    'preserve_layout': True,
    'chunk_processing': {
        'use_grounding': True,
        'maintain_positions': True
    },
    'retry': {
        'max_attempts': 5,
        'backoff_factor': 2,
        'timeout': 60  # Increase for large files
    }
}

provider = LandingAIOCRProvider(config)
provider.process_document('large_document.pdf', 'output.docx')
```

#### Example 6: Error Handling

```python
from src.ocr.ocr_factory import OCRProviderFactory
from src.config_loader import load_config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = load_config('credentials/config.dev.json')
provider = OCRProviderFactory.get_provider(config)

try:
    provider.process_document('input.pdf', 'output.docx')
    logger.info("✓ OCR completed successfully")

except FileNotFoundError as e:
    logger.error(f"✗ File not found: {e}")

except ValueError as e:
    logger.error(f"✗ Invalid file format: {e}")

except RuntimeError as e:
    logger.error(f"✗ OCR processing failed: {e}")
    logger.info("Falling back to Tesseract...")

    # Fallback
    from src.ocr.default_provider import DefaultOCRProvider
    fallback = DefaultOCRProvider({})
    fallback.process_document('input.pdf', 'output.docx')
    logger.info("✓ Fallback OCR completed")
```

### Integration Examples

#### Example 7: Document Analysis Pipeline

```python
from pathlib import Path
from src.document_analyzer import get_document_type, requires_ocr
from src.ocr.ocr_factory import OCRProviderFactory
from src.config_loader import load_config

def analyze_and_process(file_path: str):
    """Analyze document and process if needed."""
    # Analyze document
    doc_type = get_document_type(file_path)
    needs_ocr = requires_ocr(file_path)

    print(f"File: {Path(file_path).name}")
    print(f"Type: {doc_type}")
    print(f"Needs OCR: {needs_ocr}")

    if needs_ocr:
        # Load config and get provider
        config = load_config('credentials/config.dev.json')
        provider = OCRProviderFactory.get_provider(config)

        # Process
        output_file = file_path.replace('.pdf', '_ocr.docx')
        provider.process_document(file_path, output_file)
        print(f"✓ OCR completed: {output_file}")
    else:
        print("⊘ No OCR needed")

# Use it
analyze_and_process('documents/scan.pdf')
```

#### Example 8: Multi-Provider Processing

```python
from src.ocr.ocr_factory import OCRProviderFactory
from src.ocr.default_provider import DefaultOCRProvider
from src.ocr.landing_ai_provider import LandingAIOCRProvider

def process_with_best_provider(file_path: str, output_path: str):
    """Use best provider based on document complexity."""
    from src.document_analyzer import get_document_type

    doc_type = get_document_type(file_path)

    # Simple documents: use Tesseract (free)
    if doc_type in ('pdf_searchable', 'text_document', 'word_document'):
        provider = DefaultOCRProvider({})
        print("Using Tesseract (simple document)")

    # Complex documents: use LandingAI (premium)
    else:
        config = {
            'api_key': 'land_sk_...',
            'preserve_layout': True
        }
        provider = LandingAIOCRProvider(config)
        print("Using LandingAI (complex document)")

    provider.process_document(file_path, output_path)

# Use it
process_with_best_provider('complex_table.pdf', 'output.docx')
```

---

## Troubleshooting Quick Fixes

### Issue: "LandingAI provider requested but API key not found"

**Quick Fix:**

```bash
# Check your config file
cat credentials/config.dev.json | grep -A3 "landing_ai"

# Should show:
# "landing_ai": {
#   "api_key": "land_sk_..."
# }

# If empty, add your API key
vim credentials/config.dev.json
```

### Issue: "401 Unauthorized" from LandingAI API

**Quick Fix:**

```bash
# Test your API key
curl -H "Authorization: Bearer land_sk_YOUR_KEY" \
     https://api.va.landing.ai/v1/tools/ade-parse

# If it fails, regenerate your key at https://landing.ai
```

### Issue: Can't See Logs

**Quick Fix:**

```bash
# Create logs directory if missing
mkdir -p logs

# Set log level to DEBUG
export LOGLEVEL=DEBUG

# Run with logging
python index.py 2>&1 | tee logs/debug.log
```

### Issue: Tests Failing

**Quick Fix:**

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests with verbose output
python -m pytest tests/ -v -s

# Run specific test
python -m pytest tests/test_ocr_providers.py::test_factory_creates_default_provider -v
```

### Issue: Slow Processing

**Quick Fix:**

Increase timeout in configuration:

```json
{
  "ocr": {
    "landing_ai": {
      "retry": {
        "timeout": 60  // Increase from 30 to 60 seconds
      }
    }
  }
}
```

---

## Next Steps

### Learn More

1. **Migration Guide**: See `docs/MIGRATION_GUIDE.md` for detailed migration instructions
2. **API Reference**: See `docs/API_REFERENCE.md` for complete API documentation
3. **Architecture**: See `docs/ARCHITECTURE.md` for system design details

### Optimize Your Setup

1. **Configure Retry Logic**: Adjust retry settings for your network
2. **Set Up Monitoring**: Track OCR performance and costs
3. **Enable Fallback**: Configure automatic fallback to Tesseract
4. **Batch Processing**: Process multiple documents efficiently

### Get Help

- **Logs**: Check `logs/email_reader.log` for detailed information
- **Tests**: Run test suite to verify everything works
- **Examples**: See `src/ocr/example_usage.py` for more code examples

---

## Quick Reference Commands

```bash
# Check active provider
python -c "from src.ocr.ocr_factory import OCRProviderFactory; from src.config_loader import load_config; print(OCRProviderFactory.get_provider(load_config('credentials/config.dev.json')).__class__.__name__)"

# Run all tests
python -m pytest tests/ -v

# View logs
tail -f logs/email_reader.log | grep "OCR"

# Process a document
python -c "from src.ocr.ocr_factory import OCRProviderFactory; from src.config_loader import load_config; OCRProviderFactory.get_provider(load_config('credentials/config.dev.json')).process_document('input.pdf', 'output.docx')"
```

---

**Quick Start Complete!** You should now be able to use the LandingAI OCR integration.

For detailed information, see the full documentation in `docs/`.

**Last Updated**: November 15, 2025
**Version**: 1.0.0
