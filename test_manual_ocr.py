"""
Manually test the OCR process with debugging
"""
from src.ocr import OCRProviderFactory
from src.config import load_config

config = load_config()
ocr_provider = OCRProviderFactory.get_provider(config)

input_file = "ФТР Артем Строкань EB1  (1) (2).pdf"
output_file = "test_manual_debug.docx"

print(f"Processing: {input_file}")
print(f"Output: {output_file}")
print()

# Enable more detailed output by directly calling the Azure method
with open(input_file, 'rb') as f:
    pdf_bytes = f.read()

# Call the _ocr_with_azure method directly
result = ocr_provider._ocr_with_azure(pdf_bytes)

print(f"Result type: {type(result)}")
print(f"Number of pages: {len(result)}")

for i, page_content in enumerate(result, 1):
    print(f"\nPage {i}:")
    print(f"  Type: {type(page_content)}")
    if isinstance(page_content, list):
        print(f"  Number of paragraphs: {len(page_content)}")
        for j, para in enumerate(page_content[:3], 1):
            print(f"    Para {j}: {repr(para[:60])}")
    else:
        print(f"  Length: {len(page_content)}")
        print(f"  Preview: {repr(page_content[:100])}")

# Now save it
print(f"\nSaving to {output_file}...")
ocr_provider._save_as_docx(result, output_file)
print("Done!")
