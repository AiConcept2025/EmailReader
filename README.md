# Email Reader

Email reader for reading emails from yahoo account

How to create a requirements.txt:
pip freeze > requirements.txt

PyInstaller Manual
https://pyinstaller.org/en/stable/

Activate venv:
./venv/Scripts/activate

Install packages:
pip install -r requirements.txt

## Rotation Detection Setup (Optional but Recommended)

The EmailReader now includes automatic document rotation detection for rotated PDFs and images. This feature uses PaddleOCR and Tesseract to detect and correct document orientation before OCR processing.

### Installing Rotation Detection Dependencies

**Option 1: Install via requirements.txt (Recommended)**
```bash
source venv/bin/activate  # macOS/Linux
./venv/Scripts/activate   # Windows
pip install -r requirements.txt
```

**Option 2: Manual Installation**
```bash
source venv/bin/activate  # macOS/Linux
pip install "paddleocr>=2.7.0" "paddlepaddle" "img2pdf>=0.5.0"
```

### Dependencies Installed:
- **paddleocr** (3.3.2+): Advanced OCR with built-in rotation detection, supports 109 languages including Russian handwriting
- **paddlepaddle** (3.2.2+): Deep learning backend for PaddleOCR (~100MB download, open-source and free)
- **img2pdf** (0.6.3+): PDF rotation correction utility

### PaddlePaddle Installation Notes:
- **License:** Apache 2.0 (completely free and open-source)
- **Size:** ~100MB download
- **Platform:** Supports macOS (ARM64/x86), Linux, Windows
- **GPU Support:** Optional - set `use_gpu: true` in config if you have CUDA-capable GPU
- **Repository:** https://github.com/PaddlePaddle/Paddle

### Configuration

Rotation detection is enabled by default in `credentials/config.dev.json` and `credentials/config.prod.json`:

```json
{
  "preprocessing": {
    "rotation_detection": {
      "enabled": true,
      "method": "paddleocr",
      "fallback_methods": ["tesseract"],
      "confidence_threshold": 0.5,
      "paddleocr": {
        "lang": "ru",
        "use_gpu": false
      }
    }
  }
}
```

### Features:
- Detects rotation angles: 0°, 90°, 180°, 270°
- Primary method: PaddleOCR (supports multilingual handwriting)
- Fallback method: Tesseract OSD (printed text)
- Automatic correction before OCR processing
- Configurable confidence threshold

### Testing Rotation Detection

Test standalone with:
```bash
python3 test_rotation_detection.py path/to/rotated_document.pdf
```

Expected log output:
```
INFO - Rotation detection enabled, checking document orientation
INFO - Method 'paddleocr' detected rotation: 90° (confidence: 0.95)
INFO - Document rotation detected: 90° (confidence: 0.95)
INFO - Document rotated, using corrected version for OCR
```

tesseract:
https://sourceforge.net/projects/tesseract-ocr.mirror/
https://github.com/tesseract-ocr/tesseract
https://muthu.co/all-tesseract-ocr-options/

sudo apt-get install tesseract-ocr-all


pdf2image
https://pypi.org/project/pdf2image/

pytesseract
Python-tesseract is an optical character recognition (OCR) tool for python. That is, it will recognize and “read” the text embedded in images.
https://pypi.org/project/pytesseract/

PyMuPDF
https://pymupdf.readthedocs.io/en/latest/

Solving PDFInfoNotInstalledError on Ubuntu: poppler and PATH
The error "PDFInfoNotInstalledError: Unable to get page count. Is poppler installed and in PATH?" indicates that your system cannot locate the necessary Poppler libraries, which are used by applications (like Python libraries such as pdf2image or UnstructuredPDFLoader) to process PDF files. To resolve this on Ubuntu, you need to ensure Poppler is installed and accessible to your system's PATH.
Here's how to address the issue:
1. Install Poppler Utilities
Poppler provides command-line utilities for working with PDFs. You can install them using your system's package manager, apt, in Ubuntu.
Open your terminal.
Update your package list:
bash
sudo apt-get update
Install poppler-utils:
bash
sudo apt-get install -y poppler-utils

2. Verify Installation and PATH
After installation, verify that the pdfinfo command (part of Poppler) is working and accessible from your system's PATH:
Open your terminal.
Check if pdfinfo is found:
bash
which pdfinfo
This should return the path to the pdfinfo executable, typically /usr/bin/pdfinfo.
If pdfinfo is not found, or your application is still reporting the error, check your system's PATH variable to ensure that the directory containing the Poppler binaries (usually /usr/bin/) is included.
bash
echo $PATH
If /usr/bin/ is missing from your PATH, you can temporarily add it for your current session:
bash
export PATH=/usr/bin:$PATH
For a permanent solution, you would typically add this to your ~/.bashrc or similar shell configuration file. However, /usr/bin/ is usually included in the default PATH on most Ubuntu systems.
3. Reinstall or Reconfigure Poppler (if necessary)
If the above steps don't resolve the problem, you may need to:
Remove and reinstall poppler-utils: Sometimes, reinstalling can fix corrupted installations.
bash
sudo apt-get purge poppler-utils
sudo apt-get install -y poppler-utils
Specify Poppler path in your code (if using a library like pdf2image): Some libraries allow you to explicitly specify the path to Poppler utilities. Consult the documentation of the specific library you are using for details.
By following these steps, you should be able to install Poppler and resolve the PDFInfoNotInstalledError on your Ubuntu system.
COMMIT TEST
