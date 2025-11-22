"""
Analyze bounding boxes with actual text from LandingAI JSON
"""
import json
import sys
import re

if len(sys.argv) < 2:
    print("Usage: python analyze_with_text.py <landing_ai_json>")
    sys.exit(1)

json_path = sys.argv[1]

with open(json_path, 'r') as f:
    data = json.load(f)

print(f"\nLandingAI JSON: {json_path}")
print("\nAll text chunks with bounding boxes:")
print("=" * 100)
print(f"{'Height':<8} {'400x':<8} {'Text'}")
print("=" * 100)

for i, chunk in enumerate(data.get('chunks', []), 1):
    grounding = chunk.get('grounding', {})
    box = grounding.get('box', {})

    if box:
        height = box.get('bottom', 0) - box.get('top', 0)
        markdown = chunk.get('markdown', '').strip()
        # Remove HTML tags and markdown formatting
        text = re.sub(r'<[^>]+>', '', markdown)
        text = text.replace('\n', ' ').strip()
        text = text[:100]  # Truncate to 100 chars

        current_font = height * 400

        print(f"{height:<8.4f} {current_font:<8.1f} {text}")

print("=" * 100)
