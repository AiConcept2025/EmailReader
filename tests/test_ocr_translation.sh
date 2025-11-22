#!/bin/bash

################################################################################
# EmailReader OCR + Translation Test Script
#
# Tests the complete document processing pipeline:
# 1. Azure Document Intelligence OCR (PDF -> DOCX)
# 2. Google Cloud Translation API (DOCX -> Translated DOCX)
#
# Usage:
#   ./test_ocr_translation.sh <input_file.pdf>
#   ./test_ocr_translation.sh <input_file.pdf> [target_language]
#
# Examples:
#   ./test_ocr_translation.sh document.pdf
#   ./test_ocr_translation.sh document.pdf en
#   ./test_ocr_translation.sh document.pdf es
#
# Output files will be saved in the current directory:
#   - <basename>_ocr.docx          (OCR result)
#   - <basename>_translated.docx   (Translated result)
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

################################################################################
# Functions
################################################################################

print_header() {
    echo -e "${BLUE}================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_step() {
    echo -e "\n${BLUE}$1${NC}"
}

show_usage() {
    echo "Usage: $0 <input_file.pdf> [target_language]"
    echo ""
    echo "Arguments:"
    echo "  input_file.pdf    Path to PDF file to process"
    echo "  target_language   Target language code (default: en)"
    echo ""
    echo "Examples:"
    echo "  $0 document.pdf           # Translate to English"
    echo "  $0 document.pdf en        # Translate to English"
    echo "  $0 document.pdf es        # Translate to Spanish"
    echo "  $0 document.pdf fr        # Translate to French"
    echo ""
    echo "Output:"
    echo "  <basename>_ocr.docx         OCR result in current directory"
    echo "  <basename>_translated.docx  Translation result in current directory"
    exit 1
}

################################################################################
# Validate Input
################################################################################

print_header "EmailReader OCR + Translation Test"

