"""
Test Azure paragraph extraction
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

print(f"Pages: {len(result.pages)}")
print(f"Has paragraphs attr: {hasattr(result, 'paragraphs')}")

if hasattr(result, 'paragraphs') and result.paragraphs:
    print(f"Paragraphs found: {len(result.paragraphs)}")
    print()

    # Find paragraph containing our test text
    for i, para in enumerate(result.paragraphs):
        if "Я убеждена" in para.content:
            print(f"Paragraph {i + 1}:")
            print("=" * 80)
            print(para.content)
            print("=" * 80)
            print(f"Has bounding_regions: {hasattr(para, 'bounding_regions')}")
            if hasattr(para, 'bounding_regions') and para.bounding_regions:
                print(f"Page number: {para.bounding_regions[0].page_number}")
            print()
            break
else:
    print("No paragraphs found - using lines instead")
    print(f"Total lines: {sum(len(page.lines) for page in result.pages)}")
