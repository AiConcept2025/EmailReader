# Test Suite Quick Reference

Quick commands for running tests in the EmailReader OCR integration.

## Setup

```bash
cd /Users/vladimirdanishevsky/projects/EmailReader
venv/bin/python -m pip install pytest pytest-cov pytest-mock
```

## Common Commands

### Run All Tests
```bash
venv/bin/python -m pytest tests/ -v
```

### Run Tests Quietly
```bash
venv/bin/python -m pytest tests/ -q
```

### Run with Coverage
```bash
venv/bin/python -m pytest tests/ --cov=src/ocr --cov=src/document_analyzer --cov=src/utils/layout_reconstructor -v
```

### Run Specific File
```bash
# OCR providers
venv/bin/python -m pytest tests/test_ocr_providers.py -v

# Document analyzer
venv/bin/python -m pytest tests/test_document_analyzer.py -v

# Layout reconstructor
venv/bin/python -m pytest tests/test_layout_reconstructor.py -v

# Integration tests
venv/bin/python -m pytest tests/test_integration.py -v
```

### Run Specific Class
```bash
venv/bin/python -m pytest tests/test_ocr_providers.py::TestOCRProviderFactory -v
venv/bin/python -m pytest tests/test_ocr_providers.py::TestDefaultOCRProvider -v
venv/bin/python -m pytest tests/test_ocr_providers.py::TestLandingAIProvider -v
```

### Run Specific Test
```bash
venv/bin/python -m pytest tests/test_ocr_providers.py::TestLandingAIProvider::test_api_call_with_retry_success -v
```

### Run Tests Matching Pattern
```bash
# All tests with "retry" in name
venv/bin/python -m pytest tests/ -k retry -v

# All tests with "pdf" in name
venv/bin/python -m pytest tests/ -k pdf -v

# All tests with "landing" in name
venv/bin/python -m pytest tests/ -k landing -v
```

### Run with Different Output Formats
```bash
# Short traceback
venv/bin/python -m pytest tests/ --tb=short

# No traceback (clean output)
venv/bin/python -m pytest tests/ --tb=no

# Line-only traceback
venv/bin/python -m pytest tests/ --tb=line
```

### Show Test Duration
```bash
# Show slowest 10 tests
venv/bin/python -m pytest tests/ --durations=10

# Show all durations
venv/bin/python -m pytest tests/ --durations=0
```

### Stop on First Failure
```bash
venv/bin/python -m pytest tests/ -x
```

### Show Local Variables on Failure
```bash
venv/bin/python -m pytest tests/ -l
```

### Run Failed Tests from Last Run
```bash
venv/bin/python -m pytest tests/ --lf
```

### Run Failed Tests First, Then Others
```bash
venv/bin/python -m pytest tests/ --ff
```

## Coverage Commands

### Basic Coverage
```bash
venv/bin/python -m pytest tests/ --cov=src/ocr
```

### Coverage with Missing Lines
```bash
venv/bin/python -m pytest tests/ --cov=src/ocr --cov-report=term-missing
```

### HTML Coverage Report
```bash
venv/bin/python -m pytest tests/ --cov=src/ocr --cov-report=html
open htmlcov/index.html
```

### Coverage by Module
```bash
venv/bin/python -m pytest tests/ \
  --cov=src/ocr \
  --cov=src/document_analyzer \
  --cov=src/utils/layout_reconstructor \
  --cov-report=term-missing
```

## Test Development

### Run Tests in Watch Mode (requires pytest-watch)
```bash
pip install pytest-watch
ptw tests/
```

### Verbose Output with Print Statements
```bash
venv/bin/python -m pytest tests/ -v -s
```

### List All Tests Without Running
```bash
venv/bin/python -m pytest tests/ --collect-only
```

### Show Test Fixtures
```bash
venv/bin/python -m pytest tests/ --fixtures
```

## Debugging

### Drop into PDB on Failure
```bash
venv/bin/python -m pytest tests/ --pdb
```

### Drop into PDB on Exceptions
```bash
venv/bin/python -m pytest tests/ --pdbcls=IPython.terminal.debugger:TerminalPdb --pdb
```

### Show Print Statements
```bash
venv/bin/python -m pytest tests/ -s
```

### Extra Verbose Output
```bash
venv/bin/python -m pytest tests/ -vv
```

## CI/CD Integration

### Run Tests for CI
```bash
venv/bin/python -m pytest tests/ \
  --cov=src/ocr \
  --cov=src/document_analyzer \
  --cov=src/utils/layout_reconstructor \
  --cov-report=xml \
  --cov-report=term \
  --junitxml=test-results.xml \
  -v
```

### Generate All Reports
```bash
venv/bin/python -m pytest tests/ \
  --cov=src \
  --cov-report=html \
  --cov-report=xml \
  --cov-report=term-missing \
  --junitxml=test-results.xml \
  -v
```

