# EmailReader Configuration Guide

## Table of Contents

1. Overview
2. Quick Start
3. Configuration Sections
4. Setup Instructions
5. Troubleshooting
6. Migration Guide

---

## 1. OVERVIEW

### What Changed?

OLD SYSTEM (Deprecated):
- credentials/secrets.json (all settings)
- credentials/service-account-key.json (Google auth, separate file)

NEW SYSTEM (Current):
- .env (picks which environment: dev or prod)
- credentials/config.dev.json (all dev settings in one file)
- credentials/config.prod.json (all prod settings in one file)

### How It Works

1. Application reads .env file to determine environment (dev or prod)
2. Loads the appropriate config file: config.dev.json or config.prod.json
3. All settings including Google service account are in ONE file
4. Service account is automatically extracted to a temp file when needed

### Switching Environments

To use development:
  Edit .env → Set: ENV=dev

To use production:
  Edit .env → Set: ENV=prod

---

## 2. QUICK START

### Step 1: Create Environment File

```bash
cp .env.example .env
```

Edit .env and set:
```
ENV=dev
```

### Step 2: Create Config File

```bash
cp credentials/config.template.json credentials/config.dev.json
```

### Step 3: Fill In Required Values

Open credentials/config.dev.json and fill in these REQUIRED fields:

FOR DEFAULT MODE (Standard Processing):
  ✓ app.program = "default_mode"
  ✓ google_drive.parent_folder_id = "your-folder-id"
  ✓ google_drive.service_account = { complete service account JSON }
  ✓ flowise.api_url = "http://localhost:3000/api/v1"
  ✓ flowise.api_key = "your-api-key"
  ✓ flowise.chatflow_id = "your-chatflow-id"
  ✓ flowise.doc_store_id = "your-doc-store-id"
  ✓ flowise.doc_loader_docx_id = "your-loader-id"

FOR TRANSLATOR MODE (Translation Workflow):
  ✓ app.program = "translator"
  ✓ app.translator_url = "http://localhost:8000/submit"
  ✓ google_drive.parent_folder_id = "your-folder-id"
  ✓ google_drive.service_account = { complete service account JSON }

### Step 4: Run Application

```bash
python index.py
```

---

## 3. CONFIGURATION SECTIONS

### Section: app

Controls application behavior and processing mode.

PARAMETER: program
  Type: string
  Required: Yes
  Values: "translator" or "default_mode"
  What it does: Determines which workflow to use
  Used in: index.py line 23

  "default_mode" = Standard processing with FlowiseAI
    - Downloads files from Google Drive
    - Translates to English
    - Uploads to FlowiseAI for analysis

  "translator" = Translation-only workflow
    - Downloads files from Google Drive
    - Translates using external translator
    - Uploads to Completed folder
    - Posts notification to webhook

PARAMETER: translator_url
  Type: string
  Required: Only if program = "translator"
  Example: "http://localhost:8000/submit"
  What it does: Webhook URL to notify when translation completes
  Used in: process_files_for_translation.py

PARAMETER: translator_executable_path
  Type: string
  Required: No
  Example: "/Users/user/projects/GoogleTranslator/translate_document.py"
  What it does: Path to translator script or executable
  Default behavior: Auto-discovers GoogleTranslator project in sibling directory
  Used in: process_files_for_translation.py line 45

EXAMPLE:
```json
"app": {
  "program": "translator",
  "translator_url": "http://localhost:8000/submit",
  "translator_executable_path": "/path/to/translator.py"
}
```

---

### Section: google_drive

Google Drive API configuration and authentication.

PARAMETER: parent_folder_id
  Type: string
  Required: Yes
  What it does: Root Google Drive folder containing client subfolders
  Important: Client folders must have email format in name (contains @ and .)
  How to find: Open folder in Google Drive, ID is in URL after /folders/
  Example: "1XZxSOB1k7MW0QY7XbQ7rd5Xko"
  Used in: google_drive.py line 36

