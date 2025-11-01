# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EmailReader is a document processing pipeline that monitors Google Drive folders, processes documents (conversion, OCR, translation), and integrates with FlowiseAI for document analysis and predictions.

## Running the Application

### Setup
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt-get install tesseract-ocr-all poppler-utils
```

### Run
```bash
# Main application (scheduler mode)
python index.py

# Runs process_google_drive() or process_files_for_translation() every N minutes
# Interval configured in credentials/secrets.json
```

## Architecture

### Processing Flow

```
index.py (scheduler)
    ↓
process_google_drive() [main orchestrator]
    ↓
For each client folder in Google Drive:
    1. Download document from Inbox
    2. Convert/OCR (process_documents.py)
    3. Optional: Translate (process_files_for_translation.py)
    4. Upload to FlowiseAI document store (flowise_api.py)
    5. Create FlowiseAI prediction
    6. Move to In-Progress folder
    7. Cleanup local files
```

### Key Components

**Entry Points:**
- `index.py` - Scheduler that runs main processing loop every N minutes
- `src/app.py` - Placeholder for future FastAPI web server (currently minimal)

**Main Orchestration:**
- `src/process_google_drive.py` - Core processing logic, loops through client folders
- `src/process_files_for_translation.py` - Translation workflow mode

**External API Clients:**
- `src/flowise_api.py` - FlowiseAI API wrapper (document storage + predictions)
- `src/google_drive.py` - Google Drive API wrapper (download, upload, move files)

**Document Processing:**
- `src/process_documents.py` - DocProcessor class (PDF→Word, OCR, format conversion)
- `src/pdf_image_ocr.py` - OCR for image-based PDFs
- `src/convert_to_docx.py` - Format conversion utilities

**Utilities:**
- `src/logger.py` - Enhanced logging with HTTP request/response logging
- `src/utils.py` - Common utilities (file operations, config reading)

### Two Operating Modes

Configured via `credentials/secrets.json` → `"program"` field:

1. **"default_mode"** - Standard document processing (no translation)
2. **"translator"** - Runs translation workflow via external executable

## Configuration

### Main Config: `credentials/secrets.json`

```json
{
  "program": "default_mode",  // or "translator"
  "scheduling": {
    "google_drive_interval_minutes": 15
  },
  "flowiseAI": {
    "API_KEY": "...",
    "API_URL": "...",
    "DOC_STORE_ID": "...",
    "DOC_LOADER_DOCX_ID": "...",
    "CHATFLOW_ID": "..."
  },
  "google_drive": {
    "parent_folder_id": "..."  // Root folder containing client folders
  }
}
```

### Google Drive Authentication

Service account credentials: `credentials/service-account-key.json`

### Expected Google Drive Structure

```
Parent Folder (parent_folder_id)
├── client1@email.com/
│   ├── Inbox/           ← New documents here
│   ├── In-Progress/     ← Processed documents moved here
│   └── Temp/
├── client2@email.com/
│   ├── Inbox/
│   ├── In-Progress/
│   └── Temp/
```

**Important:** Client folders MUST contain `@` and `.` in name (email format detection)

## Document Processing Pipeline

### Supported Input Formats
- `.docx`, `.doc` - Word documents
- `.pdf` - PDFs (searchable or image-based with OCR)
- `.rtf` - Rich Text Format
- `.txt` - Plain text
- `.gif`, `.jpg`, `.png`, `.tiff` - Images (with OCR)

### Processing Steps

1. **Download** from Google Drive Inbox
2. **Convert/OCR** to `.docx` format
   - PDFs: Extract text or run OCR if image-based
   - Images: Run Tesseract OCR
   - Other formats: Convert to DOCX
3. **Optional Translation** (if program="translator")
   - Calls external `translate_document` executable
   - Detects source language, translates to target language
4. **Upload to FlowiseAI**
   - Document name format: `client@email.com+OriginalName.docx`
   - Uploaded to configured document store
5. **Create Prediction**
   - Sends document name to FlowiseAI chatflow
   - Waits for AI processing
6. **Move Original** from Inbox to In-Progress
7. **Cleanup** local temporary files

### File Naming Convention

Throughout processing, files use this naming pattern:
- **Original**: `document.pdf`
- **After OCR**: `document+english.docx` (if translated to English)
- **Upload to Drive**: `client@email.com+document.docx`
- **FlowiseAI name**: `client@email.com+document.docx` (via `build_flowise_question()`)

## Logging

### Log Location
`data/logs/emailreader_YYYYMMDD.log`

### Log Configuration
- Rotating file handler (10MB max, 5 backups)
- Console output with timestamps
- Module-specific loggers:
  - `EmailReader` (root)
  - `EmailReader.Flowise`
  - `EmailReader.GoogleDrive`
  - `EmailReader.DocProcessor`

### HTTP Request/Response Logging

All HTTP requests to FlowiseAI are comprehensively logged:
- Request: method, URL, headers (sanitized), body, timeout
- Response: status, duration, headers, body (truncated), size
- API keys are masked in logs (`Bearer sk-abc...xyz1`)

See `LOGGING_ENHANCEMENTS.md` for details.

## HTTP API Integration (FlowiseAI)

All HTTP methods in `flowise_api.py`:
- **GET**: List/get document stores, get document pages
- **POST**: Create stores, upload documents, create predictions
- **PUT**: Update stores
- **DELETE**: Delete stores

Authentication: Bearer token via `Authorization` header

Timeouts:
- Standard: 10 seconds
- File uploads: 60 seconds
- Predictions: 30 seconds

## Web Server Integration

For integrating EmailReader with an existing FastAPI web server, see `WEBSERVER_INTEGRATION.md`.

Key integration points:
- Import `process_google_drive()` function
- Trigger via BackgroundTasks or threading
- Optional: Register Google Drive webhooks for real-time processing

## Important Implementation Details

### Client Folder Detection
```python
# Client folders must have '@' and '.' in name
client_folders = [c for c in clients if '@' in c['name'] and '.' in c['name']]
```

### Document Naming for FlowiseAI
The `build_flowise_question()` function strips processing suffixes (`+english`, `+translated`) and ensures `.docx` extension:
```python
# Input: "letter+english.docx" or "letter.pdf"
# Output: "client@email.com+letter.docx"
```

### Translation Detection
Translation is triggered by:
1. `program="translator"` in config, OR
2. Google Drive file has `targetLanguage` app property

### Error Handling Philosophy
- Document processing errors are logged but don't crash the scheduler
- Each file processes independently
- Failed files remain in Inbox for retry on next cycle
- FlowiseAI errors return `{'name': 'Error', 'error': 'message'}` dict

## Development Notes

### System Dependencies Required
- **tesseract-ocr**: OCR for image-based PDFs and images
- **poppler-utils**: PDF processing (`pdfinfo`, `pdftotext`)

### External Executable
Translation mode expects `translate_document` executable in project root:
```bash
./translate_document -i input.docx -o output.docx --target en
```

### Temporary Files
All processing uses `data/documents/` directory. Files are cleaned up after successful processing.

### Google Drive Properties
Files can have custom app properties:
```python
google_api.get_file_app_property(file_id, 'targetLanguage')  # e.g., "en", "fr"
```
