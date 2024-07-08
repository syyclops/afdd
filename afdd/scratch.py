from afdd.utils import update_anomalies, get_latest_anomaly
import os
import psycopg
import pandas as pd


postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
conn = psycopg.connect(postgres_conn_string)


# update_list = [(("2024-07-05T12:00:00", "2024-07-05T13:00:00", 1, 1000, "5e81563a-42ca-4137-9b36-f423a6f27a73-co2"), 1474), (("2024-07-05T12:00:00", "2024-07-05T13:00:00", 1, 1000, "5e81563a-42ca-4137-9b36-f423a6f27a73-co2"), 1473)]

# update_anomalies(conn=conn, update_list=update_list)

print(get_latest_anomaly(conn=conn, timeseriesid="5e81563a-42ca-4137-9b36-f423a6f27a73-co2", rule_id=2))
