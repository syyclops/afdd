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
from dotenv import load_dotenv

async def start_rule(conn: Connection, graphInfoDF: pd.DataFrame, rule: Rule):
  """ Evaluates a rule against its threshold """
  while True:
    logger.info("---------------------------------------------------------------------------------------------------------------------------------------------------------")
    logger.info(f"*** STARTING ANALYSIS OF RULE {rule.rule_id} ***")
    resample_size = int(rule.condition.duration * 0.25)
    overlap = (rule.condition.duration / resample_size - 1) * resample_size # accounts for rolling averages from end of last iteration of loop
    start_time = datetime.datetime.now() - datetime.timedelta(seconds=rule.condition.sleep_time) - datetime.timedelta(seconds=overlap)
    end_time = datetime.datetime.now()
    logger.info(f"start_time: {start_time}, end_time: {end_time}")
    sensor = f"https://brickschema.org/schema/Brick#{rule.sensor_type}"
    logger.info(f"*** LOADING TIMESERIES DATA FOR RULE {rule.rule_id} ***")
    timeseries_df = load_timeseries(conn=conn, graphInfoDF=graphInfoDF, start_time=start_time, end_time=end_time, brick_class=sensor)
    logger.info(f"*** ANALYZING DATA FOR RULE {rule.rule_id} ***")
    anomaly_list = analyze_data(timeseries_data=timeseries_df, rule=rule, start_time=start_time)
    logger.info(f"*** APPENDING AND UPDATING ANOMALIES FOR RULE {rule.rule_id} ***")
    append_anomalies(conn=conn, anomaly_list=anomaly_list)
    logger.info(f"*** SLEEPING RULE {rule.rule_id} ***")
    await asyncio.sleep(rule.condition.sleep_time)

async def start(conn: Connection, graphInfoDF: pd.DataFrame, rules_list: List[Rule]):
  """ Creates a start_rule() coroutine object for each rule in the rules_list """
  coro_list = []
  for rule in rules_list:
    coro_list.append(start_rule(conn=conn, graphInfoDF=graphInfoDF, rule=rule))
  await asyncio.gather(*coro_list)

def main():
  env_files = {
  'env': '.env',
  'dev': '.env.dev'
  }
  env_file = env_files.get(os.getenv("ENV"), '.env.dev')
  load_dotenv(env_file, override=True)

  postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
  conn = psycopg.connect(postgres_conn_string)
  logger.info(f"postgres connection string: {postgres_conn_string}")

  # Loads rules.json into postgres then gets rules from postgres
  load_rules(conn=conn, rules_json='rules.json')
  rules_list = get_rules(conn=conn)
  
  # Load graph data into dataframe
  graph_dataframe = load_graph(devices='kaiterra_dcoffice.ttl')
  logger.info(graph_dataframe)

  # running anomaly detect in sleep time cycle
  asyncio.run(start(conn=conn, graphInfoDF=graph_dataframe, rules_list=rules_list))

if __name__ == '__main__':
  main()