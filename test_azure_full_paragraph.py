"""
Test all Azure paragraphs to see which contain newlines
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

print(f"Total paragraphs: {len(result.paragraphs)}")
print()

# Find paragraphs with newlines
for i, para in enumerate(result.paragraphs):
    if '\n' in para.content:
        page_num = para.bounding_regions[0].page_number if para.bounding_regions else '?'
        print(f"Paragraph {i+1} (page {page_num}) HAS newlines:")
        print(f"  Length: {len(para.content)}")
        print(f"  Preview: {repr(para.content[:100])}")
        print()
