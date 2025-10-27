import random
from datetime import datetime, timedelta

TARGET_SIZE_MEGABYTES = 2
TARGET_SIZE = TARGET_SIZE_MEGABYTES * 1024 * 1024
FILE_NAME = "log11.txt"

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


def calculate_lines_needed():
    """Calculate approximate number of lines needed for 500MB."""
    # Average line length from log2.txt is approximately 70-80 bytes
    avg_line_length = 75
    # target_size = 500 * 1024 * 1024  # 500MB in bytes
    return TARGET_SIZE // avg_line_length


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


def main():
    start_time = datetime(2025, 1, 1, 0, 0, 0)
    num_lines = calculate_lines_needed()

    print(f"Target: ~{TARGET_SIZE_MEGABYTES}MB per file (~{num_lines:,} lines)")
    print()

    # Generate first log file and collect its timestamps
    generate_log_file(
        FILE_NAME,
        start_time,
        num_lines
    )

    print()
    print("Generation complete!")

if __name__ == "__main__":
    main()
