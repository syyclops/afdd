from rdflib import URIRef 
from typing import List
import pandas as pd
from psycopg import Connection
import json

from afdd.models import PointReading, Rule, Condition, Metric, Severity
from afdd.logger import logger

# used for create_sample_data
def insert_timeseries(conn: Connection, data: List[PointReading]) -> None:
  """Insert a list of timeseries data into the timeseries table."""
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
  """ Inserts a list of anomalies into postgres """
  query = "INSERT INTO anomalies (start_time, end_time, rule_id, value, timeseriesid) VALUES (%s, %s, %s, %s, %s)"
  try:
    with conn.cursor() as cur:
      cur.executemany(query, anomaly_list)
      conn.commit()
  except Exception as e:
    raise e

def append_past_anomalies(conn: Connection, anomaly_list: List[tuple]):
  """ Inserts a list of anomalies into postgres, checking if the anomaly already exists in the table """
  query = """INSERT INTO anomalies (start_time, end_time, rule_id, value, timeseriesid)
  SELECT %s, %s, %s, %s, %s
  WHERE NOT EXISTS (
    SELECT 1 FROM anomalies
    WHERE start_time = %s
    AND end_time = %s
    AND rule_id = %s
    AND value = %s
    AND timeseriesid = %s )"""
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

  rules_list = [(rule["rule_id"], rule["name"], rule["sensor_type"], rule["description"], json.dumps(rule["condition"])) for rule in rules_list]
  for rule in rules_list:
    with conn.cursor() as cur:
      id_exists_query = f"SELECT * FROM rules WHERE rule_id = {rule[0]}"
      cur.execute(id_exists_query)
      if not cur.fetchall():
        insert_query = "INSERT INTO rules (rule_id, name, sensor_type, description, condition) VALUES (%s, %s, %s, %s, %s)"
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
          sensor_type=row[2], 
          description=row[3], 
          condition=Condition(
            metric=Metric[row[4]['metric'].upper()], 
            threshold=row[4]['threshold'], 
            operator=row[4]['operator'], 
            duration=row[4]['duration'], 
            sleep_time=row[4]['sleep_time'],
            severity=Severity[row[4]['severity'].upper()]
        )))
      conn.commit()
      return rule_list
  except Exception as e:
    raise e


def load_timeseries(conn: Connection, graphInfoDF: pd.DataFrame, start_time: str, end_time: str, brick_class: str) -> pd.DataFrame:
  """
  Creates a dataframe containing the timeseries data that corresponds to the given start/end time and brick class.
  Timestamp is the index, the columns contain the data of each timeseriesid.
  """
  # gets all of the timeseriesids that correspond to the given brick class
  timeseries_ids = graphInfoDF.loc[graphInfoDF['class'] == URIRef(brick_class), "timeseriesid"].to_list()

  # converting timeseriesids to strings instead of literals so we can fetch them from the database
  timeseries_ids = [str(id) for id in timeseries_ids]

  # Generating placeholders for SQL IN clause
  placeholders = ', '.join(['%s' for _ in timeseries_ids])

  query = f"""
    SELECT ts, value, timeseriesid
    FROM timeseries
    WHERE timeseriesid IN ({placeholders}) AND ts >= %s AND ts <= %s
    ORDER BY ts ASC
  """

  with conn.cursor() as cur:
    cur.execute(query, timeseries_ids + [start_time, end_time])
    rows = cur.fetchall()
    
    # make a dataframe out of the query results
    df = pd.DataFrame(rows, columns=["ts", "value", "timeseriesid"])
    logger.info(f"timeseries data: {df}")

    # convert the ts column to datetimes
    df['ts'] = pd.to_datetime(df['ts'])
    df.drop_duplicates(inplace=True)
    
    # pivot the df to have ts as the index, timeseriesid as the columns and value as the values
    df_pivoted = df.pivot(index='ts', columns='timeseriesid', values='value')
    df_pivoted.sort_index(inplace=True)

    conn.commit()
    logger.info(f"pivoted ts df: {df_pivoted}")

  return df_pivoted