SUBSECTION: service_account
  What it is: Complete Google Service Account credentials
  How to get: Download from Google Cloud Console → IAM & Admin → Service Accounts
  Important: This replaces the old service-account-key.json file

  The service_account subsection contains these fields:

  - type: Always "service_account"
  - universe_domain: Always "googleapis.com"
  - project_id: Your Google Cloud project ID
  - private_key_id: Key identifier (from service account JSON)
  - private_key: RSA private key (MUST include \n for newlines)
  - client_email: Service account email (ends with @*.iam.gserviceaccount.com)
  - client_id: Numeric client ID
  - auth_uri: Always "https://accounts.google.com/o/oauth2/auth"
  - token_uri: Always "https://oauth2.googleapis.com/token"
  - auth_provider_x509_cert_url: Always "https://www.googleapis.com/oauth2/v1/certs"
  - client_x509_cert_url: Certificate URL for your service account

HOW IT WORKS:
  1. Application reads google_drive.service_account from config
  2. Writes it to temporary file: credentials/.service-account-temp.json
  3. Uses temp file for Google Drive API authentication
  4. Temp file is auto-generated and gitignored

EXAMPLE:
```json
"google_drive": {
  "parent_folder_id": "1XZxSOB1k7MW0QY7XbQ7rd5Xko",
  "service_account": {
    "type": "service_account",
    "universe_domain": "googleapis.com",
    "project_id": "my-project-123456",
    "private_key_id": "abc123def456...",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQI...\n-----END PRIVATE KEY-----\n",
    "client_email": "emailreader@my-project-123456.iam.gserviceaccount.com",
    "client_id": "123456789012345678901",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
  }
}
```

---

### Section: flowise

FlowiseAI integration for document analysis (only used in default_mode).

PARAMETER: api_url
  Type: string
  Required: Yes (if using default_mode)
  Format: http://host:port/api/v1
  Example: "http://localhost:3000/api/v1"
  What it does: Base URL for FlowiseAI API
  Used in: flowise_api.py line 42

PARAMETER: api_key
  Type: string
  Required: Yes (if using default_mode)
  Example: "sk-flowise-abc123..."
  What it does: API key for authentication (Bearer token)
  How to get: From FlowiseAI dashboard → API Keys
  Used in: flowise_api.py line 41

PARAMETER: chatflow_id
  Type: string
  Required: Yes (if using default_mode)
  Format: UUID
  Example: "550e8400-e29b-41d4-a716-446655440000"
  What it does: Identifies which chatflow to use for predictions
  How to get: From FlowiseAI dashboard → Chatflows
  Used in: flowise_api.py line 45

PARAMETER: doc_store_id
  Type: string
  Required: Yes (if using default_mode)
  Format: UUID
  Example: "660e8400-e29b-41d4-a716-446655440001"
  What it does: Identifies document store for vector embeddings
  How to get: From FlowiseAI dashboard → Document Stores
  Used in: flowise_api.py line 43

PARAMETER: doc_loader_docx_id
  Type: string
  Required: Yes (if using default_mode)
  Format: UUID
  Example: "770e8400-e29b-41d4-a716-446655440002"
  What it does: Specifies which loader handles DOCX files
  How to get: From FlowiseAI dashboard → Document Loaders
  Used in: flowise_api.py line 44

API ENDPOINTS USED:
  - List stores: {api_url}/document-store/store
  - Upload doc: {api_url}/document-store/{doc_store_id}/loader/{doc_loader_docx_id}/upsert
  - Create prediction: {api_url}/prediction/{chatflow_id}

EXAMPLE:
```json
"flowise": {
  "api_url": "http://localhost:3000/api/v1",
  "api_key": "sk-flowise-abc123def456",
  "chatflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "doc_store_id": "660e8400-e29b-41d4-a716-446655440001",
  "doc_loader_docx_id": "770e8400-e29b-41d4-a716-446655440002"
}
```

---

### Section: scheduling

Controls how often the application processes files.

PARAMETER: google_drive_interval_minutes
  Type: integer
  Required: No
  Default: 15
  Range: 1 to any (recommended: 5-30)
  What it does: Minutes between each Google Drive scan
  Used in: index.py line 50

  How it works:
    - First run: Immediately when app starts
    - Subsequent runs: Every N minutes
    - Example: 15 means app processes files every 15 minutes

PARAMETER: email_interval_minutes
  Type: integer
  Required: No
  Default: 5
  What it does: Minutes between email checks (for future use)
  Currently: Not active, planned for future email processing mode

EXAMPLE:
```json
"scheduling": {
  "google_drive_interval_minutes": 15,
  "email_interval_minutes": 5
}
```

---

### Section: email

IMAP email processing settings (LEGACY - not currently used).

This section is for future email processing mode. Currently the application only processes Google Drive files.

