import pandas as pd
from afdd.utils import load_graph, load_timeseries, analyze_data
from afdd.models import Rule, Condition, Metric, Severity
import psycopg
import os
from afdd.logger import logger
import datetime

postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
conn = psycopg.connect(postgres_conn_string)

logger.info("started running")

graph = load_graph(devices='kaiterra_example.ttl')
ts_data = load_timeseries(conn=conn, graphInfoDF=graph, start_time='2024-07-03T20:05:00', end_time='2024-07-03T20:12:00', brick_class='https://brickschema.org/schema/Brick#CO2_Sensor')
logger.info(f"timeseries data: {ts_data}")

rules_list = [
    Rule(rule_id=1, name="CO2 Too High", sensor_type="CO2_Sensor", description="Checks if the CO2 is between 1000 and 1500 ppm for 1 minute", condition=Condition(metric=Metric.AVERAGE, threshold=(1000, 1500), operator="in", severity=Severity.HIGH, duration=60, sleep_time=120)),
    Rule(rule_id=2, name="CO2 Too High", sensor_type="CO2_Sensor", description="Checks if the CO2 is over 1500 ppm for 1 minute", condition=Condition(metric=Metric.AVERAGE, threshold=1500, operator=">", severity=Severity.CRITICAL, duration=60, sleep_time=120))]

analyze_data(conn=conn, timeseries_data=ts_data, rule=rules_list[0])
