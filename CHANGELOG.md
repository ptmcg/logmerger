## [0.10.1] - in development

### Added

- New release of the textual package added support for Ctrl-p to select from
  a list of color palettes.

### Fixed

- Fixed bug when canceling from Jump, Go to line, and Go to timestamp dialogs.


## [0.10.0] - 2024-09-30

### [Changelog][0.10.0-changes]

### Added

- Added `--ignore_non_timestamped` command-line option, to discard any log lines that do not
  have a timestamp. (Issue #42)
- Added support for Apache Log timestamp format `[Fri Dec 01 00:00:25.933177 2023]`. (Issue #36)
- CI automated unit tests across all supported Python versions (3.9-3.13).

### Fixed

- Fixed timestamp parsing that broke in Python versions pre-3.11. (Issue #43)
- Fixed bug when reordering out-of-order log lines that duplicated a previously-merged
  timestamp.
- Faster loading of data, by reducing instances where sorting is required in the readahead window.
- Fixed hanging bug when piping output to a text file.
- Piping output to a file now uses -width setting if provided.


## [0.9.0] - 2024-05-24

### [Changelog][0.9.0-changes]

### Added

- Added `"s"` key binding to capture a screenshot of the current screen.
- Support for `strace` log files; added "strace" custom timestamp format, which also accepts leading process id
  integer on each line.
- `--autoclip` command-line option, to clip merged output to the first and last timestamps found in the
  first log file.
- `--show_clock` command-line option, to show a running clock in the header of the interactive merged log display.
- Added SECURITY.md and security vulnerability reporting guidance in README.md.
- Added Python 3.13 support.


## [0.8.0] - 2023-12-07

### [Changelog][0.8.0-changes]

### Added

- Jump forward/backward by number of lines, or by time interval in microseconds, milliseconds, seconds, minutes, hours or days.
- Support for `--inline` command-line option, to merge logs into a single column instead of side by side. (Issue #32)

### Fixed

- Some Python version incompatibilities in type annotations (Issue #33)


## [0.7.0] - 2023-10-07

### [Changelog][0.7.0-changes]

### Added

- Support for CSV input files. `logmerger` looks at the first column of the CSV for the timestamp.
- Table displays and updates while loading data.
- Early detection of end-of-time-range, without reading the remainder of the input file.
- Notification when loading a large log file is complete.
- Bell when pressing `N` or `P` without defining a search string using `F`.
- Timestamps in log files that are marked with "+/-nnnn" or "Z" timezone indicators are converted to local time.
- Changelog links in CHANGELOG.md.

### Fixed

- Log lines containing rich-style text tags could raise exceptions in several output modes. Now tag introducers
  in lines are '\' escaped before sending to rich or textual.


## [0.6.0] - 2023-09-28

### [Changelog][0.6.0-changes]

### Changed

- the PyPI Project Formerly Known As `log_merger` is now `logmerger`. Install with pip using `pip install logmerger`.


## [0.5.0] - 2023-09-26

### [Changelog][0.5.0-changes]

### Added

- installation notes to README
- `--output` to stream to a file (files ending in ".md" are output in Markdown format)
- timestamp formats for common web server logs
- one-space indentation for continuation lines in multiline logs

### Changed

- changed shell command name from `log_merger` to `logmerger` (project name to be changed also, just not yet)
- made `--interactive` the default display mode; use `--output -` to display to stdout


## [0.4.0] - 2023-09-22

### [Changelog][0.4.0-changes]

### Added

- (experimental) merging `.pcap` files (such as those created using tcpdump or Wireshark)
- `--demo` command line option to run simple demo
- `ctrl-d` to toggle light/dark mode
- more natural user interaction with text in the Help/About dialog (page up/down/home/end)
- README.md for the sample `files` directory
- Python 3.12 compatibility


## [0.3.1] - 2023-09-18

### Fixed

- fixed `setup.cfg` to find all sub-packages


## [0.3.0] - 2023-09-18

### [Changelog][0.3.0-changes]

### Added

- `"f"`, `"n"`, `"p"` key bindings - Find/Next/Prev (case-insensitive text search)
- `"l"` key binding - Go to line number
- `"t"` key binding - Go to timestamp
- `"h"` key binding - Show help/about info
- `--timestamp_format` command line option to define a custom timestamp format template,
  for parsing log files with formats that do not begin with a leading timestamp
- strip escape sequences from log file lines, for consistent text alignment in columns


## [0.2.0] - 2023-09-15

### [Changelog][0.2.0-changes]

### Added

- `--line_numbers` command line option to show line numbers in the merged output
- `--encoding` command line argument to override system default encoding when reading files
- `--start` and `--end` command line arguments to specify start and end timestamps to select a
  specific time window from the merged logs; values may be an absolute timestamp in various 
  formats, or relative times such as "5m" for "5 minutes ago"
- support for direct merging of gzip-encoded files (such as `z.log.gz`)
- support for log timestamps with delimiting "T" between date and time
- support for log timestamps that are seconds (int or float) or milliseconds since epoch
- CHANGELOG.md file


## [0.1.0] - 2023-09-09

### Added

- Initial release functionality to merge multiple log files.
- Merged results can be displayed in tabular output, CSV, or in interactive terminal browser.
- Interactive browser will use the screen width by default, or accept a command-line argument.


[0.10.0]: https://github.com/ptmcg/log_merger/releases/tag/v0.10.0
[0.9.0]: https://github.com/ptmcg/log_merger/releases/tag/v0.9.0
[0.8.0]: https://github.com/ptmcg/log_merger/releases/tag/v0.8.0
[0.7.0]: https://github.com/ptmcg/log_merger/releases/tag/v0.7.0
[0.6.0]: https://github.com/ptmcg/log_merger/releases/tag/v0.6.0
[0.5.0]: https://github.com/ptmcg/log_merger/releases/tag/v0.5.0
[0.4.0]: https://github.com/ptmcg/log_merger/releases/tag/v0.4.0
[0.3.1]: https://github.com/ptmcg/log_merger/releases/tag/v0.3.1
[0.3.0]: https://github.com/ptmcg/log_merger/releases/tag/v0.3.0
[0.2.0]: https://github.com/ptmcg/log_merger/releases/tag/v0.2.0
[0.1.0]: https://github.com/ptmcg/log_merger/releases/tag/v0.1.0

[0.10.0-changes]: https://github.com/ptmcg/log_merger/compare/v0.9.0...v0.10.0
[0.9.0-changes]: https://github.com/ptmcg/log_merger/compare/v0.8.0...v0.9.0
[0.8.0-changes]: https://github.com/ptmcg/log_merger/compare/v0.7.0...v0.8.0
[0.7.0-changes]: https://github.com/ptmcg/log_merger/compare/v0.6.0...v0.7.0
[0.6.0-changes]: https://github.com/ptmcg/log_merger/compare/v0.5.0...v0.6.0
[0.5.0-changes]: https://github.com/ptmcg/log_merger/compare/v0.4.0...v0.5.0
[0.4.0-changes]: https://github.com/ptmcg/log_merger/compare/v0.3.1...v0.4.0
[0.3.1-changes]: https://github.com/ptmcg/log_merger/compare/v0.3.0...v0.3.1
[0.3.0-changes]: https://github.com/ptmcg/log_merger/compare/v0.2.0...v0.3.0
[0.2.0-changes]: https://github.com/ptmcg/log_merger/compare/v0.1.0...v0.2.0
