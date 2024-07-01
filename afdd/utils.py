from rdflib import Graph, URIRef 
from typing import List
import pandas as pd
from psycopg import Connection
import json
import operator

from afdd.models import PointReading, TimeseriesData, Rule, Anomaly, Condition
from afdd.logger import logger

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
  query = "INSERT INTO anomalies (start_time, end_time, rule_id, value, timeseriesid) VALUES (%s, %s, %s, %s, %s)"
  try:
    with conn.cursor() as cur:
      cur.executemany(query, anomaly_list)
      conn.commit()
  except Exception as e:
    raise e

def load_rules_json(rules_list: List[dict]):
  with open('rules.json', 'w') as rules:
    json.dump(rules_list, rules, indent=3)
  logger.info('Rules loaded into json.')
  
# loads rules into Postgres from a json file
def load_rules(conn: Connection, rules_json: str) -> None:
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

# Gets the table of rules from Postgres and returns a list of Rule objects
def get_rules(conn: Connection) -> List[Rule]:
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
            metric=row[4]['metric'], 
            threshold=row[4]['threshold'], 
            operator=row[4]['operator'], 
            duration=row[4]['duration'], 
            severity=row[4]['severity']
        )))
      conn.commit()
      return rule_list
  except Exception as e:
    raise e

def load_graph(devices: str) -> pd.DataFrame:
# Load our sample devices and points, takes in .ttl file of device info
  g = Graph()

  g.parse(devices, format="ttl")
  g.parse("Brick.ttl", format="ttl")

  query = """
  PREFIX brick: <https://brickschema.org/schema/Brick#>
  PREFIX ns1: <http://data.ashrae.org/bacnet/#>

  SELECT ?point ?brickClass ?externalRef ?objectOf ?timeseriesId ?device_name WHERE {
    ?point a ns1:Point ;
        ns1:HAS_BRICK_CLASS ?brickClass ;
        ns1:hasExternalReference ?externalRef ;
        ns1:objectOf ?objectOf .

      OPTIONAL {
        ?externalRef ns1:hasTimeseriesId ?timeseriesId .
    }

      OPTIONAL {
        ?objectOf ns1:device_name ?device_name .
    }
  }
  """
  # query the graph for all of the points that were loaded on
  results = g.query(query)

  # add the results of the query to a dictionary
  dict = {'class': [], 'point': [], 'timeseriesid': [], 'device name': []}

  for row in results:
    dict['class'].append(row['brickClass'])
    dict['point'].append(row['point'])
    dict['timeseriesid'].append(row['timeseriesId'])
    dict['device name'].append(row['device_name'])

  # make the result dictionary into a dataframe
  graphInfoDF = pd.DataFrame(dict)

  return graphInfoDF

def load_timeseries(conn: Connection, graphInfoDF: pd.DataFrame, start_time: str, end_time: str, brick_class: str) -> pd.DataFrame:
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
    logger.info(df)

    # convert the ts column to datetimes
    df['ts'] = pd.to_datetime(df['ts'])

    # pivot the df to have ts as the index, timeseriesid as the columns and value as the values
    df_pivoted = df.pivot(index='ts', columns='timeseriesid', values='value')
    df_pivoted = df_pivoted.sort_index()

    conn.commit()
    logger.info(df_pivoted)

  return df_pivoted

metric_map = {
  "average": pd.Series.mean,
  "min": pd.Series.min,
  "max": pd.Series.max
}

# looping through point readings and checking for anomaly
# only works for true or false rules
def analyze_data(timeseries_data: pd.DataFrame, rules: List[Rule], start_time: str, end_time: str) -> List[tuple]:
  anomaly_list = []
  for ts_id, values in timeseries_data.items():
    for rule in rules:
      func = metric_map[rule.condition.metric]
      sample_data = func(values)
      threshold = rule.condition.threshold
      logger.info(f"{ts_id}:{sample_data}, {threshold}")
      op = rule.condition.operator
      if comparator(op, sample_data, threshold):
        anomaly = Anomaly(start_time=start_time, end_time=end_time, rule_id=rule.rule_id, value=sample_data, timeseriesid=ts_id)
        anomaly_list.append(anomaly.to_tuple())
  return anomaly_list

def in_range(sample, range_tuple):
  if sample in range(range_tuple[0], range_tuple[1]):
    return True
  else:
    return False
  

symbol_map = {
    '>': operator.gt,
    '>=': operator.ge,
    '<': operator.lt, 
    '<=': operator.le,
    'in': in_range
    }

def comparator(op, sample, threshold):
    return symbol_map[op](sample, threshold)
