# EmailReader Web Server Integration Guide

## Quick Reference

**Purpose**: Connect your existing FastAPI web server to EmailReader for document processing control and webhook notifications.

---

## 1. EmailReader Integration Points

### 1.1 Import EmailReader Functions

Add to your web server:

```python
from src.process_google_drive import process_google_drive
from src.process_files_for_translation import process_files_for_translation
from src.google_drive import GoogleApi
from src.flowise_api import FlowiseAiAPI
from src.logger import logger
from src.utils import read_json_secret_file
```

### 1.2 Background Processing

Trigger EmailReader processing asynchronously:

```python
from threading import Thread

def trigger_emailreader_processing(client_email: str = None):
    """Trigger document processing in background"""
    def run():
        try:
            if client_email:
                # Process specific client (custom implementation needed)
                process_google_drive()
            else:
                # Process all clients
                process_google_drive()
        except Exception as e:
            logger.error(f"Processing failed: {e}")

    Thread(target=run, daemon=True).start()
```

---

## 2. Required API Endpoints

### 2.1 Trigger Processing

```python
from fastapi import BackgroundTasks

@app.post('/api/v1/emailreader/trigger')
async def trigger_processing(background_tasks: BackgroundTasks):
    """Manually trigger EmailReader document processing"""
    background_tasks.add_task(process_google_drive)
    return {"status": "processing_started"}
```

### 2.2 Health Check

```python
@app.get('/api/v1/emailreader/status')
async def emailreader_status():
    """Check EmailReader integration status"""
    try:
        config = read_json_secret_file('credentials/secrets.json')
        google_api = GoogleApi()
        flowise_api = FlowiseAiAPI()

        return {
            "status": "healthy",
            "google_drive": {"connected": True},
            "flowise": {"connected": True}
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
```

---

## 3. Webhook Endpoints

### 3.1 Google Drive Webhook

```python
from fastapi import Request, HTTPException

@app.post('/webhook/google-drive')
async def google_drive_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive Google Drive push notifications"""

    # Verify webhook token
    channel_token = request.headers.get('x-goog-channel-token')
    config = read_json_secret_file('credentials/secrets.json')
    expected_token = config.get('webhook', {}).get('google_drive', {}).get('verification_token')

    if channel_token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Ignore sync messages
    resource_state = request.headers.get('x-goog-resource-state')
    if resource_state == 'sync':
        return {"status": "sync_acknowledged"}

    # Trigger processing for updates
    if resource_state == 'update':
        background_tasks.add_task(process_google_drive)
        return {"status": "processing_triggered"}

    return {"status": "received"}
```

### 3.2 FlowiseAI Webhook (Optional)

```python
import hmac
import hashlib

@app.post('/webhook/flowise')
async def flowise_webhook(request: Request):
    """Receive FlowiseAI notifications"""

    # Verify HMAC signature
    signature = request.headers.get('x-flowise-signature', '')
    config = read_json_secret_file('credentials/secrets.json')
    secret = config.get('webhook', {}).get('flowise', {}).get('secret', '').encode()

    body = await request.body()
    expected = 'sha256=' + hmac.new(secret, body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()
    logger.info(f"FlowiseAI notification: {data.get('event')}")

    return {"status": "received"}
```

---

## 4. Configuration

### 4.1 Update `credentials/secrets.json`

Add webhook configuration:

```json
{
  "program": "default_mode",
  "scheduling": {
    "enabled": true,
    "google_drive_interval_minutes": 15
  },
  "webhook": {
    "enabled": true,
    "google_drive": {
      "channel_id": "your-channel-id",
      "verification_token": "RANDOM-SECURE-TOKEN-HERE",
      "auto_renew": true
    },
    "flowise": {
      "enabled": false,
      "secret": "your-webhook-secret"
    }
  },
  "flowiseAI": {
    "API_KEY": "your-api-key",
    "API_URL": "https://your-flowise.com",
    "DOC_STORE_ID": "store-id",
    "DOC_LOADER_DOCX_ID": "loader-id",
    "CHATFLOW_ID": "chatflow-id"
  },
  "google_drive": {
    "parent_folder_id": "your-folder-id"
  }
}
```

---

## 5. Google Drive Webhook Registration

### 5.1 Register Webhook Endpoint

```python
from googleapiclient.discovery import build
import time

@app.post('/api/v1/webhooks/google-drive/register')
async def register_google_webhook():
    """Register Google Drive webhook"""

    config = read_json_secret_file('credentials/secrets.json')
    google_api = GoogleApi()

    channel_id = config.get('webhook', {}).get('google_drive', {}).get('channel_id')
    webhook_url = "https://your-domain.com/webhook/google-drive"  # Your public URL
    token = config.get('webhook', {}).get('google_drive', {}).get('verification_token')
    folder_id = config.get('google_drive', {}).get('parent_folder_id')

    # Register with Google Drive API
    service = google_api.service
    body = {
        'id': channel_id,
        'type': 'web_hook',
        'address': webhook_url,
        'token': token,
        'expiration': int((time.time() + 86400) * 1000)  # 24 hours
    }

    result = service.files().watch(fileId=folder_id, body=body).execute()

    return {
        "status": "registered",
        "channel_id": result['id'],
        "resource_id": result['resourceId'],
        "expiration": result['expiration']
    }
```

