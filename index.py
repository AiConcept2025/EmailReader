"""
Start point for the application.
"""
import os
import time
from datetime import datetime
from pathlib import Path

import schedule

from src.logger import logger
from src.process_google_drive import process_google_drive
from src.utils import read_json_secret_file


def load_interval_minutes() -> int:
    cfg_path = Path('credentials/secrets.json')
    cfg = read_json_secret_file(str(cfg_path)) or {}
    scheduling = cfg.get('scheduling', {})
    return int(scheduling.get('google_drive_interval_minutes', 15))


def ensure_runtime_dirs():
    data_dir = os.path.join(os.getcwd(), 'data')
    docs_dir = os.path.join(data_dir, 'documents')
    if not os.path.isdir(data_dir):
        os.mkdir(data_dir)
    if not os.path.isdir(docs_dir):
        os.mkdir(docs_dir)
    finish_tag = os.path.join(data_dir, 'last_finish_time.txt')
    if not os.path.isfile(finish_tag):
        with open(finish_tag, 'w', encoding='utf-8') as f:
            f.write('2020-01-01 01:01:01 +0000')


def log_next_run(prefix: str = ""):
    try:
        nr = schedule.next_run
        if nr:
            mins = max(0, int((nr - datetime.now()).total_seconds() // 60))
            logger.info("%sNext cycle in ~%d minute(s) (at %s)",
                        f"{prefix} " if prefix else "",
                        mins, nr.strftime('%Y-%m-%d %H:%M:%S'))
    except Exception:
        pass


if __name__ == "__main__":
    ensure_runtime_dirs()
    interval = load_interval_minutes()
    logger.info("Configured Google Drive interval: %d minute(s)", interval)

    def run_and_log():
        logger.info("Google Drive cycle started")
        process_google_drive()
        logger.info("Google Drive cycle finished")
        log_next_run("")

    schedule.every(interval).minutes.do(run_and_log)

    # Run initial cycle immediately and log next run
    run_and_log()
    log_next_run("Initial scan complete -")

    while True:
        schedule.run_pending()
        time.sleep(1)
