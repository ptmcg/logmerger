## [0.5.0] - 2023-09-26

### Added

- installation notes to README
- `--output` to stream to a file (files ending in ".md" are output in Markdown format)
- timestamp formats for common web server logs
- one-space indentation for continuation lines in multiline logs

### Changed

- changed shell command name from `log_merger` to `logmerger` (project name to be changed also, just not yet)
- made `--interactive` the default display mode; use `--output -` to display to stdout


## [0.4.0] - 2023-09-22

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

### Added

- `"f"`, `"n"`, `"p"` key bindings - Find/Next/Prev (case-insensitive text search)
- `"l"` key binding - Go to line number
- `"t"` key binding - Go to timestamp
- `"h"` key binding - Show help/about info
- `--timestamp_format` command line option to define a custom timestamp format template,
  for parsing log files with formats that do not begin with a leading timestamp
- strip escape sequences from log file lines, for consistent text alignment in columns


## [0.2.0] - 2023-09-15

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


[0.5.0]: https://github.com/ptmcg/log_merger/compare/v0.4.0...main
[0.4.0]: https://github.com/ptmcg/log_merger/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/ptmcg/log_merger/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/ptmcg/log_merger/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/ptmcg/log_merger/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/ptmcg/log_merger/releases/tag/v0.1.0
