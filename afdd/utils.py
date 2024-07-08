from rdflib import Graph, URIRef 
from typing import List
import datetime
import pandas as pd
from psycopg import Connection
import json

from afdd.models import PointReading, Rule, Anomaly, Condition, Metric, Severity
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
  """ Inserts a list of anomalies into postgres """
  query = "INSERT INTO anomalies (start_time, end_time, rule_id, value, timeseriesid) VALUES (%s, %s, %s, %s, %s)"
  try:
    with conn.cursor() as cur:
      cur.executemany(query, anomaly_list)
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

def load_graph(devices: str) -> pd.DataFrame:
  """ Load our sample devices and points, takes in .ttl file of device info """
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

    # pivot the df to have ts as the index, timeseriesid as the columns and value as the values
    df_pivoted = df.pivot(index='ts', columns='timeseriesid', values='value')
    df_pivoted = df_pivoted.sort_index()

    conn.commit()
    logger.info(f"pivoted ts df: {df_pivoted}")

  return df_pivoted

# series comparison helpers
def series_in_range(data, threshold: tuple):
  return data.between(threshold[0], threshold[1])

series_symbol_map = {
    '>': pd.Series.gt,
    '>=': pd.Series.ge,
    '<': pd.Series.lt, 
    '<=': pd.Series.le,
    'in': series_in_range
    }

def series_comparator(op, data, threshold):
  return series_symbol_map[op](data, threshold)

# looping through point readings and checking for anomaly
# only works for true or false rules
def analyze_data(timeseries_data: pd.DataFrame, rule: Rule) -> List[tuple]:
  """
  Evaluates the given timeseries data against the given rule and returns a list of tuples representing anomalies.
  """
  anomaly_list = []
  if rule.condition.metric == Metric.AVERAGE:
    resample_size = 15 # increment size of the rolling average (how far it's going to roll each time)
    op = rule.condition.operator
    duration = rule.condition.duration

    # resample our data to "resample_size" and compute the rolling mean
    rolling_mean = timeseries_data.resample(f'{resample_size}s').mean()
    logger.info(f"resampled data: {rolling_mean}")
    overlap = (duration / resample_size) * resample_size
    throwaway_at_start = pd.to_datetime(rolling_mean.first_valid_index()) + datetime.timedelta(seconds=int(overlap)) # gets rid of the first few values of our table that aren't full windows
    rolling_mean = rolling_mean.rolling(window=f'{duration + resample_size}s').mean()[throwaway_at_start::]
    logger.info(f"DF after rolling_mean: {rolling_mean}")

    for id in rolling_mean.columns:
      # compare the rolling means to the rule's condition
      rolling_mean["results"] = series_comparator(op, rolling_mean[id], rule.condition.threshold)
      logger.debug(f"rolling_mean: {rolling_mean}")

      # put all of the trues (anomalies found) into a dataframe
      anomaly_df = rolling_mean.loc[rolling_mean["results"] == True, [id]]
      anomaly_df["start_time"] = anomaly_df.index - datetime.timedelta(seconds=duration)
      anomaly_df["start_time"] = pd.to_datetime(anomaly_df["start_time"])
      logger.info(f"anomaly_df: {anomaly_df}")

      prev_end = anomaly_df.first_valid_index()
      prev_start = anomaly_df["start_time"].get(prev_end)
      prev_value = anomaly_df[id].get(prev_end)

      # go through the series of anomalies and add them to the list
      for index, row in anomaly_df.iterrows():
        # if current anomaly's timeframe overlaps with previous, extend its timeframe by changing its start time and average the two values by weight (length of time)
        if (prev_start <= row['start_time']) & (row['start_time'] <= prev_end):
          weighted_average = calculate_weighted_avg(start1=prev_start, end1=prev_end, start2=row["start_time"], end2=index, val1=prev_value, val2=row[id])
          logger.info(f"weighted avg: {weighted_average}")
          anomaly_df.loc[index, "start_time"] = prev_start
          anomaly_df.loc[index, id] = weighted_average
          logger.info(f"Anomaly_df at iteration {index}: {anomaly_df}")

        # else make an Anomaly from the previous information
        else:
          anomaly = Anomaly(
              start_time=prev_start,
              end_time=prev_end,
              rule_id=rule.rule_id,
              value=prev_value,
              timeseriesid=id
            )
          anomaly_list.append(anomaly.to_tuple())

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
          timeseriesid=id
        )
        anomaly_list.append(anomaly.to_tuple())
  
  logger.info(f"Anomaly list:\n{anomaly_list}")
  return anomaly_list

def calculate_weighted_avg(start1: datetime.datetime, end1: datetime.datetime, start2: datetime.datetime, end2: datetime.datetime, val1: float, val2: float):
  difference1 = (end1 - start1).seconds # maybe this is in seconds or minutes
  difference2 = (end2 - start2).seconds
  return (val1*difference1 + val2*difference2)/(difference1 + difference2)