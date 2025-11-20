"""
Check how many paragraphs Azure returns per page
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

# Analyze
poller = client.begin_analyze_document("prebuilt-read", document=pdf_bytes)
result = poller.result()

print(f"Total pages: {len(result.pages)}")
print(f"Total paragraphs: {len(result.paragraphs)}\n")

# Group by page
for page_num in range(1, len(result.pages) + 1):
    page_paras = [
        para
        for para in result.paragraphs
        if hasattr(para, 'bounding_regions') and
           para.bounding_regions and
           para.bounding_regions[0].page_number == page_num
    ]

    print(f"Page {page_num}: {len(page_paras)} paragraphs")
    for i, para in enumerate(page_paras[:5], 1):  # Show first 5
        preview = para.content[:60].replace('\n', '\\n')
        print(f"  {i}. {preview}...")
