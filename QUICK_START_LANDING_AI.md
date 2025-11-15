# LandingAI OCR - Quick Start Guide

## 🚀 Quick Setup (3 Steps)

### Step 1: Get Your API Key
1. Sign up at [LandingAI](https://landing.ai)
2. Navigate to API settings
3. Generate a new API key (starts with `land_sk_`)

### Step 2: Configure EmailReader

Edit `credentials/config.dev.json` (or `config.prod.json`):

```json
{
  "ocr": {
    "provider": "landing_ai",
    "landing_ai": {
      "api_key": "land_sk_YOUR_API_KEY_HERE"
    }
  }
}
```

### Step 3: Process Documents

That's it! EmailReader will automatically use LandingAI for OCR:

```bash
source venv/bin/activate
python src/app.py
```

## 🧪 Test the Integration

Run the test suite:

```bash
source venv/bin/activate
python test_landing_ai_integration.py
```

Expected output: `✓ ALL TESTS PASSED`

## 📋 Basic Usage

### Automatic (via EmailReader)

The OCR system automatically uses LandingAI when configured:

```python
from src.ocr.ocr_factory import OCRProviderFactory
from src.config import load_config

config = load_config()
provider = OCRProviderFactory.get_provider(config)
provider.process_document('input.pdf', 'output.docx')
```

### Manual (direct usage)

```python
from src.ocr.landing_ai_provider import LandingAIOCRProvider

config = {
    'api_key': 'land_sk_...',
    'preserve_layout': True
}

provider = LandingAIOCRProvider(config)
provider.process_document('scanned.pdf', 'output.docx')
```

## ⚙️ Configuration Options

### Minimal Configuration
```json
{
  "ocr": {
    "provider": "landing_ai",
    "landing_ai": {
      "api_key": "land_sk_..."
    }
  }
}
```

### Advanced Configuration
```json
{
  "ocr": {
    "provider": "landing_ai",
    "landing_ai": {
      "api_key": "land_sk_...",
      "model": "dpt-2-latest",
      "preserve_layout": true,
      "chunk_processing": {
        "use_grounding": true,
        "maintain_positions": true
      },
      "retry": {
        "max_attempts": 3,
        "backoff_factor": 2,
        "timeout": 30
      }
    }
  }
}
```

## 🎯 Key Features

✅ **Layout Preservation** - Maintains document structure
✅ **Column Detection** - Handles multi-column layouts
✅ **Multi-Page** - Processes documents of any length
✅ **Retry Logic** - Automatic retry with exponential backoff
✅ **Error Handling** - Graceful fallback on failures
✅ **DOCX Output** - Standard Word document format

## 📊 What You Get

### Input
- Scanned PDF or image document
- Complex layouts (multi-column, tables, etc.)

### Output
- DOCX file with preserved layout
- Column breaks marked: `[Column Break]`
- Page breaks marked: `--- Page Break ---`
- Proper paragraph spacing

### Example Output Structure
```
Document Title

First column paragraph 1

First column paragraph 2

[Column Break]

Second column paragraph 1

Second column paragraph 2

--- Page Break ---

Page 2 content...
```

## 🔍 Monitoring

Check logs at `logs/email_reader.log`:

```
2025-11-15 12:00:00 | INFO | EmailReader.OCR.LandingAI | Processing document with LandingAI OCR: input.pdf
2025-11-15 12:00:02 | INFO | EmailReader.OCR.LandingAI | LandingAI API call successful (attempt 1)
2025-11-15 12:00:02 | INFO | EmailReader.OCR.LandingAI | Received 45 chunks from API
2025-11-15 12:00:03 | INFO | EmailReader.OCR.LandingAI | LandingAI OCR completed in 3.21s: output.docx
```

## 🆚 Comparison with Default (Tesseract)

| Feature | LandingAI | Tesseract (Default) |
|---------|-----------|---------------------|
| Layout Preservation | ✅ Advanced | ⚠️ Basic |
| Column Detection | ✅ Automatic | ❌ None |
| Multi-Language | ✅ Yes | ✅ Yes |
| Setup | API Key | Local Install |
| Speed | Fast (API) | Medium (Local) |
| Cost | API Usage | Free |
| Internet Required | Yes | No |

## 🛠️ Troubleshooting

### "API key is required"
- Add API key to config: `"api_key": "land_sk_..."`
- Verify config file is loaded correctly

### "API call failed"
- Check internet connection
- Verify API key is valid
- Check LandingAI service status
- Review timeout settings

### "No text extracted"
- Check document quality (resolution, clarity)
- Verify document contains readable text
- Try different model versions

### Fallback to Default
System automatically falls back to Tesseract if:
- API key is missing
- API is unreachable after retries
- You can explicitly set `"provider": "default"`

## 📚 Documentation

- **Complete Guide**: `docs/LANDING_AI_INTEGRATION.md`
- **Implementation Details**: `LANDING_AI_IMPLEMENTATION.md`
- **API Reference**: [LandingAI Docs](https://docs.landing.ai/api-reference/tools/ade-parse)

## 🎓 Examples

### Process Single Document
```python
from src.ocr.ocr_factory import OCRProviderFactory
from src.config import load_config

config = load_config()
provider = OCRProviderFactory.get_provider(config)

# Process document
provider.process_document('invoice.pdf', 'invoice_ocr.docx')
```

### Check if PDF Needs OCR
```python
provider = OCRProviderFactory.get_provider(config)

if not provider.is_pdf_searchable('document.pdf'):
    print("PDF needs OCR")
    provider.process_document('document.pdf', 'output.docx')
else:
    print("PDF already has text")
```

### Get Document Structure Metadata
```python
from src.utils.layout_reconstructor import apply_grounding_to_output

# After API call, get structure info
metadata = apply_grounding_to_output(api_chunks)

print(f"Pages: {metadata['total_pages']}")
print(f"Chunks: {metadata['total_chunks']}")
for page_num, page_info in metadata['pages'].items():
    print(f"  Page {page_num}: {page_info['columns']} columns")
```

## ✅ Verification Checklist

Before using in production:

- [ ] API key added to config
- [ ] Config file validated: `OCRProviderFactory.validate_config(config)`
- [ ] Integration tests passed: `python test_landing_ai_integration.py`
- [ ] Sample document processed successfully
- [ ] Logs reviewed in `logs/email_reader.log`
- [ ] Output DOCX quality verified

## 🚦 Status

**Implementation**: ✅ Complete
**Testing**: ✅ All tests passing
**Documentation**: ✅ Comprehensive
**Production Ready**: ✅ Yes

---

**Ready to use!** Start processing documents with advanced layout preservation. 🎉
