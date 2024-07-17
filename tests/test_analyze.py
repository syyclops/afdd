import pandas as pd
from afdd.utils import load_graph
from afdd.db import load_timeseries
from afdd.main import analyze_data
from afdd.models import Rule, Condition, Metric, Severity
import psycopg
import os
from afdd.logger import logger
import datetime

# postgres_conn_string = os.environ(['POSTGRES_CONNECTION_STRING'])
# conn = psycopg.connect(postgres_conn_string)

# logger.info("started running")

graph = load_graph(devices='kaiterra_dcoffice.ttl')
data_dict = {
    "ts": ['2024-07-10 10:10:00', '2024-07-10 10:11:00'],
    '8493663d-21bf-4fa7-ba8a-163308655319-co2' : [1200, 1500]
}
df = pd.DataFrame(data_dict)
df['ts'] = pd.to_datetime(df['ts'], utc=True)
df = df.set_index("ts")
print(df)


# df_pivoted = df.pivot(index='end_time', columns=['8493663d-21bf-4fa7-ba8a-163308655319-co2', 'start_time'], values=['8493663d-21bf-4fa7-ba8a-163308655319-co2', 'start_time'])
# ts_data = pd.DataFrame([1200,'2024-07-10 10:00:00'], index=[pd.to_datetime('2024-07-10 10:10:00')], columns=['8493663d-21bf-4fa7-ba8a-163308655319-co2', 'start_time'])
# ts_data = load_timeseries(conn=conn, graphInfoDF=graph, start_time='2024-07-08T14:38:29', end_time='2024-07-08 14:41:14', brick_class='https://brickschema.org/schema/Brick#CO2_Sensor')
# print(f"timeseries data: {df_pivoted}")

# rules_list = [
#     Rule(rule_id=1, name="CO2 Too High", sensor_type="CO2_Sensor", description="Checks if the CO2 is between 1000 and 1500 ppm for 1 minute", condition=Condition(metric=Metric.AVERAGE, threshold=(1000, 1500), operator="in", severity=Severity.HIGH, duration=60, sleep_time=120)),
#     Rule(rule_id=2, name="CO2 Too High", sensor_type="CO2_Sensor", description="Checks if the CO2 is over 1500 ppm for 1 minute", condition=Condition(metric=Metric.AVERAGE, threshold=1500, operator=">", severity=Severity.CRITICAL, duration=60, sleep_time=120))]

co2 = Rule(rule_id=1, name="CO2 Too High", sensor_type="CO2_Sensor", description="Checks if the CO2 is between 1000 and 1500 ppm for 1 minute", condition=Condition(metric=Metric.AVERAGE, threshold=(1000, 1500), operator="in", severity=Severity.HIGH, duration=60, sleep_time=120))

anomalies_list = analyze_data(graph_info_df=graph, start_time = '2024-07-10T09:00:00', timeseries_data=df, rule=co2)
# print(f"anomalies_list: {anomalies_list}")