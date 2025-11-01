# EmailReader Logging Enhancements

## Overview

Enhanced HTTP request/response logging throughout the EmailReader application to improve monitoring and debugging capabilities.

---

## Changes Made

### 1. Enhanced `src/flowise_api.py`

#### New Utility Functions

**`sanitize_headers(headers)`**
- Hides sensitive information in HTTP headers
- Masks API keys, authorization tokens
- Shows first 10 and last 4 characters for tokens > 20 chars
- Example: `Bearer sk-abcdefghij...xyz1`

**`truncate_data(data, max_length=500)`**
- Truncates large request/response bodies for logging
- Prevents log files from growing too large
- Shows total length when truncated
- Example: `{data...}... (truncated, total length: 15000)`

**`log_http_request(method, url, **kwargs)`**
- Comprehensive HTTP request logging
- Logs: Method, URL, headers (sanitized), body, params, files, timeout
- Visual separators for easy reading (`===` and `---`)

**`log_http_response(response, duration)`**
- Comprehensive HTTP response logging
- Logs: Status code, duration, headers (sanitized), body, size
- Parses JSON responses for better formatting
- Visual separators for easy reading

---

## 2. Enhanced Methods

All HTTP methods now include comprehensive logging:

### GET Requests
- `get_list_documents_store()`
- `get_specific_doc_store()`
- `get_document_page()`

### POST Requests
- `create_new_doc_store()`
- `upsert_document_to_document_store()`
- `create_new_prediction()`

### PUT Requests
- `update_specific_doc_store()`
- `update_docs_in_store()`

### DELETE Requests
- `delete_specific_doc_store()`

---

## 3. What Gets Logged

### Request Logging (DEBUG Level)
```
================================================================================
HTTP REQUEST: POST https://flowise.com/document-store/store
--------------------------------------------------------------------------------
Request Headers: {
  "Authorization": "Bearer sk-abc...xyz1",
  "Content-Type": "application/json"
}
Request JSON Body: {"status": "EMPTY", "name": "MyStore", "description": null}
Request Timeout: 10.0 seconds
```

### Response Logging (DEBUG Level)
```
--------------------------------------------------------------------------------
HTTP RESPONSE: Status 200 - Duration: 1.23 seconds
--------------------------------------------------------------------------------
Response Headers: {
  "content-type": "application/json",
  "content-length": "450"
}
Response Body (JSON): {"id": "store-123", "name": "MyStore", ...}
Response Size: 450 bytes
================================================================================
```

### Summary Logging (INFO Level)
```
2025-11-01 10:30:00 | INFO     | Creating new document store: MyStore
2025-11-01 10:30:01 | INFO     | Document store created successfully: MyStore (ID: store-123)
```

---

## 4. Log Levels

### INFO
- Method entry/exit
- Success/failure summaries
- High-level operation status
- Example: `"Creating prediction for document: file.docx"`

### DEBUG
- Full HTTP request details
- Full HTTP response details
- Request/response headers (sanitized)
- Request/response bodies (truncated)
- Request duration
- Example: `"Request Headers: {...}"`

### ERROR
- HTTP errors with status codes
- Connection failures
- Timeouts
- Exceptions with stack traces

---

## 5. Security Features

### Sensitive Data Protection

**API Keys/Tokens**:
- Original: `Bearer sk-abcdefghijklmnopqrstuvwxyz123456`
- Logged: `Bearer sk-abcdefghij...3456`

**Short Tokens**:
- Original: `short-key`
- Logged: `***HIDDEN***`

**Unaffected Headers**:
- Content-Type, Content-Length, etc. logged in full

---

## 6. Performance Features

### Request Timing
Every HTTP request includes duration measurement:
```python
start_time = time.time()
response = requests.post(...)
duration = time.time() - start_time
logger.info("HTTP RESPONSE: Status %s - Duration: %.2f seconds",
            response.status_code, duration)
```

### Data Truncation
Large payloads are automatically truncated:
- Request bodies: max 500 characters
- Response bodies: max 1000 characters
- Shows total length: `(truncated, total length: 15000)`

---

## 7. Log File Location

Logs are written to:
```
data/logs/emailreader_YYYYMMDD.log
```

**Features**:
- Daily log files
- 10MB max file size
- 5 backup files retained
- UTF-8 encoding

---

## 8. Example Log Output

### Complete HTTP Transaction

