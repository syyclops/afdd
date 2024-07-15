import pandas as pd
import datetime
import psycopg
from psycopg import Connection
from rdflib import Literal
import os
import asyncio
import logging
from dotenv import load_dotenv
from datetime import timedelta
from typing import List

from afdd.logger import logger
from afdd.models import Rule, Metric, Anomaly, Metadata
from afdd.utils import load_graph, round_time, series_comparator, calculate_weighted_avg
from afdd.db import load_timeseries, append_anomalies, load_rules, get_rules

def analyze_data(graph_info_df: pd.DataFrame, timeseries_data: pd.DataFrame, rule: Rule, start_time: str) -> List[tuple]:
  """
  Evaluates the given timeseries data against the given rule and returns a list of tuples representing anomalies.
  """
  anomaly_list = []
  if rule.condition.metric == Metric.AVERAGE:  # there's only Metric.AVERAGE at the moment
    op = rule.condition.operator
    duration = rule.condition.duration
    resample_size = int(duration * 0.25)  # increment size of the rolling average (how far it's going to roll each time)
    rounded_start = round_time(time=start_time, resample_size=resample_size)  # start time rounded to the nearest normalized time

    # nomralizes timestamps to intervals of resample size and compute the rolling mean
    rolling_mean = timeseries_data.resample(f'{resample_size}s').mean()
    logger.info(f"resampled data:\n {rolling_mean}")
    throwaway_at_start = rounded_start + timedelta(seconds=int(duration)) # gets rid of the first few values of our table that aren't full windows
    rolling_mean = rolling_mean.rolling(window=f'{duration + resample_size}s').mean()[throwaway_at_start::]
    logger.info(f"DF after rolling_mean:\n {rolling_mean}")

    for id in rolling_mean.columns:
      device_uri = graph_info_df.loc[graph_info_df["timeseriesid"] == Literal(id), "deviceURI"].values[0]
      component_uri = graph_info_df.loc[graph_info_df["timeseriesid"] == Literal(id), "componentURI"].values[0]

      # compare the rolling means to the rule's condition using vectorized operation
      rolling_mean["results"] = series_comparator(op, rolling_mean[id], rule.condition.threshold)
      logger.debug(f"result of comparing rolling means with threshold:\n {rolling_mean[[id, 'results']]}")

      # put all of the trues (anomalies found) into a dataframe
      anomaly_df = rolling_mean.loc[rolling_mean["results"] == True, [id]]
      anomaly_df["start_time"] = anomaly_df.index - timedelta(seconds=duration)
      anomaly_df["start_time"] = pd.to_datetime(anomaly_df["start_time"])
      logger.info(f"anomaly_df:\n {anomaly_df}")

      prev_end = anomaly_df.first_valid_index()
      prev_start = anomaly_df["start_time"].get(prev_end)
      prev_value = anomaly_df[id].get(prev_end)

      # go through the series of anomalies and add them to the list
      for index, row in anomaly_df.iterrows():
        # if current anomaly's timeframe overlaps with previous, extend its timeframe by changing its start time and average the two values by weight (length of time)
        if (prev_start <= row['start_time']) & (row['start_time'] <= prev_end):
          weighted_average = calculate_weighted_avg(start1=prev_start, end1=prev_end, start2=row["start_time"], end2=index, val1=prev_value, val2=row[id])
          anomaly_df.loc[index, "start_time"] = prev_start
          anomaly_df.loc[index, id] = weighted_average

        # else make an Anomaly from the previous information
        else:
          anomaly = Anomaly(
              start_time=prev_start,
              end_time=prev_end,
              rule_id=rule.rule_id,
              value=prev_value,
              timeseriesid=id,
              metadata=Metadata(
                device=device_uri,
                component_uri=component_uri
              )
            )
          anomaly_list.append(anomaly.to_tuple())
          logger.info(f"Anomaly appended. Current anomaly list: {anomaly_list}")

        # update previous information to current information
        prev_start = anomaly_df.loc[index, "start_time"]
        prev_end = index
        prev_value = anomaly_df.loc[index, id]

      # append the last row of the anomaly_df to the anomaly list if there were anomalies
      if not anomaly_df.empty:
        row = anomaly_df.tail(1)
        anomaly = Anomaly(
          start_time=row["start_time"].get(row.index[0]),
          end_time=row.index[0],
          rule_id=rule.rule_id,
          value=row[id].get(row.index[0]),
          timeseriesid=id,
          metadata=Metadata(
            device=device_uri,
            component=component_uri
          )
        )
        anomaly_list.append(anomaly.to_tuple())
        logger.info(f"Anomaly appended. Current anomaly list: {anomaly_list}")
  
  logger.info(f"Final anomaly list:\n{anomaly_list}")
  return anomaly_list

async def start_rule(conn: Connection, graphInfoDF: pd.DataFrame, rule: Rule):
  """ Evaluates a rule against its threshold """
  while True:
    logger.info("---------------------------------------------------------------------------------------------------------------------------------------------------------")
    logger.info(f"*** STARTING ANALYSIS OF RULE {rule.rule_id} ***")

    resample_size = int(rule.condition.duration * 0.25)
    overlap = (rule.condition.duration / resample_size - 1) * resample_size # accounts for rolling averages from end of last iteration of loop
    start_time = datetime.datetime.now() - datetime.timedelta(seconds=rule.condition.sleep_time) - datetime.timedelta(seconds=overlap)
    end_time = datetime.datetime.now()
    sensor = f"https://brickschema.org/schema/Brick#{rule.sensor_type}"
    logger.info(f"start_time: {start_time}, end_time: {end_time}")

    logger.info(f"*** LOADING TIMESERIES DATA FOR RULE {rule.rule_id} ***")
    timeseries_df = load_timeseries(conn=conn, graphInfoDF=graphInfoDF, start_time=start_time, end_time=end_time, brick_class=sensor)

    logger.info(f"*** ANALYZING DATA FOR RULE {rule.rule_id} ***")
    anomaly_list = analyze_data(graph_info_df=graphInfoDF, timeseries_data=timeseries_df, rule=rule, start_time=start_time)

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
  logging.info('') # makes logs show up in docker?
  
  # loads in env file
  env_files = {
  'local': '.env',
  'dev': '.env.dev'
  }
  load_dotenv()
  try:
    env_file = env_files[os.environ['ENV']]
  except Exception:
    env_file = env_files['local']  
  load_dotenv(env_file, override=True)
  
  logger.info("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
  
  postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
  logger.info(f"Postgres connection string: {postgres_conn_string}")
  conn = psycopg.connect(postgres_conn_string)

  # Loads rules.json into postgres then gets rules from postgres
  load_rules(conn=conn, rules_json='rules.json')
  rules_list = get_rules(conn=conn)
  
  # Load graph data into dataframe
  graph_dataframe = load_graph(devices='kaiterra_dcoffice.ttl')
  logger.info(f"graph dataframe: \n {graph_dataframe}")

  # running anomaly detect in sleep time cycle
  asyncio.run(start(conn=conn, graphInfoDF=graph_dataframe, rules_list=rules_list))

if __name__ == '__main__':
  main()