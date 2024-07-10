from datetime import datetime, timedelta, timezone
import os
import psycopg
import pandas as pd
import pytz

# postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
# conn = psycopg.connect(postgres_conn_string)


# # update_list = [(("2024-07-05T12:00:00", "2024-07-05T13:00:00", 1, 1000, "5e81563a-42ca-4137-9b36-f423a6f27a73-co2"), 1474), (("2024-07-05T12:00:00", "2024-07-05T13:00:00", 1, 1000, "5e81563a-42ca-4137-9b36-f423a6f27a73-co2"), 1473)]

# # update_anomalies(conn=conn, update_list=update_list)

# print(get_latest_anomaly(conn=conn, timeseriesid="5e81563a-42ca-4137-9b36-f423a6f27a73-co2", rule_id=2))

# index = pd.date_range('1/2/2000', periods=9, freq='min')
# series = pd.Series(range(9), index=index)

# df = pd.DataFrame(series)
# print(df)

# # resampled = df.resample(rule='15s', origin='2000-01-01 00:01:00', offset='5min').mean()
# # print(resampled)

# df = df['1/1/2000 00:01:30'::]
# print(f"df after slicing: {df}")

# time = '2024-09-07 12:30:24'
# # Parse start time string into datetime object
# start_time = datetime.strptime(time,"%Y-%m-%d %H:%M:%S")
# start_time = start_time.replace(tzinfo=timezone.utc)
# print(f"{start_time} type: {type(start_time)}")

# # Convert start time to total seconds since midnight
# total_seconds = start_time.hour * 3600 + start_time.minute * 60 + start_time.second

# # Calculate nearest multiple of 150 seconds
# rounded_seconds = round(total_seconds / 150) * 150

# # Construct rounded time as datetime object
# rounded_time = timedelta(seconds=rounded_seconds)
# print(rounded_time)

# # Add rounded time to start of the day (midnight) to get the final rounded datetime
# rounded_datetime = datetime.combine(start_time.date(), datetime.min.time()) + rounded_time
# rounded_datetime = rounded_datetime.replace(tzinfo=timezone.utc)
# print(datetime.min.time())

# # Format rounded datetime as string
# rounded_time_str = rounded_datetime.strftime('%Y-%m-%d %H:%M:%S')

# print(type(rounded_datetime))

# # TIMEZONE AWARENESS
# aware = datetime.datetime(2024, 9, 7, 12, 30, 24, pytz.UTC)

# if start_time == aware:
#     print(f"{start_time}, {aware}, are equal")

duplicates = [True, False, False]
if True in duplicates:
      print(f"duplicates exist")

rows = [
    ['2024-07-10 12:00:00', 100, '5a'],
    ['2024-07-10 12:00:00', 500, '8b'],
    ['2024-07-10 13:00:00', 600, 'e7'],
    ['2024-07-10 12:00:00', 100, '5a'],
    ['2024-07-10 13:00:00', 100, '5a'],
]

# Create DataFrame
df = pd.DataFrame(rows, columns=["ts", "value", "timeseriesid"])

# Convert 'ts' column to datetime
df['ts'] = pd.to_datetime(df['ts'])
print(f"df from pg: {df}")

df_pivoted = df.pivot(index='ts', columns='timeseriesid', values='value')
print(f"pivoted df: {df_pivoted}")