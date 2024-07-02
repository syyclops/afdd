from rdflib import URIRef, Literal
from typing import List
import pandas as pd
import time
import datetime
from afdd.logger import logger
import psycopg
from psycopg import Connection
import os
import asyncio

from afdd.models import Rule
from afdd.utils import load_timeseries, append_anomalies, analyze_data, load_rules, get_rules, load_graph

async def start_rule(conn: Connection, graphInfoDF: pd.DataFrame, rule: Rule):
  while True:
    start_time = datetime.datetime.now() - datetime.timedelta(seconds=rule.condition.sleep_time)
    end_time = datetime.datetime.now()
    sensor = f"https://brickschema.org/schema/Brick#{rule.sensor_type}"
    timeseries_df = load_timeseries(conn=conn, graphInfoDF=graphInfoDF, start_time=start_time, end_time=end_time, brick_class=sensor)
    anomaly_list = analyze_data(timeseries_data=timeseries_df, rule=rule)
    append_anomalies(conn=conn, anomaly_list=anomaly_list)
    await asyncio.sleep(rule.condition.sleep_time)

async def start(conn: Connection, graphInfoDF: pd.DataFrame, rules_list: List[Rule]):
  coro_list = []
  for rule in rules_list:
    coro_list.append(start_rule(conn=conn, graphInfoDF=graphInfoDF, rule=rule))
  await asyncio.gather(*coro_list)

def main():
  postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
  conn = psycopg.connect(postgres_conn_string)

  load_rules(conn=conn, rules_json='rules.json')
  rules_list = get_rules(conn=conn)
  
  # Load graph data into dataframe
  graph_dataframe = load_graph(devices='kaiterra_example.ttl')
  logger.info(graph_dataframe)

  # running anomaly detect in sleep time cycle
  asyncio.run(start(conn=conn, graphInfoDF=graph_dataframe, rules_list=rules_list))

if __name__ == '__main__':
  main()