from typing import List, TypedDict, Optional
from dataclasses import  dataclass
from enum import Enum

from .postgres import Postgres

class TimeseriesInterval(Enum):
  MINUTE = 'minute'
  HOUR = 'hour'
  DAY = 'day'
  WEEK = 'week'
  MONTH = 'month'
  YEAR = 'year'

@dataclass
class PointReading:
  ts: str
  value: float
  timeseriesid: str

class TimeseriesData(TypedDict):
  data: List[PointReading]
  timeseriesid: str

class Timescale:
  """This class is responsible for managing the timeseries data in the timescale database."""
  def __init__(self, postgres: Postgres) -> None:
    self.postgres = postgres
    self.collection_name = 'timeseries'
    self.setup_db()
    
  def setup_db(self):
    """Make sure the timescaledb extension is enabled, the table and indexes are created"""
    try:
      with self.postgres.cursor() as cur:
        # Create timescaledb extension
        cur.execute('CREATE EXTENSION IF NOT EXISTS timescaledb') 

        # Check if timeseries table exists
        cur.execute(f'SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = \'{self.collection_name}\')') 
        if not cur.fetchone()[0]: 
          cur.execute(f'CREATE TABLE {self.collection_name} (ts timestamptz NOT NULL, value FLOAT NOT NULL, timeseriesid TEXT NOT NULL)') # Create timeseries table if it doesn't exist
          cur.execute(f'SELECT create_hypertable(\'{self.collection_name}\', \'ts\')') # Create hypertable if it doesn't exist
          cur.execute(f'CREATE INDEX {self.collection_name}_timeseriesid_ts_asc_idx ON {self.collection_name} (ts ASC)') # Create the timeseriesid index if it doesn't exist
          cur.execute(f"CREATE INDEX {self.collection_name}_timeseriesid_value_idx_2 ON {self.collection_name} (timeseriesid)") 
          self.postgres.conn.commit()
    except Exception as e:
      raise e
  
  def get_timeseries(self, timeseriesIds: List[str], start_time: str, end_time: str, interval: Optional[TimeseriesInterval] = None) -> List[TimeseriesData]:
    """Fetch timeseries data given some ids and a start and end time. Times should use ISO format string."""
    ids_array = '{' + ','.join(timeseriesIds) + '}'
    if interval:
      select_clause = f"date_trunc('{interval.value}', ts) as ts, AVG(value) as value, timeseriesid"
      group_by = f"GROUP BY date_trunc('{interval.value}', ts), timeseriesid"
    else:
      select_clause = "ts, value, timeseriesid"
      group_by = ""

    query = f"""
    SELECT {select_clause}
    FROM {self.collection_name}
    WHERE timeseriesid = ANY(%s) AND ts >= %s AND ts <= %s
    {group_by}
    ORDER BY ts ASC
    """

    try:
      with self.postgres.cursor() as cur:
        cur.execute(query, (ids_array, start_time, end_time))
        rows = cur.fetchall()
        result: List[TimeseriesData] = []
        for id in timeseriesIds:
          data = [PointReading(ts=row[0].isoformat(), value=row[1], timeseriesid=row[2]) for row in rows if row[2] == id]
          result.append(TimeseriesData(data=data, timeseriesid=id))
        self.postgres.conn.commit()
        return result
    except Exception as e:
      self.postgres.conn.rollback()
      raise e
    
  def get_latest_values(self, timeseriesIds: List[str]) -> List[PointReading]:
    """
    Get the most recent reading for a list of timeseriesIds. Limit to the last 30 minutes.
    """
    ids = ', '.join([f'\'{id}\'' for id in timeseriesIds])
    query = f"SELECT DISTINCT ON (timeseriesid) * FROM timeseries WHERE timeseriesid IN ({ids}) AND ts >= NOW() - INTERVAL '30 minutes' ORDER BY timeseriesid, ts DESC"
    try:
      with self.postgres.cursor() as cur:
        cur.execute(query)
        return [PointReading(ts=row[0].isoformat(), value=row[1], timeseriesid=row[2]) for row in cur.fetchall()]
    except Exception as e:
      raise e
    
  def insert_timeseries(self, data: List[PointReading]) -> None:
    """Insert a list of timeseries data into the timeseries table."""
    query = "INSERT INTO timeseries (ts, value, timeseriesid) VALUES "
    values = []
    placeholders = []

    for reading in data:
      placeholders.append("(%s, %s, %s)")
      values.extend([reading.ts, reading.value, reading.timeseriesid])

    query += ", ".join(placeholders)

    try:
      with self.postgres.cursor() as cur:
        cur.execute(query, values)
        cur.execute('COMMIT')
    except Exception as e:
      raise e