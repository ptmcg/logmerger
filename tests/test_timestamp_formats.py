import pytest
from datetime import datetime, timezone, timedelta
from logmerger.timestamp_wrapper import TimestampedLineTransformer

local_time = datetime.now().astimezone()
local_tz = local_time.tzinfo


@pytest.mark.parametrize(
    "string_date, expected_datetime",
    [
        (
            "2023-07-14 08:00:01,000Z Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=timezone.utc),
        ),
        (
            "2023-07-14 08:00:01,123+0200 Log",
            datetime(2023, 7, 14, 8, 0, 1, 123000, tzinfo=timezone(timedelta(hours=2))),
        ),
        (
            "2023-07-14 08:00:01.000Z Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=timezone.utc),
        ),
        (
            "2023-07-14 08:00:01.123+0200 Log",
            datetime(2023, 7, 14, 8, 0, 1, 123000, tzinfo=timezone(timedelta(hours=2))),
        ),
        (
            "2023-07-14 08:00:01 Log", 
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=local_tz)),
        (
            "2023-07-14T08:00:01,000Z Log",
            datetime(2023, 7, 14, 8, 0, 1, tzinfo=timezone.utc),
        ),
        (
            "Jul 14 08:00:01 Log",
            datetime(datetime.now().year, 7, 14, 8, 0, 1, tzinfo=local_tz),
        ),
        (
            "1694561169.550987 Log",
            datetime.fromtimestamp(1694561169.550987, tz=timezone.utc),
        ),
        (
            "1694561169550 Log",
            datetime.fromtimestamp(1694561169550 / 1000, tz=timezone.utc),
        ),
        (
            "1694561169 Log",
            datetime.fromtimestamp(1694561169, tz=timezone.utc),
        ),
    ],
)
def test_make_transformer_from_sample_line(string_date, expected_datetime):
    transformer = TimestampedLineTransformer.make_transformer_from_sample_line(
        string_date
    )

    parsed_datetime, _ = transformer(string_date)

    parsed_datetime = parsed_datetime.astimezone(timezone.utc)

    assert parsed_datetime == expected_datetime
