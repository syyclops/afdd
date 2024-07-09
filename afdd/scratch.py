
import os
import psycopg
import pandas as pd


# postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
# conn = psycopg.connect(postgres_conn_string)


# # update_list = [(("2024-07-05T12:00:00", "2024-07-05T13:00:00", 1, 1000, "5e81563a-42ca-4137-9b36-f423a6f27a73-co2"), 1474), (("2024-07-05T12:00:00", "2024-07-05T13:00:00", 1, 1000, "5e81563a-42ca-4137-9b36-f423a6f27a73-co2"), 1473)]

# # update_anomalies(conn=conn, update_list=update_list)

# print(get_latest_anomaly(conn=conn, timeseriesid="5e81563a-42ca-4137-9b36-f423a6f27a73-co2", rule_id=2))

index = pd.date_range('1/1/2000', periods=9, freq='min')
series = pd.Series(range(9), index=index)

df = pd.DataFrame(series)
print(df)

# resampled = df.resample(rule='15s', origin='2000-01-01 00:01:00', offset='5min').mean()
# print(resampled)

start_time = '2000-01-01'
end_time = '2000-01-03'

df = df.asfreq(period=10)
print(f"df after resample: {df}")

df = df[start_time:end_time]
print(f"df after slicing: {df}")