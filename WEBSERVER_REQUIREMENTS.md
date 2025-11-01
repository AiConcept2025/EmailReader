# Web Server Requirements for EmailReader Integration

## Document Information
- **Project**: EmailReader Web Server API
- **Purpose**: REST API and Webhook Server for EmailReader Application
- **Target Branch**: `claude/document-http-webhook-011CUhLcHo5q96CqBMCMxzt1`
- **Date**: 2025-11-01
- **Status**: Requirements Specification

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Current Architecture](#current-architecture)
3. [Technical Requirements](#technical-requirements)
4. [API Endpoints Specification](#api-endpoints-specification)
5. [Integration Points](#integration-points)
6. [Security Requirements](#security-requirements)
7. [Configuration](#configuration)
8. [Error Handling](#error-handling)
9. [Testing Requirements](#testing-requirements)
10. [Deployment](#deployment)
11. [Success Criteria](#success-criteria)

---

## 1. Project Overview

### 1.1 Context
The EmailReader application currently operates on a **scheduled polling model**, processing documents from Google Drive every 15 minutes (configurable). This web server will enable:

1. **REST API** for programmatic control of EmailReader
2. **Webhook endpoints** for real-time event processing
3. **Status monitoring** and health checks
4. **Manual trigger** capabilities for document processing

### 1.2 Goals
- Reduce processing latency from 15 minutes to near real-time
- Provide external API for integration with other systems
- Enable webhook-driven workflows (Google Drive, FlowiseAI)
- Maintain backward compatibility with scheduled processing

### 1.3 Non-Goals
- Replace the existing scheduler entirely (keep both options)
- Modify core document processing logic in `src/process_google_drive.py`
- Change authentication mechanisms for external APIs (Google Drive, FlowiseAI)

---

## 2. Current Architecture

### 2.1 Application Structure
```
EmailReader/
├── index.py                    # Scheduler entry point
├── src/
│   ├── app.py                 # [IMPLEMENT HERE] Web server
│   ├── flowise_api.py         # FlowiseAI HTTP client
│   ├── google_drive.py        # Google Drive API
│   ├── process_google_drive.py # Main processing orchestrator
│   ├── process_documents.py   # Document conversion/OCR
│   └── logger.py              # Logging infrastructure
└── credentials/
    ├── secrets.json           # Configuration
    └── service-account-key.json # Google credentials
```

### 2.2 Current Processing Flow
```
Scheduler (every 15 min)
    ↓
process_google_drive()
    ├── Get client folders from Google Drive
    ├── For each client's Inbox folder:
    │   ├── Download document
    │   ├── Convert/OCR/Translate (if needed)
    │   ├── Upload to FlowiseAI document store
    │   ├── Create FlowiseAI prediction
    │   ├── Move to In-Progress folder
    │   └── Cleanup local files
    └── Complete
```

### 2.3 Key Dependencies
```python
# From requirements.txt (inferred)
flask                  # Web framework
requests              # HTTP client
google-api-python-client
google-auth
schedule              # Current scheduler
python-docx           # Document processing
pytesseract           # OCR
pdf2image             # PDF conversion
```

---

## 3. Technical Requirements

### 3.1 Technology Stack

**Required**:
- **Framework**: Flask 3.0+
- **Python**: 3.10+ (match existing codebase)
- **WSGI Server**: Gunicorn (production) or Flask dev server (development)
- **Authentication**: JWT or API Key based
- **Validation**: Flask-RESTX or Marshmallow for request validation

**Optional** (for enhanced functionality):
- **Rate Limiting**: Flask-Limiter
- **CORS**: Flask-CORS (if needed for web clients)
- **API Documentation**: Swagger/OpenAPI (via Flask-RESTX)

### 3.2 File Location
- **Main file**: `src/app.py`
- **Additional modules** (if needed):
  - `src/api_auth.py` - Authentication/authorization
  - `src/api_routes.py` - Route definitions
  - `src/webhook_handlers.py` - Webhook processing logic

### 3.3 Server Configuration
```python
# Development
HOST = "127.0.0.1"
PORT = 5000

# Production
HOST = "0.0.0.0"
PORT = 8080  # or from environment variable
```

---

## 4. API Endpoints Specification

### 4.1 Health & Status Endpoints

#### `GET /health`
**Purpose**: Health check for load balancers/monitoring

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-11-01T10:30:00Z",
  "version": "1.0.0"
}
```

#### `GET /api/v1/status`
**Purpose**: Application status and configuration

**Authentication**: Required

**Response** (200 OK):
```json
{
  "scheduler": {
    "enabled": true,
    "interval_minutes": 15,
    "next_run": "2025-11-01T10:45:00Z",
    "last_run": "2025-11-01T10:30:00Z"
  },
  "webhooks": {
    "enabled": true,
    "google_drive": {
      "registered": true,
      "channel_id": "unique-channel-id",
      "expires_at": "2025-11-02T10:30:00Z"
    },
    "flowise": {
      "url": "https://flowise-instance.com",
      "connected": true
    }
  },
  "processing": {
    "active_jobs": 2,
    "queued_jobs": 0,
    "total_processed_today": 45
  }
}
```

---

### 4.2 Processing Control Endpoints

#### `POST /api/v1/process/trigger`
**Purpose**: Manually trigger document processing cycle

**Authentication**: Required

**Request Body**:
```json
{
  "client_email": "optional@email.com",  // Process specific client only
  "force": false                          // Force reprocess even if no new files
}
```

**Response** (202 Accepted):
```json
{
  "job_id": "uuid-v4",
  "status": "queued",
  "message": "Processing started",
  "started_at": "2025-11-01T10:30:00Z"
}
```

**Error Response** (409 Conflict):
```json
{
  "error": "Processing already in progress",
  "active_job_id": "existing-uuid"
}
```

#### `GET /api/v1/process/status/{job_id}`
**Purpose**: Check status of processing job

**Authentication**: Required

**Response** (200 OK):
```json
{
  "job_id": "uuid-v4",
  "status": "in_progress",  // queued, in_progress, completed, failed
  "progress": {
    "current": 3,
    "total": 10,
    "current_file": "client@email.com/document.pdf"
  },
  "started_at": "2025-11-01T10:30:00Z",
  "completed_at": null,
  "errors": []
}
```

#### `GET /api/v1/process/history`
**Purpose**: Get processing history

**Authentication**: Required

**Query Parameters**:
- `limit`: int (default: 50, max: 200)
- `offset`: int (default: 0)
- `status`: string (all, completed, failed)

**Response** (200 OK):
```json
{
  "total": 150,
  "limit": 50,
  "offset": 0,
  "jobs": [
    {
      "job_id": "uuid-v4",
      "status": "completed",
      "files_processed": 5,
      "started_at": "2025-11-01T09:30:00Z",
      "completed_at": "2025-11-01T09:35:00Z",
      "duration_seconds": 300
    }
  ]
}
```

---

### 4.3 Webhook Endpoints

#### `POST /webhook/google-drive`
**Purpose**: Receive Google Drive push notifications

**Authentication**: Signature verification (X-Goog-Channel-Token)

**Request Headers**:
```
X-Goog-Channel-ID: unique-channel-id
X-Goog-Channel-Token: verification-token
X-Goog-Resource-ID: resource-id
X-Goog-Resource-State: update|sync
X-Goog-Changed: content,properties
```

**Request Body**: (may be empty)

**Response** (200 OK):
```json
{
  "status": "received",
  "action": "processing_triggered"
}
```

**Implementation Logic**:
1. Verify channel token matches configured value
2. Ignore "sync" messages (initial handshake)
3. For "update" messages:
   - Extract folder/file information
   - Trigger `process_google_drive()` asynchronously
   - Return 200 immediately (don't wait for processing)

#### `POST /webhook/flowise`
**Purpose**: Receive FlowiseAI processing notifications (future use)

**Authentication**: HMAC signature verification

**Request Headers**:
```
X-Flowise-Signature: sha256=<signature>
X-Flowise-Event: prediction.completed|document.processed
```

**Request Body**:
```json
{
  "event": "prediction.completed",
  "chatflow_id": "chatflow-id",
  "data": {
    "prediction_id": "prediction-uuid",
    "document_name": "client@email.com+document.docx",
    "status": "completed",
    "result": "..."
  },
  "timestamp": "2025-11-01T10:30:00Z"
}
```

**Response** (200 OK):
```json
{
  "status": "received"
}
```

---

### 4.4 Configuration Endpoints

#### `GET /api/v1/config`
**Purpose**: Get current configuration (sanitized)

**Authentication**: Required

**Response** (200 OK):
```json
{
  "program_mode": "default_mode",
  "scheduling": {
    "interval_minutes": 15
  },
  "flowise": {
    "url": "https://flowise-instance.com",
    "doc_store_id": "store-id"
  },
  "google_drive": {
    "parent_folder_id": "folder-id"
  }
}
```

**Note**: API keys and secrets must NOT be included in response

#### `PUT /api/v1/config/scheduler`
**Purpose**: Update scheduler configuration

**Authentication**: Required

**Request Body**:
```json
{
  "enabled": true,
  "interval_minutes": 30
}
```

**Response** (200 OK):
```json
{
  "status": "updated",
  "scheduler": {
    "enabled": true,
    "interval_minutes": 30,
    "next_run": "2025-11-01T11:00:00Z"
  }
}
```

---

### 4.5 Webhook Management Endpoints

#### `POST /api/v1/webhooks/google-drive/register`
**Purpose**: Register Google Drive webhook subscription

**Authentication**: Required

**Request Body**:
```json
{
  "folder_id": "optional-folder-id",  // default: parent_folder_id from config
  "expiration_hours": 24              // default: 24, max: 168 (7 days)
}
```

**Response** (200 OK):
```json
{
  "status": "registered",
  "channel_id": "unique-channel-id",
  "resource_id": "google-resource-id",
  "expires_at": "2025-11-02T10:30:00Z",
  "webhook_url": "https://your-domain.com/webhook/google-drive"
}
```

**Implementation**:
- Use Google Drive API `files.watch()` method
- Store channel_id and resource_id in configuration
- Set up automatic renewal before expiration

#### `DELETE /api/v1/webhooks/google-drive/unregister`
**Purpose**: Unregister Google Drive webhook

**Authentication**: Required

**Response** (200 OK):
```json
{
  "status": "unregistered",
  "channel_id": "unique-channel-id"
}
```

#### `GET /api/v1/webhooks/status`
**Purpose**: Check webhook registration status

**Authentication**: Required

**Response** (200 OK):
```json
{
  "google_drive": {
    "registered": true,
    "channel_id": "unique-channel-id",
    "expires_at": "2025-11-02T10:30:00Z",
    "time_to_expiration_hours": 23.5
  },
  "flowise": {
    "configured": false
  }
}
```

---

## 5. Integration Points

### 5.1 Integration with Existing Code

**DO NOT MODIFY** the following files directly:
- `src/process_google_drive.py` - Core processing logic
- `src/flowise_api.py` - FlowiseAI client
- `src/google_drive.py` - Google Drive client
- `src/process_documents.py` - Document processing

**IMPORT AND USE** existing functions:
```python
# In src/app.py
from src.process_google_drive import process_google_drive
from src.process_files_for_translation import process_files_for_translation
from src.google_drive import GoogleApi
from src.flowise_api import FlowiseAiAPI
from src.logger import logger
from src.utils import read_json_secret_file
```

### 5.2 Asynchronous Processing

**Requirement**: API endpoints must not block

**Implementation Options**:

**Option A: Threading** (Recommended for initial implementation)
```python
from threading import Thread
import queue

job_queue = queue.Queue()

def process_documents_async(job_id):
    """Background thread worker"""
    try:
        process_google_drive()
        # Update job status
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")

@app.route('/api/v1/process/trigger', methods=['POST'])
def trigger_process():
    job_id = str(uuid.uuid4())
    thread = Thread(target=process_documents_async, args=(job_id,))
    thread.start()
    return jsonify({"job_id": job_id, "status": "queued"}), 202
```

**Option B: Celery** (For production/scale)
- More complex setup
- Better for multiple workers
- Requires Redis/RabbitMQ

### 5.3 State Management

**Job Status Tracking**:
```python
# Simple in-memory store (development)
job_status = {}

# Or persistent store (production)
# - SQLite database
# - Redis
# - JSON file
```

**Job Status Schema**:
```python
{
    "job_id": str,
    "status": str,  # queued, in_progress, completed, failed
    "progress": {
        "current": int,
        "total": int,
        "current_file": str
    },
    "started_at": datetime,
    "completed_at": datetime | None,
    "errors": List[str],
    "files_processed": int
}
```

### 5.4 Scheduler Integration

**Requirement**: Web server and scheduler should coexist

**Implementation**:
```python
# src/app.py
import schedule
from threading import Thread

def run_scheduler():
    """Background thread for scheduled tasks"""
    while True:
        schedule.run_pending()
        time.sleep(1)

def create_app():
    app = Flask(__name__)

    # Load configuration
    config = read_json_secret_file('credentials/secrets.json')

    # Setup scheduler if enabled
    if config.get('scheduling', {}).get('enabled', True):
        interval = config.get('scheduling', {}).get('interval_minutes', 15)
        schedule.every(interval).minutes.do(process_google_drive)

        scheduler_thread = Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()

    # Setup routes
    # ...

    return app
```

---

## 6. Security Requirements

### 6.1 Authentication

**Method**: API Key or JWT Bearer Token

**Configuration** (`credentials/secrets.json`):
```json
{
  "api": {
    "enabled": true,
    "api_keys": [
      {
        "key": "generated-api-key-hash",
        "name": "Integration Service",
        "created_at": "2025-11-01T10:00:00Z",
        "last_used": null
      }
    ],
    "jwt_secret": "random-secret-key"
  }
}
```

**Implementation**:
```python
from functools import wraps
from flask import request, jsonify

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401

        # Bearer token format: "Bearer <token>"
        parts = auth_header.split()
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            return jsonify({'error': 'Invalid authorization header'}), 401

        token = parts[1]
        if not verify_api_key(token):
            return jsonify({'error': 'Invalid API key'}), 401

        return f(*args, **kwargs)
    return decorated_function

# Usage
@app.route('/api/v1/status')
@require_auth
def get_status():
    return jsonify({...})
```

### 6.2 Webhook Signature Verification

**Google Drive Webhooks**:
```python
def verify_google_webhook(request):
    """Verify Google Drive webhook authenticity"""
    channel_token = request.headers.get('X-Goog-Channel-Token')

    # Load expected token from configuration
    config = read_json_secret_file('credentials/secrets.json')
    expected_token = config.get('webhook', {}).get('google_channel_token')

    return channel_token == expected_token
```

**FlowiseAI Webhooks** (HMAC):
```python
import hmac
import hashlib

def verify_flowise_webhook(request):
    """Verify FlowiseAI webhook signature"""
    signature = request.headers.get('X-Flowise-Signature', '')

    # Load webhook secret
    config = read_json_secret_file('credentials/secrets.json')
    secret = config.get('webhook', {}).get('flowise_secret', '').encode()

    # Compute expected signature
    expected = 'sha256=' + hmac.new(
        secret,
        request.data,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)
```

### 6.3 Rate Limiting

**Requirements**:
- API endpoints: 100 requests/minute per API key
- Webhook endpoints: 1000 requests/minute (legitimate services may send bursts)

**Implementation** (using Flask-Limiter):
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

@app.route('/api/v1/process/trigger', methods=['POST'])
@limiter.limit("10 per minute")  # Stricter limit for processing
@require_auth
def trigger_process():
    ...
```

### 6.4 HTTPS Enforcement

**Requirement**: Production deployment MUST use HTTPS

**Implementation**:
```python
@app.before_request
def enforce_https():
    if not request.is_secure and app.config.get('ENFORCE_HTTPS'):
        return jsonify({'error': 'HTTPS required'}), 403
```

### 6.5 Input Validation

**Requirements**:
- Validate all request body parameters
- Sanitize file paths and email addresses
- Prevent path traversal attacks

**Implementation**:
```python
from marshmallow import Schema, fields, validate, ValidationError

class TriggerProcessSchema(Schema):
    client_email = fields.Email(required=False, allow_none=True)
    force = fields.Boolean(missing=False)

@app.route('/api/v1/process/trigger', methods=['POST'])
@require_auth
def trigger_process():
    schema = TriggerProcessSchema()
    try:
        data = schema.load(request.json or {})
    except ValidationError as err:
        return jsonify({'error': 'Validation error', 'details': err.messages}), 400

    # Process with validated data
    ...
```

---

## 7. Configuration

### 7.1 Configuration File Updates

**Location**: `credentials/secrets.json`

**New sections to add**:
```json
{
  "program": "default_mode",
  "scheduling": {
    "enabled": true,
    "google_drive_interval_minutes": 15
  },
  "api": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false,
    "api_keys": [
      {
        "key": "your-secure-api-key-here",
        "name": "Default API Key",
        "created_at": "2025-11-01T10:00:00Z"
      }
    ]
  },
  "webhook": {
    "enabled": true,
    "google_drive": {
      "channel_id": "emailreader-channel-001",
      "verification_token": "random-secure-token",
      "auto_renew": true
    },
    "flowise": {
      "enabled": false,
      "secret": "flowise-webhook-secret"
    }
  },
  "flowiseAI": {
    "API_KEY": "...",
    "API_URL": "...",
    "DOC_STORE_ID": "...",
    "DOC_LOADER_DOCX_ID": "...",
    "CHATFLOW_ID": "..."
  },
  "google_drive": {
    "parent_folder_id": "..."
  }
}
```

### 7.2 Environment Variables (Optional)

**Support for environment variable overrides**:
```python
import os

# Override API port from environment
PORT = os.getenv('EMAILREADER_PORT', config.get('api', {}).get('port', 8080))

# Override API keys from environment
API_KEY = os.getenv('EMAILREADER_API_KEY', config.get('api', {}).get('api_keys', [{}])[0].get('key'))
```

---

## 8. Error Handling

### 8.1 Error Response Format

**Standard error response**:
```json
{
  "error": "Human-readable error message",
  "error_code": "SPECIFIC_ERROR_CODE",
  "details": {
    "field": "client_email",
    "reason": "Invalid email format"
  },
  "timestamp": "2025-11-01T10:30:00Z",
  "request_id": "uuid-v4"
}
```

### 8.2 HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Success |
| 201 | Resource created |
| 202 | Accepted (async processing) |
| 400 | Bad request (validation error) |
| 401 | Unauthorized (missing/invalid auth) |
| 403 | Forbidden (valid auth, insufficient permissions) |
| 404 | Not found |
| 409 | Conflict (e.g., processing already in progress) |
| 429 | Too many requests (rate limit) |
| 500 | Internal server error |
| 503 | Service unavailable (e.g., Google Drive API down) |

### 8.3 Logging Requirements

**Use existing logger** from `src/logger.py`:
```python
from src.logger import logger

# Log all API requests
@app.before_request
def log_request():
    logger.info(f"API Request: {request.method} {request.path}")

# Log errors with context
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Unhandled error: {error}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'error_code': 'INTERNAL_ERROR'
    }), 500
```

**Log levels**:
- INFO: API requests, webhook received, processing started/completed
- WARNING: Rate limit hit, webhook verification failed
- ERROR: Processing failures, API errors, configuration errors
- DEBUG: Request/response details, internal state changes

---

## 9. Testing Requirements

### 9.1 Unit Tests

**Test file**: `tests/test_app.py`

**Required test coverage**:
- Authentication middleware (valid/invalid/missing tokens)
- Request validation (valid/invalid payloads)
- Webhook signature verification
- API endpoint responses
- Error handling

**Example test structure**:
```python
import unittest
from src.app import create_app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.api_key = "test-api-key"

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')

    def test_status_requires_auth(self):
        response = self.client.get('/api/v1/status')
        self.assertEqual(response.status_code, 401)

    def test_status_with_valid_auth(self):
        response = self.client.get(
            '/api/v1/status',
            headers={'Authorization': f'Bearer {self.api_key}'}
        )
        self.assertEqual(response.status_code, 200)

    def test_trigger_process(self):
        response = self.client.post(
            '/api/v1/process/trigger',
            headers={'Authorization': f'Bearer {self.api_key}'},
            json={'force': False}
        )
        self.assertEqual(response.status_code, 202)
        data = response.get_json()
        self.assertIn('job_id', data)
```

### 9.2 Integration Tests

**Test with real Google Drive API** (optional, requires test credentials):
- Webhook registration/unregistration
- Document processing trigger
- File operations

### 9.3 Manual Testing Checklist

- [ ] Health endpoint responds without auth
- [ ] Status endpoint requires valid auth
- [ ] Invalid API key returns 401
- [ ] Trigger processing returns job_id
- [ ] Job status can be retrieved
- [ ] Google Drive webhook can be registered
- [ ] Webhook endpoint accepts valid webhook requests
- [ ] Webhook endpoint rejects invalid signatures
- [ ] Rate limiting works (101st request in minute is blocked)
- [ ] Configuration endpoint returns sanitized config
- [ ] Scheduler continues running alongside web server
- [ ] Processing errors are logged correctly

---

## 10. Deployment

### 10.1 Development Server

**Running the web server**:
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Run Flask development server
python -m src.app

# Or with environment variable
EMAILREADER_PORT=5000 python -m src.app
```

**Entry point** in `src/app.py`:
```python
if __name__ == '__main__':
    app = create_app()
    config = read_json_secret_file('credentials/secrets.json')

    host = config.get('api', {}).get('host', '127.0.0.1')
    port = config.get('api', {}).get('port', 5000)
    debug = config.get('api', {}).get('debug', False)

    logger.info(f"Starting EmailReader API server on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
```

### 10.2 Production Server (Gunicorn)

**Installation**:
```bash
pip install gunicorn
```

**Running**:
```bash
gunicorn -w 4 -b 0.0.0.0:8080 "src.app:create_app()"
```

**Systemd service** (`/etc/systemd/system/emailreader-api.service`):
```ini
[Unit]
Description=EmailReader API Server
After=network.target

[Service]
Type=notify
User=emailreader
WorkingDirectory=/opt/emailreader
Environment="PATH=/opt/emailreader/venv/bin"
ExecStart=/opt/emailreader/venv/bin/gunicorn -w 4 -b 0.0.0.0:8080 "src.app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

### 10.3 Reverse Proxy (Nginx)

**Nginx configuration** (`/etc/nginx/sites-available/emailreader`):
```nginx
server {
    listen 443 ssl http2;
    server_name emailreader.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/emailreader.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/emailreader.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 10.4 Docker Deployment (Optional)

**Dockerfile**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-all \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Run gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "src.app:create_app()"]
```

### 10.5 Environment Considerations

**Production checklist**:
- [ ] HTTPS enabled (reverse proxy)
- [ ] API keys are strong and unique
- [ ] Debug mode disabled
- [ ] Proper logging configured
- [ ] Rate limiting enabled
- [ ] Webhook URLs are publicly accessible
- [ ] Google Drive webhook auto-renewal configured
- [ ] Error notifications configured
- [ ] Monitoring/health checks set up

---

## 11. Success Criteria

### 11.1 Functional Requirements
- ✅ All API endpoints respond with correct status codes
- ✅ Authentication works for protected endpoints
- ✅ Webhook registration with Google Drive succeeds
- ✅ Webhook notifications trigger document processing
- ✅ Manual processing can be triggered via API
- ✅ Job status can be tracked
- ✅ Configuration can be retrieved via API
- ✅ Scheduler continues to work alongside API

### 11.2 Performance Requirements
- ✅ API endpoints respond within 200ms (except processing triggers)
- ✅ Webhook endpoints respond within 100ms
- ✅ Processing triggers return immediately (async)
- ✅ Server handles at least 100 concurrent requests

### 11.3 Security Requirements
- ✅ All protected endpoints require authentication
- ✅ Invalid authentication returns 401
- ✅ Webhook signatures are verified
- ✅ Rate limiting prevents abuse
- ✅ No secrets are exposed in API responses
- ✅ HTTPS is enforced in production

### 11.4 Reliability Requirements
- ✅ Server recovers from processing errors
- ✅ Failed jobs don't crash the server
- ✅ Webhook registrations are automatically renewed
- ✅ All errors are logged with context
- ✅ Health endpoint always responds (even under load)

---

## 12. Implementation Phases

### Phase 1: Basic REST API (Priority: HIGH)
**Estimated Time**: 4-6 hours

- [ ] Set up Flask application in `src/app.py`
- [ ] Implement health endpoint (`GET /health`)
- [ ] Implement authentication middleware
- [ ] Implement status endpoint (`GET /api/v1/status`)
- [ ] Implement configuration endpoint (`GET /api/v1/config`)
- [ ] Add error handling and logging
- [ ] Write basic unit tests

**Deliverable**: Working REST API with authentication

---

### Phase 2: Processing Control (Priority: HIGH)
**Estimated Time**: 4-6 hours

- [ ] Implement async processing with threading
- [ ] Implement trigger endpoint (`POST /api/v1/process/trigger`)
- [ ] Implement job status endpoint (`GET /api/v1/process/status/{job_id}`)
- [ ] Implement job history endpoint (`GET /api/v1/process/history`)
- [ ] Add job state management (in-memory or SQLite)
- [ ] Integrate with existing `process_google_drive()`
- [ ] Write integration tests

**Deliverable**: API can trigger and track document processing

---

### Phase 3: Google Drive Webhooks (Priority: MEDIUM)
**Estimated Time**: 3-4 hours

- [ ] Implement webhook endpoint (`POST /webhook/google-drive`)
- [ ] Implement webhook signature verification
- [ ] Implement webhook registration (`POST /api/v1/webhooks/google-drive/register`)
- [ ] Implement webhook unregistration (`DELETE /api/v1/webhooks/google-drive/unregister`)
- [ ] Implement webhook status (`GET /api/v1/webhooks/status`)
- [ ] Add webhook auto-renewal logic
- [ ] Test with Google Drive API

**Deliverable**: Real-time processing via Google Drive webhooks

---

### Phase 4: Advanced Features (Priority: LOW)
**Estimated Time**: 2-3 hours

- [ ] Implement FlowiseAI webhook endpoint
- [ ] Implement scheduler control (`PUT /api/v1/config/scheduler`)
- [ ] Add rate limiting
- [ ] Add API documentation (Swagger)
- [ ] Add CORS support (if needed)
- [ ] Add metrics/monitoring endpoints

**Deliverable**: Production-ready API server

---

## Appendix A: Example Implementation Skeleton

```python
# src/app.py
"""
EmailReader Web Server API
"""
import os
import uuid
from datetime import datetime
from threading import Thread
from functools import wraps

from flask import Flask, request, jsonify
from src.logger import logger
from src.utils import read_json_secret_file
from src.process_google_drive import process_google_drive
import schedule
import time

# Global state (replace with DB in production)
job_status = {}

def verify_api_key(token):
    """Verify API key against configuration"""
    config = read_json_secret_file('credentials/secrets.json')
    api_keys = config.get('api', {}).get('api_keys', [])
    return any(key.get('key') == token for key in api_keys)

def require_auth(f):
    """Authentication decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401

        token = auth_header[7:]  # Remove 'Bearer '
        if not verify_api_key(token):
            return jsonify({'error': 'Invalid API key'}), 401

        return f(*args, **kwargs)
    return decorated

def process_async(job_id):
    """Background processing worker"""
    try:
        job_status[job_id]['status'] = 'in_progress'
        job_status[job_id]['started_at'] = datetime.utcnow().isoformat() + 'Z'

        process_google_drive()

        job_status[job_id]['status'] = 'completed'
        job_status[job_id]['completed_at'] = datetime.utcnow().isoformat() + 'Z'
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)
        job_status[job_id]['status'] = 'failed'
        job_status[job_id]['error'] = str(e)

def run_scheduler():
    """Background scheduler thread"""
    while True:
        schedule.run_pending()
        time.sleep(1)

def create_app():
    app = Flask(__name__)

    # Load configuration
    config = read_json_secret_file('credentials/secrets.json')

    # Setup scheduler if enabled
    if config.get('scheduling', {}).get('enabled', True):
        interval = config.get('scheduling', {}).get('google_drive_interval_minutes', 15)
        schedule.every(interval).minutes.do(process_google_drive)
        Thread(target=run_scheduler, daemon=True).start()
        logger.info(f"Scheduler enabled: every {interval} minutes")

    # Routes
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'version': '1.0.0'
        })

    @app.route('/api/v1/status')
    @require_auth
    def get_status():
        return jsonify({
            'scheduler': {
                'enabled': config.get('scheduling', {}).get('enabled', True),
                'interval_minutes': config.get('scheduling', {}).get('google_drive_interval_minutes', 15)
            }
        })

    @app.route('/api/v1/process/trigger', methods=['POST'])
    @require_auth
    def trigger_process():
        job_id = str(uuid.uuid4())
        job_status[job_id] = {
            'job_id': job_id,
            'status': 'queued',
            'started_at': None,
            'completed_at': None
        }

        Thread(target=process_async, args=(job_id,), daemon=True).start()

        return jsonify({
            'job_id': job_id,
            'status': 'queued',
            'message': 'Processing started'
        }), 202

    @app.route('/api/v1/process/status/<job_id>')
    @require_auth
    def get_job_status(job_id):
        if job_id not in job_status:
            return jsonify({'error': 'Job not found'}), 404
        return jsonify(job_status[job_id])

    # Error handlers
    @app.errorhandler(Exception)
    def handle_error(error):
        logger.error(f"Unhandled error: {error}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    config = read_json_secret_file('credentials/secrets.json')

    host = config.get('api', {}).get('host', '127.0.0.1')
    port = config.get('api', {}).get('port', 5000)
    debug = config.get('api', {}).get('debug', False)

    logger.info(f"Starting EmailReader API on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
```

---

## Appendix B: Configuration File Template

**File**: `credentials/secrets.json`

```json
{
  "program": "default_mode",
  "scheduling": {
    "enabled": true,
    "google_drive_interval_minutes": 15
  },
  "api": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false,
    "api_keys": [
      {
        "key": "CHANGE-THIS-TO-SECURE-RANDOM-STRING",
        "name": "Default API Key",
        "created_at": "2025-11-01T10:00:00Z"
      }
    ]
  },
  "webhook": {
    "enabled": true,
    "google_drive": {
      "channel_id": "emailreader-webhook-001",
      "verification_token": "CHANGE-THIS-TO-RANDOM-TOKEN",
      "auto_renew": true
    },
    "flowise": {
      "enabled": false,
      "secret": "flowise-webhook-secret"
    }
  },
  "flowiseAI": {
    "API_KEY": "your-flowise-api-key",
    "API_URL": "https://your-flowise-instance.com",
    "DOC_STORE_ID": "your-doc-store-id",
    "DOC_LOADER_DOCX_ID": "your-loader-id",
    "CHATFLOW_ID": "your-chatflow-id"
  },
  "google_drive": {
    "parent_folder_id": "your-google-drive-folder-id"
  }
}
```

---

## End of Requirements Document

**Questions or Clarifications**: Contact the project maintainer

**Document Version**: 1.0

**Last Updated**: 2025-11-01
