## [0.2.0] - not yet released

### Added

- `--encoding` command line argument to override system default encoding when reading files
- support for direct merging of gzip-encoded files (such as `z.log.gz`)
- support for timestamps that are seconds (int or float) or milliseconds since epoch
- CHANGELOG.md file


## [0.1.0] - 2023-09-09

### Added

- Initial release functionality to merge multiple log files.
- Merged results can be displayed in tabular output, CSV, or in interactive terminal browser.
- Interactive browser will use the screen width by default, or accept a command-line argument.

[0.2.0]: https://github.com/ptmcg/log_merger/compare/v0.1.0...main
[0.1.0]: https://github.com/ptmcg/log_merger/releases/tag/v0.1.0
