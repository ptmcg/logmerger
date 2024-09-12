import pytest

from .util import contains_list
from .logmerger_testing import LogMergerTestApp


@pytest.mark.parametrize(
    "log_files,expected_lines",
    [
        (
            ["files/log1.txt", "files/log2.txt"],
            [
                '2023-07-14 08:00:01.000 | WARN   Connection lost due to timeout                 | INFO   Request processed successfully',
                '2023-07-14 08:00:03.000 |                                                       | INFO   User authentication succeeded',
                '2023-07-14 08:00:04.000 | ERROR  Request processed unsuccessfully               |',
                '                        |  Something went wrong                                 |',
                '                        |  Traceback (last line is latest):                     |',
                '                        |      sample.py: line 32                               |',
                '                        |          divide(100, 0)                               |',
                '                        |      sample.py: line 8                                |',
                '                        |          return a / b                                 |',
                '                        |  ZeroDivisionError: division by zero                  |',
                '2023-07-14 08:00:06.000 | INFO   User authentication failed                     | DEBUG  Starting data synchronization',
            ],
        )
    ]
)
def test_merging(log_files, expected_lines):
    from pprint import pprint

    print(log_files)
    log_merger = LogMergerTestApp(log_files)
    merged_lines = log_merger()
    pprint(merged_lines, width=200)
    pprint(expected_lines, width=200)
    assert contains_list(merged_lines, expected_lines)


@pytest.mark.parametrize(
    "log_file,expected_lines",
    [
        (
            "tests/log1_10_log_lines.txt",
            [
                '2023-07-14 08:00:01.000 | WARN   Connection lost due to timeout',
                '2023-07-14 08:00:04.000 | ERROR  Request processed unsuccessfully',
                '2023-07-14 08:00:06.000 | INFO   User authentication failed',
                '2023-07-14 08:00:08.000 | DEBUG  Starting data synchronization',
                '2023-07-14 08:00:11.000 | INFO   Processing incoming request',
                '                        | INFO   Processing incoming request (a little more...)',
                '2023-07-14 08:00:14.000 | DEBUG  Performing database backup',
                '2023-07-14 08:00:16.000 | WARN   Invalid input received: missing required field',
                '2023-07-14 08:00:19.000 | ERROR  Failed to connect to remote server',
                '2023-07-14 08:00:22.000 | INFO   Sending email notification',
            ]
        ),
        (
            "tests/log1_10_log_lines_ooo_duplicate_timestamp.txt",
            [
                '2023-07-14 08:00:11.000 | INFO   Processing incoming request',
                '                        | INFO   Processing incoming request (a little more...)',
                '                        | ERROR  Failed to connect to remote server (OOO ++)',
                '2023-07-14 08:00:14.000 | DEBUG  Performing database backup',
            ]
        ),
        (
            "tests/log1_10_log_lines_ooo_unique_timestamp.txt",
            [
                '2023-07-14 08:00:11.000 | INFO   Processing incoming request',
                '                        | INFO   Processing incoming request (a little more...)',
                '2023-07-14 08:00:12.000 | ERROR  Failed to connect to remote server (OOO)',
                '2023-07-14 08:00:14.000 | DEBUG  Performing database backup',
            ]
        ),
        (
            "tests/log1_10_log_lines_with_multiline.txt",
            [
                '2023-07-14 08:00:11.000 | INFO   Processing incoming request',
                '                        |  Something went wrong',
                '                        |  Traceback (last line is latest):',
                '                        |      sample.py: line 32',
                '                        |          divide(100, 0)',
                '                        |      sample.py: line 8',
                '                        |          return a / b',
                '                        |  ZeroDivisionError: division by zero',
                '                        | INFO   Processing incoming request (a little more...)',
                '                        | INFO   Processing incoming request (a little more...) (OOO)',
            ]
        ),
        (
            "tests/log1_61_log_lines.txt",
            [
                '2023-07-14 08:02:50.000 | INFO   Processing incoming request'
            ]
        ),
        (
            "tests/log1_ooo_unique_timestamp.txt",
            [
                '2023-07-14 08:00:01.000 | WARN   Connection lost due to timeout',
                '2023-07-14 08:00:03.000 | WARN   Insufficient disk space available (OOO)',
                '2023-07-14 08:00:04.000 | ERROR  Request processed unsuccessfully',
            ]
        ),
        (
            "tests/log1_ooo_duplicate_timestamp.txt",
            [
                '2023-07-14 08:02:33.000 | INFO   Request received from IP: 192.168.0.1',
                '                        | DEBUG  Performing database backup',
            ]
        ),
        (
            "tests/log1_ooo_duplicate_timestamp_multiline.txt",
            [
                '2023-07-14 08:02:33.000 | INFO   Request received from IP: 192.168.0.1',
                '                        | DEBUG  Performing database backup',
                '                        |  Backing up 50000 records...',
                '                        |  Backup complete',
            ]
        ),
        (
            "tests/log1_ooo_duplicate_timestamp_multiline2.txt",
            [
                '2023-07-14 08:02:33.000 | INFO   Request received from IP: 192.168.0.1',
                '                        | DEBUG  Performing database backup',
                '                        |  Backing up 50000 records...',
                '                        |  Backup complete',
                '                        | INFO   Data synchronization completed',
            ]
        ),
        (
            "",
            [
            ]
        ),
    ]
)
def test_line_ooo_and_dedup(log_file: str, expected_lines):
    from pprint import pprint

    if not log_file:
        return
    print(log_file)
    log_merger = LogMergerTestApp(log_file)
    merged_lines = log_merger()
    pprint(merged_lines, width=200)
    pprint(expected_lines, width=200)
    assert contains_list(merged_lines, expected_lines)
