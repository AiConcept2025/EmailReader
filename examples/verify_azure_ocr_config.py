#!/usr/bin/env python3
"""
Azure OCR Configuration Verification Script

This script verifies that Azure Document Intelligence OCR is correctly
configured and ready to use in the EmailReader project.

Usage:
    python verify_azure_ocr_config.py [--detailed]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class AzureOCRVerifier:
    """Verification utility for Azure OCR configuration."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.successes: List[str] = []

    def print_header(self, text: str) -> None:
        """Print a section header."""
        print(f"\n{BLUE}{'=' * 80}{RESET}")
        print(f"{BLUE}{text}{RESET}")
        print(f"{BLUE}{'=' * 80}{RESET}\n")

    def print_success(self, text: str) -> None:
        """Print a success message."""
        print(f"{GREEN}✓ {text}{RESET}")
        self.successes.append(text)

    def print_error(self, text: str) -> None:
        """Print an error message."""
        print(f"{RED}✗ {text}{RESET}")
        self.issues.append(text)

    def print_warning(self, text: str) -> None:
        """Print a warning message."""
        print(f"{YELLOW}⚠ {text}{RESET}")
        self.warnings.append(text)

    def print_info(self, text: str) -> None:
        """Print an info message."""
        if self.verbose:
            print(f"  {text}")

    def verify_config_file(self) -> Tuple[bool, Dict[str, Any]]:
        """Verify that config file exists and is valid JSON."""
        self.print_header("Step 1: Verifying Configuration File")

        config_path = Path("credentials/config.dev.json")

        if not config_path.exists():
            self.print_error(f"Configuration file not found: {config_path}")
            return False, {}

        self.print_success(f"Configuration file exists: {config_path}")

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.print_success("Configuration file is valid JSON")
            return True, config
        except json.JSONDecodeError as e:
            self.print_error(f"Configuration file is not valid JSON: {e}")
            return False, {}

    def verify_ocr_section(self, config: Dict[str, Any]) -> bool:
        """Verify OCR section in configuration."""
        self.print_header("Step 2: Verifying OCR Configuration Section")

        if 'ocr' not in config:
            self.print_error("Configuration missing 'ocr' section")
            return False

        self.print_success("Configuration has 'ocr' section")
        ocr_config = config['ocr']

        # Check provider setting
        provider = ocr_config.get('provider')
        if not provider:
            self.print_error("OCR provider not specified")
            return False

        self.print_success(f"OCR provider configured: '{provider}'")

        # Check valid provider
        valid_providers = {'azure', 'landing_ai', 'default'}
        if provider not in valid_providers:
            self.print_error(f"Invalid OCR provider: '{provider}'. Valid: {valid_providers}")
            return False

        self.print_success(f"OCR provider is valid")

        return True

    def verify_azure_config(self, config: Dict[str, Any]) -> bool:
        """Verify Azure-specific configuration."""
        self.print_header("Step 3: Verifying Azure OCR Configuration")

        ocr_config = config.get('ocr', {})

        # Check if Azure is the provider
        provider = ocr_config.get('provider')
        if provider != 'azure':
            self.print_warning(f"Current provider is '{provider}', not 'azure'")
            self.print_info("Checking Azure configuration anyway...")

        # Check Azure section exists
        if 'azure' not in ocr_config:
            self.print_error("Configuration missing 'ocr.azure' section")
            return False

        self.print_success("Configuration has 'ocr.azure' section")
        azure_config = ocr_config['azure']

        # Check required fields
        required_fields = ['endpoint', 'api_key', 'model']
        all_present = True

        for field in required_fields:
            if field not in azure_config:
                self.print_error(f"Azure config missing required field: '{field}'")
                all_present = False
            else:
                value = azure_config[field]
                self.print_success(f"Azure config has '{field}' field")

                # Check if it's a placeholder
                placeholder_indicators = [
                    'AZURE_ENDPOINT_HERE',
                    'AZURE_API_KEY_HERE',
                    'YOUR_',
                    'PLACEHOLDER',
                    'EXAMPLE'
                ]

                if any(indicator in str(value).upper() for indicator in placeholder_indicators):
                    self.print_error(f"Azure '{field}' appears to be a placeholder: {value}")
                    all_present = False
                else:
                    self.print_info(f"  Value: {value[:50]}..." if len(str(value)) > 50 else f"  Value: {value}")

        # Check optional sections
        optional_sections = ['page_processing', 'retry']
        for section in optional_sections:
            if section in azure_config:
                self.print_success(f"Azure config has optional '{section}' section")
                if self.verbose:
                    self.print_info(f"  {section}: {azure_config[section]}")
            else:
                self.print_warning(f"Azure config missing optional '{section}' section")

        return all_present

    def verify_azure_endpoint_format(self, config: Dict[str, Any]) -> bool:
        """Verify Azure endpoint has correct format."""
        self.print_header("Step 4: Verifying Azure Endpoint Format")

        azure_config = config.get('ocr', {}).get('azure', {})
        endpoint = azure_config.get('endpoint', '')

        if not endpoint:
            self.print_error("No endpoint found")
            return False

        # Check if it's a placeholder
        if 'AZURE_ENDPOINT_HERE' in endpoint:
            self.print_error("Endpoint is a placeholder value")
            return False

        # Check URL format
        valid_formats = [
            endpoint.startswith('https://'),
            '.cognitiveservices.azure.com' in endpoint or '.api.cognitive.microsoft.com' in endpoint
        ]

        if all(valid_formats):
            self.print_success(f"Endpoint has valid format: {endpoint}")
            return True
        else:
            self.print_warning(f"Endpoint format may be incorrect: {endpoint}")
            self.print_info("  Expected format: https://<resource-name>.cognitiveservices.azure.com/")
            return False

    def verify_python_dependencies(self) -> bool:
        """Verify required Python packages are installed."""
        self.print_header("Step 5: Verifying Python Dependencies")

        requirements_file = Path("requirements.txt")

        if not requirements_file.exists():
            self.print_error("requirements.txt not found")
            return False

        self.print_success("requirements.txt exists")

        # Read requirements
        with open(requirements_file, 'r') as f:
            requirements = f.read()

        # Check for Azure SDK
        azure_packages = [
            'azure-ai-formrecognizer',
            'azure-core'
        ]

        all_found = True
        for package in azure_packages:
            if package in requirements:
                self.print_success(f"Required package in requirements.txt: {package}")
                # Extract version if present
                for line in requirements.split('\n'):
                    if package in line:
                        self.print_info(f"  {line.strip()}")
            else:
                self.print_error(f"Required package missing from requirements.txt: {package}")
                all_found = False

        # Try to import packages
        self.print_info("\nChecking if packages are actually installed...")

        try:
            import azure.ai.formrecognizer
            try:
                version = azure.ai.formrecognizer._version.VERSION
            except AttributeError:
                version = "unknown"
            self.print_success(f"azure-ai-formrecognizer is installed (version: {version})")
        except ImportError:
            self.print_error("azure-ai-formrecognizer is NOT installed")
            self.print_info("  Install with: pip install azure-ai-formrecognizer>=3.3.0")
            all_found = False

        try:
            import azure.core
            self.print_success(f"azure-core is installed")
        except ImportError:
            self.print_error("azure-core is NOT installed")
            self.print_info("  Install with: pip install azure-core>=1.28.0")
            all_found = False

        return all_found

    def verify_implementation_files(self) -> bool:
        """Verify Azure OCR implementation files exist."""
        self.print_header("Step 6: Verifying Implementation Files")

        required_files = [
            'src/ocr/__init__.py',
            'src/ocr/base_provider.py',
            'src/ocr/azure_provider.py',
            'src/ocr/ocr_factory.py'
        ]

        all_exist = True
        for file_path in required_files:
            path = Path(file_path)
            if path.exists():
                self.print_success(f"Implementation file exists: {file_path}")
                self.print_info(f"  Size: {path.stat().st_size} bytes")
            else:
                self.print_error(f"Implementation file missing: {file_path}")
                all_exist = False

        return all_exist

    def verify_azure_provider_implementation(self) -> bool:
        """Verify Azure provider implementation."""
        self.print_header("Step 7: Verifying Azure Provider Implementation")

        provider_file = Path("src/ocr/azure_provider.py")

        if not provider_file.exists():
            self.print_error("Azure provider file not found")
            return False

        with open(provider_file, 'r') as f:
            content = f.read()

        # Check for required imports
        required_imports = [
            'from azure.ai.formrecognizer import DocumentAnalysisClient',
            'from azure.core.credentials import AzureKeyCredential',
            'from src.ocr.base_provider import BaseOCRProvider'
        ]

        all_imports_found = True
        for import_stmt in required_imports:
            if import_stmt in content:
                self.print_success(f"Required import found: {import_stmt.split('import')[1].strip()}")
            else:
                self.print_error(f"Missing import: {import_stmt}")
                all_imports_found = False

        # Check for required methods
        required_methods = [
            'def __init__',
            'def process_document',
            'def is_pdf_searchable',
            'def _ocr_with_azure'
        ]

        all_methods_found = True
        for method in required_methods:
            if method in content:
                self.print_success(f"Required method found: {method.replace('def ', '')}")
            else:
                self.print_error(f"Missing method: {method}")
                all_methods_found = False

        # Check for proper error handling
        if 'try:' in content and 'except' in content:
            self.print_success("Error handling implemented")
        else:
            self.print_warning("Error handling may be missing")

        return all_imports_found and all_methods_found

    def verify_factory_integration(self) -> bool:
        """Verify OCR factory integration."""
        self.print_header("Step 8: Verifying Factory Integration")

        factory_file = Path("src/ocr/ocr_factory.py")

        if not factory_file.exists():
            self.print_error("Factory file not found")
            return False

        with open(factory_file, 'r') as f:
            content = f.read()

        # Check for Azure provider support
        checks = [
            ("if provider_type == 'azure':", "Azure provider case in factory"),
            ("from src.ocr.azure_provider import AzureOCRProvider", "Azure provider import"),
            ("return AzureOCRProvider(azure_config)", "Azure provider instantiation")
        ]

        all_checks_pass = True
        for check_str, description in checks:
            if check_str in content:
                self.print_success(description)
            else:
                self.print_error(f"Missing: {description}")
                all_checks_pass = False

        return all_checks_pass

    def check_environment_variables(self) -> None:
        """Check for environment variable configuration."""
        self.print_header("Step 9: Checking Environment Variables (Optional)")

        env_vars = [
            'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT',
            'AZURE_DOCUMENT_INTELLIGENCE_API_KEY'
        ]

        found_any = False
        for var in env_vars:
            value = os.getenv(var)
            if value:
                self.print_success(f"Environment variable set: {var}")
                self.print_info(f"  Value: {value[:50]}..." if len(value) > 50 else f"  Value: {value}")
                found_any = True
            else:
                self.print_info(f"Environment variable not set: {var}")

        if not found_any:
            self.print_warning("No Azure environment variables found")
            self.print_info("  This is OK if credentials are in config file")
            self.print_info("  Alternative: Set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and AZURE_DOCUMENT_INTELLIGENCE_API_KEY")

    def generate_summary(self) -> None:
        """Generate verification summary."""
        self.print_header("Verification Summary")

        print(f"{GREEN}Successes: {len(self.successes)}{RESET}")
        print(f"{YELLOW}Warnings: {len(self.warnings)}{RESET}")
        print(f"{RED}Errors: {len(self.issues)}{RESET}")

        if self.issues:
            print(f"\n{RED}Critical Issues Found:{RESET}")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")

        if self.warnings:
            print(f"\n{YELLOW}Warnings:{RESET}")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

        # Overall status
        print(f"\n{BLUE}{'=' * 80}{RESET}")
        if not self.issues:
            print(f"{GREEN}✓ Azure OCR Configuration is VALID and ready to use!{RESET}")
        else:
            print(f"{RED}✗ Azure OCR Configuration has ISSUES that need to be fixed{RESET}")
        print(f"{BLUE}{'=' * 80}{RESET}\n")

    def run_verification(self) -> bool:
        """Run complete verification."""
        print(f"{BLUE}Azure OCR Configuration Verification{RESET}")
        print(f"{BLUE}EmailReader Project{RESET}\n")

        # Run all verification steps
        config_ok, config = self.verify_config_file()
        if not config_ok:
            self.generate_summary()
            return False

        ocr_section_ok = self.verify_ocr_section(config)
        azure_config_ok = self.verify_azure_config(config)
        endpoint_ok = self.verify_azure_endpoint_format(config)
        deps_ok = self.verify_python_dependencies()
        files_ok = self.verify_implementation_files()
        impl_ok = self.verify_azure_provider_implementation()
        factory_ok = self.verify_factory_integration()

        # Optional check
        self.check_environment_variables()

        # Generate summary
        self.generate_summary()

        # Return overall status
        return all([
            config_ok,
            ocr_section_ok,
            azure_config_ok,
            deps_ok,
            files_ok,
            impl_ok,
            factory_ok
        ])


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Verify Azure OCR configuration in EmailReader project'
    )
    parser.add_argument(
        '--detailed',
        '-d',
        action='store_true',
        help='Show detailed information'
    )

    args = parser.parse_args()

    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # Run verification
    verifier = AzureOCRVerifier(verbose=args.detailed)
    success = verifier.run_verification()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
