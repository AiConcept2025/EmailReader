# Test Mode Usage Guide

## Overview

Test mode allows you to process files from the Inbox without removing them. This is essential for:
- Testing and debugging processing pipelines
- Iterative quality improvement
- A/B testing different configurations
- Collecting metrics without affecting production workflow

## Setup

### 1. Enable Test Mode in Configuration

Add the following sections to your `credentials/config.dev.json` or `credentials/config.prod.json`:

```json
{
  "processing": {
    "test_mode": true,
    "remove_from_inbox": false,
    "track_processed_method": "metadata"
  },

  "metrics": {
    "enabled": true,
    "output_directory": "metrics",
    "upload_to_drive": false
  },

  "quality": {
    "validation_enabled": true,
    "font_size_thresholds": {
      "min": 7.0,
      "max": 48.0,
      "body_text_range": [10.0, 13.0],
      "heading_range": [13.0, 24.0],
      "title_range": [24.0, 48.0]
    },
    "calibration_factor": 400.0
  }
}
```

### 2. Create Metrics Directory

```bash
mkdir -p metrics
```

## How Test Mode Works

### File Tracking

Instead of moving files from Inbox to In-Progress, test mode:
1. Marks files as processed using Google Drive file properties
2. Property name: `processed_at`
3. Property value: ISO timestamp (e.g., `2025-11-17T07:50:00.123456`)

This allows:
- Files remain in Inbox for repeated processing
- System tracks which files have been processed to avoid duplicates
- You can manually clear the property to reprocess a file

### Processing Flow

**Normal Mode (test_mode: false):**
```
Inbox → Download → Process → Upload → Move to In-Progress ✗ (removed from Inbox)
```

**Test Mode (test_mode: true):**
```
Inbox → Download → Process → Upload → Mark as processed ✓ (stays in Inbox)
```

## Running Tests

### Option 1: Run Main Application in Test Mode

```bash
# Set environment
export ENV=dev

# Run the main application (will use test mode if enabled in config)
python index.py
```

The application will:
- Process files without removing them from Inbox
- Collect metrics in `metrics/` directory
- Log everything to `logs/email_reader.log`

### Option 2: Run Iterative Quality Testing

The `test_iterative_processing.py` script allows targeted testing with quality validation:

#### Basic Usage

Process first unprocessed file from danishevsky@yahoo.com/Inbox:

```bash
python test_iterative_processing.py
```

#### Specify a Specific File

```bash
python test_iterative_processing.py --file-name "document.pdf"
```

#### Set Maximum Iterations

```bash
python test_iterative_processing.py --max-iterations 5
```

#### Enable Auto-Tuning

Automatically tries different calibration factors (380, 390, 400, 410, 420):

```bash
python test_iterative_processing.py --auto-tune
```

#### Different Client

```bash
python test_iterative_processing.py --client "otherclient@example.com"
```

#### Combined Example

```bash
python test_iterative_processing.py \
  --file-name "scanned-document.pdf" \
  --max-iterations 10 \
  --auto-tune
```

## What Gets Validated

The quality validator checks:

### Font Size Validation (50 points)
- All font sizes within 7-48pt range
- Body text (10-13pt): 50-85% of document
- Headings (13-24pt): ≥10% of document
- Titles (24-48pt): ≤10% of document
- No outlier fonts outside acceptable range

### Layout Validation (40 points)
- Page breaks preserved (25 points)
- Page count matches source (if known)
- Column detection accurate (15 points)

### Quality Bonus (10 points)
- No outlier font sizes detected

**Passing Score:** ≥70/100

## Understanding Results

### Console Output

The iterative test script provides:

1. **Per-Iteration Reports:**
   ```
   ============================================================
   QUALITY VALIDATION REPORT
   ============================================================
   File: document.docx
   Overall Score: 85.0/100
   Status: ✓ PASS

   FONT SIZE VALIDATION:
     Valid: ✓
     Body Text: 72.5%
     Headings: 18.3%
     Titles: 5.2%

   LAYOUT VALIDATION:
     Page count: 4
     Page breaks: ✓
     Column detection: ✓
   ============================================================
   ```

2. **Final Summary:**
   ```
   ============================================================
   FINAL SUMMARY
   ============================================================
   Total iterations: 3
   Passed: 1/3

   Best result:
     Iteration: 3
     Score: 85.0/100
     Calibration factor: 400.0

   ✓ Quality targets achieved in iteration 3
   ============================================================
   ```

### Metrics JSON Files

Located in `metrics/` directory:

#### `metrics_report_YYYYMMDD_HHMMSS.json`
```json
{
  "summary": {
    "session_id": "20251117_075000",
    "total_files": 1,
    "successful_files": 1,
    "timing": {
      "avg_download": 2.5,
      "avg_processing": 12.3,
      "avg_upload": 3.1,
      "avg_total": 18.9
    },
    "font_statistics": {
      "min_font_size": 10.0,
      "max_font_size": 24.0,
      "mean_font_size": 11.5,
      "avg_body_percentage": 72.5,
      "avg_heading_percentage": 18.3
    }
  },
  "files": [...]
}
```

#### `iterative_test_YYYYMMDD_HHMMSS.json`
```json
{
  "test_summary": {
    "target_client": "danishevsky@yahoo.com",
    "total_iterations": 3,
    "passed_iterations": 1,
    "max_score": 85.0
  },
  "iterations": [
    {
      "iteration": 1,
      "score": 65.0,
      "passed": false,
      "calibration_factor": 380
    },
    {
      "iteration": 2,
      "score": 75.0,
      "passed": true,
      "calibration_factor": 390
    }
  ]
}
```

