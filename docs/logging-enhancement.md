# Google Document Translator - Logging Enhancement Summary

## Overview
Enhanced the `google_doc_translator.py` with comprehensive DEBUG-level logging to diagnose connection and API endpoint issues.

## Changes Made

### 1. Enhanced Initialization Logging (`__init__`)
Added detailed logging during client initialization:

- **Configuration Display**: Shows all config parameters (project_id, location, endpoint, use_service_account, mime_type)
- **Environment Variables**: Checks and logs GOOGLE_APPLICATION_CREDENTIALS path and file existence
- **Endpoint Configuration**:
  - Logs whether using custom or default endpoint
  - Shows full API endpoint URL construction
  - Displays expected Google API endpoints for reference
- **Transport Details**: Attempts to log internal transport/connection information
- **Success/Failure Markers**: Clear visual separators (=== lines) for initialization status

### 2. Enhanced API Call Logging (`_call_translation_api`)
Added comprehensive logging for each API request:

- **Request Details**:
  - Parent path (projects/{project}/locations/{location})
  - Target and source language codes
  - Document size in bytes and KB
  - Full API URL that will be called

- **Payload Configuration**:
  - MIME type used for document
  - Content length and type
  - Source language auto-detect status

- **Connection Information**:
  - Transport host and type
  - Request object details

- **Response Details**:
  - API call duration
  - Translated content size
  - Size change percentage
  - Detected source language (if auto-detected)
  - Response MIME type

### 3. Enhanced Error Logging
Comprehensive error handling with specific diagnostics:

- **Google API Errors**:
  - Logs gRPC status codes
  - Full error messages
  - Request details for debugging

- **Specific Error Types**:
  - UNAUTHENTICATED: Shows credentials path
  - PERMISSION_DENIED: Suggests checking permissions/quota
  - NOT_FOUND: Suggests checking project ID, location, endpoint
  - INVALID_ARGUMENT: Suggests checking request parameters

- **Unexpected Errors**:
  - Full exception type and message
  - Complete stack trace
  - All request parameters for debugging

## Configuration Analysis

### Current config.dev.json Settings
```json
"translation": {
  "provider": "google_doc",
  "google_doc": {
    "project_id": "synologysafeaccess-320003",
    "location": "global",
    "endpoint": "translate.googleapis.com",
    "use_service_account": true,
    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  }
}
```

### Configuration Issues Identified

#### 1. Location Setting: ❌ INCORRECT
```json
"location": "global"
```

**Problem**: `global` is NOT a valid location for the Document Translation API.

**Valid Locations**:
- `us-central1` (recommended for US)
- `europe-west1` (recommended for Europe)
- `asia-east1` (recommended for Asia)
- Other regional locations

**Recommendation**:
```json
"location": "us-central1"
```

#### 2. Endpoint Format: ⚠️ POTENTIALLY INCORRECT
```json
"endpoint": "translate.googleapis.com"
```

**Issue**: This endpoint format may not work correctly with the location-based API.

**Options**:

**Option A - Use Default Endpoint (Recommended)**:
```json
"translation": {
  "provider": "google_doc",
  "google_doc": {
    "project_id": "synologysafeaccess-320003",
    "location": "us-central1",
    "use_service_account": true
  }
}
```
Remove the `endpoint` field entirely. The Google Cloud SDK will automatically use the correct endpoint.

**Option B - Use Regional Endpoint**:
```json
"endpoint": "us-central1-translate.googleapis.com"
```

**Option C - Keep Global Endpoint**:
```json
"endpoint": "translate.googleapis.com"
```
Only if you're certain this works with your API configuration.

## Expected API URL Construction

With the enhanced logging, you'll see the exact URL being called:

### Current Configuration
```
Base URL: https://translate.googleapis.com
Parent: projects/synologysafeaccess-320003/locations/global
Full URL: https://translate.googleapis.com/v3/projects/synologysafeaccess-320003/locations/global:translateDocument
```

### Recommended Configuration (Option A)
```
Base URL: https://translate.googleapis.com (auto-selected)
Parent: projects/synologysafeaccess-320003/locations/us-central1
Full URL: https://translate.googleapis.com/v3/projects/synologysafeaccess-320003/locations/us-central1:translateDocument
```

