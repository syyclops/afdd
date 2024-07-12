import argparse
from rdflib import Graph
from psycopg import Connection
import psycopg
import os
import json
from afdd.logger import logger
from dotenv import load_dotenv

from afdd.models import Rule, Condition, Metric, Severity
from afdd.db import load_timeseries, append_past_anomalies
from afdd.main import analyze_data
from afdd.utils import load_graph

def analyze_past_data(conn: Connection, start_time: str, end_time: str, rule_id: int, graph: Graph):
  """
  Creates a json file with all anomalies that happened between start and end time for a specified rule and appends them to Postgresql anomalies table
  """
  logger.info("---------------------------------------------------------------------------------")
  logger.info(f"*** STARTED ANALYZING PAST DATA FROM {start_time} to {end_time} ***")

  # create rule object by querying rules table using rule_id
  query = """SELECT rule_id, name, sensor_type, description, condition FROM rules WHERE rule_id=%s"""

  with conn.cursor() as cur:
    cur.execute(query, (rule_id,))
    result = cur.fetchall()
    result = result[0]
  
  rule_object = Rule(
    rule_id=rule_id, 
    name=result[1], 
    sensor_type=result[2], 
    description=result[3], 
    condition=Condition(
      metric=Metric[result[4]['metric'].upper()], 
      threshold=result[4]['threshold'], 
      operator=result[4]['operator'], 
      duration=result[4]['duration'], 
      sleep_time=result[4]['sleep_time'],
      severity=Severity[result[4]['severity'].upper()]))

  brick_class = f"https://brickschema.org/schema/Brick#{rule_object.sensor_type}"
  timeseries_df = load_timeseries(conn=conn, graphInfoDF=graph, start_time=start_time, end_time=end_time, brick_class=brick_class)
  anomalies_list = analyze_data(start_time=start_time, timeseries_data=timeseries_df, rule=rule_object)

  # convert the anomalies list of tuples to a list of dictionaries in order to make it a json file
  dict_list = []
  for anomaly in anomalies_list:
    dict = {
      "start_time": str(anomaly[0]),
      "end_time": str(anomaly[1]),
      "rule_id": anomaly[2],
      "value": anomaly[3],
      "timeseriesid": anomaly[4]
    }
    dict_list.append(dict)
  
  # taking colons out of times because they can't be used in filenames on windows
  start_time_no_colon = start_time.replace(":", "")
  end_time_no_colon = end_time.replace(":", "")
  file_name = f"{start_time_no_colon}_to_{end_time_no_colon}_anomalies_{rule_id}.json"
  with open(file_name, 'w') as f:
    json.dump(dict_list, f, indent=3)

  append_past_anomalies(conn=conn, anomaly_list=anomalies_list)
  
  return f"Report file generated: {file_name}"

def main():
  parser = argparse.ArgumentParser(description="Analyze past timeseries data for anomalies.")
  parser.add_argument("--start_time", required=True, help="start time in iso format")
  parser.add_argument("--end_time", required=True, help="end time in iso format")
  parser.add_argument("--rule_id", required=True, help="id of desired rule to be run")
  parser.add_argument("--graph", required=True, help="name of ttl file containing points graph")
  args = parser.parse_args()

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
  
  postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
  conn = psycopg.connect(postgres_conn_string)

  graph = load_graph(args.graph)

  analyze_past_data(conn=conn, start_time=args.start_time, end_time=args.end_time, rule_id=args.rule_id, graph=graph)

if __name__ == "__main__":
  main()