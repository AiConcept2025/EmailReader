"""
Iterative testing script for email processing quality improvement

This script:
1. Enables test mode to avoid removing files from Inbox
2. Processes a specific file from danishevsky@yahoo.com/Inbox
3. Validates output quality against specifications
4. Collects metrics and displays results
5. Allows parameter tuning and re-runs (max 10 iterations)
6. Auto-stops when quality targets are met

Usage:
    python test_iterative_processing.py [--file-name "specific-file.pdf"] [--max-iterations 10]
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.logger import logger
from src.config import load_config, get_config_value
from src.google_drive import GoogleApi
from src.process_documents import DocProcessor
from src.quality_validator import QualityValidator, ValidationResult
from src.metrics_tracker import MetricsTracker


class IterativeProcessor:
    """Manages iterative processing and quality improvement"""

    def __init__(self, target_client: str = "danishevsky@yahoo.com", max_iterations: int = 10):
        """
        Initialize iterative processor

        Args:
            target_client: Client email to process files from
            max_iterations: Maximum number of iterations to run
        """
        self.target_client = target_client
        self.max_iterations = max_iterations
        self.current_iteration = 0

        # Initialize components
        self.google_api = GoogleApi()
        self.validator = QualityValidator()
        self.metrics_tracker = MetricsTracker()

        # Results tracking
        self.iteration_results: List[Dict[str, Any]] = []

        logger.info("IterativeProcessor initialized")
        logger.info("  Target client: %s", target_client)
        logger.info("  Max iterations: %d", max_iterations)

    def find_client_inbox(self) -> Optional[str]:
        """Find the Inbox folder ID for target client"""
        logger.info("Searching for client folder: %s", self.target_client)

        # Get all folders at root level
        folders = self.google_api.get_subfolders_list_in_folder()

        # Look for direct client folder
        client_folder = None
        for folder in folders:
            if self.target_client in folder['name']:
                client_folder = folder
                break

        if not client_folder:
            # Check company folders
            for company in folders:
                if '@' not in company['name']:  # It's a company folder
                    nested = self.google_api.get_subfolders_list_in_folder(company['id'])
                    for folder in nested:
                        if self.target_client in folder['name']:
                            client_folder = folder
                            break
                    if client_folder:
                        break

        if not client_folder:
            logger.error("Client folder not found: %s", self.target_client)
            return None

        logger.info("Found client folder: %s (ID: %s)", client_folder['name'], client_folder['id'])

        # Get Inbox subfolder
        subfolders = self.google_api.get_subfolders_list_in_folder(client_folder['id'])
        inbox = next((f for f in subfolders if f['name'] == 'Inbox'), None)

        if not inbox:
            logger.error("Inbox folder not found for client: %s", self.target_client)
            return None

        logger.info("Found Inbox folder: %s", inbox['id'])
        return inbox['id']

    def get_unprocessed_files(self, inbox_id: str, target_file_name: Optional[str] = None) -> List[Dict[str, str]]:
        """Get list of unprocessed files from Inbox"""
        files = self.google_api.get_file_list_in_folder(inbox_id)

        if target_file_name:
            # Filter for specific file
            files = [f for f in files if f['name'] == target_file_name]

        # Filter out already processed files
        unprocessed = []
        for file in files:
            processed_at = self.google_api.get_file_property(file['id'], 'processed_at')
            if not processed_at:
                unprocessed.append(file)

        logger.info("Found %d unprocessed file(s)", len(unprocessed))
        return unprocessed

    def process_single_file(
        self,
        file_info: Dict[str, str],
        inbox_id: str
    ) -> Optional[str]:
        """
        Process a single file and return path to output DOCX

        Args:
            file_info: File metadata from Google Drive
            inbox_id: Inbox folder ID

        Returns:
            Path to processed DOCX file, or None if failed
        """
        file_name = file_info['name']
        file_id = file_info['id']

        logger.info("Processing file: %s", file_name)

        try:
            # Create document folder
            cwd = os.getcwd()
            document_folder = os.path.join(cwd, 'data', 'documents')
            os.makedirs(document_folder, exist_ok=True)

            # Download file
            file_path = os.path.join(document_folder, file_name)
            logger.info("Downloading file...")
            if not self.google_api.download_file_from_google_drive(file_id, file_path):
                logger.error("Failed to download file")
                return None

            # Process file
            doc_processor = DocProcessor(document_folder)
            _, file_ext = os.path.splitext(file_name)

            logger.info("Processing document...")
            start_time = time.time()

            if file_ext.lower() in ['.doc', '.docx']:
                (
                    new_file_path,
                    new_file_name,
                    original_file_name,
                    original_file_path
                ) = doc_processor.process_word_file(
                    client=self.target_client,
                    file_name=file_name,
                    document_folder=document_folder
                )
            elif file_ext.lower() == '.pdf':
                (
                    new_file_path,
                    new_file_name,
                    original_file_name,
                    original_file_path
                ) = doc_processor.convert_pdf_file_to_word(
                    client=self.target_client,
                    file_name=file_name,
                    document_folder=document_folder
                )
            else:
                logger.error("Unsupported file type: %s", file_ext)
                return None

            processing_time = time.time() - start_time
            logger.info("Processing complete in %.2fs: %s", processing_time, new_file_name)

            return new_file_path

        except Exception as e:
            logger.error("Error processing file: %s", e, exc_info=True)
            return None

    def run_iteration(
        self,
        target_file_name: Optional[str] = None,
        calibration_factor: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Run a single iteration of processing and validation

        Args:
            target_file_name: Specific file to process, or None for first unprocessed
            calibration_factor: Override calibration factor for this iteration

        Returns:
            Dictionary with iteration results
        """
        self.current_iteration += 1
        logger.info("")
        logger.info("="*60)
        logger.info("ITERATION %d/%d", self.current_iteration, self.max_iterations)
        logger.info("="*60)

        iteration_start = time.time()

        # Apply calibration factor override if provided
        if calibration_factor:
            logger.info("Using calibration factor: %.1f", calibration_factor)
            # TODO: Apply calibration factor to OCR processor
            # This would require modifying the OCR provider configuration

        # Find client Inbox
        inbox_id = self.find_client_inbox()
        if not inbox_id:
            return {
                "iteration": self.current_iteration,
                "success": False,
                "error": "Client Inbox not found"
            }

        # Get unprocessed files
        files = self.get_unprocessed_files(inbox_id, target_file_name)
        if not files:
            return {
                "iteration": self.current_iteration,
                "success": False,
                "error": "No unprocessed files found"
            }

        # Process first file
        file_info = files[0]
        logger.info("Selected file: %s", file_info['name'])

        # Process the file
        output_path = self.process_single_file(file_info, inbox_id)
        if not output_path:
            return {
                "iteration": self.current_iteration,
                "success": False,
                "error": "File processing failed"
            }

        # Validate output
        logger.info("Validating output quality...")
        validation_result = self.validator.validate_docx(output_path)
        validation_result.print_report()

        # Mark file as processed (for test mode)
        from datetime import datetime
        self.google_api.set_file_property(
            file_id=file_info['id'],
            property_name=f'processed_iteration_{self.current_iteration}',
            property_value=datetime.now().isoformat()
        )

        iteration_time = time.time() - iteration_start

        result = {
            "iteration": self.current_iteration,
            "success": True,
            "file_name": file_info['name'],
            "output_path": output_path,
            "validation": validation_result.to_dict(),
            "passed": validation_result.passed,
            "score": validation_result.score,
            "processing_time": iteration_time,
            "calibration_factor": calibration_factor or get_config_value('quality.calibration_factor', 400.0)
        }

        self.iteration_results.append(result)

        logger.info("")
        logger.info("Iteration %d complete:", self.current_iteration)
        logger.info("  Status: %s", "PASS ✓" if result['passed'] else "FAIL ✗")
        logger.info("  Score: %.1f/100", result['score'])
        logger.info("  Time: %.2fs", iteration_time)

        return result

    def run_iterative_test(
        self,
        target_file_name: Optional[str] = None,
        auto_tune: bool = False
    ) -> None:
        """
        Run iterative testing until quality targets met or max iterations reached

        Args:
            target_file_name: Specific file to test with
            auto_tune: Whether to automatically adjust parameters between iterations
        """
        logger.info("")
        logger.info("="*60)
        logger.info("STARTING ITERATIVE QUALITY TESTING")
        logger.info("="*60)
        logger.info("Target client: %s", self.target_client)
        logger.info("Target file: %s", target_file_name or "first unprocessed")
        logger.info("Max iterations: %d", self.max_iterations)
        logger.info("Auto-tune: %s", auto_tune)
        logger.info("="*60)

        # Calibration factors to test (if auto-tune enabled)
        calibration_factors = [380, 390, 400, 410, 420] if auto_tune else [None]
        factor_index = 0

        for i in range(self.max_iterations):
            # Select calibration factor
            calibration_factor = None
            if auto_tune and factor_index < len(calibration_factors):
                calibration_factor = calibration_factors[factor_index]
                factor_index += 1

            # Run iteration
            result = self.run_iteration(target_file_name, calibration_factor)

            if not result['success']:
                logger.error("Iteration failed: %s", result.get('error'))
                break

            # Check if quality targets met
            if result['passed']:
                logger.info("")
                logger.info("="*60)
                logger.info("✓ QUALITY TARGETS MET!")
                logger.info("="*60)
                logger.info("Stopping after %d iteration(s)", self.current_iteration)
                break

            # Continue if more iterations available
            if self.current_iteration < self.max_iterations:
                logger.info("")
                logger.info("Quality targets not met - continuing to next iteration...")
                time.sleep(2)  # Brief pause between iterations

        # Print final summary
        self.print_final_summary()

        # Save results
        self.save_results()

    def print_final_summary(self) -> None:
        """Print summary of all iterations"""
        if not self.iteration_results:
            return

        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        print(f"Total iterations: {len(self.iteration_results)}")

        passed_count = sum(1 for r in self.iteration_results if r['passed'])
        print(f"Passed: {passed_count}/{len(self.iteration_results)}")

        best_result = max(self.iteration_results, key=lambda r: r['score'])
        print(f"\nBest result:")
        print(f"  Iteration: {best_result['iteration']}")
        print(f"  Score: {best_result['score']:.1f}/100")
        print(f"  Calibration factor: {best_result['calibration_factor']}")

        if passed_count > 0:
            print(f"\n✓ Quality targets achieved in iteration {min(r['iteration'] for r in self.iteration_results if r['passed'])}")
        else:
            print(f"\n✗ Quality targets not achieved in {len(self.iteration_results)} iteration(s)")

        print("="*60)

    def save_results(self) -> None:
        """Save all iteration results to JSON"""
        output_dir = Path(os.getcwd()) / 'metrics'
        output_dir.mkdir(exist_ok=True)

        output_file = output_dir / f"iterative_test_{self.metrics_tracker.session_id}.json"

        data = {
            "test_summary": {
                "target_client": self.target_client,
                "total_iterations": len(self.iteration_results),
                "passed_iterations": sum(1 for r in self.iteration_results if r['passed']),
                "max_score": max(r['score'] for r in self.iteration_results) if self.iteration_results else 0,
                "session_id": self.metrics_tracker.session_id
            },
            "iterations": self.iteration_results
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info("Results saved to: %s", output_file)
        print(f"\nResults saved to: {output_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Iterative email processing quality testing')
    parser.add_argument(
        '--file-name',
        type=str,
        help='Specific file name to process (otherwise first unprocessed file)'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=10,
        help='Maximum number of iterations (default: 10)'
    )
    parser.add_argument(
        '--client',
        type=str,
        default='danishevsky@yahoo.com',
        help='Client email to process from (default: danishevsky@yahoo.com)'
    )
    parser.add_argument(
        '--auto-tune',
        action='store_true',
        help='Automatically try different calibration factors'
    )

    args = parser.parse_args()

    # Verify test mode is enabled
    config = load_config()
    test_mode = get_config_value('processing.test_mode', False)

    if not test_mode:
        print("ERROR: Test mode is not enabled in configuration!")
        print("Please set 'processing.test_mode' to true in your config file")
        print("This ensures files are not removed from Inbox during testing")
        sys.exit(1)

    logger.info("Test mode confirmed: enabled")

    # Run iterative testing
    processor = IterativeProcessor(
        target_client=args.client,
        max_iterations=args.max_iterations
    )

    processor.run_iterative_test(
        target_file_name=args.file_name,
        auto_tune=args.auto_tune
    )


if __name__ == "__main__":
    main()
