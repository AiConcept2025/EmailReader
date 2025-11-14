# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EmailReader is a Python application that processes documents from email attachments and Google Drive, performs OCR and translation, and integrates with FlowiseAI for document analysis. The application supports two modes: standard document processing and translation workflow.

## Setup and Installation

### Environment Setup
```bash
# Activate virtual environment
./venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt
```

### External Dependencies
- **Tesseract OCR**: Required for PDF image OCR processing
  - Ubuntu: `sudo apt-get install tesseract-ocr-all`
  - Download: https://github.com/tesseract-ocr/tesseract

- **Poppler**: Required for PDF processing
  - Ubuntu: `sudo apt-get install -y poppler-utils`
  - Verify: `which pdfinfo` should return `/usr/bin/pdfinfo`

### Configuration

The application uses environment-aware configuration files:

- **credentials/config.{env}.json**: Main configuration file (env = dev or prod)
  - Controlled by `ENV` environment variable (defaults to `dev`)
  - `app.program`: Mode selector ("translator" or default)
  - `scheduling.google_drive_interval_minutes`: Processing interval (default: 15 minutes)
  - `google_drive.parent_folder_id`: Google Drive parent folder ID
  - `email`: Email configuration (for email processing mode)
  - `google_drive`: Google Drive API settings
  - `flowise`: FlowiseAI API credentials
  - `app.translator_url`: URL for translation service notifications
  - `google_drive.service_account`: Google Service Account credentials (embedded)

- **credentials/config.template.json**: Template for creating new config files

**Environment Selection:**
```bash
# Use development config (default)
export ENV=dev  # Loads config.dev.json

# Use production config
export ENV=prod  # Loads config.prod.json
```

## Running the Application

### Main Entry Point
```bash
python index.py
```

This starts the scheduled processing loop that runs every N minutes (configured in config.{env}.json).

### Manual Processing
```bash
# For Google Drive processing
python src/app.py
```

## Architecture

### Application Modes

The application has two distinct operational modes controlled by the `app.program` field in `credentials/config.{env}.json`:

1. **Default Mode** (`process_google_drive()`):
   - Downloads files from client Google Drive Inbox folders
   - Processes documents (PDF/Word/RTF/text)
   - Translates non-English documents to English
   - Uploads to FlowiseAI document store
   - Creates predictions via FlowiseAI
   - Moves processed files to In-Progress folder

2. **Translator Mode** (`process_files_for_translation()`):
   - Uses external `translate_document` executable
   - Downloads files from Google Drive Inbox
   - Translates using subprocess call to translator
   - Uploads translated files to Completed folder
   - Posts notification to external webhook

### Core Processing Flow

#### Standard Mode Flow (process_google_drive):
1. Scan Google Drive parent folder for client folders (identified by email format: `@` and `.` in name)
2. For each client folder:
   - Ensure subfolders exist: `Inbox`, `In-Progress`, `Temp`
   - Get files from Inbox folder
   - Download file locally
   - Process based on type:
     - **Word (.doc/.docx)**: Check language → rename as `+english` or translate → rename as `+translated`
     - **PDF**: Check if searchable → OCR if needed → translate → convert to DOCX
   - Upload processed file to In-Progress as `{client_email}+{filename}+{suffix}.docx`
   - Upload to FlowiseAI doc store with name: `{client_email}+{filename}+{suffix}`
   - Create prediction with same name
   - Wait 2 minutes (for processing)
   - Move original from Inbox to In-Progress
   - Clean up local temp files

#### File Naming Convention (Standard Mode):
- Input: `document.docx`
- If English: `client@email.com+document+english.docx`
- If foreign:
  - Original: `client@email.com+document+original.docx`
  - Translated: `client@email.com+document+translated.docx`

### Key Components

#### GoogleApi (src/google_drive.py)
Wrapper for Google Drive API v3 operations:
- `get_file_list_in_folder()`: List files in a folder
- `get_subfolders_list_in_folder()`: List subfolders
- `upload_file_to_google_drive()`: Upload file with metadata and properties
- `download_file_from_google_drive()`: Download file by ID
- `move_file_to_folder_id()`: Move file between folders
- `get_file_app_property()`: Read appProperties (e.g., `targetLanguage`)
- Uses service account authentication from `credentials/service-account-key.json`

