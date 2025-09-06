VERSION = "0.11.0"
RELEASE_YEAR = "2025"

text = fr"""
# logmerger

The `logmerger` utility provides a view of one or more log files, merged by timestamps found in those files. It is 
helpful when analyzing interactions between separate programs by viewing their individual log files side-by-side, in
timestamp order.

In practice, log files often use various formats for their log timestamps. `logmerger` looks for several 
standard timestamp formats, at the start of each line of the log file:

| Format                          | Description                                                                     |
|---------------------------------|---------------------------------------------------------------------------------|
| YYYY-MM-DD HH:MM:SS,SSS         | date and time with milliseconds (, decimal) (default Python asctime log format) |
| YYYY-MM-DD HH:MM:SS.SSS         | date and time with milliseconds (. decimal)                                     |
| YYYY-MM-DD HH:MM:SS             | date and time                                                                   |
| 0000000000.000000               | float seconds since epoch                                                       |
| 0000000000000                   | milliseconds since epoch                                                        |
| 0000000000                      | integer seconds since epoch                                                     |
| HH:MM:SS.SSSSSS                 | timestamp with milliseconds (strace format)                                     |
| Jan DD HH:MM:SS                 | month + day + time (timestamp in syslog files); year is inferred from the create date of the log file |
| DD/Jan/YYYY HH:MM:SS            | day/month/year + time                                                           |
| DD/Jan/YYYY:HH:MM:SS ±ZZZZ      | day/month/year : time + timezone offset (converts to local time)                |
| strace                          | uses HH:MM:SS.SSSSSS format with leading process id integer                     |
| [Mon Jan DD HH:MM:SS.SSSS YYYY] | Apache log format                                                               |

For log files that do not have the timestamp at the start of the line, you can define a custom format using
the command line option `--timestamp_format`.  See `Custom timestamp formats` below.

## Interactive functions

The interactive mode of `logmerger` defines several keystroke navigation commands:

| Key | Function                                                                                                                   |
|:---:|----------------------------------------------------------------------------------------------------------------------------|
| ^D  | Toggle dark/light mode                                                                                                     |
|  J  | Jump by line count or time interval                                                                                        |
|  F  | Prompt for search string and advance to first line containing that string (case-insensitive)                               |
|  N  | Advance (to next instance of the search string or by current jump interval)                                                |
|  P  | Move back (to previous instance of the search string or by current jump interval)                                          |
|  L  | Prompt for line number to move cursor to (if line number > total number of merged lines, advances to end)                  |
|  T  | Prompt for timestamp to move cursor to (if no log message at the exact timestamp, will move to first line after timestamp) |
|  S  | Capture a screenshot of the current visible screen                                                                         |
|  H  | Display this helpful text                                                                                                  |
|  Q  | Quit                                                                                                                       |

When using the Jump command, enter an integer number followed by "l", "us", "ms", "s", "m", "h", or "d", to indicate whether jumping
by number of lines, microseconds, milliseconds, seconds, minutes, hours, or days. Then press N and P to advance or go back by your jump interval.
For example:

    3s - jump forward or backward in 3 second steps
    5l - jump forward or backward in 5 line steps

When jumping by a time interval, if there is no entry at the exact interval difference from
the current line, advancing will jump to the next timestamp after the computed target time,
reversing will jump to the next timestamp before the computed target time.

## Command line options

The command to run `logmerger` accepts several options, followed by one or more file names:

| Option                   | Description                                                                                      |
|--------------------------|--------------------------------------------------------------------------------------------------|
| --interactive, -i        | display in interactive mode (default)                                                            |
| --inline                 | display interactive merged content into a single inline column (only supported in interactive mode) (default is side-by-side) |
| --output, -o             | save output to file ('-' for stdout; files ending in `.md` are saved using Markdown)             |
| --width, -w              | total display width - if greater than the screen width, will display with a horizontal scrollbar |
| --line_numbers, -ln      | display with a leading line number column                                                        |
| --show_clock, -clock     | show running clock in header                                                                     |
| --start, -s              | start time for merging logs                                                                      |
| --end, -e                | end time for merging logs                                                                        |
| --autoclip, -ac          | clip start and end times from logs in first log file                                             |
| --ignore_non_timestamped | ignore log lines that do not have a timestamp                                                    |
| --csv                    | output merged logs as CSV                                                                        |
| --timestamp_format       | define one or more custom formats for log file timestamps                                        |
| --demo                   | run logmerger with simulated log file content (in either text or interactive modes)              |


## Usage tips

### Use `logmerger` with a single log file

You can use `logmerger` even with just a single log file to make use of `logmerger`'s interactive viewing or
CSV formatting. `logmerger` normalizes timestamps to a standard `YYYY-MM-DD HH:MM:SS.SSS` format, making logs
that use seconds-since-epoch timestamps more human-readable.


### Supported file types

`logmerger` accepts the following file types:

- text log files
- text log files that have been gzip compressed (such as those created by logrotate)
  - (filename ending in `.gz`)
- CSV files (timestamp is read from first data column)
  - (filename ending in `.csv`)
- JSONL files - files containing a JSON object per-line (timestamp is read from first data column)
  - (filename ending in `.jsonl`)
  - if `orjson` package is installed, uses that for JSON parsing instead of the the stdlib json module.
- packet capture files, created using tcpdump or WireShark (experimental)
  - (filename ending in `.pcap`)

### Multi-line logs

Some logs may contain messages that extend beyond a single line, or are followed by untimestamped lines
(such as JSON data or an exception with traceback). `logmerger` detects these lines and groups them with the
previous timestamped line.


### Out-of-sequence log lines

For the most part, log lines are written in ascending time order. But on occasion, some log messages may
get recorded out of time order. `logmerger` uses a rolling window sort to reorder out-of-sequence log lines
into proper ascending time order.


### Merging logs sourced from different computers

Be aware that system clocks between different computers will rarely be in synch, even for those maintaining
their clocks using NTP.


### Custom timestamp formats

Custom timestamp formats are defined using regular expressions,
with the exception that in place of
the regex pattern for the actual timestamp, the template should contain `(...)`. 

The template will have the form of:

    ((...)trailing)

or

    (leading)((...)trailing)

where `trailing` can be any trailing spaces or delimiter that follows the timestamp, and
`leading` can be a regex fragment for any leading text that comes before the timestamp.

The template performs 3 functions:
- `(...)` will create a capture group containing the actual timestamp value
- `((...)trailing)` will define a capture group for text that will be removed from the log line
  before adding it to the table (so that timestamps and trailing delimiters do not get duplicated in the
  timestamp column _and_ in the log text itself)
- `(leading)` defines a capture group that comes before the timestamp, and which should
  be preserved in the presented log line

Here are some example log lines and suggested format templates:

| Log line                                    | Template           |
|---------------------------------------------|--------------------|
| INFO - 2022-01-01 12:34:56 log message      | (&#92;w+ - )((...) )   |
| [INFO] 2022-01-01 12:34:56 log message      | (&#92;[&#92;w+&#92;] )((...) ) |
| [2022-01-01 12:34:56&#124;INFO] log message | (&#92;[)((...)&#92;&#124;)  |


## About logmerger

logmerger version {VERSION}

by Paul McGuire, {RELEASE_YEAR}

MIT License

GitHub: `https://github.com/ptmcg/logmerger`
"""  # noqa