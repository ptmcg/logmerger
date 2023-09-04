# log_merger

log_merger is a TUI for viewing a merged display of multiple log files, merged by timestamp.

Given these two log files:

```
# log1.txt
2023-07-14 08:00:01 WARN   Connection lost due to timeout
2023-07-14 08:00:04 ERROR  Request processed unsuccessfully
Something went wrong
Traceback (last line is latest):
    blah
    blah
ValueError("shouldn't have done that")
2023-07-14 08:00:06 INFO   User authentication succeeded
2023-07-14 08:00:08 DEBUG  Starting data synchronization
2023-07-14 08:00:11 INFO   Processing incoming request
```

```
# log2.txt
2023-07-14 08:00:01 INFO   Request processed successfully
2023-07-14 08:00:03 INFO   User authentication succeeded
2023-07-14 08:00:06 DEBUG  Starting data synchronization
2023-07-14 08:00:08 INFO   Processing incoming request
2023-07-14 08:00:11 DEBUG  Performing database backup
2023-07-14 08:00:14 WARN   Invalid input received: missing required field
```

Shows the following merged display:
```
  Timestamp                 Log1.Txt                        Log2.Txt             
 ─────────────────────────────────────────────────────────────────────────────────────────
  2023-07-14 08:00:01.000   WARN   Connection lost due to   INFO   Request processed
                            timeout                         successfully
  2023-07-14 08:00:03.000                                   INFO   User authentication
                                                            succeeded
  2023-07-14 08:00:04.000   ERROR  Request processed
                            unsuccessfully
                            Something went wrong
                            Traceback (last line is
                            latest):
                                blah
                                blah
                            ValueError("shouldn't have
                            done that")
  2023-07-14 08:00:06.000   INFO   User authentication      DEBUG  Starting data
                            succeeded                       synchronization
  2023-07-14 08:00:08.000   DEBUG  Starting data            INFO   Processing incoming
                            synchronization                 request
  2023-07-14 08:00:11.000   INFO   Processing incoming      DEBUG  Performing database
                            request                         backup
                            INFO   Processing incoming
                            request (a little more...)
  2023-07-14 08:00:14.000   DEBUG  Performing database      WARN   Invalid input
                            backup                          received: missing required
                                                            field
```
