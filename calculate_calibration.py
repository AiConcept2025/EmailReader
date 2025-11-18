"""
Calculate calibration factor from LandingAI JSON and actual font sizes
"""
import json
import sys
from collections import defaultdict

if len(sys.argv) < 2:
    print("Usage: python calculate_calibration.py <landing_ai_json>")
    sys.exit(1)

json_path = sys.argv[1]

with open(json_path, 'r') as f:
    data = json.load(f)

# Extract bounding box heights
heights = []
text_samples = {}

for chunk in data.get('chunks', []):
    grounding = chunk.get('grounding', {})
    box = grounding.get('box', {})

    if box:
        height = box.get('bottom', 0) - box.get('top', 0)
        # Extract text from markdown field
        markdown = chunk.get('markdown', '').strip()
        # Remove HTML tags and markdown formatting for display
        import re
        text = re.sub(r'<[^>]+>', '', markdown)
        text = text.replace('\n', ' ').strip()

        if height > 0 and text:
            heights.append(height)
            if height not in text_samples:
                text_samples[height] = text[:80]

print(f"\nLandingAI JSON: {json_path}")
print(f"Total chunks with bounding boxes: {len(heights)}")
print("\nBounding box heights (normalized 0-1):")
print("-" * 80)
print(f"{'Height':<12} {'Current (400x)':<15} {'Sample Text'}")
print("-" * 80)

# Group by similar heights
height_groups = defaultdict(list)
for h in heights:
    rounded = round(h, 3)
    height_groups[rounded].append(h)

# Show unique heights with current font sizes
for height in sorted(height_groups.keys())[:20]:  # Show first 20
    avg_height = sum(height_groups[height]) / len(height_groups[height])
    current_font = avg_height * 400
    sample = text_samples.get(height, "")
    print(f"{avg_height:<12.4f} {current_font:<15.1f} {sample}")

print("-" * 80)
print(f"\nHeight range: {min(heights):.4f} to {max(heights):.4f}")
print(f"\nWith calibration factor 400:")
print(f"  Min font: {min(heights) * 400:.1f}pt")
print(f"  Max font: {max(heights) * 400:.1f}pt")

# Calculate what calibration factor would give us 12pt for typical body text
# Assuming body text is around the median height
sorted_heights = sorted(heights)
median_height = sorted_heights[len(sorted_heights) // 2]
print(f"\nMedian height: {median_height:.4f}")
print(f"  Current font (400x): {median_height * 400:.1f}pt")

# Calculate calibration factors for target sizes
target_body = 12.0
target_title = 14.0

# Find a typical title height (larger texts, top 10%)
title_height = sorted_heights[int(len(sorted_heights) * 0.9)]
print(f"\nTypical title height (90th percentile): {title_height:.4f}")
print(f"  Current font (400x): {title_height * 400:.1f}pt")

# Calculate calibration factors
calibration_for_body = target_body / median_height
calibration_for_title = target_title / title_height

print(f"\n" + "=" * 80)
print("CALIBRATION RECOMMENDATIONS:")
print("=" * 80)
print(f"For body text at 12pt:  calibration = {calibration_for_body:.1f}")
print(f"For title text at 14pt: calibration = {calibration_for_title:.1f}")
print(f"Recommended calibration (average): {(calibration_for_body + calibration_for_title) / 2:.1f}")
