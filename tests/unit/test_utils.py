from datetime import datetime, timezone

from afdd.utils import round_time

def test_round_time():
    time = "2024-10-24T12:34:56"
    rounded = round_time(time, 300)
    assert rounded == datetime(2024, 10, 24, 12, 35, tzinfo=timezone.utc)