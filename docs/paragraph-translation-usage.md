# Paragraph Translation Method - Usage Guide

## Overview

A new batch paragraph translation method has been added to `GoogleDocTranslator` class. This method efficiently translates lists of paragraphs while preserving order, formatting, and maintaining backward compatibility.

## Implementation Summary

### Files Modified

- **src/translation/google_doc_translator.py**
  - Added `translate_paragraphs()` public method
  - Added `_translate_text_batch()` private helper method
  - Updated imports to include `List` from `typing`

### Changes Made

1. **New Public Method**: `translate_paragraphs()`
   - Translates a list of paragraph strings in batches
   - Preserves paragraph order and empty paragraphs
   - Implements automatic retry logic for failed batches
   - Logs detailed progress information

2. **New Helper Method**: `_translate_text_batch()`
   - Internal method for batch text translation
   - Uses Google Cloud Translation API's text endpoint (not document endpoint)
   - Handles delimiter-based paragraph boundary preservation
   - Implements fallback for mismatched result counts

3. **Type Imports**: Added `List` to typing imports

## Method Signature

```python
def translate_paragraphs(
    self,
    paragraphs: List[str],
    target_lang: str,
    batch_size: int = 15,
    preserve_formatting: bool = True
) -> List[str]:
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `paragraphs` | `List[str]` | *required* | List of paragraph text strings to translate |
| `target_lang` | `str` | *required* | Target language code (e.g., 'en', 'es', 'fr') |
| `batch_size` | `int` | `15` | Number of paragraphs per API call (optimization) |
| `preserve_formatting` | `bool` | `True` | Maintain paragraph boundaries and order |

## Returns

- `List[str]`: Translated paragraphs in the same order as input

## Raises

- `ValueError`: If `paragraphs` list format is invalid or `target_lang` is missing
- `RuntimeError`: If translation fails after retry attempts

## Usage Examples

### Basic Usage

```python
from src.translation.google_doc_translator import GoogleDocTranslator
from src.utils import load_config

# Load configuration
config = load_config()
translation_config = config.get('translation', {}).get('google_doc', {})
service_account = config.get('google_drive', {}).get('service_account')
if service_account:
    translation_config['service_account'] = service_account

# Initialize translator
translator = GoogleDocTranslator(translation_config)

# Translate paragraphs
paragraphs = [
    "Hello, how are you?",
    "This is a test document.",
    "We are testing batch translation."
]

translated = translator.translate_paragraphs(
    paragraphs=paragraphs,
    target_lang='es'
)

for original, translated_text in zip(paragraphs, translated):
    print(f"{original} -> {translated_text}")
```

### With Custom Batch Size

```python
# Translate large document with smaller batches
large_paragraphs = [f"Paragraph {i}" for i in range(100)]

translated = translator.translate_paragraphs(
    paragraphs=large_paragraphs,
    target_lang='fr',
    batch_size=10  # Process 10 paragraphs per API call
)
```

### Handling Empty Paragraphs

```python
# Empty paragraphs are preserved in the output
paragraphs = [
    "First paragraph",
    "",  # Empty paragraph
    "Third paragraph"
]

translated = translator.translate_paragraphs(
    paragraphs=paragraphs,
    target_lang='de'
)

# translated[1] will be an empty string ""
assert translated[1] == ""
```

### Integration with Document Processing

```python
from docx import Document

# Extract paragraphs from DOCX
doc = Document('input.docx')
paragraphs = [para.text for para in doc.paragraphs]

# Translate
translated = translator.translate_paragraphs(
    paragraphs=paragraphs,
    target_lang='en'
)

# Create new document with translated text
output_doc = Document()
for translated_text in translated:
    output_doc.add_paragraph(translated_text)

output_doc.save('output.docx')
```

## How It Works

### Batching Strategy

1. **Filter Empty Paragraphs**: Tracks indices of non-empty paragraphs
2. **Batch Processing**: Combines paragraphs using a unique delimiter
3. **API Call**: Sends batched text to Google Translation API
4. **Split Results**: Splits translated text back into individual paragraphs
5. **Reconstruct**: Restores empty paragraphs at original positions

### Delimiter Approach

```python
# Paragraphs are joined with a unique delimiter
delimiter = "\n\n###PARAGRAPH_BOUNDARY###\n\n"

# Example:
input = ["Hello", "World"]
combined = "Hello\n\n###PARAGRAPH_BOUNDARY###\n\nWorld"

# After translation:
translated = "Hola\n\n###PARAGRAPH_BOUNDARY###\n\nMundo"

