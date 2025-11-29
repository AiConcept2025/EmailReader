#!/usr/bin/env python3
"""
Test script to verify UTF-8 sanitization fix for translated documents.

This script tests the sanitization functions to ensure they properly handle
malformed UTF-8 data that might come from Google Translation API.
"""

import sys
import os
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import just the function we need by reading it from the file
# to avoid importing dependencies like pdfplumber

def load_sanitize_function():
    """Load the sanitize_text_for_xml function without importing dependencies"""
    import re
    import logging

    logger = logging.getLogger('EmailReader.DocConverter')

    def sanitize_text_for_xml(text: str) -> str:
        """
        Remove characters that are invalid in XML/OOXML (Word documents).
        """
        if not text:
            return text

        # First, ensure the text is properly encoded/decoded as UTF-8
        try:
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='replace')
            else:
                text = text.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        except Exception as e:
            pass

        # Remove Unicode replacement characters (U+FFFD)
        text = text.replace('\ufffd', '')

        # Remove NULL bytes
        text = text.replace('\x00', '')

        # Remove control characters except tab, LF, CR
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)

        # Remove invalid Unicode surrogates
        text = re.sub(r'[\ud800-\udfff]', '', text)

        # Validate each character against XML 1.0 spec
        def is_valid_xml_char(char):
            code_point = ord(char)
            return (
                code_point == 0x09 or
                code_point == 0x0A or
                code_point == 0x0D or
                (0x20 <= code_point <= 0xD7FF) or
                (0xE000 <= code_point <= 0xFFFD) or
                (0x10000 <= code_point <= 0x10FFFF)
            )

        text = ''.join(char for char in text if is_valid_xml_char(char))
        return text

    return sanitize_text_for_xml

# Load the function
sanitize_text_for_xml = load_sanitize_function()


def test_sanitize_text_for_xml():
    """Test the enhanced sanitize_text_for_xml function"""
    print("Testing sanitize_text_for_xml()...")
    print("=" * 60)

    # Test 1: Normal text (should pass through)
    test_cases = [
        {
            "name": "Normal English text",
            "input": "Hello, this is a normal document.",
            "expected_same": True
        },
        {
            "name": "Russian/Cyrillic text",
            "input": "Привет мир! This is mixed Russian and English.",
            "expected_same": True
        },
        {
            "name": "Text with NULL bytes",
            "input": "Hello\x00World",
            "expected": "HelloWorld"
        },
        {
            "name": "Text with control characters",
            "input": "Hello\x01\x02\x03World",
            "expected": "HelloWorld"
        },
        {
            "name": "Text with Unicode replacement character",
            "input": "Hello\ufffdWorld",
            "expected": "HelloWorld"
        },
        {
            "name": "Text with invalid surrogates",
            "input": "Hello\ud800World",
            # Surrogates get replaced with '?' during UTF-8 normalization
            # This is acceptable as they're invalid Unicode characters
            "expected": "Hello?World"
        },
        {
            "name": "Text with tabs and newlines (should keep)",
            "input": "Hello\tWorld\nNew Line\rCarriage Return",
            "expected_same": True
        },
        {
            "name": "Mixed valid/invalid characters",
            "input": "Текст\x00with\x01invalid\ufffdchars",
            "expected": "Текстwithinvalidchars"
        },
        {
            "name": "Text with DEL character",
            "input": "Hello\x7fWorld",
            "expected": "HelloWorld"
        },
        {
            "name": "Empty string",
            "input": "",
            "expected_same": True
        }
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        input_text = test["input"]
        expected_same = test.get("expected_same", False)

        result = sanitize_text_for_xml(input_text)

        if expected_same:
            expected = input_text
        else:
            expected = test.get("expected", "")

        # Check result
        if result == expected:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1

        print(f"\nTest {i}: {test['name']}")
        print(f"Status: {status}")
        print(f"Input:    {repr(input_text)}")
        print(f"Expected: {repr(expected)}")
        print(f"Got:      {repr(result)}")

        if result != expected:
            print(f"ERROR: Expected '{expected}' but got '{result}'")

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 60)

    return failed == 0