### Regional Endpoint Configuration (Option B)
```
Base URL: https://us-central1-translate.googleapis.com
Parent: projects/synologysafeaccess-320003/locations/us-central1
Full URL: https://us-central1-translate.googleapis.com/v3/projects/synologysafeaccess-320003/locations/us-central1:translateDocument
```

## How to Use the Enhanced Logging

### 1. Enable DEBUG Logging
Ensure your logging configuration includes DEBUG level for the translator:

```python
import logging

# Set DEBUG level for translation module
logging.getLogger('EmailReader.Translation.GoogleDoc').setLevel(logging.DEBUG)

# Or set for all EmailReader modules
logging.getLogger('EmailReader').setLevel(logging.DEBUG)
```

### 2. Check Log Output
When the translator initializes, you'll see:
```
================================================================================
INITIALIZING GOOGLE CLOUD TRANSLATION API v3 CLIENT
================================================================================
Full configuration received:
  - project_id: synologysafeaccess-320003
  - location: global
  - endpoint: translate.googleapis.com
  - use_service_account: True
  - mime_type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
Environment variables:
  - GOOGLE_APPLICATION_CREDENTIALS: /path/to/credentials.json
  - Credentials file exists: YES
  - Credentials file size: 2345 bytes
...
```

### 3. During API Calls
```
================================================================================
CALLING GOOGLE TRANSLATION API v3
================================================================================
Request Configuration:
  - Parent path: projects/synologysafeaccess-320003/locations/global
  - Target language: en
  - Source language: auto-detect
  - Document size: 54321 bytes (53.05 KB)
API Endpoint Details:
  - Project ID: synologysafeaccess-320003
  - Location: global
  - Endpoint: translate.googleapis.com
  - Full API URL: https://translate.googleapis.com/v3/projects/synologysafeaccess-320003/locations/global:translateDocument
...
```

### 4. Error Diagnostics
If an error occurs:
```
================================================================================
GOOGLE TRANSLATION API ERROR
================================================================================
Error Type: GoogleAPIError
Error Details:
  - Status code: NOT_FOUND
  - Message: Location 'global' not found
  - Full error: 404 Location not found: global
Request Details (for debugging):
  - API URL: https://translate.googleapis.com/v3/projects/synologysafeaccess-320003/locations/global:translateDocument
  - Parent: projects/synologysafeaccess-320003/locations/global
  - Project ID: synologysafeaccess-320003
  - Location: global
  - Target language: en
  - Endpoint: translate.googleapis.com
NOT FOUND - Check project ID, location, and endpoint
================================================================================
```

## Recommended Actions

### 1. Immediate Fix - Update config.dev.json
```json
"translation": {
  "provider": "google_doc",
  "google_doc": {
    "project_id": "synologysafeaccess-320003",
    "location": "us-central1",
    "use_service_account": true,
    "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  }
}
```

### 2. Verify API is Enabled
Ensure the Cloud Translation API is enabled for your project:
```bash
gcloud services enable translate.googleapis.com --project=synologysafeaccess-320003
```

### 3. Verify Service Account Permissions
The service account needs these roles:
- `roles/cloudtranslate.user` or
- `roles/cloudtranslate.editor`

### 4. Test with Enhanced Logging
Run a translation test and examine the detailed logs to confirm:
- Correct endpoint is being used
- Credentials are loading properly
- API URL is correctly constructed
- Response is successful

## Files Modified

1. `/Users/vladimirdanishevsky/projects/EmailReader/src/translation/google_doc_translator.py`
   - Enhanced `__init__()` with detailed initialization logging
   - Enhanced `_call_translation_api()` with comprehensive request/response logging
   - Added specific error type diagnostics

## Next Steps

1. ✅ Update `config.dev.json` with correct location (`us-central1` instead of `global`)
2. ✅ Remove `endpoint` field to use default (or update to regional endpoint)
3. ✅ Run a test translation to verify the fix
4. ✅ Review logs to confirm correct API endpoint is being used
5. ✅ Update `config.prod.json` with the same corrections

## References

- [Google Cloud Translation API Documentation](https://cloud.google.com/translate/docs)
- [Document Translation API Reference](https://cloud.google.com/translate/docs/advanced/translating-documents-v3)
- [Supported Locations](https://cloud.google.com/translate/docs/advanced/locations)
