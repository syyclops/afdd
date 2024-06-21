from rdflib import Graph, URIRef, Literal
from typing import List
import pandas as pd

from timescale import Timescale, TimeseriesData
from postgres import Postgres

# not used bc there is no create_kaiterra_devices script
def load_graph(facility_uri: str, device_list: List[dict]) -> pd.DataFrame:
# Load our sample devices and points

  if type(facility_uri) != str:
    raise TypeError('Facility URI must be a string. ')
  
  if not isinstance(device_list, list):
    raise TypeError('Device list must be a list of tuples in the format (device_name, device_udid). ')
  try:
    for i in device_list:
      for j in i:
        if type(j) != str:
          raise TypeError('Device name and id must be strings. ')
  except ValueError:
    raise Exception('Device list must be a list of tuples in the format (device_name, device_udid). ')

  g = create_empty_kaiterra_graph(facility_uri, device_list, True)
  
  g.parse("https://raw.githubusercontent.com/syyclops/brontes/main/ontology/Brick.ttl", format="ttl")

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

def load_timeseries(graphInfoDF: pd.DataFrame, start_time: str, end_time: str, brick_class: str) -> List[TimeseriesData]:
  # gets all of the timeseriesids that correspond to the given brick class
  tsid = graphInfoDF.loc[graphInfoDF['class'] == URIRef(brick_class), "timeseriesid"].to_list()

  # converting timeseriesids to strings instead of literals so we can use .get_timeseries method
  for i in range(len(tsid)):
    tsid[i] = str(tsid[i])

  postgres = Postgres()
  timescale = Timescale(postgres=postgres)
  ts_data_list = timescale.get_timeseries(timeseriesIds = tsid, start_time = start_time, end_time = end_time)
  
  return ts_data_list

def append_anomalies(anomaly_list: List[tuple]):
  postgres = Postgres()

  query = "INSERT INTO anomalies (ts, rule, name, device, point, value) VALUES (%s, %s, %s, %s, %s, %s)"
  try:
    with postgres.cursor() as cur:
      cur.executemany(query, anomaly_list)
      postgres.conn.commit()
  except Exception as e:
    raise e