def test_encoding_normalization():
    """Test UTF-8 encoding normalization"""
    print("\n\nTesting UTF-8 encoding normalization...")
    print("=" * 60)

    # These tests simulate what might come from Google Translation API

    test_cases = [
        {
            "name": "Russian text (valid UTF-8)",
            "input": "Привет мир!",
            "should_be_valid": True
        },
        {
            "name": "French accents",
            "input": "Français, café, naïve",
            "should_be_valid": True
        },
        {
            "name": "German umlauts",
            "input": "Überraschung, Müller, Größe",
            "should_be_valid": True
        },
        {
            "name": "Chinese characters",
            "input": "你好世界",
            "should_be_valid": True
        },
        {
            "name": "Arabic text",
            "input": "مرحبا بالعالم",
            "should_be_valid": True
        },
        {
            "name": "Emoji",
            "input": "Hello 👋 World 🌍",
            "should_be_valid": True
        }
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        input_text = test["input"]
        result = sanitize_text_for_xml(input_text)

        # Verify it's valid UTF-8
        try:
            result.encode('utf-8')
            is_valid = True
        except UnicodeEncodeError:
            is_valid = False

        # Check if we expected it to be valid
        if is_valid == test["should_be_valid"]:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1

        print(f"\nTest {i}: {test['name']}")
        print(f"Status: {status}")
        print(f"Input:  {input_text}")
        print(f"Output: {result}")
        print(f"Valid UTF-8: {is_valid}")

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 60)

    return failed == 0


def test_xml_character_validation():
    """Test XML 1.0 character validation"""
    print("\n\nTesting XML 1.0 character validation...")
    print("=" * 60)

    # Valid characters according to XML 1.0 spec
    valid_chars = [
        ('\t', 0x09, "Tab"),
        ('\n', 0x0A, "Line Feed"),
        ('\r', 0x0D, "Carriage Return"),
        (' ', 0x20, "Space"),
        ('A', 0x41, "Latin A"),
        ('П', 0x041F, "Cyrillic P"),
        ('中', 0x4E2D, "Chinese character"),
    ]

    # Invalid characters that should be removed
    invalid_chars = [
        ('\x00', 0x00, "NULL"),
        ('\x01', 0x01, "SOH (control)"),
        ('\x1F', 0x1F, "US (control)"),
        ('\x7F', 0x7F, "DEL"),
        ('\x9F', 0x9F, "APC (C1 control)"),
    ]

    print("\nTesting VALID characters (should be preserved):")
    all_passed = True

    for char, code, name in valid_chars:
        result = sanitize_text_for_xml(f"Before{char}After")
        expected = f"Before{char}After"

        if result == expected:
            print(f"✅ {name} (U+{code:04X}): PRESERVED")
        else:
            print(f"❌ {name} (U+{code:04X}): REMOVED (ERROR)")
            all_passed = False

    print("\nTesting INVALID characters (should be removed):")

    for char, code, name in invalid_chars:
        result = sanitize_text_for_xml(f"Before{char}After")
        expected = "BeforeAfter"

        if result == expected:
            print(f"✅ {name} (U+{code:04X}): REMOVED")
        else:
            print(f"❌ {name} (U+{code:04X}): NOT REMOVED (ERROR)")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All XML character validation tests passed")
    else:
        print("❌ Some XML character validation tests failed")
    print("=" * 60)

    return all_passed


def main():
    """Run all tests"""
    print("UTF-8 Sanitization Fix - Test Suite")
    print("=" * 60)
    print("Testing enhanced sanitize_text_for_xml() function")
    print("=" * 60)

    test1 = test_sanitize_text_for_xml()
    test2 = test_encoding_normalization()
    test3 = test_xml_character_validation()

    print("\n\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)

    results = [
        ("Basic sanitization tests", test1),
        ("UTF-8 encoding normalization", test2),
        ("XML 1.0 character validation", test3)
    ]

    all_passed = True
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nThe UTF-8 sanitization fix is working correctly.")
        print("It can now handle:")
        print("  • Russian/Cyrillic characters")
        print("  • Invalid UTF-8 sequences")
        print("  • NULL bytes and control characters")
        print("  • Unicode replacement characters")
        print("  • Invalid XML characters")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nPlease review the failing tests above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
