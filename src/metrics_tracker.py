"""
Metrics tracking module for quality analysis and iterative improvement
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict, field

from src.config import get_config_value
from src.logger import logger


@dataclass
class FileMetrics:
    """Metrics for a single file processing"""
    file_id: str
    file_name: str
    client_email: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False

    # Timing metrics (seconds)
    download_time: float = 0.0
    processing_time: float = 0.0
    upload_time: float = 0.0
    flowise_upload_time: float = 0.0
    prediction_time: float = 0.0
    total_time: float = 0.0

    # Document metrics
    page_count: int = 0
    chunk_count: int = 0
    column_count: int = 0
    has_grounding_data: bool = False

    # Font size metrics
    font_sizes: List[float] = field(default_factory=list)
    font_size_min: float = 0.0
    font_size_max: float = 0.0
    font_size_mean: float = 0.0
    body_text_percentage: float = 0.0
    heading_percentage: float = 0.0
    title_percentage: float = 0.0

    # Quality flags
    has_page_breaks: bool = False
    has_multi_column: bool = False

    # Errors
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class MetricsTracker:
    """Track processing metrics for quality analysis"""

    def __init__(self):
        """Initialize metrics tracker"""
        self.session_start = datetime.now()
        self.session_id = self.session_start.strftime("%Y%m%d_%H%M%S")
        self.current_file: Optional[FileMetrics] = None
        self.completed_files: List[FileMetrics] = []

        # Get output directory from config
        self.output_dir = get_config_value('metrics.output_directory', 'metrics')
        self.output_path = Path(os.getcwd()) / self.output_dir
        self.output_path.mkdir(exist_ok=True)

        logger.info("MetricsTracker initialized - session: %s", self.session_id)

    def start_file_processing(self, file_id: str, file_name: str, client_email: str) -> None:
        """Start tracking a new file"""
        self.current_file = FileMetrics(
            file_id=file_id,
            file_name=file_name,
            client_email=client_email,
            start_time=time.time()
        )
        logger.debug("Started tracking metrics for file: %s", file_name)

    def record_timing(self, operation: str, duration: float) -> None:
        """Record timing for an operation"""
        if not self.current_file:
            logger.warning("No current file to record timing for")
            return

        if operation == 'download':
            self.current_file.download_time = duration
        elif operation == 'processing':
            self.current_file.processing_time = duration
        elif operation == 'upload':
            self.current_file.upload_time = duration
        elif operation == 'flowise_upload':
            self.current_file.flowise_upload_time = duration
        elif operation == 'prediction':
            self.current_file.prediction_time = duration

        logger.debug("Recorded %s time: %.2fs", operation, duration)

    def record_document_metrics(
        self,
        page_count: int = 0,
        chunk_count: int = 0,
        column_count: int = 0,
        has_grounding_data: bool = False
    ) -> None:
        """Record document structure metrics"""
        if not self.current_file:
            return

        self.current_file.page_count = page_count
        self.current_file.chunk_count = chunk_count
        self.current_file.column_count = column_count
        self.current_file.has_grounding_data = has_grounding_data
        self.current_file.has_page_breaks = page_count > 1
        self.current_file.has_multi_column = column_count > 1

        logger.debug(
            "Document metrics: %d pages, %d chunks, %d columns",
            page_count, chunk_count, column_count
        )

    def record_font_metrics(self, font_sizes: List[float]) -> None:
        """Record font size metrics and calculate statistics"""
        if not self.current_file or not font_sizes:
            return

        self.current_file.font_sizes = font_sizes
        self.current_file.font_size_min = min(font_sizes)
        self.current_file.font_size_max = max(font_sizes)
        self.current_file.font_size_mean = sum(font_sizes) / len(font_sizes)

        # Calculate distribution percentages
        total = len(font_sizes)
        body_count = sum(1 for s in font_sizes if 10.0 <= s <= 13.0)
        heading_count = sum(1 for s in font_sizes if 13.0 < s <= 24.0)
        title_count = sum(1 for s in font_sizes if 24.0 < s <= 48.0)

        self.current_file.body_text_percentage = (body_count / total) * 100
        self.current_file.heading_percentage = (heading_count / total) * 100
        self.current_file.title_percentage = (title_count / total) * 100

        logger.debug(
            "Font metrics: min=%.1f, max=%.1f, mean=%.1f, body=%.1f%%, heading=%.1f%%, title=%.1f%%",
            self.current_file.font_size_min,
            self.current_file.font_size_max,
            self.current_file.font_size_mean,
            self.current_file.body_text_percentage,
            self.current_file.heading_percentage,
            self.current_file.title_percentage
        )

    def record_error(self, error: str) -> None:
        """Record an error"""
        if not self.current_file:
            return

        self.current_file.errors.append(error)
        logger.debug("Recorded error: %s", error)

    def finalize_file_processing(self, success: bool = True) -> None:
        """Finalize metrics for current file"""
        if not self.current_file:
            return

        self.current_file.end_time = time.time()
        self.current_file.total_time = self.current_file.end_time - self.current_file.start_time
        self.current_file.success = success

        self.completed_files.append(self.current_file)

        logger.info(
            "File metrics finalized: %s (%.2fs total, success=%s)",
            self.current_file.file_name,
            self.current_file.total_time,
            success
        )

        self.current_file = None

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the session"""
        if not self.completed_files:
            return {
                "total_files": 0,
                "successful_files": 0,
                "failed_files": 0
            }

        successful = [f for f in self.completed_files if f.success]
        failed = [f for f in self.completed_files if not f.success]

        # Calculate timing averages
        avg_times = {}
        if successful:
            avg_times = {
                "avg_download": sum(f.download_time for f in successful) / len(successful),
                "avg_processing": sum(f.processing_time for f in successful) / len(successful),
                "avg_upload": sum(f.upload_time for f in successful) / len(successful),
                "avg_flowise": sum(f.flowise_upload_time for f in successful) / len(successful),
                "avg_prediction": sum(f.prediction_time for f in successful) / len(successful),
                "avg_total": sum(f.total_time for f in successful) / len(successful)
            }

        # Calculate font size statistics
        all_font_sizes = []
        for f in successful:
            all_font_sizes.extend(f.font_sizes)

        font_stats = {}
        if all_font_sizes:
            font_stats = {
                "min_font_size": min(all_font_sizes),
                "max_font_size": max(all_font_sizes),
                "mean_font_size": sum(all_font_sizes) / len(all_font_sizes),
                "avg_body_percentage": sum(f.body_text_percentage for f in successful if f.font_sizes) / max(1, sum(1 for f in successful if f.font_sizes)),
                "avg_heading_percentage": sum(f.heading_percentage for f in successful if f.font_sizes) / max(1, sum(1 for f in successful if f.font_sizes)),
                "avg_title_percentage": sum(f.title_percentage for f in successful if f.font_sizes) / max(1, sum(1 for f in successful if f.font_sizes))
            }

        # Quality metrics
        quality_stats = {}
        if successful:
            quality_stats = {
                "files_with_page_breaks": sum(1 for f in successful if f.has_page_breaks),
                "files_with_multi_column": sum(1 for f in successful if f.has_multi_column),
                "avg_page_count": sum(f.page_count for f in successful) / len(successful),
                "avg_chunk_count": sum(f.chunk_count for f in successful) / len(successful)
            }

        return {
            "session_id": self.session_id,
            "session_start": self.session_start.isoformat(),
            "total_files": len(self.completed_files),
            "successful_files": len(successful),
            "failed_files": len(failed),
            "timing": avg_times,
            "font_statistics": font_stats,
            "quality": quality_stats
        }

    def save_report(self, filename: Optional[str] = None) -> str:
        """Save metrics report to JSON file"""
        if filename is None:
            filename = f"metrics_report_{self.session_id}.json"

        report_path = self.output_path / filename

        report_data = {
            "summary": self.get_summary_stats(),
            "files": [f.to_dict() for f in self.completed_files]
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        logger.info("Metrics report saved to: %s", report_path)
        return str(report_path)

    def print_summary(self) -> None:
        """Print summary to console"""
        stats = self.get_summary_stats()

        print("\n" + "="*60)
        print("METRICS SUMMARY")
        print("="*60)
        print(f"Session ID: {stats['session_id']}")
        print(f"Total Files: {stats['total_files']}")
        print(f"Successful: {stats['successful_files']}")
        print(f"Failed: {stats['failed_files']}")

        if stats.get('timing'):
            print("\nTIMING (averages):")
            print(f"  Download: {stats['timing']['avg_download']:.2f}s")
            print(f"  Processing: {stats['timing']['avg_processing']:.2f}s")
            print(f"  Upload: {stats['timing']['avg_upload']:.2f}s")
            print(f"  FlowiseAI: {stats['timing']['avg_flowise']:.2f}s")
            print(f"  Prediction: {stats['timing']['avg_prediction']:.2f}s")
            print(f"  Total: {stats['timing']['avg_total']:.2f}s")

        if stats.get('font_statistics'):
            print("\nFONT SIZE DISTRIBUTION:")
            print(f"  Range: {stats['font_statistics']['min_font_size']:.1f} - {stats['font_statistics']['max_font_size']:.1f}pt")
            print(f"  Mean: {stats['font_statistics']['mean_font_size']:.1f}pt")
            print(f"  Body Text: {stats['font_statistics']['avg_body_percentage']:.1f}%")
            print(f"  Headings: {stats['font_statistics']['avg_heading_percentage']:.1f}%")
            print(f"  Titles: {stats['font_statistics']['avg_title_percentage']:.1f}%")

        if stats.get('quality'):
            print("\nQUALITY METRICS:")
            print(f"  Files with page breaks: {stats['quality']['files_with_page_breaks']}")
            print(f"  Files with multi-column: {stats['quality']['files_with_multi_column']}")
            print(f"  Avg pages/file: {stats['quality']['avg_page_count']:.1f}")
            print(f"  Avg chunks/file: {stats['quality']['avg_chunk_count']:.1f}")

        print("="*60)