## Test Statistics

### Count Tests
```bash
venv/bin/python -m pytest tests/ --collect-only -q | tail -1
```

### Count Tests by File
```bash
venv/bin/python -m pytest tests/test_ocr_providers.py --collect-only -q | tail -1
venv/bin/python -m pytest tests/test_document_analyzer.py --collect-only -q | tail -1
venv/bin/python -m pytest tests/test_layout_reconstructor.py --collect-only -q | tail -1
venv/bin/python -m pytest tests/test_integration.py --collect-only -q | tail -1
```

## Test Markers (for future use)

### Define Custom Markers in pytest.ini
```ini
[tool:pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### Run by Marker
```bash
# Run only unit tests
venv/bin/python -m pytest tests/ -m unit

# Skip slow tests
venv/bin/python -m pytest tests/ -m "not slow"

# Run integration tests
venv/bin/python -m pytest tests/ -m integration
```

## Useful Combinations

### Quick Check (fast, minimal output)
```bash
venv/bin/python -m pytest tests/ -q --tb=no
```

### Full Report (verbose, coverage, durations)
```bash
venv/bin/python -m pytest tests/ -v \
  --cov=src/ocr \
  --cov-report=term-missing \
  --durations=10
```

### Debug Specific Test
```bash
venv/bin/python -m pytest tests/test_ocr_providers.py::TestLandingAIProvider::test_api_call_with_retry_success -v -s --pdb
```

### CI Pipeline
```bash
venv/bin/python -m pytest tests/ \
  --cov=src \
  --cov-report=xml \
  --cov-report=term \
  --junitxml=test-results.xml \
  --tb=short \
  -v
```

## Expected Output

### Success
```
============================= test session starts ==============================
platform darwin -- Python 3.13.5, pytest-9.0.1, pluggy-1.6.0
rootdir: /Users/vladimirdanishevsky/projects/EmailReader
plugins: mock-3.15.1, cov-7.0.0
collected 107 items

tests/test_document_analyzer.py ........................                 [ 22%]
tests/test_integration.py .................                              [ 38%]
tests/test_layout_reconstructor.py ...............................       [ 67%]
tests/test_ocr_providers.py .................................            [100%]

============================= 107 passed in 0.24s ==============================
```

### Failure Example
```
============================= test session starts ==============================
...
FAILED tests/test_ocr_providers.py::TestLandingAIProvider::test_api_call_fails
...
=========================== short test summary info ============================
FAILED tests/test_ocr_providers.py::TestLandingAIProvider::test_api_call_fails
========================= 1 failed, 106 passed in 0.28s ========================
```

## Troubleshooting

### Issue: Tests can't find source modules
```bash
# Solution: Run from project root
cd /Users/vladimirdanishevsky/projects/EmailReader
venv/bin/python -m pytest tests/
```

### Issue: Tests skip with "file not found"
```bash
# Solution: Verify test files exist
ls -la test_docs/
```

### Issue: Import errors
```bash
# Solution: Check virtual environment
which python
venv/bin/python --version
```

### Issue: Coverage warnings
```bash
# Solution: Run coverage with correct module paths
venv/bin/python -m pytest tests/ --cov=src/ocr --cov-report=term
```

## Performance Tips

1. **Run changed tests first**: `venv/bin/python -m pytest tests/ --ff`
2. **Stop on first failure**: `venv/bin/python -m pytest tests/ -x`
3. **Run in parallel** (requires pytest-xdist): `venv/bin/python -m pytest tests/ -n auto`
4. **Skip slow tests**: Add markers and use `-m "not slow"`

## Best Practices

1. **Always run from project root**: `/Users/vladimirdanishevsky/projects/EmailReader`
2. **Use virtual environment**: `venv/bin/python -m pytest`
3. **Run all tests before commit**: `venv/bin/python -m pytest tests/ -v`
4. **Check coverage regularly**: `--cov=src --cov-report=term-missing`
5. **Fix failures immediately**: Don't accumulate test debt

## Quick Test Development Workflow

### 1. Write Test (TDD)
```bash
# Edit test file
code tests/test_ocr_providers.py

# Run new test (should fail)
venv/bin/python -m pytest tests/test_ocr_providers.py::TestLandingAIProvider::test_new_feature -v
```

### 2. Implement Feature
```bash
# Edit source file
code src/ocr/landing_ai_provider.py

# Run test (should pass)
venv/bin/python -m pytest tests/test_ocr_providers.py::TestLandingAIProvider::test_new_feature -v
```

### 3. Verify All Tests Pass
```bash
venv/bin/python -m pytest tests/ -v
```

### 4. Check Coverage
```bash
venv/bin/python -m pytest tests/ --cov=src/ocr --cov-report=term-missing
```

---

**Quick Start:** `venv/bin/python -m pytest tests/ -v`

**Last Updated:** 2025-11-15
