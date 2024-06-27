from rdflib import URIRef, Literal
from typing import List
import pandas as pd
import time
import datetime
from afdd.logger import logger
import psycopg
import os

from afdd.models import Anomaly, Condition, Rule, Metric, Severity
from afdd.utils import load_graph, load_timeseries, append_anomalies, load_rules_json, analyze_data, load_rules
from afdd.rule_functions import co2_too_high

def main():
  postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
  conn = psycopg.connect(postgres_conn_string)
  
  # load co2 rule into rules table in postgres
  co2Rule = Rule(rule_id=1, name="CO2 Too High", 
                sensor_type="CO2_Sensor", 
                description="Triggers when average CO2 level exceeds 1000 ppm for 5 minutes",
                condition=Condition(metric=Metric.AVERAGE, threshold=(1000, 1500), operator="in", duration=300, severity=Severity.HIGH))

  co2Rule2 = Rule(rule_id=2, name="CO2 Critical", 
                sensor_type="CO2_Sensor", 
                description="Triggers when average CO2 level exceeds 1500 ppm for 5 minutes",
                condition=Condition(metric=Metric.AVERAGE, threshold=1500, operator=">", duration=300, severity=Severity.CRITICAL))

  rules_list = [co2Rule.to_dict(), co2Rule2.to_dict()]

  load_rules_json(rules_list=rules_list)
  load_rules(conn=conn, rules_json='rules.json')
  
  # Load graph data into dataframe
  graph_dataframe = load_graph(devices='kaiterra_example.ttl')
  logger.info(graph_dataframe)

  # running anomaly detect every 30 minutes
  while True:
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(minutes=1)
    end_time = end_time.isoformat(timespec='seconds')
    start_time = start_time.isoformat(timespec='seconds')
    logger.info(f'start time: {start_time} \nend time: {end_time}')
    brick_class_co2 = "https://brickschema.org/schema/Brick#CO2_Sensor"

    # load timeseries data for co2 sensors
    co2_df = load_timeseries(conn=conn, graphInfoDF=graph_dataframe, start_time=start_time, end_time=end_time, brick_class=brick_class_co2)

    # find anomalies in said data and put in list of tuples
    anomaly_list = analyze_data(timeseries_data=co2_df, rules=rules_list, start_time=start_time, end_time=end_time)
    logger.info('analyzing done')

    # append anomalies to anomalies table in postgres
    append_anomalies(conn, anomaly_list)

    time.sleep(60)

if __name__ == '__main__':
  main()