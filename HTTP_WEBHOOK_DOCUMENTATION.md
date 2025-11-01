# HTTP Request and Webhook Documentation

## HTTP Request Implementation

### Overview
The application uses the Python `requests` library to interact with the FlowiseAI API. All HTTP operations are centralized in the `FlowiseAiAPI` class.

**Location**: `src/flowise_api.py`

### Authentication
All API requests use Bearer token authentication:
```python
headers = {"Authorization": f"Bearer {self.API_KEY}"}
```

Configuration is stored in `credentials/secrets.json`:
```json
{
  "flowiseAI": {
    "API_KEY": "your-api-key",
    "API_URL": "https://your-flowise-instance.com",
    "DOC_STORE_ID": "store-id",
    "DOC_LOADER_DOCX_ID": "loader-id",
    "CHATFLOW_ID": "chatflow-id"
  }
}
```

### HTTP Methods

#### 1. GET Requests

**List Document Stores** (`src/flowise_api.py:90`)
```python
def get_list_documents_store() -> List[Dict]:
    response = requests.get(
        url=f"{API_URL}/document-store/store",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=10000
    )
    return response.json()
```

**Get Specific Document Store** (`src/flowise_api.py:107`)
```python
def get_specific_doc_store(store_id: str) -> Dict:
    response = requests.get(
        url=f"{API_URL}/document-store/store/{store_id}",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=10000
    )
    return response.json()
```

**Get Document Page** (`src/flowise_api.py:257`)
```python
def get_document_page(store_id: str, doc_id: str, page: int = 0) -> Dict:
    response = requests.get(
        url=f"{API_URL}/document-store/chunks/{store_id}/{doc_id}/{page}",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=10000
    )
    return response.json()
```

#### 2. POST Requests

**Create Document Store** (`src/flowise_api.py:53`)
```python
def create_new_doc_store(name: str, description: str = None) -> Dict:
    response = requests.post(
        url=f"{API_URL}/document-store/store",
        headers={"Authorization": f"Bearer {API_KEY}",
                 "Content-Type": "application/json"},
        json={"status": "EMPTY", "name": name, "description": description},
        timeout=10000
    )
    return response.json()
```

**Upload Document** (`src/flowise_api.py:166`)
```python
def upsert_document_to_document_store(doc_path: str, doc_name: str,
                                      store_id: str, loader_id: str) -> Dict:
    with open(doc_path, 'rb') as file:
        response = requests.post(
            url=f"{API_URL}/document-store/upsert/{store_id}",
            files={"files": (doc_name, file)},
            data={"docId": loader_id},
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=60000  # Large files need more time
        )
    return response.json()
```

**Create Prediction** (`src/flowise_api.py:326`)
```python
def create_new_prediction(doc_name: str) -> Dict:
    response = requests.post(
        url=f"{API_URL}/prediction/{CHATFLOW_ID}",
        json={
            "question": doc_name,
            "overrideConfig": {},
            "history": []
        },
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=30000
    )
    return response.json()
```

#### 3. PUT Requests

**Update Document Store** (`src/flowise_api.py:128`)
```python
def update_specific_doc_store(store_id: str) -> Dict:
    response = requests.put(
        url=f"{API_URL}/document-store/store/{store_id}",
        headers={"Authorization": f"Bearer {API_KEY}",
                 "Content-Type": "application/json"},
        json={"status": "EMPTY"},
        timeout=10000
    )
    return response.json()
```

#### 4. DELETE Requests

**Delete Document Store** (`src/flowise_api.py:149`)
```python
def delete_specific_doc_store(store_id: str) -> Dict:
    response = requests.delete(
        url=f"{API_URL}/document-store/store/{store_id}",
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=10000
    )
    return response.json()
```

### Error Handling

The application handles common HTTP errors:

```python
try:
    response = requests.post(...)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"HTTP {response.status_code}: {response.text}")
        return {'name': 'Error', 'error': response.text}

except requests.exceptions.Timeout:
    logger.error("Request timeout")
    return {'name': 'Error', 'error': 'Request timeout'}

except requests.exceptions.ConnectionError as e:
    logger.error(f"Connection error: {e}")
    return {'name': 'Error', 'error': str(e)}
```