# Check arguments
if [ $# -lt 1 ]; then
    print_error "No input file specified"
    echo ""
    show_usage
fi

INPUT_FILE="$1"
TARGET_LANG="${2:-en}"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    print_error "Input file not found: $INPUT_FILE"
    exit 1
fi

# Check if input is a PDF
if [[ ! "$INPUT_FILE" =~ \.pdf$ ]]; then
    print_error "Input file must be a PDF (.pdf extension)"
    exit 1
fi

# Get absolute path
INPUT_FILE="$(cd "$(dirname "$INPUT_FILE")" && pwd)/$(basename "$INPUT_FILE")"

# Get base name without extension
BASENAME=$(basename "$INPUT_FILE" .pdf)

# Output file paths in current directory
OCR_OUTPUT="$(pwd)/${BASENAME}_ocr.docx"
TRANSLATION_OUTPUT="$(pwd)/${BASENAME}_translated.docx"

################################################################################
# Display Configuration
################################################################################

print_info "Configuration:"
echo "  Input file:        $INPUT_FILE"
echo "  Target language:   $TARGET_LANG"
echo "  OCR output:        $OCR_OUTPUT"
echo "  Translation output: $TRANSLATION_OUTPUT"
echo ""

################################################################################
# Check Virtual Environment
################################################################################

print_step "Step 1: Checking virtual environment"

if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run: python -m venv venv"
    exit 1
fi

print_success "Virtual environment found"

# Activate virtual environment
source venv/bin/activate
print_success "Virtual environment activated"

################################################################################
# Verify Configuration
################################################################################

print_step "Step 2: Verifying configuration"

python - <<EOF
from src.config import load_config
import sys

try:
    config = load_config()

    # Check OCR config
    ocr_config = config.get('ocr', {})
    if not ocr_config:
        print("✗ OCR configuration not found")
        sys.exit(1)

    provider = ocr_config.get('provider')
    if provider != 'azure':
        print(f"✗ OCR provider is '{provider}', expected 'azure'")
        sys.exit(1)

    azure_config = ocr_config.get('azure', {})
    if not azure_config.get('endpoint') or not azure_config.get('api_key'):
        print("✗ Azure OCR credentials not configured")
        sys.exit(1)

    print(f"✓ OCR configured: Azure Document Intelligence")

    # Check Translation config
    translation_config = config.get('translation', {})
    if not translation_config:
        print("✗ Translation configuration not found")
        sys.exit(1)

    trans_provider = translation_config.get('provider')
    if trans_provider != 'google_doc':
        print(f"✗ Translation provider is '{trans_provider}', expected 'google_doc'")
        sys.exit(1)

    google_doc_config = translation_config.get('google_doc', {})
    project_id = google_doc_config.get('project_id')
    if not project_id:
        print("✗ Google Translation project_id not configured")
        sys.exit(1)

    print(f"✓ Translation configured: Google Cloud Translation (project: {project_id})")

except Exception as e:
    print(f"✗ Configuration error: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    print_error "Configuration verification failed"
    exit 1
fi

################################################################################
# Step 1: Azure OCR
################################################################################

print_step "Step 3: Running Azure Document Intelligence OCR"

print_info "Processing: $INPUT_FILE"
print_info "This may take 10-30 seconds depending on document size..."

python - <<EOF
from src.ocr import OCRProviderFactory
from src.config import load_config
import sys
import time

try:
    start_time = time.time()

    # Load config and create OCR provider
    config = load_config()
    ocr_provider = OCRProviderFactory.get_provider(config)

    print(f"  Provider: {type(ocr_provider).__name__}")

    # Process document
    ocr_provider.process_document(
        "$INPUT_FILE",
        "$OCR_OUTPUT"
    )

    duration = time.time() - start_time

    import os
    if os.path.exists("$OCR_OUTPUT"):
        size = os.path.getsize("$OCR_OUTPUT") / 1024
        print(f"✓ OCR completed in {duration:.1f} seconds")
        print(f"✓ Output file: $OCR_OUTPUT ({size:.1f} KB)")
    else:
        print("✗ OCR failed: Output file not created")
        sys.exit(1)

except Exception as e:
    print(f"✗ OCR failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    print_error "Azure OCR failed"
    exit 1
fi

print_success "OCR completed successfully"

################################################################################
# Step 2: Google Cloud Translation
################################################################################

print_step "Step 4: Running Google Cloud Translation"

print_info "Translating to: $TARGET_LANG"
print_info "This may take 5-15 seconds..."

python - <<EOF
from src.translation import get_translator
from src.config import load_config
import sys
import time

try:
    start_time = time.time()

    # Load config and create translator
    config = load_config()
    translator = get_translator(config)

    print(f"  Translator: {type(translator).__name__}")

    # Translate document
    translator.translate_document(
        input_path="$OCR_OUTPUT",
        output_path="$TRANSLATION_OUTPUT",
        target_lang="$TARGET_LANG"
    )

    duration = time.time() - start_time

    import os
    if os.path.exists("$TRANSLATION_OUTPUT"):
        size = os.path.getsize("$TRANSLATION_OUTPUT") / 1024
        print(f"✓ Translation completed in {duration:.1f} seconds")
        print(f"✓ Output file: $TRANSLATION_OUTPUT ({size:.1f} KB)")
    else:
        print("✗ Translation failed: Output file not created")
        sys.exit(1)

except Exception as e:
    print(f"✗ Translation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    print_error "Google Cloud Translation failed"
    exit 1
fi

print_success "Translation completed successfully"

################################################################################
# Summary
################################################################################

print_header "Test Completed Successfully"

echo ""
print_success "All steps completed successfully"
echo ""
echo "Results:"
echo "  OCR Result:         $OCR_OUTPUT"
echo "  Translation Result: $TRANSLATION_OUTPUT"
echo ""
echo "You can now:"
echo "  - Open the OCR result to verify text extraction"
echo "  - Open the translation result to verify translation quality"
echo "  - Compare the original and translated documents"
echo ""

# Show file sizes
if [ -f "$OCR_OUTPUT" ] && [ -f "$TRANSLATION_OUTPUT" ]; then
    echo "File Sizes:"
    ls -lh "$OCR_OUTPUT" | awk '{print "  OCR:         " $5 " - " $9}'
    ls -lh "$TRANSLATION_OUTPUT" | awk '{print "  Translation: " $5 " - " $9}'
    echo ""
fi

exit 0