## Clearing Processed Flags

To reprocess a file that's already been marked as processed:

### Option 1: Using Google Drive API (Programmatic)

```python
from src.google_drive import GoogleApi

google_api = GoogleApi()

# Clear the processed flag
# (Google Drive API doesn't support removing individual properties,
#  so you'll need to update with empty value or use file metadata)
```

### Option 2: Manual via Google Drive UI

Unfortunately, custom file properties are not visible in the Google Drive UI. To reprocess a file in test mode:

1. Temporarily disable the processed check in code
2. Or add a `--force-reprocess` flag to the test script
3. Or move the file to a new location and back

### Option 3: Delete and Re-upload

The simplest approach for testing:
1. Download the file from Inbox
2. Delete it from Inbox
3. Re-upload it to Inbox
4. It will be treated as a new, unprocessed file

## Switching Back to Production Mode

When testing is complete and you want to resume normal operation:

1. Set `test_mode` to `false` in config:
   ```json
   {
     "processing": {
       "test_mode": false,
       "remove_from_inbox": true
     }
   }
   ```

2. Restart the application:
   ```bash
   python index.py
   ```

3. Files will now be moved from Inbox to In-Progress after processing

## Troubleshooting

### "Test mode is not enabled" Error

The iterative test script requires test mode to be enabled:

```bash
ERROR: Test mode is not enabled in configuration!
Please set 'processing.test_mode' to true in your config file
```

**Solution:** Add the `processing` section to your config file as shown in Setup section.

### Import Errors

If you see import errors for new modules:

```bash
ModuleNotFoundError: No module named 'src.metrics_tracker'
```

**Solution:** Ensure you're running from the project root directory:
```bash
cd /Users/vladimirdanishevsky/projects/EmailReader
python test_iterative_processing.py
```

### No Files Found

If the script reports "No unprocessed files found":

**Possible causes:**
1. All files in Inbox have been processed (check for `processed_at` property)
2. The client folder doesn't exist
3. The Inbox folder is empty

**Solution:** Upload a new file or clear processed flags.

## Best Practices

### 1. Use Separate Environment

Run tests with `ENV=dev` to avoid affecting production:

```bash
export ENV=dev
python test_iterative_processing.py
```

### 2. Review Metrics Regularly

Check `metrics/` directory for:
- Processing time trends
- Font size distribution
- Quality score progression
- Error patterns

### 3. Iterative Improvement

1. Run initial test to establish baseline
2. Identify quality issues from validation report
3. Adjust configuration (calibration factor, thresholds)
4. Re-run and compare scores
5. Repeat until targets met

### 4. Document Findings

Keep notes on:
- Best calibration factors for different document types
- Common quality issues and solutions
- Optimal configurations discovered

### 5. A/B Testing

Use auto-tune to test multiple configurations:

```bash
python test_iterative_processing.py --auto-tune --max-iterations 10
```

Compare results to find optimal settings.

## Example Workflow

Here's a complete example of using test mode for quality improvement:

```bash
# 1. Enable test mode
# Edit credentials/config.dev.json to set test_mode: true

# 2. Set environment
export ENV=dev

# 3. Run initial test
python test_iterative_processing.py --file-name "test-document.pdf"

# 4. Review results
cat metrics/iterative_test_*.json | jq '.test_summary'

# 5. If needed, run with auto-tune
python test_iterative_processing.py \
  --file-name "test-document.pdf" \
  --auto-tune \
  --max-iterations 5

# 6. Examine best configuration
cat metrics/iterative_test_*.json | jq '.iterations[] | select(.passed == true) | .calibration_factor'

# 7. Update main config with optimal calibration factor
# Edit config to set quality.calibration_factor

# 8. Test with production-like run (still in test mode)
python index.py
# Let it run for one cycle, then Ctrl+C

# 9. Review metrics
ls -lh metrics/

# 10. When satisfied, disable test mode and deploy
# Set test_mode: false in config
```

## Files Created

The test mode implementation added:

1. **Source Files:**
   - `src/process_google_drive_test.py` - Test version of processing (non-destructive)
   - `src/metrics_tracker.py` - Metrics collection and reporting
   - `src/quality_validator.py` - Quality validation against specifications
   - Updated `src/google_drive.py` - Added file property methods
   - Updated `src/config.py` - Configuration support (already existed)
   - Updated `index.py` - Test mode switching

2. **Test Scripts:**
   - `test_iterative_processing.py` - Iterative testing with quality validation

3. **Configuration:**
   - Updated `credentials/config.template.json` - Added test mode sections

4. **Documentation:**
   - `TEST_MODE_USAGE.md` - This file

## Next Steps

After successful testing:

1. **Apply Learnings:** Update main configuration with optimal settings discovered
2. **Production Deploy:** Disable test mode and deploy to production
3. **Monitor:** Continue collecting metrics in production to track quality
4. **Iterate:** Periodically re-run tests as document types evolve

## Support

For issues or questions:
1. Check logs: `logs/email_reader.log`
2. Review metrics: `metrics/*.json`
3. Check configuration: `credentials/config.{env}.json`
4. Examine code: Source files listed above
