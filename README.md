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