### 5.2 Unregister Webhook

```python
@app.delete('/api/v1/webhooks/google-drive/unregister')
async def unregister_google_webhook():
    """Unregister Google Drive webhook"""

    config = read_json_secret_file('credentials/secrets.json')
    google_api = GoogleApi()

    channel_id = config.get('webhook', {}).get('google_drive', {}).get('channel_id')
    # resource_id stored from registration response

    service = google_api.service
    service.channels().stop(body={'id': channel_id, 'resourceId': 'resource-id'}).execute()

    return {"status": "unregistered"}
```

---

## 6. Optional: Scheduler Integration

Run EmailReader on schedule within your web server:

```python
import schedule
from threading import Thread
from contextlib import asynccontextmanager

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start scheduler
    config = read_json_secret_file('credentials/secrets.json')
    if config.get('scheduling', {}).get('enabled', True):
        interval = config.get('scheduling', {}).get('google_drive_interval_minutes', 15)
        schedule.every(interval).minutes.do(process_google_drive)

        scheduler_thread = Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info(f"EmailReader scheduler started: every {interval} minutes")

    yield

    # Shutdown
    logger.info("EmailReader scheduler stopped")

app = FastAPI(lifespan=lifespan)
```

---

## 7. Request/Response Examples

### Trigger Processing

**Request:**
```bash
POST /api/v1/emailreader/trigger
Content-Type: application/json

{}
```

**Response:**
```json
{
  "status": "processing_started"
}
```

### Google Drive Webhook

**Request Headers:**
```
X-Goog-Channel-ID: your-channel-id
X-Goog-Channel-Token: your-verification-token
X-Goog-Resource-State: update
```

**Response:**
```json
{
  "status": "processing_triggered"
}
```

---

## 8. Security Checklist

- ✅ Use HTTPS for webhook URLs
- ✅ Verify webhook tokens/signatures
- ✅ Store secrets in `credentials/secrets.json` (not in code)
- ✅ Use environment variables for sensitive URLs
- ✅ Set webhook expiration and auto-renewal
- ✅ Log all webhook events

---

## 9. Testing

### Test Manual Trigger

```bash
curl -X POST http://localhost:8000/api/v1/emailreader/trigger
```

### Test Google Drive Webhook

```bash
curl -X POST http://localhost:8000/webhook/google-drive \
  -H "X-Goog-Channel-Token: your-token" \
  -H "X-Goog-Resource-State: update"
```

### Test Health Check

```bash
curl http://localhost:8000/api/v1/emailreader/status
```

---

## 10. Common Integration Patterns

### Pattern A: Webhook-Only (Real-time)

```python
# No scheduler needed
# Only process when Google Drive sends notification

@app.post('/webhook/google-drive')
async def google_drive_webhook(request: Request, background_tasks: BackgroundTasks):
    # Verify and trigger processing
    background_tasks.add_task(process_google_drive)
    return {"status": "triggered"}
```

### Pattern B: Scheduler + Webhook (Hybrid)

```python
# Scheduler as backup (every 15 min)
# Webhook for real-time processing

# Enable both in configuration
{
  "scheduling": {"enabled": true, "interval_minutes": 15},
  "webhook": {"enabled": true}
}
```

### Pattern C: Manual Trigger Only

```python
# No scheduler, no webhook
# Process only via API calls

@app.post('/api/v1/emailreader/trigger')
async def trigger(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_google_drive)
    return {"status": "triggered"}
```

---

## 11. Complete Minimal Example

```python
from fastapi import FastAPI, BackgroundTasks, Request, HTTPException
from src.process_google_drive import process_google_drive
from src.utils import read_json_secret_file
from src.logger import logger

app = FastAPI()

@app.post('/api/v1/emailreader/trigger')
async def trigger(background_tasks: BackgroundTasks):
    """Trigger EmailReader processing"""
    background_tasks.add_task(process_google_drive)
    return {"status": "processing_started"}

@app.post('/webhook/google-drive')
async def google_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle Google Drive webhook"""

    # Verify token
    token = request.headers.get('x-goog-channel-token')
    config = read_json_secret_file('credentials/secrets.json')
    expected = config.get('webhook', {}).get('google_drive', {}).get('verification_token')

    if token != expected:
        raise HTTPException(status_code=401)

    # Ignore sync, process updates
    state = request.headers.get('x-goog-resource-state')
    if state == 'update':
        background_tasks.add_task(process_google_drive)
        return {"status": "processing_triggered"}

    return {"status": "received"}

@app.get('/api/v1/emailreader/status')
async def status():
    """Check EmailReader status"""
    return {"status": "healthy", "service": "emailreader"}
```

---

## Summary

**3 endpoints to add to your web server:**
1. `POST /api/v1/emailreader/trigger` - Manual trigger
2. `POST /webhook/google-drive` - Receive Google Drive notifications
3. `GET /api/v1/emailreader/status` - Health check

**Import 1 function:**
```python
from src.process_google_drive import process_google_drive
```

**Run in background:**
```python
background_tasks.add_task(process_google_drive)
```

That's it! EmailReader is now integrated with your web server.
