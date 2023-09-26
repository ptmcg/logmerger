logfile_1 = """\
0001-01-01 00:00:00 Original log file:

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
 2023-07-14 08:00:11 INFO   Processing incoming request (a little more...)
 2023-07-14 08:00:14 DEBUG  Performing database backup
 2023-07-14 08:00:16 WARN   Invalid input received: missing required field
 2023-07-14 08:00:19 ERROR  Failed to connect to remote server
 2023-07-14 08:00:26 INFO   Sending email notification (out of sequence time)
 2023-07-14 08:00:25 WARN   Slow response time detected
 2023-07-14 08:00:27 INFO   Data synchronization completed
 2023-07-14 08:00:30 DEBUG  Executing scheduled task
 2023-07-14 08:00:32 INFO   Request received from IP: 192.168.0.1
 2023-07-14 08:00:35 WARN   Insufficient disk space available
 2023-07-14 08:00:38 ERROR  Database connection failed

Merged data:
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
2023-07-14 08:00:11 INFO   Processing incoming request (a little more...)
2023-07-14 08:00:14 DEBUG  Performing database backup
2023-07-14 08:00:16 WARN   Invalid input received: missing required field
2023-07-14 08:00:19 ERROR  Failed to connect to remote server
2023-07-14 08:00:26 INFO   Sending email notification (out of sequence time)
2023-07-14 08:00:25 WARN   Slow response time detected
2023-07-14 08:00:27 INFO   Data synchronization completed
2023-07-14 08:00:30 DEBUG  Executing scheduled task
2023-07-14 08:00:32 INFO   Request received from IP: 192.168.0.1
2023-07-14 08:00:35 WARN   Insufficient disk space available
2023-07-14 08:00:38 ERROR  Database connection failed
"""

logfile_2 = """\
0001-01-01 00:00:00 Original log file:

 2023-07-14 08:00:01 INFO   Request processed successfully
 2023-07-14 08:00:03 INFO   User authentication succeeded
 2023-07-14 08:00:06 DEBUG  Starting data synchronization
 2023-07-14 08:00:08 INFO   Processing incoming request
 2023-07-14 08:00:11 DEBUG  Performing database backup
 2023-07-14 08:00:14 WARN   Invalid input received: missing required field
 2023-07-14 08:00:17 ERROR  Failed to connect to remote server
 2023-07-14 08:00:19 INFO   Sending email notification
 2023-07-14 08:00:22 WARN   Slow response time detected
 2023-07-14 08:00:25 INFO   Data synchronization completed
 2023-07-14 08:00:28 DEBUG  Executing scheduled task
 2023-07-14 08:00:31 INFO   Request received from IP: 192.168.0.1
 2023-07-14 08:00:34 WARN   Insufficient disk space available
 2023-07-14 08:00:37 ERROR  Database connection failed
 2023-07-14 08:00:40 INFO   Request processed successfully
 2023-07-14 08:00:43 INFO   User authentication succeeded
 2023-07-14 08:00:45 DEBUG  Starting data synchronization

2023-07-14 08:00:01 INFO   Request processed successfully
2023-07-14 08:00:03 INFO   User authentication succeeded
2023-07-14 08:00:06 DEBUG  Starting data synchronization
2023-07-14 08:00:08 INFO   Processing incoming request
2023-07-14 08:00:11 DEBUG  Performing database backup
2023-07-14 08:00:14 WARN   Invalid input received: missing required field
2023-07-14 08:00:17 ERROR  Failed to connect to remote server
2023-07-14 08:00:19 INFO   Sending email notification
2023-07-14 08:00:22 WARN   Slow response time detected
2023-07-14 08:00:25 INFO   Data synchronization completed
2023-07-14 08:00:28 DEBUG  Executing scheduled task
2023-07-14 08:00:31 INFO   Request received from IP: 192.168.0.1
2023-07-14 08:00:34 WARN   Insufficient disk space available
2023-07-14 08:00:37 ERROR  Database connection failed
2023-07-14 08:00:40 INFO   Request processed successfully
2023-07-14 08:00:43 INFO   User authentication succeeded
2023-07-14 08:00:45 DEBUG  Starting data synchronization
"""