PARAMETER: username
  Type: string
  Example: "documents@company.com"
  What it does: Email account for IMAP login

PARAMETER: password
  Type: string
  Example: "app-specific-password"
  What it does: Email password or app-specific password

PARAMETER: imap_server
  Type: string
  Examples: "imap.gmail.com", "outlook.office365.com"
  What it does: IMAP server hostname

PARAMETER: initial_folder
  Type: string
  Default: "INBOX"
  What it does: Which folder to scan for attachments

PARAMETER: date_file
  Type: string
  Default: "data/last_finish_time.txt"
  What it does: File storing last email scan timestamp

PARAMETER: start_date
  Type: string
  Format: YYYY-MM-DD HH:MM:SS TZ
  Example: "2024-01-01 00:00:00 -0800"
  What it does: Starting date for first email scan

EXAMPLE:
```json
"email": {
  "username": "documents@company.com",
  "password": "app-password-here",
  "imap_server": "imap.gmail.com",
  "initial_folder": "INBOX",
  "date_file": "data/last_finish_time.txt",
  "start_date": "2024-01-01 00:00:00 -0800"
}
```

---

### Section: storage

Local file storage settings.

PARAMETER: documents_folder
  Type: string
  Required: No
  Default: "documents"
  What it does: Subfolder name under data/ for temporary files
  Full path: {project_root}/data/{documents_folder}/

  How it's used:
    - Downloaded files stored here temporarily
    - Processed files staged here
    - Cleaned up after upload to Google Drive

EXAMPLE:
```json
"storage": {
  "documents_folder": "documents"
}
```

---

## 4. SETUP INSTRUCTIONS

### For Default Mode (FlowiseAI Processing)

STEP 1: Get Google Drive Folder ID
  1. Open Google Drive in browser
  2. Navigate to parent folder containing client folders
  3. Copy ID from URL: https://drive.google.com/drive/folders/[THIS-IS-THE-ID]

STEP 2: Get Google Service Account
  1. Go to Google Cloud Console
  2. Navigate to IAM & Admin → Service Accounts
  3. Create or select service account
  4. Click "Keys" → "Add Key" → "Create new key" → JSON
  5. Download JSON file
  6. Copy ENTIRE contents into google_drive.service_account section

STEP 3: Get FlowiseAI Credentials
  1. Open FlowiseAI dashboard
  2. Go to API Keys → Copy your API key
  3. Go to Chatflows → Copy chatflow ID (from URL or settings)
  4. Go to Document Stores → Copy document store ID
  5. Go to Document Loaders → Copy DOCX loader ID

STEP 4: Create Configuration File
  ```bash
  cp credentials/config.template.json credentials/config.dev.json
  ```

STEP 5: Fill In Values
  Edit credentials/config.dev.json:

  ```json
  {
    "environment": "development",
    "app": {
      "program": "default_mode"
    },
    "google_drive": {
      "parent_folder_id": "PASTE-FOLDER-ID-HERE",
      "service_account": {
        PASTE-ENTIRE-SERVICE-ACCOUNT-JSON-HERE
      }
    },
    "flowise": {
      "api_url": "http://localhost:3000/api/v1",
      "api_key": "PASTE-API-KEY-HERE",
      "chatflow_id": "PASTE-CHATFLOW-ID-HERE",
      "doc_store_id": "PASTE-DOC-STORE-ID-HERE",
      "doc_loader_docx_id": "PASTE-LOADER-ID-HERE"
    },
    "scheduling": {
      "google_drive_interval_minutes": 15
    },
    "storage": {
      "documents_folder": "documents"
    }
  }
  ```

STEP 6: Create .env File
  ```bash
  echo "ENV=dev" > .env
  ```

STEP 7: Test Configuration
  ```bash
  python -c "from src.config import load_config; print('✓ Config loaded')"
  ```

STEP 8: Run Application
  ```bash
  python index.py
  ```

---

### For Translator Mode

STEP 1: Get Google Drive Folder ID
  (Same as default mode - see above)

STEP 2: Get Google Service Account
  (Same as default mode - see above)

STEP 3: Locate Translator Script
  Option A: Use GoogleTranslator project
    Path: /path/to/GoogleTranslator/translate_document.py

  Option B: Let app auto-discover
    - Place GoogleTranslator as sibling directory to EmailReader
    - App will find it automatically

