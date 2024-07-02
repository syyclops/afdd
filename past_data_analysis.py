import argparse

from typing import List
from afdd.utils import * 
from afdd.models import *
import psycopg
import os
import json

def analyze_past_data(conn: Connection, start_time: str, end_time: str, rule_id: int):
  """
  Creates a json file with all anomalies that happened between start and end time for a specified rule.
  """
  graph = load_graph(devices="kaiterra_example.ttl")
  
  # get full rule from rules table in postgres by rule_id
  query = f"""SELECT rule_id, name, sensor_type, description, condition
  FROM rules
  WHERE rule_id={rule_id}"""

  with conn.cursor() as cur:
    cur.execute(query)
    result = cur.fetchall()
    result = result[0]
    print(result)
  
  rule_object = Rule(
    rule_id=rule_id, 
    name=result[1], 
    sensor_type=result[2], 
    description=result[3], 
    condition=Condition(
      metric=result[4]['metric'], 
      threshold=result[4]['threshold'], 
      operator=result[4]['operator'], 
      duration=result[4]['duration'], 
      sleep_time=result[4]['sleep_time'],
      severity=result[4]['severity']))

  brick_class = f"https://brickschema.org/schema/Brick#{rule_object.sensor_type}"
  timeseries_df = load_timeseries(conn=conn, graphInfoDF=graph, start_time=start_time, end_time=end_time, brick_class=brick_class)
  anomalies_list = analyze_data(timeseries_data=timeseries_df, rule=rule_object)

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

  # append_anomalies(conn=conn, anomaly_list=anomalies_list)  # not right now
  
  return f"Report file generated: {file_name}"

def main():
  parser = argparse.ArgumentParser(description="Analyze past timeseries data for anomalies.")
  parser.add_argument("--start_time", required=True, help="start time in iso format")
  parser.add_argument("--end_time", required=True, help="end time in iso format")
  parser.add_argument("--rule_id", required=True, help="id of desired rule to be run")
  args = parser.parse_args()

  postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
  conn = psycopg.connect(postgres_conn_string)

  name = analyze_past_data(conn=conn, start_time=args.start_time, end_time=args.end_time, rule_id=args.rule_id)
  print(name)

if __name__ == "__main__":
  main()