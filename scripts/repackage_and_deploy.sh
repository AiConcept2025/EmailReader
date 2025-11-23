#!/usr/bin/env bash
#
#  repackage_and_deploy.sh - EmailReader Project
#  ──────────────────────────────────────────────
#  1. ensure ./venv       – installs/updates deps
#  2. PyInstaller build   – creates docReader executable
#  3. Uses built-in Google Cloud Translation API v3 (google_doc provider)
#
#  Make executable:  chmod +x repackage_and_deploy.sh
#  Run:              ./repackage_and_deploy.sh
#
set -euo pipefail

##### CONFIG ##################################################################
APP_ENTRY="index.py"                # entry script for EmailReader
PYI_NAME="docReader"                # resulting binary name
BUILD_DIR="dist"                     # PyInstaller output directory
###############################################################################

echo "==> Setting up virtual-env…"
if [[ ! -d venv ]]; then
    python3 -m venv venv
fi
source venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt
python -m pip install -q pyinstaller

echo "==> Building docReader executable…"
# Clean previous builds
rm -rf build/ dist/ __pycache__/
rm -f "$PYI_NAME"

# Check if entry point exists
if [[ ! -f "$APP_ENTRY" ]]; then
    echo "✗ Error: Entry point '$APP_ENTRY' does not exist!"
    exit 1
fi

# Build with PyInstaller
pyinstaller --clean --onedir \
            --name "$PYI_NAME" \
            --add-data "credentials:credentials" \
            --hidden-import "googleapiclient" \
            --hidden-import "google.oauth2" \
            --hidden-import "langdetect" \
            --hidden-import "docx" \
            --hidden-import "pypdf" \
            --hidden-import "pdf2image" \
            --hidden-import "pytesseract" \
            --hidden-import "schedule" \
            --hidden-import "requests" \
            --hidden-import "pdfplumber" \
            --hidden-import "striprtf" \
            --hidden-import "imap_tools" \
            --collect-all "google-api-python-client" \
            --collect-all "google-auth" \
            --collect-all "google-auth-httplib2" \
            --collect-all "google-auth-oauthlib" \
            "$APP_ENTRY"

# Ensure the onedir executable exists
if [[ ! -x "$BUILD_DIR/$PYI_NAME/$PYI_NAME" ]]; then
    echo "✗ Build failed – executable not found at $BUILD_DIR/$PYI_NAME/$PYI_NAME"
    exit 1
fi

echo "✓ Build complete – $BUILD_DIR/$PYI_NAME/$PYI_NAME"

# GoogleTranslator dependency removed - using built-in Google Cloud Translation API
# (cd ../GoogleTranslator && ./repackage_deploy.sh)
# cp ../GoogleTranslator/dist/translate_document .
# chmod +x translate_document
echo "✓ Using built-in Google Cloud Translation API (google_doc provider)"