```
2025-11-01 10:30:00 | INFO     | EmailReader.Flowise | Creating prediction for document: client@email.com+document.docx
================================================================================
HTTP REQUEST: POST https://flowise.com/prediction/chatflow-123
--------------------------------------------------------------------------------
Request Headers: {
  "Authorization": "Bearer sk-abcd...xyz1"
}
Request JSON Body: {
  "question": "client@email.com+document.docx",
  "overrideConfig": {},
  "history": []
}
Request Timeout: 30.0 seconds
--------------------------------------------------------------------------------
HTTP RESPONSE: Status 200 - Duration: 2.45 seconds
--------------------------------------------------------------------------------
Response Headers: {
  "content-type": "application/json",
  "content-length": "1245"
}
Response Body (JSON): {"text": "Analysis complete...", "chatMessageId": "msg-123"}
Response Size: 1245 bytes
================================================================================
2025-11-01 10:30:02 | INFO     | EmailReader.Flowise | Prediction created successfully for: client@email.com+document.docx
```

---

## 9. Debugging Benefits

### 1. **Complete Request Tracing**
- See exactly what's being sent to FlowiseAI
- Verify request parameters are correct
- Debug authentication issues

### 2. **Response Analysis**
- See full response from FlowiseAI
- Identify API changes or errors
- Validate data format

### 3. **Performance Monitoring**
- Track request durations
- Identify slow API calls
- Detect timeout issues

### 4. **Error Diagnosis**
- Full exception stack traces
- HTTP status codes and error messages
- Connection error details

### 5. **Audit Trail**
- Complete record of all API interactions
- Timestamps for every operation
- Success/failure tracking

---

## 10. Log Analysis Examples

### Find All Failed Requests
```bash
grep "HTTP RESPONSE: Status [45]" data/logs/emailreader_*.log
```

### Find Slow Requests (>5 seconds)
```bash
grep "Duration: [5-9]\." data/logs/emailreader_*.log
```

### Track Specific Document
```bash
grep "document.docx" data/logs/emailreader_*.log
```

### View All HTTP Requests
```bash
grep "HTTP REQUEST:" data/logs/emailreader_*.log
```

### Count Requests by Method
```bash
grep "HTTP REQUEST:" data/logs/emailreader_*.log | awk '{print $4}' | sort | uniq -c
```

---

## 11. Configuration

### Change Log Level

Edit `src/logger.py`:
```python
# Current: DEBUG level (logs everything)
logger.setLevel(logging.DEBUG)

# For production: INFO level (less verbose)
logger.setLevel(logging.INFO)

# For minimal logging: WARNING level
logger.setLevel(logging.WARNING)
```

### Adjust Truncation Limits

Edit `src/flowise_api.py`:
```python
# Current: 500 chars for requests, 1000 for responses
def truncate_data(data: Any, max_length: int = 500) -> str:
    ...

# In log_http_response:
logger.debug("Response Body (JSON): %s", truncate_data(response_json, 1000))

# Increase limits:
truncate_data(data, max_length=2000)  # More detail
truncate_data(data, max_length=100)   # Less detail
```

---

## 12. Best Practices

### When to Check Logs

1. **Document Upload Failures**
   - Check request body and file metadata
   - Verify authentication headers
   - Review response error messages

2. **Prediction Errors**
   - Verify question format
   - Check chatflow ID
   - Review response status

3. **Performance Issues**
   - Monitor request durations
   - Identify slow endpoints
   - Track timeout occurrences

4. **API Integration Issues**
   - Compare request format with API docs
   - Verify response structure
   - Check for API changes

### Log Rotation

Logs automatically rotate when:
- File size exceeds 10MB
- Or daily (new file each day)

Old logs are kept:
- Maximum 5 backup files
- Named: `emailreader_YYYYMMDD.log.1`, `.2`, etc.

---

## 13. Monitoring Recommendations

### Real-time Monitoring
```bash
# Follow logs in real-time
tail -f data/logs/emailreader_$(date +%Y%m%d).log

# Follow only HTTP requests
tail -f data/logs/emailreader_*.log | grep "HTTP REQUEST\|HTTP RESPONSE"

# Follow only errors
tail -f data/logs/emailreader_*.log | grep "ERROR"
```

### Automated Monitoring

Create alerts for:
- Multiple consecutive failures (HTTP 4xx/5xx)
- Requests taking longer than threshold
- Connection errors
- Authentication failures

---

## Summary

**All HTTP requests now include:**
- ✅ Complete request details (method, URL, headers, body)
- ✅ Complete response details (status, headers, body)
- ✅ Request duration timing
- ✅ Sanitized sensitive data (API keys)
- ✅ Truncated large payloads
- ✅ Visual separators for easy reading
- ✅ Contextual logging (INFO for summaries, DEBUG for details)

**Benefits:**
- 🔍 Enhanced debugging capabilities
- 📊 Performance monitoring
- 🔒 Security (sensitive data masked)
- 📝 Complete audit trail
- 🚀 Faster issue resolution