# Split back:
result = ["Hola", "Mundo"]
```

### Error Handling

1. **Batch Failure**: If a batch fails, retry individual paragraphs
2. **Individual Failure**: If a paragraph fails, keep the original text
3. **Count Mismatch**: If result count doesn't match, retry individually
4. **Empty Input**: Returns empty list immediately

## Performance Considerations

### Batch Size Optimization

| Batch Size | API Calls (100 paragraphs) | Trade-offs |
|------------|---------------------------|------------|
| 5 | 20 | More API calls, better error isolation |
| 15 (default) | 7 | Balanced approach |
| 50 | 2 | Fewer API calls, but larger failure impact |

### Recommended Batch Sizes

- **Small documents** (< 20 paragraphs): `batch_size=10`
- **Medium documents** (20-100 paragraphs): `batch_size=15` (default)
- **Large documents** (> 100 paragraphs): `batch_size=20-25`

## Limitations and Considerations

### API Rate Limits

- Google Cloud Translation API has quotas per project
- Each batch counts as one API call
- Monitor usage in Google Cloud Console

### Character Limits

- Maximum characters per request: ~30,000 (Google Cloud limit)
- Adjust `batch_size` if paragraphs are very long
- Method doesn't currently validate total character count

### Paragraph Boundaries

- Delimiter approach works for most languages
- Some translations may alter delimiter slightly
- Fallback logic handles edge cases

### Cost Implications

- Pricing: $20 per million characters (as of 2024)
- Batching reduces API calls but not character count
- Empty paragraphs don't incur costs (filtered out)

## Backward Compatibility

### Existing Method Unchanged

The original `translate_document()` method remains **completely unchanged**:

```python
# Still works exactly as before
translator.translate_document(
    input_path='input.docx',
    output_path='output.docx',
    target_lang='en'
)
```

### No Breaking Changes

- All existing code continues to work
- No configuration changes required
- Same initialization process
- Same error handling patterns

## Testing

### Unit Tests

Run the unit test suite to verify implementation:

```bash
python3 test_paragraph_translation_unit.py
```

### Integration Tests

For full API testing (requires valid credentials):

```python
# Uncomment in test_paragraph_translation.py:
# results.append(("Basic Paragraph Translation", test_basic_paragraph_translation()))
# results.append(("Large Batch Translation", test_large_batch_translation()))

python3 test_paragraph_translation.py
```

## Logging

The method provides detailed logging at different levels:

### INFO Level
```
Translating 50 paragraphs to 'en' in batches of 15
Processing batch 1/4 (15 paragraphs)
Processing batch 2/4 (15 paragraphs)
Translation completed: 50 paragraphs processed
```

### DEBUG Level
```
Skipping empty paragraph at index 3
Combined 15 texts into single string (2458 chars)
API call completed in 1.23 seconds
Split translated text into 15 paragraphs
```

### WARNING/ERROR Level
```
Batch 2/4 failed: API error. Retrying with individual translations.
Translation result count mismatch: expected 15, got 14
```

## Example: Complete Workflow

```python
#!/usr/bin/env python3
"""Complete example of paragraph translation workflow."""

from src.translation.google_doc_translator import GoogleDocTranslator
from src.utils import load_config
from docx import Document
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def translate_document_by_paragraphs(input_path, output_path, target_lang='en'):
    """Translate a DOCX document paragraph by paragraph."""

    # Load config and initialize translator
    config = load_config()
    translation_config = config.get('translation', {}).get('google_doc', {})
    service_account = config.get('google_drive', {}).get('service_account')
    if service_account:
        translation_config['service_account'] = service_account

    translator = GoogleDocTranslator(translation_config)

    # Extract paragraphs
    logger.info("Reading document: %s", input_path)
    doc = Document(input_path)
    paragraphs = [para.text for para in doc.paragraphs]
    logger.info("Extracted %d paragraphs", len(paragraphs))

    # Translate
    logger.info("Translating to %s", target_lang)
    translated = translator.translate_paragraphs(
        paragraphs=paragraphs,
        target_lang=target_lang,
        batch_size=15
    )

    # Create output document
    logger.info("Creating output document: %s", output_path)
    output_doc = Document()

    for para, translated_text in zip(doc.paragraphs, translated):
        # Preserve paragraph formatting
        new_para = output_doc.add_paragraph(translated_text)
        new_para.style = para.style

    output_doc.save(output_path)
    logger.info("Translation complete!")

if __name__ == '__main__':
    translate_document_by_paragraphs(
        'input.docx',
        'output.docx',
        target_lang='es'
    )
```

## Support and Troubleshooting

### Common Issues

**Issue**: "Translation result count mismatch"
- **Cause**: Delimiter appears in source text or translation altered it
- **Solution**: Method automatically retries with individual translations

**Issue**: "Batch failed: PERMISSION_DENIED"
- **Cause**: Service account lacks Translation API permissions
- **Solution**: Ensure "Cloud Translation API User" role in Google Cloud Console

**Issue**: High API costs
- **Cause**: Too many small batches or inefficient batch size
- **Solution**: Increase `batch_size` for large documents

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

Potential improvements for future versions:

1. **Character count validation** - Warn if batch exceeds API limits
2. **Source language detection** - Auto-detect language for better accuracy
3. **Async/await support** - Parallel batch processing
4. **Custom delimiters** - Allow user-specified paragraph separators
5. **Progress callbacks** - Real-time progress updates for UI integration
6. **Caching** - Cache translations to reduce redundant API calls

## Changelog

### Version 1.0 (2025-11-19)

- Initial implementation of `translate_paragraphs()` method
- Added `_translate_text_batch()` helper method
- Comprehensive error handling and retry logic
- Full backward compatibility maintained
- Unit tests and integration tests added
