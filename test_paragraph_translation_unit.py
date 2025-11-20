#!/usr/bin/env python3
"""
Unit tests for the translate_paragraphs method.

These tests verify the method signature, docstring, and integration
without requiring Google Cloud API credentials.
"""

import os
import sys
import inspect
import ast

# Test file location
TRANSLATOR_FILE = os.path.join(
    os.path.dirname(__file__),
    'src/translation/google_doc_translator.py'
)


def test_method_exists():
    """Verify that translate_paragraphs method exists in the file."""
    print("=" * 80)
    print("TEST 1: Method Exists")
    print("=" * 80)

    with open(TRANSLATOR_FILE, 'r') as f:
        content = f.read()

    if 'def translate_paragraphs(' in content:
        print("✓ PASSED: translate_paragraphs method found in file")
        return True
    else:
        print("✗ FAILED: translate_paragraphs method not found")
        return False


def test_method_signature():
    """Verify the method signature matches requirements."""
    print("\n" + "=" * 80)
    print("TEST 2: Method Signature")
    print("=" * 80)

    with open(TRANSLATOR_FILE, 'r') as f:
        tree = ast.parse(f.read())

    # Find the GoogleDocTranslator class
    translator_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'GoogleDocTranslator':
            translator_class = node
            break

    if not translator_class:
        print("✗ FAILED: GoogleDocTranslator class not found")
        return False

    # Find translate_paragraphs method
    method = None
    for item in translator_class.body:
        if isinstance(item, ast.FunctionDef) and item.name == 'translate_paragraphs':
            method = item
            break

    if not method:
        print("✗ FAILED: translate_paragraphs method not found in class")
        return False

    # Extract parameter names
    params = [arg.arg for arg in method.args.args]
    print(f"Method parameters: {params}")

    # Required parameters
    required = ['self', 'paragraphs', 'target_lang']
    optional = ['batch_size', 'preserve_formatting']

    # Check required parameters
    for req in required:
        if req not in params:
            print(f"✗ FAILED: Missing required parameter: {req}")
            return False

    # Check optional parameters
    for opt in optional:
        if opt not in params:
            print(f"✗ FAILED: Missing optional parameter: {opt}")
            return False

    print("✓ PASSED: Method signature is correct")
    print(f"  Parameters: {', '.join(params)}")
    return True


def test_method_docstring():
    """Verify the method has proper documentation."""
    print("\n" + "=" * 80)
    print("TEST 3: Method Documentation")
    print("=" * 80)

    with open(TRANSLATOR_FILE, 'r') as f:
        tree = ast.parse(f.read())

    # Find the method
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'GoogleDocTranslator':
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == 'translate_paragraphs':
                    docstring = ast.get_docstring(item)
                    if docstring:
                        print("✓ PASSED: Method has docstring")
                        print(f"  Length: {len(docstring)} characters")

                        # Check for key sections
                        required_sections = ['Args:', 'Returns:', 'Raises:', 'Example:']
                        for section in required_sections:
                            if section in docstring:
                                print(f"  ✓ Contains '{section}' section")
                            else:
                                print(f"  ✗ Missing '{section}' section")

                        return True
                    else:
                        print("✗ FAILED: Method lacks docstring")
                        return False

    print("✗ FAILED: Method not found")
    return False


def test_backward_compatibility():
    """Verify translate_document method still exists."""
    print("\n" + "=" * 80)
    print("TEST 4: Backward Compatibility")
    print("=" * 80)

    with open(TRANSLATOR_FILE, 'r') as f:
        content = f.read()

    # Check that translate_document still exists
    if 'def translate_document(' in content:
        print("✓ PASSED: translate_document method still exists")

        # Verify it hasn't been modified (check signature)
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'GoogleDocTranslator':
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == 'translate_document':
                        params = [arg.arg for arg in item.args.args]
                        expected = ['self', 'input_path', 'output_path', 'target_lang']

                        if params == expected:
                            print(f"  ✓ Signature unchanged: {params}")
                            return True
                        else:
                            print(f"  ✗ Signature changed from {expected} to {params}")
                            return False

        print("✗ FAILED: Could not verify signature")
        return False
    else:
        print("✗ FAILED: translate_document method not found")
        return False


def test_helper_method():
    """Verify the _translate_text_batch helper method exists."""
    print("\n" + "=" * 80)
    print("TEST 5: Helper Method Exists")
    print("=" * 80)

    with open(TRANSLATOR_FILE, 'r') as f:
        content = f.read()

    if 'def _translate_text_batch(' in content:
        print("✓ PASSED: _translate_text_batch helper method exists")

        # Parse and check signature
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == 'GoogleDocTranslator':
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == '_translate_text_batch':
                        params = [arg.arg for arg in item.args.args]
                        print(f"  Parameters: {params}")

                        required = ['self', 'texts', 'target_lang']
                        for req in required:
                            if req not in params:
                                print(f"  ✗ Missing parameter: {req}")
                                return False

                        print("  ✓ All required parameters present")
                        return True

        return True
    else:
        print("✗ FAILED: _translate_text_batch helper method not found")
        return False


def test_imports():
    """Verify List type import was added."""
    print("\n" + "=" * 80)
    print("TEST 6: Type Imports")
    print("=" * 80)

    with open(TRANSLATOR_FILE, 'r') as f:
        content = f.read()

    # Check for List import
    if 'from typing import' in content and 'List' in content.split('from typing import')[1].split('\n')[0]:
        print("✓ PASSED: List type imported from typing")
        return True
    else:
        print("✗ FAILED: List type not imported")
        return False


def test_code_structure():
    """Verify the file is valid Python and can be parsed."""
    print("\n" + "=" * 80)
    print("TEST 7: Code Structure")
    print("=" * 80)

    try:
        with open(TRANSLATOR_FILE, 'r') as f:
            ast.parse(f.read())
        print("✓ PASSED: File is valid Python code")
        return True
    except SyntaxError as e:
        print(f"✗ FAILED: Syntax error in file: {e}")
        return False


def main():
    """Run all unit tests."""
    print("\n" + "#" * 80)
    print("# PARAGRAPH TRANSLATION METHOD - UNIT TEST SUITE")
    print("#" * 80 + "\n")

    tests = [
        ("Method Exists", test_method_exists),
        ("Method Signature", test_method_signature),
        ("Method Documentation", test_method_docstring),
        ("Backward Compatibility", test_backward_compatibility),
        ("Helper Method", test_helper_method),
        ("Type Imports", test_imports),
        ("Code Structure", test_code_structure),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            results.append((test_name, test_func()))
        except Exception as e:
            print(f"\n✗ EXCEPTION in {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    total = len(results)
    passed = sum(1 for _, result in results if result)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")

    print("-" * 80)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 80)

    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
