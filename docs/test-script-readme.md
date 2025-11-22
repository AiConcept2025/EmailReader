# OCR + Translation Test Script

## Overview

`test_ocr_translation.sh` is a comprehensive test script that validates the complete document processing pipeline in the EmailReader project:

1. **Azure Document Intelligence OCR** - Extracts text from PDF documents
2. **Google Cloud Translation API** - Translates the extracted text

## Features

- ✅ Accepts any PDF file as input
- ✅ Runs Azure OCR to extract text
- ✅ Runs Google Translation to translate the document
- ✅ Saves both OCR and translated results in current directory
- ✅ Supports custom target language
- ✅ Comprehensive error handling and validation
- ✅ Color-coded output for easy reading
- ✅ Progress indicators and timing information

## Prerequisites

- Virtual environment activated (`venv/`)
- Azure Document Intelligence credentials configured
- Google Cloud Translation credentials configured
- Input file must be a PDF

## Usage

### Basic Usage

```bash
./test_ocr_translation.sh <input_file.pdf>
```

This will:
- Run OCR on the PDF
- Translate to English (default)
- Save results in current directory

### Specify Target Language

```bash
./test_ocr_translation.sh <input_file.pdf> <language_code>
```

**Supported Language Codes:**
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `ru` - Russian
- `zh` - Chinese
- `ja` - Japanese
- And many more...

## Examples

### Example 1: Translate to English
```bash
./test_ocr_translation.sh document.pdf
```

Output files:
- `document_ocr.docx` - OCR result
- `document_translated.docx` - English translation

### Example 2: Translate to Spanish
```bash
./test_ocr_translation.sh document.pdf es
```

Output files:
- `document_ocr.docx` - OCR result
- `document_translated.docx` - Spanish translation

### Example 3: Process Russian Document
```bash
./test_ocr_translation.sh russian_document.pdf en
```

Output files:
- `russian_document_ocr.docx` - OCR result (Russian text)
- `russian_document_translated.docx` - English translation

## Output

The script creates two files in the **current directory**:

1. **`<basename>_ocr.docx`**
   - Result of Azure OCR
   - Contains extracted text from PDF
   - Preserves document structure

2. **`<basename>_translated.docx`**
   - Result of Google Translation
   - Contains translated text
   - Maintains formatting

## Script Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Validate Input                                           │
│    - Check file exists                                      │
│    - Verify PDF format                                      │
│    - Check virtual environment                              │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│ 2. Verify Configuration                                     │
│    - Check OCR configuration (Azure)                        │
│    - Check Translation configuration (Google)               │
│    - Validate credentials                                   │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│ 3. Azure Document Intelligence OCR                          │
│    - Process PDF with Azure                                 │
│    - Extract text and formatting                            │
│    - Save to <basename>_ocr.docx                           │
│    - Duration: 5-30 seconds                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│ 4. Google Cloud Translation                                 │
│    - Translate OCR result                                   │
│    - Preserve formatting                                    │
│    - Save to <basename>_translated.docx                    │
│    - Duration: 1-10 seconds                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│ 5. Display Results                                          │
│    - Show output file paths                                 │
│    - Display file sizes                                     │
│    - Provide next steps                                     │
└─────────────────────────────────────────────────────────────┘
```

## Sample Output

```
================================================================================
EmailReader OCR + Translation Test
================================================================================
ℹ Configuration:
  Input file:        /path/to/document.pdf
  Target language:   en
  OCR output:        /current/dir/document_ocr.docx
  Translation output: /current/dir/document_translated.docx

Step 1: Checking virtual environment
✓ Virtual environment found
✓ Virtual environment activated

Step 2: Verifying configuration
✓ OCR configured: Azure Document Intelligence
✓ Translation configured: Google Cloud Translation (project: synologysafeaccess-320003)

Step 3: Running Azure Document Intelligence OCR
ℹ Processing: /path/to/document.pdf
ℹ This may take 10-30 seconds depending on document size...
  Provider: AzureOCRProvider
✓ OCR completed in 6.2 seconds
✓ Output file: /current/dir/document_ocr.docx (37.2 KB)
✓ OCR completed successfully

Step 4: Running Google Cloud Translation
ℹ Translating to: en
ℹ This may take 5-15 seconds...
  Translator: GoogleDocTranslator
✓ Translation completed in 1.3 seconds
✓ Output file: /current/dir/document_translated.docx (37.5 KB)
✓ Translation completed successfully

================================================================================
Test Completed Successfully
================================================================================

✓ All steps completed successfully

Results:
  OCR Result:         /current/dir/document_ocr.docx
  Translation Result: /current/dir/document_translated.docx

File Sizes:
  OCR:         37K - /current/dir/document_ocr.docx
  Translation: 38K - /current/dir/document_translated.docx
```

## Error Handling

The script includes comprehensive error handling:

### Configuration Errors
```
✗ OCR configuration not found
✗ Azure OCR credentials not configured
✗ Translation configuration not found
```

### Processing Errors
```
✗ OCR failed: Invalid API key
✗ Translation failed: Permission denied
```

### File Errors
```
✗ Input file not found: document.pdf
✗ Input file must be a PDF (.pdf extension)
```

## Performance

Typical processing times:

- **OCR (Azure)**: 5-30 seconds
  - Depends on document size and complexity
  - Includes API call and document processing

- **Translation (Google)**: 1-10 seconds
  - Depends on document length
  - Usually faster than OCR

**Total Time**: 6-40 seconds for complete pipeline

## Troubleshooting

### Script not executable
```bash
chmod +x test_ocr_translation.sh
```

### Virtual environment not found
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Azure credentials not configured
Edit `credentials/config.dev.json`:
```json
{
  "ocr": {
    "provider": "azure",
    "azure": {
      "endpoint": "https://your-resource.cognitiveservices.azure.com/",
      "api_key": "your-api-key"
    }
  }
}
```

### Google Translation credentials not configured
Edit `credentials/config.dev.json`:
```json
{
  "translation": {
    "provider": "google_doc",
    "google_doc": {
      "project_id": "your-project-id"
    }
  }
}
```

## Testing Different Scenarios

### Test 1: English Document
```bash
./test_ocr_translation.sh test_docs/file-sample-pdf.pdf en
```

### Test 2: Russian Document to English
```bash
./test_ocr_translation.sh test_docs/PDF-scanned-rus-words.pdf en
```

### Test 3: Multiple Language Translation
```bash
./test_ocr_translation.sh document.pdf es  # Spanish
./test_ocr_translation.sh document.pdf fr  # French
./test_ocr_translation.sh document.pdf de  # German
```

## Integration with EmailReader

This script validates the same pipeline used by EmailReader for:
- Processing email attachments
- Google Drive document processing
- Automated document translation workflow

## Related Files

- `verify_azure_ocr_config.py` - Verifies Azure OCR configuration
- `test_azure_permissions.py` - Tests Azure API permissions
- `test_translation_config.py` - Verifies Google Translation configuration
- `test_translation_permissions.py` - Tests Google Translation permissions

## Support

For issues or questions:
1. Check configuration in `credentials/config.dev.json`
2. Verify credentials are valid
3. Review error messages for specific issues
4. Check Azure Portal for API status
5. Check Google Cloud Console for Translation API status

## Version History

- **v1.0** (2025-11-18)
  - Initial release
  - Azure OCR support
  - Google Cloud Translation support
  - Comprehensive error handling
  - Color-coded output