STEP 4: Set Up Webhook Endpoint
  - Prepare endpoint to receive POST notifications
  - Example: http://localhost:8000/submit
  - Payload includes: client email, file name, status

STEP 5: Create Configuration File
  ```bash
  cp credentials/config.template.json credentials/config.dev.json
  ```

STEP 6: Fill In Values
  Edit credentials/config.dev.json:

  ```json
  {
    "environment": "development",
    "app": {
      "program": "translator",
      "translator_url": "http://localhost:8000/submit",
      "translator_executable_path": "/path/to/GoogleTranslator/translate_document.py"
    },
    "google_drive": {
      "parent_folder_id": "PASTE-FOLDER-ID-HERE",
      "service_account": {
        PASTE-ENTIRE-SERVICE-ACCOUNT-JSON-HERE
      }
    },
    "scheduling": {
      "google_drive_interval_minutes": 15
    }
  }
  ```

STEP 7: Create .env File
  ```bash
  echo "ENV=dev" > .env
  ```

STEP 8: Run Application
  ```bash
  python index.py
  ```

---

### Setting Up Production

STEP 1: Create Production Config
  ```bash
  cp credentials/config.dev.json credentials/config.prod.json
  ```

STEP 2: Update Production Values
  Edit credentials/config.prod.json:
  - Change environment to "production"
  - Update Google Drive folder ID (production folder)
  - Update service account (production service account)
  - Update FlowiseAI URLs and credentials (production instance)
  - Update translator URL (production webhook)

STEP 3: Switch to Production
  Edit .env:
  ```
  ENV=prod
  ```

STEP 4: Run Application
  ```bash
  python index.py
  ```

---

## 5. TROUBLESHOOTING

### Error: Configuration file not found

SYMPTOM:
  FileNotFoundError: Configuration file not found: credentials/config.dev.json

SOLUTION:
  1. Check .env file exists: ls .env
  2. Check ENV value: cat .env
  3. Check config file exists: ls credentials/config.dev.json
  4. Create from template: cp credentials/config.template.json credentials/config.dev.json

---

### Error: Service account not found

SYMPTOM:
  KeyError: 'google_drive.service_account' not found in configuration

SOLUTION:
  1. Open your config file
  2. Verify google_drive section exists
  3. Verify service_account subsection exists
  4. Copy COMPLETE service account JSON from Google Cloud
  5. Paste entire JSON object (not just path to file)

EXAMPLE OF CORRECT FORMAT:
```json
"google_drive": {
  "parent_folder_id": "...",
  "service_account": {
    "type": "service_account",
    "project_id": "...",
    ... (entire service account JSON)
  }
}
```

---

### Error: Invalid JSON

SYMPTOM:
  json.JSONDecodeError: Expecting property name enclosed in double quotes

SOLUTION:
  1. Validate JSON syntax:
     python -m json.tool credentials/config.dev.json

  2. Common issues:
     - Missing comma between properties
     - Using single quotes instead of double quotes
     - Missing closing brace or bracket
     - Extra comma after last property

  3. Special case - private_key field:
     Must use \n for newlines, not actual newlines

     CORRECT:
     "private_key": "-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n"

     WRONG:
     "private_key": "-----BEGIN PRIVATE KEY-----
     MIIE...
     -----END PRIVATE KEY-----"

---

### Error: Google Drive authentication failed

SYMPTOM:
  google.auth.exceptions.RefreshError
  OR
  HttpError 403: Permission denied

SOLUTION:
  1. Verify service account has access to Google Drive folder
  2. Share folder with service account email (client_email from service account)
  3. Grant "Editor" or "Contributor" permissions
  4. Check service account JSON is complete and unmodified

---

### Error: FlowiseAI connection failed

SYMPTOM:
  Connection refused
  OR
  requests.exceptions.ConnectionError

SOLUTION:
  1. Verify FlowiseAI is running: curl http://localhost:3000/api/v1/
  2. Check api_url is correct (include /api/v1)
  3. Verify API key is valid
  4. Check chatflow_id, doc_store_id exist in FlowiseAI dashboard

---

### Wrong environment loading

SYMPTOM:
  App uses production settings when you expect development

SOLUTION:
  1. Check .env file: cat .env
  2. Verify ENV value matches intended environment
  3. Restart application after changing .env
  4. Check logs at startup: "Environment: dev" or "Environment: prod"

---

### Translator executable not found

