"""
Test Azure paragraph content to see if line breaks are in the source
"""
from src.config import load_config
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

# Load config
config = load_config()
azure_config = config['ocr']['azure']

# Create client
client = DocumentAnalysisClient(
    endpoint=azure_config['endpoint'],
    credential=AzureKeyCredential(azure_config['api_key'])
)

# Read PDF
pdf_path = "ФТР Артем Строкань EB1  (1) (2).pdf"
with open(pdf_path, 'rb') as f:
    pdf_bytes = f.read()

print(f"Processing {pdf_path}...")
print()

# Analyze
poller = client.begin_analyze_document("prebuilt-read", document=pdf_bytes)
result = poller.result()

# Find paragraph containing our test text
for i, para in enumerate(result.paragraphs):
    if "Я убеждена" in para.content:
        print(f"Paragraph {i + 1} content:")
        print("=" * 80)
        print(repr(para.content))  # Use repr to see actual \n characters
        print("=" * 80)
        print()
        print("Visual representation:")
        print(para.content)
        print("=" * 80)
        break
