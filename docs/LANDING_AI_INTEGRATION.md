# LandingAI OCR Integration

## Overview

This document describes the LandingAI ADE Parse API integration for the EmailReader OCR system. The integration provides advanced OCR capabilities with complete layout preservation using grounding data.

## Features

- **Layout Preservation**: Uses grounding data to maintain document spatial structure
- **Column Detection**: Automatically detects and handles multi-column layouts
- **Page Management**: Properly handles multi-page documents with page breaks
- **Retry Logic**: Robust retry mechanism with exponential backoff
- **Error Handling**: Graceful fallback to simple concatenation if layout reconstruction fails
- **DOCX Output**: Converts OCR results to DOCX format matching existing OCR providers

## Architecture

### Components

1. **LandingAIOCRProvider** (`src/ocr/landing_ai_provider.py`)
   - Main OCR provider implementing the `BaseOCRProvider` interface
   - Handles API communication with retry logic
   - Manages configuration and processing workflow

2. **Layout Reconstructor** (`src/utils/layout_reconstructor.py`)
   - Processes grounding data to reconstruct document layout
   - Detects column structures
   - Maintains spatial positioning of text elements

### Data Flow

```
Input Document (PDF/Image)
    ↓
LandingAI ADE Parse API
    ↓
API Response (chunks with grounding data)
    ↓
Layout Reconstructor
    ↓
Text with Preserved Layout
    ↓
DOCX Converter
    ↓
Output DOCX File
```

## Configuration

### Basic Configuration

Add to your `credentials/config.{env}.json`:

```json
{
  "ocr": {
    "provider": "landing_ai",
    "landing_ai": {
      "api_key": "land_sk_...",
      "model": "dpt-2-latest",
      "preserve_layout": true,
      "split_mode": "page"
    }
  }
}
```

### Advanced Configuration

Full configuration with all options:

```json
{
  "ocr": {
    "provider": "landing_ai",
    "landing_ai": {
      "api_key": "land_sk_...",
      "base_url": "https://api.va.landing.ai/v1",
      "model": "dpt-2-latest",
      "split_mode": "page",
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

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_key` | string | (required) | LandingAI API authentication key |
| `base_url` | string | `https://api.va.landing.ai/v1` | API endpoint URL |
| `model` | string | `dpt-2-latest` | OCR model to use |
| `split_mode` | string | `page` | Document splitting mode |
| `preserve_layout` | boolean | `true` | Enable layout preservation |
| `chunk_processing.use_grounding` | boolean | `true` | Use grounding data for layout |
| `chunk_processing.maintain_positions` | boolean | `true` | Maintain spatial positions |
| `retry.max_attempts` | integer | `3` | Maximum retry attempts |
| `retry.backoff_factor` | integer | `2` | Exponential backoff factor |
| `retry.timeout` | integer | `30` | Request timeout in seconds |

## API Reference

### LandingAI API Endpoint

**Endpoint**: `POST https://api.va.landing.ai/v1/tools/ade-parse`

**Authentication**: Bearer token in `Authorization` header

**Request**:
```http
POST /v1/tools/ade-parse
Authorization: Bearer YOUR_API_KEY
Content-Type: multipart/form-data

document: (binary file)
model: "dpt-2-latest"
split_mode: "page"
preserve_layout: true
```

**Response**:
```json
{
  "chunks": [
    {
      "text": "Extracted text content",
      "grounding": {
        "page": 0,
        "box": {
          "left": 0.1,
          "top": 0.2,
          "right": 0.9,
          "bottom": 0.3
        }
      }
    }
  ]
}
```

### Grounding Data Structure

- **page**: Page number (0-indexed)
- **box**: Bounding box with normalized coordinates (0-1)
  - **left**: Left edge position
  - **top**: Top edge position
  - **right**: Right edge position
  - **bottom**: Bottom edge position

## Layout Reconstruction

### Column Detection

The layout reconstructor automatically detects column structures based on horizontal positioning:

- Chunks with similar horizontal positions are grouped into the same column
- Columns are separated by gaps > 20% of page width
- Each column is reconstructed top-to-bottom independently
- Columns are combined with `[Column Break]` markers

### Paragraph Detection

Paragraph breaks are detected using vertical spacing:

- Vertical gaps > 5% of page height trigger paragraph breaks
- Blank lines are inserted between paragraphs
- Maintains reading flow within single-column text

### Multi-Page Handling

Pages are processed independently and combined:

- Each page is reconstructed separately
- Pages are joined with `--- Page Break ---` markers
- Page numbers from grounding data are preserved

## Usage Examples

### Basic Usage

```python
from src.ocr.landing_ai_provider import LandingAIOCRProvider

# Initialize provider
config = {
    'api_key': 'land_sk_...',
    'preserve_layout': True
}
provider = LandingAIOCRProvider(config)

# Process document
provider.process_document('input.pdf', 'output.docx')
```

### Layout Reconstruction

```python
from src.utils.layout_reconstructor import reconstruct_layout

# API response chunks with grounding data
chunks = [
    {
        'text': 'Sample text',
        'grounding': {
            'page': 0,
            'box': {'left': 0.1, 'top': 0.1, 'right': 0.9, 'bottom': 0.2}
        }
    }
]

# Reconstruct layout
text = reconstruct_layout(chunks)
```

