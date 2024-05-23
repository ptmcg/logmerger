# Demo log files

This directory contains a number of log files for experimenting with `logmerger`.

### Merging log files

These files all cover roughly the same time span but with varying timestamp formats, and so can be merged in any
number and combination to compare results with different timestamp formats. You can pass `log3.txt.gz` directly to
`logmerger`, and its contents will be unpacked internally.

| file          | description                                                                                                                  |
|---------------|------------------------------------------------------------------------------------------------------------------------------|
| `log0.txt`    | plaintext log file using `2023-07-14 08:00:01` format timestamps; to demonstrate autoclip to time window of first log file   |
| `log1.txt`    | plaintext log file using `2023-07-14 08:00:01` format timestamps                                                             |
| `log2.txt`    | plaintext log file using `2023-07-14 08:00:01` format timestamps                                                             |
| `log3.txt`    | plaintext log file using `2023-07-14 08:00:01,000` format timestamps                                                         |
| `log3.txt.gz` | gzip'ed copy of `log3.txt`                                                                                                   |
| `log4.txt`    | plaintext log file using `1689339601` (integer seconds since epoch) format timestamps                                        |
| `log5.txt`    | plaintext log file using `1689339601.000` (float seconds since epoch) format timestamps                                      |
| `log6.txt`    | plaintext log file using `1689339601000` (integer milliseconds since epoch) format timestamps                                |
| `log7.txt`    | plaintext log file using `[1689339790.262003500`&#124;`INFO](process_name)` format timestamps with embedded escape sequences |
| `syslog1.txt` | plaintext Ubuntu syslog file using `Jul 14 08:00:02` format timestamps                                                       |

NOTE: Using the custom timestamp format in `log7.txt` will require adding this command-line 
option: `--timestamp_format '(.*m\[)((...)\|)'`.


### Merging log files and packet capture files

These 3 sample files together demonstrate using `logmerger` with interacting processes, and optionally
merging in packet capture data gathered using Wireshark:

| file                      | description                                                                               |
|---------------------------|-------------------------------------------------------------------------------------------|
| `server_log.txt`          | server listening on port 8881 for up to 12 strings, and replying with the string reversed |
| `client_log.txt`          | client sending strings to the server                                                      |
| `mirror_server_8881.pcap` | packet capture recorded during client->server session                                     |

You can run `logmerger` and pass these 3 files directly as file arguments. `logmerger` will unpack the contents of the
`.pcap` file and merge them in with the plaintext log messages of the other two.
