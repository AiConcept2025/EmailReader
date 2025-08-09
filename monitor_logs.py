#!/usr/bin/env python3
"""
Log monitoring utility for EmailReader
"""
import os
import sys
from datetime import datetime
import time


def tail_log(log_file: str, lines: int = 50) -> None:
    """Display the last n lines of the log file"""
    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        return

    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.readlines()
        last_lines = content[-lines:]

        print(f"\n{'='*60}")
        print(f"Last {lines} lines from {log_file}")
        print(f"{'='*60}\n")

        for line in last_lines:
            # Color code based on log level
            if 'ERROR' in line:
                print(f"\033[91m{line}\033[0m", end='')  # Red
            elif 'WARNING' in line:
                print(f"\033[93m{line}\033[0m", end='')  # Yellow
            elif 'INFO' in line:
                print(f"\033[92m{line}\033[0m", end='')  # Green
            else:
                print(line, end='')


def monitor_errors(log_file: str) -> None:
    """Monitor for errors in real-time"""
    print(f"Monitoring {log_file} for errors...")
    print("Press Ctrl+C to stop\n")

    with open(log_file, 'r', encoding='utf-8') as f:
        # Go to end of file
        f.seek(0, 2)

        try:
            while True:
                line = f.readline()
                if line:
                    if 'ERROR' in line or 'CRITICAL' in line:
                        print(
                            (f"\033[91m{datetime.now().strftime('%H:%M:%S')} "
                             f"- {line}\033[0m"),
                            end='')
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")


if __name__ == "__main__":
    log_dir = os.path.join(os.getcwd(), 'data', 'logs')
    today_log = f"emailreader_{datetime.now().strftime('%Y%m%d')}.log"
    log_file = os.path.join(log_dir, today_log)

    if len(sys.argv) > 1 and sys.argv[1] == '--errors':
        monitor_errors(log_file)
    else:
        tail_log(log_file)
