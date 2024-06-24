from rdflib import Graph, URIRef 
from typing import List
import pandas as pd
from psycopg import Connection

from models import PointReading, TimeseriesData

def insert_timeseries(conn: Connection, data: List[PointReading]) -> None:
  """Insert a list of timeseries data into the timeseries table."""
  query = "INSERT INTO timeseries (ts, value, timeseriesid) VALUES "
  values = []
  placeholders = []

  for reading in data:
    placeholders.append("(%s, %s, %s)")
    values.extend([reading.ts, reading.value, reading.timeseriesid])

  query += ", ".join(placeholders)

  print(query)
  print(values)

  try:
    with conn.cursor() as cur:
      cur.execute(query, values)
      conn.commit()
  except Exception as e:
    raise e
  
def append_anomalies(conn: Connection, anomaly_list: List[tuple]):
  query = "INSERT INTO anomalies (ts, rule, name, device, point, value) VALUES (%s, %s, %s, %s, %s, %s)"
  try:
    with conn.cursor() as cur:
      cur.executemany(query, anomaly_list)
      conn.commit()
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

def load_timeseries(conn: Connection, graphInfoDF: pd.DataFrame, start_time: str, end_time: str, brick_class: str) -> List[TimeseriesData]:
  # gets all of the timeseriesids that correspond to the given brick class
  tsid = graphInfoDF.loc[graphInfoDF['class'] == URIRef(brick_class), "timeseriesid"].to_list()

  # converting timeseriesids to strings instead of literals so we can fetch them from the database
  for i in range(len(tsid)):
    tsid[i] = str(tsid[i])

  query = """
    SELECT ts, value, timeseriesid 
    FROM timeseries
    WHERE timeseriesid ANY(%s) AND ts >= %s AND ts <= %s
    ORDER BY ts ASC
  """

  with conn.cursor() as cur:
    cur.execute(query, (tsid, start_time, end_time))
    rows = cur.fetchall()
    result: List[TimeseriesData] = []
    for id in tsid:
      data = [PointReading(ts=row[0].isoformat(), value=row[1], timeseriesid=row[2]) for row in rows if row[2] == id]
      result.append(TimeseriesData(data=data, timeseriesid=id))
    conn.commit()

  return result