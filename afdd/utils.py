from rdflib import Graph, Literal
from datetime import datetime, timedelta, timezone
import pandas as pd

def load_graph(devices: str) -> pd.DataFrame:
  """ Load our sample devices and points, takes in .ttl file of device info """
  g = Graph()

  g.parse(devices, format="ttl")
  g.parse("Brick.ttl", format="ttl")

  query = """
  PREFIX brick: <https://brickschema.org/schema/Brick#>
  PREFIX ns1: <http://data.ashrae.org/bacnet/#>

  SELECT DISTINCT ?point ?brickClass ?externalRef ?deviceURI ?timeseriesId ?componentURI WHERE {
    ?point a ns1:Point ;
        ns1:HAS_BRICK_CLASS ?brickClass ;
        ns1:hasExternalReference ?externalRef ;
        ns1:objectOf ?deviceURI .

      OPTIONAL {
        ?externalRef ns1:hasTimeseriesId ?timeseriesId .
    }

      OPTIONAL {
        ?deviceURI ns1:isDeviceOf ?componentURI .
    }
  }
  """
  
  # query the graph for all of the points that were loaded on
  results = g.query(query)

  # add the results of the query to a dictionary
  dict = {'class': [], 'point': [], 'timeseriesid': [], 'deviceURI': [], 'componentURI': []}
  for row in results:
    dict['class'].append(row['brickClass'])
    dict['point'].append(row['point'])
    dict['timeseriesid'].append(row['timeseriesId'])
    dict['deviceURI'].append(row['deviceURI'])
    dict['componentURI'].append(row['componentURI'])

  # make the result dictionary into a dataframe
  graphInfoDF = pd.DataFrame(dict)

  graphInfoDF['class'] = graphInfoDF['class'].apply(strip_brick_prefix)

  return graphInfoDF

def strip_brick_prefix(uri: Literal):
  """ Gets rid of brick prefix from a URI and removes periods so the Brick class can be used as a variable """
  uri = str(uri)
  parts = uri.split("#")
  ending = parts[-1].replace(".", "")
  return ending

def round_time(time: str | datetime, resample_size: int) -> datetime:
  """
  Helper method to round a time to the nearest resample size (resample size is in seconds)
  """
  if type(time) == str:
  # Parse start time string into datetime object
    time = datetime.strptime(time,"%Y-%m-%dT%H:%M:%S")

  # Convert start time to total seconds since midnight
  total_seconds = time.hour * 3600 + time.minute * 60 + time.second

  # Calculate nearest multiple of resample size
  rounded_seconds = round(total_seconds / resample_size) * resample_size

  # Construct rounded time as datetime object
  rounded_time = timedelta(seconds=rounded_seconds)

  # Add rounded time to start of the day (midnight) to get the final rounded datetime
  rounded_datetime = datetime.combine(time.date(), datetime.min.time()) + rounded_time
  rounded_datetime = rounded_datetime.replace(tzinfo=timezone.utc)
  
  return rounded_datetime

# series comparison helpers using vectorized operation
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

def calculate_weighted_avg(start1: datetime, end1: datetime, start2: datetime, end2: datetime, val1: float, val2: float):
  """
  Calculates weighted average of two values based on their respective timedeltas
  """
  difference1 = (pd.to_datetime(end1) - pd.to_datetime(start1)).total_seconds()
  difference2 = (pd.to_datetime(end2) - pd.to_datetime(start2)).total_seconds()
  result = (val1*difference1 + val2*difference2)/(difference1 + difference2)
  
  return result