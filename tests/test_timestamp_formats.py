import pytest

from datetime import datetime, timezone, timedelta
from logmerger.timestamp_wrapper import TimestampedLineTransformer

local_time = datetime.now().astimezone()
local_tz = local_time.tzinfo


def _test_timestamp_format_parsing(string_date: str, expected_transformer_class_name: str, expected_datetime: datetime) -> None:
    transformer = TimestampedLineTransformer.make_transformer_from_sample_line(
        string_date
    )

    # assert that we got the expected transformer
    assert type(transformer).__name__ == expected_transformer_class_name

    try:
        parsed_datetime, _ = transformer(string_date)
    except ValueError as ve:
        raise AssertionError(
            f"failed to parse {string_date!r} with transformer {type(transformer).__name__}"
        ) from ve

    # convert naive datetimes to UTC for test comparison
    if parsed_datetime.tzinfo is None:
        parsed_datetime = parsed_datetime.replace(tzinfo=local_tz).astimezone(timezone.utc)
    print(repr(string_date))
    print(type(transformer).__name__)
    print("Parsed time  :", parsed_datetime)
    print("Expected time:", expected_datetime)
    assert parsed_datetime == expected_datetime, f"failed to convert {string_date!r} with transformer {type(transformer).__name__}"


@pytest.mark.parametrize(
    "tz_class, string_date, expected_datetime",
    [
        (
            "YMDHMScommaFZ",
            "2023-07-14 08:00:01,000Z Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=timezone.utc),
        ),
        (
            "YMDHMScommaFZ",
            "2023-07-14 08:00:01,123+0200 Log",
            datetime(2023, 7, 14, 8, 0, 1, 123000, tzinfo=timezone(timedelta(hours=2))),
        ),
        (
            "YMDHMScommaF",
            "2023-07-14 08:00:01,123 Log",
            datetime(2023, 7, 14, 8, 0, 1, 123000, tzinfo=local_tz),
        ),
        (
            "YMDHMSdotFZ",
            "2023-07-14 08:00:01.123Z Log",
            datetime(2023, 7, 14, 8, 0, 1, 123000, tzinfo=timezone.utc),
        ),
        (
            "YMDHMSdotFZ",
            "2023-07-14 08:00:01.123+0200 Log",
            datetime(2023, 7, 14, 8, 0, 1, 123000, tzinfo=timezone(timedelta(hours=2))),
        ),
        (
            "YMDHMSdotF",
            "2023-07-14 08:00:01.123 Log",
            datetime(2023, 7, 14, 8, 0, 1, 123000, tzinfo=local_tz)
        ),
        (
            "YMDHMSZ",
            "2023-07-14 08:00:01Z Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=timezone.utc),
        ),
        (
            "YMDHMSZ",
            "2023-07-14 08:00:01+0200 Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=timezone(timedelta(hours=2))),
        ),
        (
            "YMDHMS",
            "2023-07-14 08:00:01 Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=local_tz)
        ),
        (
            "YMDTHMScommaFZ",
            "2023-07-14T08:00:01,000Z Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=timezone.utc),
        ),
        (
            "YMDTHMScommaFZ",
            "2023-07-14T08:00:01,000+0200 Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=timezone(timedelta(hours=2))),
        ),
        (
            "YMDTHMScommaF",
            "2023-07-14T08:00:01,000 Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=local_tz),
        ),
        (
            "YMDTHMSdotFZ",
            "2023-07-14T08:00:01.000Z Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=timezone.utc),
        ),
        (
            "YMDTHMSdotFZ",
            "2023-07-14T08:00:01.000+0200 Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=timezone(timedelta(hours=2))),
        ),
        (
            "YMDTHMSdotF",
            "2023-07-14T08:00:01.000 Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=local_tz),
        ),
        (
            "YMDTHMSZ",
            "2023-07-14T08:00:01Z Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=timezone.utc),
        ),
        (
            "YMDTHMSZ",
            "2023-07-14T08:00:01+0200 Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=timezone(timedelta(hours=2))),
        ),
        (
            "YMDTHMS",
            "2023-07-14T08:00:01 Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=local_tz)
        ),
        (
            "BDHMS",
            "Jul 14 08:00:01 Log",
            datetime(datetime.now().year, 7, 14, 8, 0, 1, tzinfo=local_tz),
        ),
        # HMSdot - TODO - gets date from file timestamp
        (
            "PythonHttpServerLog",
            '''::1 - - [22/Sep/2023 21:58:40] "GET /log1.txt HTTP/1.1" 200 -''',
            datetime(2023, 9, 22, 21, 58, 40, tzinfo=local_tz),
        ),
        (
            "HttpServerAccessLog",
            '''91.194.60.14 - - [16/Sep/2023:19:05:06 +0000] "GET /python_nutshell_app_a_search HTTP/1.1" 200 1027 "-"''',
            datetime(2023, 9, 16, 19, 5, 6, tzinfo=timezone.utc),
        ),
        (
            "FloatSecondsSinceEpoch",
            "1694561169.550987 Log",
            datetime.fromtimestamp(1694561169.550987, tz=timezone.utc),
        ),
        (
            "MilliSecondsSinceEpoch",
            "1694561169550 Log",
            datetime.fromtimestamp(1694561169550 / 1000, tz=timezone.utc),
        ),
        (
            "SecondsSinceEpoch",
            "1694561169 Log",
            datetime.fromtimestamp(1694561169, tz=timezone.utc),
        ),
        (
            "ApacheLogFormat",
            "[Fri Dec 01 00:00:25.933177 2023] Log",
            datetime(2023, 12, 1, 0, 0, 25, 933177, tzinfo=local_tz),
        ),
    ],
)
def test_timestamp_format_parsing(tz_class: str, string_date: str, expected_datetime: datetime):
    _test_timestamp_format_parsing(string_date, tz_class, expected_datetime)