**Timeout Values**:
- Standard operations: 10 seconds (10000ms)
- File uploads: 60 seconds (60000ms)
- Predictions: 30 seconds (30000ms)

### Request Flow

```
index.py (scheduler)
    ↓
process_google_drive()
    ↓
FlowiseAiAPI.upsert_document_to_document_store()
    ↓
HTTP POST → /document-store/upsert/{store_id}
    ↓
FlowiseAiAPI.create_new_prediction()
    ↓
HTTP POST → /prediction/{chatflow_id}
```

---

## Webhook Registration

### Current Status
**NOT IMPLEMENTED** - The application currently runs on a scheduled polling model (default: every 15 minutes).

### Implementation Needed

To enable webhook functionality, the following components need to be implemented:

#### 1. Flask Application Setup

**File**: `src/app.py` (currently minimal)

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

# Load webhook secret from configuration
WEBHOOK_SECRET = "your-webhook-secret"

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook request is authentic"""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)

@app.route('/webhook/flowise', methods=['POST'])
def flowise_webhook():
    """Handle incoming webhooks from FlowiseAI"""
    signature = request.headers.get('X-Flowise-Signature')

    if not verify_webhook_signature(request.data, signature):
        return jsonify({'error': 'Invalid signature'}), 401

    data = request.json
    # Process webhook data here

    return jsonify({'status': 'received'}), 200

@app.route('/webhook/google-drive', methods=['POST'])
def google_drive_webhook():
    """Handle Google Drive push notifications"""
    # Process Google Drive webhook
    return jsonify({'status': 'received'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

#### 2. Webhook Registration

**Google Drive Push Notifications**:

```python
from googleapiclient.discovery import build

def register_google_drive_webhook(channel_id: str, webhook_url: str):
    """Register webhook for Google Drive folder changes"""
    service = build('drive', 'v3', credentials=creds)

    body = {
        'id': channel_id,
        'type': 'web_hook',
        'address': webhook_url,
        'token': 'optional-verification-token',
        'expiration': int((time.time() + 86400) * 1000)  # 24 hours
    }

    response = service.files().watch(
        fileId='folder_id',
        body=body
    ).execute()

    return response
```

**FlowiseAI Webhook Configuration**:

Add to `credentials/secrets.json`:
```json
{
  "webhook": {
    "enabled": true,
    "secret": "your-webhook-secret",
    "url": "https://your-domain.com/webhook/flowise",
    "google_drive_channel_id": "unique-channel-id"
  }
}
```

#### 3. Webhook Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/webhook/flowise` | POST | Receive FlowiseAI processing notifications |
| `/webhook/google-drive` | POST | Receive Google Drive file change notifications |
| `/webhook/register` | POST | Register new webhook subscriptions |
| `/webhook/status` | GET | Check webhook registration status |

#### 4. Security Considerations

1. **Signature Verification**: Always verify webhook signatures
2. **HTTPS Only**: Never accept webhooks over plain HTTP
3. **IP Whitelisting**: Restrict webhook sources to known IPs
4. **Rate Limiting**: Implement rate limits to prevent abuse
5. **Secret Rotation**: Regularly rotate webhook secrets

#### 5. Converting from Polling to Webhooks

Current (Polling):
```python
# index.py
schedule.every(15).minutes.do(process_google_drive)
```

With Webhooks:
```python
# Remove scheduler, run Flask app
# Process documents when webhook received
@app.route('/webhook/google-drive', methods=['POST'])
def handle_drive_change():
    process_google_drive()
    return jsonify({'status': 'processed'}), 200
```

---

## Summary

### HTTP Requests
- **Library**: `requests`
- **Authentication**: Bearer token
- **Location**: `src/flowise_api.py`
- **Methods Used**: GET, POST, PUT, DELETE
- **Error Handling**: Timeout, connection errors, HTTP status codes

### Webhooks
- **Status**: Not implemented
- **Required**: Flask server, endpoint handlers, signature verification
- **Benefit**: Real-time processing instead of polling
- **Security**: HMAC signature verification required