### Structure Metadata

```python
from src.utils.layout_reconstructor import apply_grounding_to_output

# Extract structure metadata
metadata = apply_grounding_to_output(chunks)

# Returns:
# {
#   'total_pages': 2,
#   'total_chunks': 15,
#   'pages': {
#     0: {'chunks': 8, 'columns': 2, 'has_multi_column': True},
#     1: {'chunks': 7, 'columns': 1, 'has_multi_column': False}
#   }
# }
```

## Testing

### Run Integration Tests

```bash
source venv/bin/activate
python test_landing_ai_integration.py
```

### Test Output

The test script validates:
- BoundingBox calculations
- Single-column layout reconstruction
- Multi-column layout detection
- Multi-page document handling
- Structure metadata extraction
- Provider initialization
- Edge cases and error handling

## Error Handling

### Retry Logic

The provider implements exponential backoff retry:

1. **Attempt 1**: Immediate
2. **Attempt 2**: Wait 2^0 = 1 second
3. **Attempt 3**: Wait 2^1 = 2 seconds

### Fallback Behavior

If layout reconstruction fails:
1. Logs warning with error details
2. Falls back to simple concatenation
3. Continues processing without layout preservation

### HTTP Error Handling

- **4xx errors**: No retry (client error)
- **5xx errors**: Retry with backoff (server error)
- **Timeout**: Retry with backoff
- **Connection errors**: Retry with backoff

## Logging

### Log Levels

- **DEBUG**: Detailed processing information
  - API requests and responses
  - Chunk processing details
  - Layout reconstruction steps
  - File operations

- **INFO**: High-level progress
  - Provider initialization
  - Document processing start/completion
  - API call success
  - Layout reconstruction summary

- **WARNING**: Recoverable issues
  - Missing grounding data
  - Empty chunks
  - Fallback to simple concatenation
  - Retry attempts

- **ERROR**: Processing failures
  - API errors
  - File operations errors
  - Configuration errors

### Log Output Example

```
2025-11-15 12:00:00 | INFO     | EmailReader.OCR.LandingAI | Processing document with LandingAI OCR: input.pdf
2025-11-15 12:00:01 | DEBUG    | EmailReader.OCR.LandingAI | Calling LandingAI API
2025-11-15 12:00:02 | INFO     | EmailReader.OCR.LandingAI | LandingAI API call successful (attempt 1)
2025-11-15 12:00:02 | INFO     | EmailReader.OCR.LandingAI | Received 45 chunks from API
2025-11-15 12:00:02 | INFO     | EmailReader.LayoutReconstructor | Reconstructing layout from 45 chunks
2025-11-15 12:00:02 | DEBUG    | EmailReader.LayoutReconstructor | Detected 2 columns on page
2025-11-15 12:00:02 | INFO     | EmailReader.LayoutReconstructor | Layout reconstruction complete (2 pages, 5432 characters)
2025-11-15 12:00:03 | INFO     | EmailReader.OCR.LandingAI | LandingAI OCR completed in 3.21s: output.docx (5432 characters)
```

## Performance Considerations

### API Timeout

- Default: 30 seconds
- Adjust based on document size and complexity
- Large documents may require higher timeout values

### Retry Strategy

- Default: 3 attempts with 2x backoff
- Balance between resilience and processing time
- Adjust based on API reliability requirements

### Memory Usage

- Layout reconstruction processes all chunks in memory
- Very large documents may require optimization
- Consider chunking for documents with > 10,000 text chunks

## Limitations

1. **API Rate Limits**: Subject to LandingAI API quotas and rate limits
2. **Network Dependency**: Requires internet connection for API calls
3. **Column Detection**: Simple heuristic may not handle complex layouts perfectly
4. **Table Structures**: Basic layout preservation; complex tables may need enhancement

## Future Enhancements

- **Table Detection**: Dedicated table structure recognition
- **Image Preservation**: Extract and preserve images in output
- **Font Styling**: Preserve font information from API
- **Advanced Column Detection**: More sophisticated column detection algorithms
- **Caching**: Cache API responses for duplicate documents
- **Batch Processing**: Process multiple documents in single API call

## Troubleshooting

### "No chunks in API response"

- Check document quality (scan resolution, clarity)
- Verify document contains readable text
- Try different model versions

### "Layout reconstruction failed"

- System falls back to simple concatenation
- Check logs for specific error details
- Verify grounding data is present in API response

### "API call failed after N attempts"

- Check API key validity
- Verify network connectivity
- Check LandingAI service status
- Review timeout settings for large documents

### "Missing grounding data"

- Some chunks may not have grounding information
- System uses safe defaults (page 0, full-width box)
- Warning logged but processing continues

## Support

For issues or questions:
1. Check logs in `logs/email_reader.log`
2. Run integration tests: `python test_landing_ai_integration.py`
3. Verify configuration in `credentials/config.{env}.json`
4. Review LandingAI API documentation: https://docs.landing.ai/api-reference/tools/ade-parse

## References

- [LandingAI ADE Parse API Documentation](https://docs.landing.ai/api-reference/tools/ade-parse)
- [EmailReader OCR System Documentation](./OCR_SYSTEM.md)
- [Configuration Guide](./CONFIGURATION.md)