#### DocProcessor (src/process_documents.py)
Handles document conversion and processing:
- `process_word_file()`: Language detection → rename or translate Word docs
- `convert_pdf_file_to_word()`: PDF → OCR (if needed) → DOCX → translate
- `convert_plain_text_to_word()`: TXT → DOCX with language detection
- `convert_rtf_text_to_world()`: RTF → plain text → DOCX → translate
- Returns tuple: `(new_file_path, new_file_name, original_file_name, original_file_path)`

#### FlowiseAiAPI (src/flowise_api.py)
FlowiseAI integration for document analysis:
- `upsert_document_to_document_store()`: Upload document for vector embedding
  - Requires: doc_path, doc_name, store_id, loader_id
  - Returns dict with success/error
- `create_new_prediction()`: Create AI prediction/analysis for a document
  - Input: doc_name (should match upserted document name)
  - Returns prediction result
- Critical: Document name must be identical for both upsert and prediction

#### Email Processing (src/email_reader.py)
Legacy email processing (currently not active):
- Reads IMAP mailbox for new emails
- Processes attachments with supported types
- Tracks last scan time in `data/last_finish_time.txt`

### Supported File Types
- Documents: `.doc`, `.docx`, `.pdf`, `.txt`, `.rtf`
- Images (for OCR): `.gif`, `.jpg`, `.png`, `.tiff`, `.tif`
- MIME types handled in `email_reader.py:supported_types`

### Language Detection and Translation
- Uses `langdetect` library to identify document language
- Translation handled by:
  - Standard mode: `utils.translate_document_to_english()` (uses `doctr` library)
  - Translator mode: External `translate_document` executable with `--source` and `--target` args
- Supports optional `targetLanguage` from Google Drive file's appProperties

## File Structure

```
EmailReader/
├── index.py                    # Main entry point with scheduler
├── src/
│   ├── app.py                  # Manual processing entry
│   ├── email_reader.py         # Email/IMAP processing (legacy)
│   ├── google_drive.py         # Google Drive API wrapper
│   ├── process_google_drive.py # Main Google Drive processing logic
│   ├── process_files_for_translation.py  # Translation mode logic
│   ├── process_documents.py    # Document conversion and processing
│   ├── flowise_api.py          # FlowiseAI API integration
│   ├── pdf_image_ocr.py        # PDF OCR utilities
│   ├── convert_to_docx.py      # Document conversion utilities
│   ├── logger.py               # Logging configuration
│   └── utils.py                # Utility functions
├── data/
│   ├── documents/              # Temporary document storage
│   └── last_finish_time.txt    # Last email scan timestamp
├── credentials/
│   ├── secrets.json            # Configuration and API keys
│   └── service-account-key.json # Google service account
└── requirements.txt            # Python dependencies
```

## Logging

The application uses Python's logging module with hierarchical loggers:
- `EmailReader.GoogleDrive`: Google Drive processing logs
- `EmailReader.Flowise`: FlowiseAI API interaction logs
- Logs include detailed operation tracking: downloads, uploads, predictions, errors
- Key log patterns:
  - `DOWNLOAD original: id=... name=...`
  - `UPLOAD to In-Progress: ...`
  - `DOC STORE upload name: ...`
  - `PREDICTION send: ...`

## Testing

No formal test suite currently exists. Manual testing via:
```bash
python src/app.py  # Test single processing run
```

## Common Workflows

### Adding Support for New File Types
1. Add MIME type to `supported_types` in `src/email_reader.py`
2. Add processing logic in `DocProcessor` class
3. Handle conversion to Word format in `process_google_drive.py` or `process_documents.py`

### Debugging Document Processing Issues
1. Check logs for `DOWNLOAD` and `UPLOAD` operations
2. Verify file exists in `data/documents/` folder
3. Check FlowiseAI API responses in logs
4. Ensure `targetLanguage` appProperty is set correctly if translation fails

### Modifying Translation Behavior
- Standard mode: Edit `src/utils.py:translate_document_to_english()`
- Translator mode: Update subprocess call in `src/process_files_for_translation.py:translate_document()`
- Language detection threshold in `DocProcessor` methods

## Important Notes

- **File Naming**: The system uses `+` as a delimiter in filenames to separate client email, original name, and processing status
- **Synchronization**: 2-minute wait after prediction creation before moving files (allows FlowiseAI processing time)
- **Error Handling**: Most operations return success/failure dicts with `{'name': 'Error', 'id': error_msg}` pattern
- **Temp Files**: Always cleaned up after processing to avoid disk space issues
- **Google Drive Structure**: Client folders must contain email format in name; subfolders are auto-created if missing
