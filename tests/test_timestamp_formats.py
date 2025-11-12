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

    # Normalize both parsed and expected datetimes to UTC to avoid DST/local offset issues
    def _to_utc(dt: datetime) -> datetime:
        # Convert any datetime to UTC, interpreting naive datetimes as local time
        # at that date (respecting DST at that time).
        import time
        if dt.tzinfo is None:
            # Interpret naive datetime as local time for that date using mktime (DST-aware)
            epoch_local = time.mktime(dt.timetuple()) + dt.microsecond / 1_000_000
            return datetime.fromtimestamp(epoch_local, tz=timezone.utc)
        # Special case: if tzinfo looks like the local fixed-offset timezone (Windows),
        # treat it as local wall time at that date and compute UTC via mktime.
        try:
            is_fixed_tz = isinstance(dt.tzinfo, type(timezone.utc))
            same_named_local = is_fixed_tz and (dt.tzinfo.tzname(None) == local_tz.tzname(None))
        except Exception:
            same_named_local = False
        if same_named_local:
            dt_naive = dt.replace(tzinfo=None)
            epoch_local = time.mktime(dt_naive.timetuple()) + dt_naive.microsecond / 1_000_000
            return datetime.fromtimestamp(epoch_local, tz=timezone.utc)
        return dt.astimezone(timezone.utc)

    parsed_datetime_utc = _to_utc(parsed_datetime)
    expected_datetime_utc = _to_utc(expected_datetime)

    print(repr(string_date))
    print(type(transformer).__name__)
    print("Raw parsed   :", parsed_datetime, "tzinfo=", parsed_datetime.tzinfo)
    print("Raw expected :", expected_datetime, "tzinfo=", expected_datetime.tzinfo)
    print("Parsed time  :", parsed_datetime_utc)
    print("Expected time:", expected_datetime_utc)
    assert parsed_datetime_utc == expected_datetime_utc, f"failed to convert {string_date!r} with transformer {type(transformer).__name__}"


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


# Additional tests: ISO-8601 fractional seconds with 1–6 digits (comma/dot, space/T, tz/naive)

def _build_fractional_cases():
    cases = []
    base_dt = (2023, 7, 14, 8, 0, 1)
    # lengths 1..6
    fracs = ["1", "12", "123", "1234", "12345", "123456"]

    def micros(s: str) -> int:
        # pad right to 6 to convert fractional seconds to microseconds
        return int(s.ljust(6, "0"))

    # Space-separated with comma
    for f in fracs:
        # Z
        cases.append((
            "YMDHMScommaFZ",
            f"{base_dt[0]:04d}-{base_dt[1]:02d}-{base_dt[2]:02d} {base_dt[3]:02d}:{base_dt[4]:02d}:{base_dt[5]:02d},{f}Z Log",
            datetime(*base_dt, micros(f), tzinfo=timezone.utc),
        ))
        # +0200
        cases.append((
            "YMDHMScommaFZ",
            f"{base_dt[0]:04d}-{base_dt[1]:02d}-{base_dt[2]:02d} {base_dt[3]:02d}:{base_dt[4]:02d}:{base_dt[5]:02d},{f}+0200 Log",
            datetime(*base_dt, micros(f), tzinfo=timezone(timedelta(hours=2))),
        ))
        # naive
        cases.append((
            "YMDHMScommaF",
            f"{base_dt[0]:04d}-{base_dt[1]:02d}-{base_dt[2]:02d} {base_dt[3]:02d}:{base_dt[4]:02d}:{base_dt[5]:02d},{f} Log",
            datetime(*base_dt, micros(f), tzinfo=local_tz),
        ))

    # Space-separated with dot
    for f in fracs:
        # Z
        cases.append((
            "YMDHMSdotFZ",
            f"{base_dt[0]:04d}-{base_dt[1]:02d}-{base_dt[2]:02d} {base_dt[3]:02d}:{base_dt[4]:02d}:{base_dt[5]:02d}.{f}Z Log",
            datetime(*base_dt, micros(f), tzinfo=timezone.utc),
        ))
        # +0200
        cases.append((
            "YMDHMSdotFZ",
            f"{base_dt[0]:04d}-{base_dt[1]:02d}-{base_dt[2]:02d} {base_dt[3]:02d}:{base_dt[4]:02d}:{base_dt[5]:02d}.{f}+0200 Log",
            datetime(*base_dt, micros(f), tzinfo=timezone(timedelta(hours=2))),
        ))
        # naive
        cases.append((
            "YMDHMSdotF",
            f"{base_dt[0]:04d}-{base_dt[1]:02d}-{base_dt[2]:02d} {base_dt[3]:02d}:{base_dt[4]:02d}:{base_dt[5]:02d}.{f} Log",
            datetime(*base_dt, micros(f), tzinfo=local_tz),
        ))

    # T-separated with comma
    for f in fracs:
        # Z
        cases.append((
            "YMDTHMScommaFZ",
            f"{base_dt[0]:04d}-{base_dt[1]:02d}-{base_dt[2]:02d}T{base_dt[3]:02d}:{base_dt[4]:02d}:{base_dt[5]:02d},{f}Z Log",
            datetime(*base_dt, micros(f), tzinfo=timezone.utc),
        ))
        # +0200
        cases.append((
            "YMDTHMScommaFZ",
            f"{base_dt[0]:04d}-{base_dt[1]:02d}-{base_dt[2]:02d}T{base_dt[3]:02d}:{base_dt[4]:02d}:{base_dt[5]:02d},{f}+0200 Log",
            datetime(*base_dt, micros(f), tzinfo=timezone(timedelta(hours=2))),
        ))
        # naive
        cases.append((
            "YMDTHMScommaF",
            f"{base_dt[0]:04d}-{base_dt[1]:02d}-{base_dt[2]:02d}T{base_dt[3]:02d}:{base_dt[4]:02d}:{base_dt[5]:02d},{f} Log",
            datetime(*base_dt, micros(f), tzinfo=local_tz),
        ))

    # T-separated with dot
    for f in fracs:
        # Z
        cases.append((
            "YMDTHMSdotFZ",
            f"{base_dt[0]:04d}-{base_dt[1]:02d}-{base_dt[2]:02d}T{base_dt[3]:02d}:{base_dt[4]:02d}:{base_dt[5]:02d}.{f}Z Log",
            datetime(*base_dt, micros(f), tzinfo=timezone.utc),
        ))
        # +0200
        cases.append((
            "YMDTHMSdotFZ",
            f"{base_dt[0]:04d}-{base_dt[1]:02d}-{base_dt[2]:02d}T{base_dt[3]:02d}:{base_dt[4]:02d}:{base_dt[5]:02d}.{f}+0200 Log",
            datetime(*base_dt, micros(f), tzinfo=timezone(timedelta(hours=2))),
        ))
        # naive
        cases.append((
            "YMDTHMSdotF",
            f"{base_dt[0]:04d}-{base_dt[1]:02d}-{base_dt[2]:02d}T{base_dt[3]:02d}:{base_dt[4]:02d}:{base_dt[5]:02d}.{f} Log",
            datetime(*base_dt, micros(f), tzinfo=local_tz),
        ))

    return cases


_fractional_param_cases = _build_fractional_cases()


@pytest.mark.parametrize("tz_class, string_date, expected_datetime", _fractional_param_cases)
def test_timestamp_format_parsing_fractional(tz_class: str, string_date: str, expected_datetime: datetime):
    _test_timestamp_format_parsing(string_date, tz_class, expected_datetime)
