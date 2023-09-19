text = """\
# log_merger

The log_merger provides a view of one or more log files, merged by timestamps found in those files. It is helpful
when analyzing interactions between separate programs by viewing their individual log files side-by-side, in
timestamp order.

In practice, log files often use various formats for their log timestamps. log_merger looks for several 
standard timestamp formats, at the start of each line of the log file:

| Format                  | Description                                                                    |
|-------------------------|--------------------------------------------------------------------------------|
| YYYY-MM-DD HH:MM:SS,SSS | date and time with milliseconds (, decimal) (defaut Python asctime log format) |
| YYYY-MM-DD HH:MM:SS.SSS | date and time with milliseconds (. decimal)                                    |
| YYYY-MM-DD HH:MM:SS     | date and time                                                                  |
| 0000000000.000000       | float seconds since epoch                                                      |
| 0000000000000           | milliseconds since epoch                                                       |
| 0000000000              | integer seconds since epoch                                                    |
| Jan 01 00:00:00         | month, day, and time (syslog) (year is taken from the log file create date)    |

For log files that do not have the timestamp at the start of the line, you can define a custom format using
the command line option `--timestamp_format`.  See `Custom timestamp formats` below.

## Interactive functions

The interactive mode of log_merger defines several keystroke navigation commands:

| Key | Function                                                                                                                   |
|:---:|----------------------------------------------------------------------------------------------------------------------------|
|  F  | Prompt for search string and advance to first line containing that string (case-insensitive)                               |
|  N  | Advance to next instance of the current search string                                                                      |
|  P  | Move back to previous instance of the current search string                                                                |
|  L  | Prompt for line number to move cursor to (if line number > total number of merged lines, advances to end)                  |
|  T  | Prompt for timestamp to move cursor to (if no log message at the exact timestamp, will move to first line after timestamp) |
|  H  | Display this helpful text                                                                                                  |
|  Q  | Quit                                                                                                                       |


## Command line options

The command to run log_merger accepts several options:

| Option              | Description                                                                                      |
|---------------------|--------------------------------------------------------------------------------------------------|
| --width, -w         | total display width - if greater than the screen width, will display with a horizontal scrollbar |
| --line_numbers, -ln | display with a leading line number column                                                        |
| --start, -s         | start time for merging logs                                                                      |
| --end, -e           | end time for merging logs                                                                        |
| --interactive, -i   | display in interactive mode                                                                      |
| --csv               | output merged logs as CSV                                                                        |
| --timestamp_format  | define one or more custom formats for log file timestamps                                        |


## Usage tips

### Use log_merger with a single log file

You can use log_merger even with just a single log file to make use of log_merger's interactive viewing or
CSV formatting. log_merger normalizes timestamps to a standard `YYYY-MM-DD HH:MM:SS.SSS` format, making logs
that use seconds-since-epoch timestamps more human-readable.

### Multi-line logs

Some logs may contain messages that extend beyond a single line, or are followed by untimestamped lines
(such as JSON data or and exception with traceback). log_merger detects these lines and groups them with the
previous timestamped line.

### Out-of-sequence log lines

For the most part, log lines are written in ascending time order. But on occasion, some log messages may
get recorded out of time order. log_merger uses a rolling window sort to reorder out-of-sequence log lines
into proper ascending time order.

### Custom timestamp formats

Custom timestamp formats are defined using regular expressions,
with the exception that in place of
the regex pattern for the actual timestamp, the template should contain `(...)`. 

The template will have the form of:

    ((...)x)

or

    (leading)((...)x)

where `x` can be any trailing spaces or delimiter that follows the timestamp, and
`leading` can be a regex fragment for any leading text that comes before the timestamp.

The template performs 3 functions:
- `(...)` will create a capture group containing the actual timestamp value
- `((...)x)` will define a capture group for text that will be removed from the log line
  before adding it to the table (so that timestamps do not get duplicated in the
  timestamp column _and_ in the log text itself
- `(leading)` defines a capture group that comes before the timestamp, and which should
  be preserved in the presented log line

Here are some example log lines and suggested format templates:

| Log line                                    | Template           |
|---------------------------------------------|--------------------|
| INFO - 2022-01-01 12:34:56 log message      | (\w+ - )((...) )   |
| [INFO] 2022-01-01 12:34:56 log message      | (\[\w+\] )((...) ) |
| [2022-01-01 12:34:56&#124;INFO] log message | (\[)((...)&#124;)  |


## About log_merger

log_merger version 0.4.0 (in development)

by Paul McGuire, 2023

MIT License

GitHub: `https://github.com/ptmcg/log_merger`
"""  # noqa