SYMPTOM:
  Translator executable not found
  OR
  FileNotFoundError: translate_document

SOLUTION:
  1. Verify translator_executable_path in config:
     cat credentials/config.dev.json | grep translator_executable_path

  2. Check file exists:
     ls -l /path/from/config

  3. For auto-discovery, verify GoogleTranslator location:
     ls ../GoogleTranslator/translate_document.py

  4. Set explicit path in config:
     "translator_executable_path": "/full/path/to/translate_document.py"

---

## 6. MIGRATION GUIDE

### Migrating from Old System

OLD FILES (Don't use these anymore):
  - credentials/secrets.json
  - credentials/service-account-key.json

NEW FILES (Use these now):
  - .env
  - credentials/config.dev.json
  - credentials/config.prod.json

### Step-by-Step Migration

STEP 1: Create Template
  ```bash
  # Template already exists in repo
  ls credentials/config.template.json
  ```

STEP 2: Create Dev Config
  ```bash
  cp credentials/config.template.json credentials/config.dev.json
  ```

STEP 3: Migrate Settings from secrets.json

  Open old secrets.json and new config.dev.json side by side:

  FROM secrets.json → TO config.dev.json:

  program → app.program
  translator_url → app.translator_url
  translator_executable_path → app.translator_executable_path
  parent_folder_id → google_drive.parent_folder_id
  email.* → email.* (same structure)
  flowiseAI.api_url → flowise.api_url
  flowiseAI.api_key → flowise.api_key
  flowiseAI.chatflow_id → flowise.chatflow_id
  flowiseAI.doc_store_id → flowise.doc_store_id
  flowiseAI.doc_loader_docx_id → flowise.doc_loader_docx_id
  scheduling.* → scheduling.* (same structure)

STEP 4: Migrate Service Account

  Open credentials/service-account-key.json
  Copy ENTIRE contents
  Paste into config.dev.json under google_drive.service_account

STEP 5: Create .env File
  ```bash
  echo "ENV=dev" > .env
  ```

STEP 6: Test New Config
  ```bash
  python -c "from src.config import load_config, get_service_account_path; \
             config = load_config(); \
             sa_path = get_service_account_path(); \
             print('✓ Config loaded'); \
             print('✓ Service account extracted to:', sa_path)"
  ```

STEP 7: Run Test Processing
  ```bash
  python src/app.py
  ```

  Watch for:
  - "Loading configuration from: credentials/config.dev.json"
  - "Google Drive API client initialized successfully"
  - No errors about missing files

STEP 8: Create Production Config
  ```bash
  cp credentials/config.dev.json credentials/config.prod.json
  ```

  Edit config.prod.json with production values

STEP 9: Backup Old Files
  ```bash
  mkdir credentials/backup_old_system
  mv credentials/secrets.json credentials/backup_old_system/
  mv credentials/service-account-key.json credentials/backup_old_system/
  ```

STEP 10: Update Documentation
  - Update any internal docs referencing secrets.json
  - Update deployment scripts to use .env
  - Update team instructions

---

## QUICK REFERENCE

### Files You Need

MUST CREATE:
  ✓ .env (contains: ENV=dev or ENV=prod)
  ✓ credentials/config.dev.json (development settings)
  ✓ credentials/config.prod.json (production settings)

AUTO-GENERATED (don't create manually):
  - credentials/.service-account-temp.json (created by app, gitignored)

TEMPLATES (already in repo):
  - .env.example
  - credentials/config.template.json

### Essential Commands

Check environment:
  cat .env

Validate config JSON:
  python -m json.tool credentials/config.dev.json

Test config loading:
  python -c "from src.config import load_config; print(load_config()['app']['program'])"

Get service account path:
  python -c "from src.config import get_service_account_path; print(get_service_account_path())"

Switch to production:
  echo "ENV=prod" > .env

Switch to development:
  echo "ENV=dev" > .env

### What Goes in .gitignore

PROTECTED (never commit):
  .env
  credentials/config.*.json (except config.template.json)
  credentials/.service-account-temp.json

SAFE TO COMMIT:
  .env.example
  credentials/config.template.json

### Getting Help

Configuration loading code:
  src/config.py

Main entry point:
  index.py

Google Drive integration:
  src/google_drive.py

FlowiseAI integration:
  src/flowise_api.py

Translation mode:
  src/process_files_for_translation.py

---

Last Updated: 2025-11-11
Version: 2.0
