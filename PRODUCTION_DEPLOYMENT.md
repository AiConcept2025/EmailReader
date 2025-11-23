# EmailReader Production Deployment Guide

This guide provides step-by-step instructions for deploying EmailReader to a production server.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Installation Setup](#pre-installation-setup)
3. [Python Environment Setup](#python-environment-setup)
4. [System Dependencies Installation](#system-dependencies-installation)
5. [Application Installation](#application-installation)
6. [Configuration](#configuration)
7. [Service Setup (Optional)](#service-setup-optional)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Hardware Requirements
- **CPU:** 2+ cores
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 10GB minimum free space
- **Network:** Stable internet connection for API calls

### Supported Operating Systems
- Ubuntu 20.04 LTS or later (recommended)
- Debian 11 or later
- CentOS/RHEL 8 or later
- macOS 11 or later

### Required Services Access
- Google Cloud Platform (Translation API, Document AI)
- Azure Cognitive Services (Document Intelligence)
- Google Drive API
- Email account (IMAP access)
- FlowiseAI server (if using default_mode)
- Pinecone account (optional, if using Pinecone mode)

---

## Pre-Installation Setup

### 1. Update System Packages

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

**CentOS/RHEL:**
```bash
sudo yum update -y
```

**macOS:**
```bash
brew update
brew upgrade
```

### 2. Create Application User (Linux only)

```bash
# Create dedicated user for the application
sudo useradd -m -s /bin/bash emailreader

# Switch to the application user
sudo su - emailreader
```

### 3. Create Application Directory

```bash
# Create application directory
mkdir -p ~/emailreader
cd ~/emailreader

# Clone or copy application files here
# git clone <repository-url> .
# OR upload files via scp/rsync
```

---

## Python Environment Setup

### 1. Install Python 3.11+

**Ubuntu/Debian:**
```bash
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
```

**CentOS/RHEL:**
```bash
sudo yum install -y python311 python311-devel
```

**macOS:**
```bash
brew install python@3.11
```

### 2. Verify Python Installation

```bash
python3.11 --version
# Should output: Python 3.11.x or later
```

### 3. Create Virtual Environment

```bash
cd ~/emailreader
python3.11 -m venv venv
```

### 4. Activate Virtual Environment

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
.\venv\Scripts\activate
```

### 5. Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

---

## System Dependencies Installation

### 1. Tesseract OCR

Tesseract is required for OCR processing and rotation detection fallback.

**Ubuntu/Debian:**
```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-all
```

**CentOS/RHEL:**
```bash
sudo yum install -y tesseract tesseract-langpack-*
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Verify Installation:**
```bash
tesseract --version
# Should output: tesseract 4.x or 5.x
```

### 2. Poppler (PDF Processing)

**Ubuntu/Debian:**
```bash
sudo apt-get install -y poppler-utils
```

**CentOS/RHEL:**
```bash
sudo yum install -y poppler-utils
```

**macOS:**
```bash
brew install poppler
```

**Verify Installation:**
```bash
pdfinfo -v
which pdfinfo
# Should return: /usr/bin/pdfinfo or similar
```

### 3. Additional System Libraries

**Ubuntu/Debian:**
```bash
sudo apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev
```

**CentOS/RHEL:**
```bash
sudo yum groupinstall -y "Development Tools"
sudo yum install -y \
    openssl-devel \
    libffi-devel \
    libxml2-devel \
    libxslt-devel \
    libjpeg-devel \
    libpng-devel \
    zlib-devel
```

---

## Application Installation

### 1. Install Python Dependencies

```bash
cd ~/emailreader
source venv/bin/activate  # If not already activated

# Install all required packages
pip install -r requirements.txt
```

**Expected packages include:**
- google-cloud-translate>=3.15.0
- azure-ai-formrecognizer>=3.3.0
- python-docx
- paddleocr>=2.7.0
- **paddlepaddle>=3.2.0** (required for PaddleOCR rotation detection)
- img2pdf>=0.5.0
- pytesseract
- pillow
- PyMuPDF
- and many more (see requirements.txt)

**Installation may take 5-10 minutes.**

**Note on PaddlePaddle:**
- **License:** Apache 2.0 (completely free and open-source)
- **Size:** ~100MB download
- **Platform Support:** macOS (ARM64/x86), Linux (x86_64, ARM), Windows
- **Purpose:** Deep learning backend required for PaddleOCR's advanced rotation detection
- **GPU Support:** Optional - install `paddlepaddle-gpu` instead if you have CUDA-capable GPU
- **Repository:** https://github.com/PaddlePaddle/Paddle

### 2. Verify Installation

```bash
# Test PaddleOCR
python -c "import paddleocr; print('PaddleOCR version:', paddleocr.__version__)"

# Test PaddlePaddle backend (CRITICAL for rotation detection)
python -c "import paddle; print('PaddlePaddle version:', paddle.__version__)"

# Test Azure
python -c "from azure.ai.formrecognizer import DocumentAnalysisClient; print('Azure SDK OK')"

# Test Google Cloud
python -c "from google.cloud import translate_v3; print('Google Cloud SDK OK')"

# Test img2pdf
python -c "import img2pdf; print('img2pdf OK')"
```

All commands should complete without errors.

---

## Configuration

### 1. Create Credentials Directory

```bash
mkdir -p ~/emailreader/credentials
cd ~/emailreader/credentials
```

### 2. Configure Application Settings

Copy the template configuration:

```bash
cp config.template.json config.prod.json
```

### 3. Edit Production Configuration

```bash
nano config.prod.json  # or vim, vi, etc.
```

**Required Configuration Sections:**

#### A. Google Drive Settings
```json
{
  "google_drive": {
    "parent_folder_id": "YOUR_GOOGLE_DRIVE_FOLDER_ID",
    "service_account": {
      "type": "service_account",
      "project_id": "YOUR_PROJECT_ID",
      "private_key_id": "YOUR_PRIVATE_KEY_ID",
      "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
      "client_email": "YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com",
      "client_id": "YOUR_CLIENT_ID",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
    }
  }
}
```

#### B. Azure OCR Settings
```json
{
  "ocr": {
    "provider": "azure",
    "azure": {
      "endpoint": "https://YOUR_REGION.api.cognitive.microsoft.com/",
      "api_key": "YOUR_AZURE_API_KEY",
      "model": "prebuilt-layout",
      "paragraph_processor": {
        "min_content_length": 10,
        "max_consecutive_empty": 1,
        "normalize_whitespace": true
      }
    }
  }
}
```

#### C. Translation Settings
```json
{
  "translation": {
    "provider": "google_doc",
    "google_doc": {
      "project_id": "YOUR_PROJECT_ID",
      "location": "us-central1",
      "default_source_language": "ru",
      "default_target_language": "en"
    }
  }
}
```

#### D. Email Settings
```json
{
  "email": {
    "username": "your-email@example.com",
    "password": "YOUR_APP_PASSWORD",
    "initial_folder": "INBOX",
    "imap_server": "imap.example.com",
    "date_file": "data/last_finish_time.txt",
    "start_date": "2020-01-01 00:00:00 -0800"
  }
}
```

#### E. Rotation Detection Settings (Enabled by default)
```json
{
  "preprocessing": {
    "rotation_detection": {
      "enabled": true,
      "method": "paddleocr",
      "fallback_methods": ["tesseract"],
      "confidence_threshold": 0.8,
      "paddleocr": {
        "lang": "ru",
        "use_gpu": false
      }
    }
  }
}
```

**Note:** Set `use_gpu: true` only if you have CUDA-capable GPU installed.

#### F. FlowiseAI Settings (for default_mode)
```json
{
  "flowise": {
    "api_url": "http://YOUR_FLOWISE_HOST:PORT/api/v1",
    "api_key": "YOUR_FLOWISE_API_KEY",
    "chatflow_id": "YOUR_CHATFLOW_ID",
    "doc_store_id": "YOUR_DOC_STORE_ID",
    "doc_loader_docx_id": "YOUR_DOC_LOADER_ID"
  }
}
```

#### G. Pinecone Settings (optional)
```json
{
  "use_pinecone": false,
  "pinecone": {
    "api_key": "YOUR_PINECONE_API_KEY"
  }
}
```

#### H. Program Mode
```json
{
  "app": {
    "program": "translator",
    "translator_url": "http://localhost:8000/submit"
  }
}
```

**Mode Options:**
- `"translator"` - Pure translation workflow (no FlowiseAI, no Pinecone)
- `"default_mode"` - Document analysis with FlowiseAI/Pinecone

### 4. Set File Permissions

```bash
chmod 600 config.prod.json
# Only owner can read/write configuration files
```

### 5. Create Required Directories

```bash
cd ~/emailreader
mkdir -p data documents logs metrics
```

---

## Service Setup (Optional)

For running EmailReader as a system service that starts automatically.

### 1. Create Systemd Service File (Linux)

```bash
sudo nano /etc/systemd/system/emailreader.service
```

**Service Configuration:**

```ini
[Unit]
Description=EmailReader - Document Processing Service
After=network.target

[Service]
Type=simple
User=emailreader
Group=emailreader
WorkingDirectory=/home/emailreader/emailreader
Environment="PATH=/home/emailreader/emailreader/venv/bin"
Environment="ENV=prod"
ExecStart=/home/emailreader/emailreader/venv/bin/python index.py
Restart=on-failure
RestartSec=10
StandardOutput=append:/home/emailreader/emailreader/logs/emailreader.log
StandardError=append:/home/emailreader/emailreader/logs/emailreader_error.log

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable emailreader

# Start service
sudo systemctl start emailreader

# Check status
sudo systemctl status emailreader
```

### 3. Service Management Commands

```bash
# Start service
sudo systemctl start emailreader

# Stop service
sudo systemctl stop emailreader

# Restart service
sudo systemctl restart emailreader

# View logs
sudo journalctl -u emailreader -f

# Or view log files directly
tail -f ~/emailreader/logs/emailreader.log
```

---

## Testing

### 1. Test Rotation Detection

```bash
cd ~/emailreader
source venv/bin/activate

python3 test_rotation_detection.py path/to/test_document.pdf
```

**Expected Output:**
```
INFO - Rotation detection enabled, checking document orientation
INFO - Method 'paddleocr' detected rotation: 90� (confidence: 0.95)
INFO - Document rotation detected: 90� (confidence: 0.95)
INFO - Document rotated, using corrected version for OCR
```

### 2. Test Manual Processing

```bash
python src/app.py
```

Monitor logs for successful processing:
```bash
tail -f logs/email_reader.log
```

### 3. Test Scheduled Processing

```bash
python index.py
```

**Expected Output:**
```
INFO - Starting EmailReader application
INFO - Program mode: translator
INFO - Google Drive processing scheduled every 15 minutes
INFO - Starting first run...
```

### 4. Verify Cloud Services

**Test Azure OCR:**
```bash
python verify_azure_ocr_config.py
```

**Test Google Cloud Translation:**
```bash
python -c "from src.config import load_config; config = load_config(); print('Config loaded:', 'translation' in config)"
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. ModuleNotFoundError: No module named 'paddleocr'

**Solution:**
```bash
source venv/bin/activate
pip install "paddleocr>=2.7.0" "img2pdf>=0.5.0"
```

#### 2. Tesseract not found

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-all

# Verify
tesseract --version
which tesseract
```

#### 3. PDFInfoNotInstalledError

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# Verify
which pdfinfo
```

#### 4. Google Cloud Authentication Error

**Solution:**
- Verify service account JSON in config.prod.json
- Check project_id matches your GCP project
- Ensure APIs are enabled in GCP console:
  - Cloud Translation API
  - Google Drive API

#### 5. Azure Cognitive Services Error (403)

**Solution:**
- Verify endpoint URL is correct for your region
- Check API key is valid
- Ensure you've accepted Azure terms of service
- For Free tier (F0): only first 2 pages of PDFs are processed

#### 6. Rotation Detection Not Working

**Solution:**
```bash
# Check if preprocessing config exists
grep -A 10 "preprocessing" credentials/config.prod.json

# Should see:
# "preprocessing": {
#   "rotation_detection": {
#     "enabled": true,
#     ...
```

#### 7. Permission Denied Errors

**Solution:**
```bash
# Fix ownership
sudo chown -R emailreader:emailreader ~/emailreader

# Fix permissions
chmod 755 ~/emailreader
chmod 600 ~/emailreader/credentials/*.json
```

#### 8. Service Fails to Start

**Solution:**
```bash
# Check logs
sudo journalctl -u emailreader -n 50

# Check service status
sudo systemctl status emailreader

# Verify paths in service file
sudo nano /etc/systemd/system/emailreader.service

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart emailreader
```

---

## Performance Tuning

### 1. Enable GPU Acceleration (if available)

Edit `config.prod.json`:
```json
{
  "preprocessing": {
    "rotation_detection": {
      "paddleocr": {
        "use_gpu": true
      }
    }
  }
}
```

**Requirements:**
- NVIDIA GPU
- CUDA toolkit installed
- cuDNN installed

### 2. Adjust Processing Intervals

Edit `config.prod.json`:
```json
{
  "scheduling": {
    "google_drive_interval_minutes": 15
  }
}
```

### 3. Configure Paragraph Processor

For better OCR quality control:
```json
{
  "ocr": {
    "azure": {
      "paragraph_processor": {
        "min_content_length": 10,
        "max_consecutive_empty": 1,
        "normalize_whitespace": true
      }
    }
  }
}
```

---

## Security Best Practices

### 1. Configuration Files

```bash
# Restrict access to config files
chmod 600 credentials/*.json

# Never commit config files to git
echo "credentials/config.*.json" >> .gitignore
```

### 2. Log Files

```bash
# Restrict log access
chmod 640 logs/*.log

# Rotate logs to prevent disk fill
# Use logrotate or similar
```

### 3. Service Account

```bash
# Run as dedicated user, not root
# Already configured in systemd service
```

### 4. Network Security

- Use firewall rules to restrict access
- Enable HTTPS for all API calls
- Use VPN if processing sensitive documents

---

## Monitoring and Maintenance

### 1. Log Monitoring

```bash
# Monitor application logs
tail -f ~/emailreader/logs/email_reader.log

# Monitor service logs
sudo journalctl -u emailreader -f
```

### 2. Disk Space Monitoring

```bash
# Check disk usage
df -h ~/emailreader

# Clean up old temporary files
find ~/emailreader/documents -type f -mtime +30 -delete
```

### 3. Regular Updates

```bash
# Update Python packages monthly
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Update system packages
sudo apt-get update && sudo apt-get upgrade
```

---

## Environment Variables

Alternative to config file for sensitive data:

```bash
export ENV=prod
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export AZURE_OCR_ENDPOINT=https://your-region.api.cognitive.microsoft.com/
export AZURE_OCR_API_KEY=your-api-key
```

---

## Production Checklist

Before going live, verify:

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] All system dependencies installed (tesseract, poppler)
- [ ] All Python packages installed from requirements.txt
- [ ] config.prod.json configured with production credentials
- [ ] File permissions set correctly (600 for configs)
- [ ] Required directories created (data, documents, logs, metrics)
- [ ] Google Cloud APIs enabled and credentials valid
- [ ] Azure Cognitive Services account active
- [ ] Email IMAP access configured
- [ ] Rotation detection tested and working
- [ ] Service file created (if using systemd)
- [ ] Service enabled and started
- [ ] Logs monitoring configured
- [ ] Backup strategy in place

---

## Support and Documentation

- **Application README:** `README.md`
- **Test Script Guide:** `TEST_SCRIPT_README.md`
- **Mode Reference:** `MODE_QUICK_REFERENCE.md`
- **Pinecone Analysis:** `PINECONE_MODE_ANALYSIS.md`
- **Configuration Template:** `credentials/config.template.json`

---

## Version Information

- **Application:** EmailReader
- **Python Required:** 3.11+
- **PaddleOCR:** 3.3.2+
- **Azure SDK:** 3.3.0+
- **Google Cloud Translation:** 3.15.0+

---

**Last Updated:** November 2024
