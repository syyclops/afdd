import pandas as pd
from afdd.utils import analyze_data, load_graph, load_timeseries
from afdd.models import Rule, Condition, Metric, Severity
import psycopg
import os

postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
conn = psycopg.connect(postgres_conn_string)

graph = load_graph(devices='kaiterra_example.ttl')
ts_data = load_timeseries(conn=conn, graphInfoDF=graph, start_time='2024-07-01T20:06:48', end_time='2024-07-01T20:12:48', brick_class='https://brickschema.org/schema/Brick#CO2_Sensor')
print(ts_data)
rules_list = [
    Rule(rule_id=1, name="CO2 Too High", sensor_type="CO2_Sensor", description="Checks if the CO2 is between 1000 and 1500 ppm for 1 minute", condition=Condition(metric=Metric.AVERAGE, threshold=(1000, 1500), operator="in", severity=Severity.HIGH, duration=60)),
    Rule(rule_id=2, name="CO2 Too High", sensor_type="CO2_Sensor", description="Checks if the CO2 is over 1500 ppm for 1 minute", condition=Condition(metric=Metric.AVERAGE, threshold=1500, operator=">", severity=Severity.CRITICAL, duration=60))]

print(analyze_data(timeseries_data=ts_data, rules=rules_list, start_time='2024-07-01T20:06:48', end_time='2024-07-01T20:12:48'))
