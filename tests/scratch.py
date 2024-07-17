from datetime import datetime, timedelta, timezone
import os
import psycopg
import pandas as pd
import pytz
import os

start1 = "2024-07-03 00:00:00+00:00"
end1 = "2024-07-04 00:00:00+00:00"
timedelta_value = pd.to_datetime(end1) - pd.to_datetime(start1)

print(timedelta_value.total_seconds())