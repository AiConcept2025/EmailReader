"""
Start point for the application.
"""
import os
import time
from datetime import datetime

import schedule

from src.logger import logger
from src.process_google_drive import process_google_drive
from src.process_files_for_translation import process_files_for_translation
from src.process_files_for_formatting import process_files_for_formatting
from src.config import load_config


def select_program_mode() -> str:
    """Select the program mode based on configuration."""
    logger.debug("Entering select_program_mode()")
    logger.debug("Loading configuration")

    cfg = load_config()
    program_mode = cfg.get('app', {}).get('program', 'default_mode')
    logger.debug(
        "Raw program mode value: %s (type: %s)",
        program_mode,
        type(program_mode).__name__)

    # Ensure we always return a string; handle the case where
    # 'program' may be a dict.
    if isinstance(program_mode, dict):
        logger.debug("Program mode is dict, extracting string value")
        # try to extract a sensible string value
        for key in ('name', 'mode', 'program'):
            val = program_mode.get(key)
            if isinstance(val, str):
                program_mode = val
                logger.debug(
                    "Extracted program mode from key '%s': %s",
                    key,
                    program_mode)
                break
        else:
            # fallback to a deterministic string representation
            program_mode = str(program_mode)
            logger.warning(
                "Could not extract string from dict, using: %s",
                program_mode)

    logger.info("Selected program mode: %s", program_mode)
    return program_mode


def load_interval_minutes() -> int:
    """Load the Google Drive processing interval from configuration."""
    logger.debug("Entering load_interval_minutes()")
    cfg = load_config()
    scheduling = cfg.get('scheduling', {})
    interval = int(scheduling.get('google_drive_interval_minutes', 15))
    logger.debug("Loaded interval: %d minutes", interval)
    return interval


def ensure_runtime_dirs() -> None:
    """Ensure necessary directories and files exist."""
    logger.debug("Entering ensure_runtime_dirs()")
    cwd = os.getcwd()
    logger.debug("Current working directory: %s", cwd)

    data_dir = os.path.join(cwd, 'data')
    docs_dir = os.path.join(data_dir, 'documents')

    if not os.path.isdir(data_dir):
        logger.info("Creating data directory: %s", data_dir)
        os.mkdir(data_dir)
    else:
        logger.debug("Data directory exists: %s", data_dir)

    if not os.path.isdir(docs_dir):
        logger.info("Creating documents directory: %s", docs_dir)
        os.mkdir(docs_dir)
    else:
        logger.debug("Documents directory exists: %s", docs_dir)

    finish_tag = os.path.join(data_dir, 'last_finish_time.txt')
    if not os.path.isfile(finish_tag):
        logger.info("Creating last_finish_time.txt with default value")
        with open(finish_tag, 'w', encoding='utf-8') as f:
            f.write('2020-01-01 01:01:01 +0000')
    else:
        logger.debug("last_finish_time.txt exists: %s", finish_tag)

    logger.debug("Runtime directories ensured successfully")


def log_next_run(prefix: str = "") -> None:
    """Log the next scheduled run time."""
    try:
        nr = schedule.next_run()
        if nr:
            mins = max(0, int((nr - datetime.now()).total_seconds() // 60))
            logger.info("%sNext cycle in ~%d minute(s) (at %s)",
                        f"{prefix} " if prefix else "",
                        mins, nr.strftime('%Y-%m-%d %H:%M:%S'))
    except (AttributeError, TypeError, ValueError) as e:
        logger.debug("Could not determine next run time: %s", str(e))


def run_and_log() -> None:
    """Run the Google Drive processing and log the next run time."""
    logger.info("="*80)
    logger.info("Google Drive cycle started")
    logger.debug("Entering run_and_log()")

    try:
        mode = select_program_mode()
        logger.info("Running in mode: %s", mode)

        if mode == "translator":
            logger.info("Starting translation workflow")
            process_files_for_translation()
            logger.info("Translation workflow completed")
        elif mode == "format":
            logger.info("Starting formatting workflow")
            process_files_for_formatting()
            logger.info("Formatting workflow completed")
        else:
            logger.info("Starting standard processing workflow")
            process_google_drive()
            logger.info("Standard processing workflow completed")

        logger.info("Google Drive cycle finished successfully")
        logger.info("="*80)
    except Exception as e:
        logger.error("Critical error in run_and_log(): %s", e, exc_info=True)
        logger.info("="*80)
        raise
    finally:
        log_next_run("")


if __name__ == "__main__":
    logger.info("="*80)
    logger.info("EmailReader main process starting")
    logger.debug("Python process started")

    try:
        logger.debug("Ensuring runtime directories exist")
        ensure_runtime_dirs()

        logger.debug("Loading configuration")
        interval = load_interval_minutes()
        logger.info("Configured Google Drive interval: %d minute(s)", interval)

        logger.debug("Setting up schedule: every %d minutes", interval)
        schedule.every(interval).minutes.do(run_and_log)

        # Run initial cycle immediately and log next run
        logger.info("Running initial processing cycle")
        run_and_log()
        log_next_run("Initial scan complete -")

        logger.info("Entering main scheduler loop")
        logger.debug("Scheduler will check every 1 second for pending jobs")

        while True:
            schedule.run_pending()
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("="*80)
        logger.info("Received keyboard interrupt - shutting down gracefully")
        logger.info("="*80)
    except Exception as e:
        logger.error("="*80)
        logger.error("Fatal error in main process: %s", e, exc_info=True)
        logger.error("="*80)
        raise
