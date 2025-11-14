import random
from datetime import datetime, timedelta
from pathlib import Path
import argparse

# Defaults (can be overridden via CLI)
DEFAULT_TARGET_SIZE_MEGABYTES = 50
DEFAULT_FILE_NAME = "log16.txt"
DEFAULT_OUTPUT_DIR = "."

# Log messages pool
LOG_MESSAGES = [
    ("INFO", "Request processed successfully"),
    ("INFO", "User authentication succeeded"),
    ("DEBUG", "Starting data synchronization"),
    ("INFO", "Processing incoming request"),
    ("DEBUG", "Performing database backup"),
    ("WARN", "Invalid input received: missing required field"),
    ("ERROR", "Failed to connect to remote server"),
    ("INFO", "Sending email notification"),
    ("WARN", "Slow response time detected"),
    ("INFO", "Data synchronization completed"),
    ("DEBUG", "Executing scheduled task"),
    ("INFO", "Request received from IP: 192.168.0.1"),
    ("WARN", "Insufficient disk space available"),
    ("ERROR", "Database connection failed"),
    ("INFO", "Cache cleared successfully"),
    ("DEBUG", "Memory usage within normal range"),
    ("WARN", "High CPU usage detected"),
    ("ERROR", "Timeout waiting for response"),
    ("INFO", "Configuration updated"),
    ("DEBUG", "Validating user permissions"),
    ("WARN", "Deprecated API endpoint accessed"),
    ("ERROR", "File not found"),
    ("INFO", "Session established"),
    ("DEBUG", "Garbage collection completed"),
    ("WARN", "Retry attempt exceeded"),
    ("ERROR", "Authentication token expired"),
    ("INFO", "Data export completed"),
    ("DEBUG", "Loading configuration file"),
    ("WARN", "Connection pool exhausted"),
    ("ERROR", "Invalid JSON format"),
]


def generate_log_line(timestamp):
    """Generate a single log line with given timestamp."""
    level, message = random.choice(LOG_MESSAGES)
    return f"{timestamp:%Y-%m-%d %H:%M:%S} {level:<6} {message}\n"


def calculate_lines_needed(target_size_bytes: int) -> int:
    """Calculate approximate number of lines needed for target size in bytes."""
    # Compute average line length
    avg_line_length = int(
        sum(len(msg) for _, msg in LOG_MESSAGES) / len(LOG_MESSAGES)
    )
    fixed_field_length = len("2025-01-01 00:00:00 DEBUG ")
    return target_size_bytes // (fixed_field_length + avg_line_length)


def generate_log_file(filename, start_time, num_lines):
    """
    Generate a log file with specified number of lines.

    Args:
        filename: Output file name
        start_time: Starting datetime
        num_lines: Number of log lines to generate
    """
    current_time = start_time

    print(f"Generating {filename}...")
    with open(filename, 'w') as f:
        for i in range(1, num_lines + 1):
            # Advance time by random interval (0-10 seconds)
            interval = random.randint(0, 10)
            current_time += timedelta(seconds=interval)

            line = generate_log_line(current_time)
            f.write(line)

            # Progress indicator
            if i % 100000 == 0:
                print(f"  Written {i:,} lines ({i / num_lines * 100:.1f}%)")

    print(f"  Completed: {num_lines:,} lines")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a synthetic log file of approximately the specified size."
    )
    parser.add_argument(
        "--size-mb",
        type=int,
        default=DEFAULT_TARGET_SIZE_MEGABYTES,
        help=f"Approximate size of the generated file in megabytes (default: {DEFAULT_TARGET_SIZE_MEGABYTES}).",
    )
    parser.add_argument(
        "--file-name",
        type=str,
        default=DEFAULT_FILE_NAME,
        help=f"Name of the output log file (default: {DEFAULT_FILE_NAME}).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the file will be written (default: current directory).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.size_mb <= 0:
        raise SystemExit("--size-mb must be a positive integer")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / args.file_name

    target_size_bytes = args.size_mb * 1024 * 1024

    start_time = datetime(2025, 1, 1, 0, 0, 0)
    num_lines = calculate_lines_needed(target_size_bytes)

    print(f"Target: ~{args.size_mb}MB per file (~{num_lines:,} lines)")
    print()

    # Generate the log file
    generate_log_file(
        str(output_path),
        start_time,
        num_lines,
    )

    print()
    print("Generation complete!")

if __name__ == "__main__":
    main()
