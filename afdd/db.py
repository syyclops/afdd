from rdflib import URIRef 
from typing import List
import pandas as pd
from psycopg import Connection
import json

from afdd.models import PointReading, Rule, Condition, Metric, Severity
from afdd.logger import logger

def insert_timeseries(conn: Connection, data: List[PointReading]) -> None:
  """Insert a list of timeseries data into the timeseries table. Used for creating sample data."""
  query = "INSERT INTO timeseries (ts, value, timeseriesid) VALUES "
  values = []
  placeholders = []

  for reading in data:
    placeholders.append("(%s, %s, %s)")
    values.extend([reading.ts, reading.value, reading.timeseriesid])

  query += ", ".join(placeholders)

  try:
    with conn.cursor() as cur:
      cur.execute(query, values)
      conn.commit()
  except Exception as e:
    raise e

def append_anomalies(conn: Connection, anomaly_list: List[tuple]):
  """ Inserts a list of anomalies into postgres. Used for real time analysis. """
  query = "INSERT INTO anomalies (start_time, end_time, rule_id, points, metadata) VALUES (%s, %s, %s, %s, %s)"
  try:
    with conn.cursor() as cur:
      cur.executemany(query, anomaly_list)
      conn.commit()
  except Exception as e:
    raise e

def append_past_anomalies(conn: Connection, anomaly_list: List[tuple]):
  """ Inserts a list of anomalies into postgres, checking if the anomaly already exists in the table. Used for past data analysis. """
  query = """INSERT INTO anomalies (start_time, end_time, rule_id, points, metadata)
  SELECT %s, %s, %s, %s, %s
  WHERE NOT EXISTS (
    SELECT 1 FROM anomalies
    WHERE start_time = %s
    AND end_time = %s
    AND rule_id = %s
    AND points = %s
    AND metadata = %s )"""
  try:
    with conn.cursor() as cur:
      for anomaly in anomaly_list:
        param = anomaly + anomaly
        cur.execute(query, param)
      conn.commit()
  except Exception as e:
    raise e
  
def load_rules(conn: Connection, rules_json: str) -> None:
  """ Loads rules into Postgres from a json file """
  with open(rules_json) as file:
    rules_list = json.load(file)

  rules_list = [(rule["rule_id"], rule["name"], rule["component_type"], json.dumps(rule["sensor_types"]), rule["description"], json.dumps(rule["condition"])) for rule in rules_list]
  for rule in rules_list:
    with conn.cursor() as cur:
      id_exists_query = f"SELECT * FROM rules WHERE rule_id = {rule[0]}"
      cur.execute(id_exists_query)
      if not cur.fetchall():
        insert_query = "INSERT INTO rules (rule_id, name, component_type, sensor_types, description, condition) VALUES (%s, %s, %s, %s, %s, %s)"
        cur.execute(insert_query, rule)
      else:
        logger.info(f"Rule_id of, {rule}, already exists. ")
        continue
      cur.execute('COMMIT')

def get_rules(conn: Connection) -> List[Rule]:
  """ Gets the table of rules from Postgres and returns a list of Rule objects """
  query = "SELECT * FROM RULES ;"
  rule_list = []

  try:
    with conn.cursor() as cur:
      cur.execute(query)
      rows = cur.fetchall()
      for row in rows:
        rule_list.append(Rule(
          rule_id=row[0], 
          name=row[1],
          component_type=row[2],
          sensor_types=row[3], 
          description=row[4], 
          condition=Condition(
            equation=row[5]['equation'],
            metric=Metric[row[5]['metric'].upper()], 
            duration=row[5]['duration'], 
            sleep_time=row[5]['sleep_time'],
            severity=Severity[row[5]['severity'].upper()]
            )))
      conn.commit()
      return rule_list
    
  except Exception as e:
    raise e

def load_timeseries(conn: Connection, graph: pd.DataFrame, start_time: str, end_time: str, brick_list: List[str]) -> pd.DataFrame:
  """
  Creates a dataframe containing the timeseries data between given start and end time for given brick classes.
  The brick classes should just be passed in as the ending of the URI (everything after https://brickschema.org/schema/Brick#).
  It returns a multi-indexed dataframe where the level 0 index is component, the level 1 index is timestamp, and each column is a brick class.
  """
  # gets all of the timeseriesids that correspond to the given brick class
  all_ts_ids = []
  for brick_class in brick_list:
    timeseries_ids = graph.loc[graph['class'] == brick_class, "timeseriesid"].to_list()
    timeseries_ids = [str(id).strip() for id in timeseries_ids]
    all_ts_ids.extend(timeseries_ids)

  logger.info(f"all timeseries ids that correspond with the brick classes {brick_list}: {all_ts_ids}")
  # Generating placeholders for SQL IN clause
  placeholders = ', '.join(['%s' for _ in all_ts_ids])

  query = f"""
    SELECT ts, value, timeseriesid
    FROM timeseries
    WHERE timeseriesid IN ({placeholders}) AND ts >= %s AND ts <= %s
    ORDER BY ts ASC
  """

  with conn.cursor() as cur:
    parameters = (*all_ts_ids, start_time, end_time)
    cur.execute(query, parameters)
    rows = cur.fetchall()
    
    # make a dataframe out of the query results
    df = pd.DataFrame(rows, columns=["ts", "value", "timeseriesid"])
    logger.info(f"timeseries data: {df}")

    # convert the ts column to datetimes
    df['ts'] = pd.to_datetime(df['ts'])
    df.drop_duplicates(inplace=True)

    # strip whitespaces so that merge can match timeseriesids
    graph["timeseriesid"] = graph["timeseriesid"].str.strip()
    df['timeseriesid'] = df['timeseriesid'].str.strip()

    # merge ts dataframe and information from graph by matching up timeseriesid
    timeseries_df = pd.merge(df, graph[["class", "timeseriesid", "componentURI"]], on="timeseriesid", how="left")
    logger.info(f"timeseriesdf merged: \n{timeseries_df}")

    # pivot the df to have ts as the index, timeseriesid as the columns and value as the values
    df_pivoted = timeseries_df.pivot_table(index=['componentURI', 'ts'], columns='class', values='value', aggfunc="first")
    df_pivoted.sort_index(inplace=True)

    conn.commit()
    logger.info(f"pivoted ts df: \n{df_pivoted.to_string()}")

  return df_pivoted
