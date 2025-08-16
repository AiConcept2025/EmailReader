#!/usr/bin/env bash
#
#  repackage_and_deploy.sh - EmailReader Project
#  ──────────────────────────────────────────────
#  1. git pull            – fast-forwards the current branch
#  2. ensure ./venv       – installs/updates deps
#  3. PyInstaller build   – creates docReader executable
#  4. Package creation    – creates the docReader package (no deployment)
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

#echo "==> 1/4  Pulling latest commit…"
#git pull --ff-only                               # current branch only

echo "==> 2/4  Setting up virtual-env…"
if [[ ! -d venv ]]; then
    python3 -m venv venv
fi
source venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt

# Install PyInstaller if not already installed
python -m pip install -q pyinstaller

echo "==> 3/4  Building docReader executable…"
# Clean previous builds
rm -rf build/ dist/ __pycache__/
rm -f "$PYI_NAME"

# Check if entry point exists
if [[ ! -f "$APP_ENTRY" ]]; then
    echo "✗ Error: Entry point '$APP_ENTRY' does not exist!"
    exit 1
fi

# Build with PyInstaller
# Using onedir to avoid bootloader parent/child processes
# Adding necessary data files and hidden imports for the project
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

echo "==> 4/4  Finalizing build…"
# Ensure the onedir executable exists and is executable
if [[ -x "$BUILD_DIR/$PYI_NAME/$PYI_NAME" ]]; then
    chmod +x "$BUILD_DIR/$PYI_NAME/$PYI_NAME"
    echo "✓ Build complete – onedir created at: $BUILD_DIR/$PYI_NAME/"
    echo "  Executable location: $(pwd)/$BUILD_DIR/$PYI_NAME/$PYI_NAME"
    echo "  Size: $(du -h $BUILD_DIR/$PYI_NAME/$PYI_NAME | cut -f1)"
else
    echo "✗ Build failed – executable not found at $BUILD_DIR/$PYI_NAME/$PYI_NAME"
    exit 1
fi

# Optional: Create a backup with timestamp (archive the onedir)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
tar -C "$BUILD_DIR" -czf "backups/${PYI_NAME}_${TIMESTAMP}.tar.gz" "$PYI_NAME"
echo "  Backup created: backups/${PYI_NAME}_${TIMESTAMP}.tar.gz"

echo ""
echo "To run the application: ./$BUILD_DIR/$PYI_NAME/$PYI_NAME"
echo ""


