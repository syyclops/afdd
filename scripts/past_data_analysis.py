import argparse
from rdflib import Graph
from psycopg import Connection
import psycopg
import os
import json
from afdd.logger import logger
from dotenv import load_dotenv
from neo4j import GraphDatabase

from afdd.models import Rule, Condition, Metric, Severity
from afdd.db import load_timeseries, append_past_anomalies, load_graph_neo4j
from afdd.main import analyze_data
from afdd.utils import load_graph

def analyze_past_data(conn: Connection, driver: GraphDatabase.driver, start_time: str, end_time: str, rule_id: int):
  """
  Creates a json file with all anomalies that happened between start and end time for a specified rule and appends them to Postgresql anomalies table
  """
  logger.info("---------------------------------------------------------------------------------")
  logger.info(f"*** STARTED ANALYZING PAST DATA FROM {start_time} to {end_time} ***")

  # create rule object by querying rules table using rule_id
  query = """SELECT * FROM rules WHERE rule_id=%s"""

  with conn.cursor() as cur:
    cur.execute(query, (rule_id,))
    result = cur.fetchone()
    # print(f"query result: {result}")
    # result = result[0]
    # print(type(result[5]))
  
  rule_object = Rule(
          rule_id=result[0], 
          name=result[1],
          component_type=result[4],
          sensor_types=result[5], 
          description=result[2], 
          condition=Condition(
            equation=result[3]["equation"],
            metric=Metric[result[3]['metric'].upper()], 
            duration=result[3]['duration'], 
            sleep_time=result[3]['sleep_time'],
            severity=Severity[result[3]['severity'].upper()]
            ))
  
  # Load graph data into dataframe
  graph = load_graph_neo4j(driver=driver, component_class=rule_object.component_type)
  logger.info(f"graph dataframe: \n {graph.to_string()}")

  brick_list = rule_object.sensor_types
  timeseries_df = load_timeseries(conn=conn, graph=graph, start_time=start_time, end_time=end_time, brick_list=brick_list)
  anomalies_list = analyze_data(graph=graph, start_time=start_time, timeseries_data=timeseries_df, rule=rule_object)

  # convert the anomalies list of tuples to a list of dictionaries in order to make it a json file
  dict_list = []
  for anomaly in anomalies_list:
    dict = {
      "start_time": str(anomaly[0]),
      "end_time": str(anomaly[1]),
      "rule_id": anomaly[2],
      "points": anomaly[3],
      "metadata": anomaly[4]
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

  neo4j_uri = os.environ['NEO4J_URI']
  neo4j_user = os.environ['NEO4J_USER']
  neo4j_password = os.environ['NEO4J_PASSWORD']
  
  neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password), max_connection_lifetime=200)
  neo4j_driver.verify_connectivity()
  
  analyze_past_data(conn=conn, driver=neo4j_driver, start_time=args.start_time, end_time=args.end_time, rule_id=args.rule_id)
  neo4j_driver.close()

if __name__ == "__main__":
  main()