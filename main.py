from rdflib import URIRef, Literal
from typing import List
import pandas as pd
import time
import datetime
import logging

from brontes.infra.timescale import TimeseriesData
from brontes.infra.postgres import Postgres
from brontes.core.models.anomaly import Anomaly
from brontes.core.models.rule import Rule
from brontes.core.ops.anomaly_ops import load_graph, load_timeseries, co2_too_high

logging.basicConfig(level=logging.DEBUG)

# looping through point readings and checking for anomaly
# only works for true or false rules
def analyze_data(ts_data_list: List[TimeseriesData], graphInfoDF: pd.DataFrame, rule: Rule, rule_func) -> List[dict]:
  anomaly_list = []
  for i in ts_data_list:
    data = i['data']  # list of pointReadings
    for pointReading in data:
      if rule_func(pointReading.value):
        anomaly = Anomaly(name=rule.name, 
                          rule=rule.id,
                          timestamp=pointReading.ts, 
                          device=str(graphInfoDF.loc[graphInfoDF['timeseriesid'] == Literal(pointReading.timeseriesid), 'device name'].values[0]),  # gets device name based on unique timeseriesid in graphInfoDF
                          point=str(graphInfoDF.loc[graphInfoDF['timeseriesid'] == Literal(pointReading.timeseriesid), 'point'].values[0]),
                          value=pointReading.value)
        anomaly_list.append(anomaly.to_tuple())  # change to tuple to insert as row in postgres table
        logging.info(anomaly_list)
    logging.info('finished going through data')
  return anomaly_list

def append_anomalies(anomaly_list: List[tuple]):
  postgres = Postgres()

  query = "INSERT INTO anomalies (ts, rule, name, device, point, value) VALUES (%s, %s, %s, %s, %s, %s)"
  try:
    with postgres.cursor() as cur:
      cur.executemany(query, anomaly_list)
      postgres.conn.commit()
  except Exception as e:
    raise e

# creating a postgres table for anomalies data
def setup_anomalies_table():
  postgres = Postgres()
  collection_name = 'anomalies'
  """Make sure the timescaledb extension is enabled, the table and indexes are created"""
  try:
    with postgres.cursor() as cur:
      # Create timescaledb extension
      cur.execute('CREATE EXTENSION IF NOT EXISTS timescaledb') 

      # Check if anomalies table exists
      cur.execute(f'SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = \'{collection_name}\')') 
      if not cur.fetchone()[0]: 
        cur.execute(f'CREATE TABLE {collection_name} (ts timestamptz NOT NULL, rule INT NOT NULL, name TEXT NOT NULL, device TEXT NOT NULL, point TEXT NOT NULL, value FLOAT NOT NULL)') # Create anomalies table if it doesn't exist
        cur.execute(f'SELECT create_hypertable(\'{collection_name}\', \'ts\')') # Create hypertable if it doesn't exist
        cur.execute(f'CREATE INDEX {collection_name}_rule_ts_idx ON {collection_name} (rule, ts DESC)') # Create the rule index
        postgres.conn.commit()
  except Exception as e:
    raise e

def setup_rules_table():
  postgres = Postgres()
  collection_name = 'rules'
  """Make sure the timescaledb extension is enabled, the table and indexes are created"""
  try:
    with postgres.cursor() as cur:
      # Create timescaledb extension
      cur.execute('CREATE EXTENSION IF NOT EXISTS timescaledb') 

      # Check if rules table exists
      cur.execute(f'SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = \'{collection_name}\')') 
      if not cur.fetchone()[0]: 
        cur.execute(f'CREATE TABLE {collection_name} (id INT NOT NULL, name TEXT NOT NULL, description TEXT NOT NULL, sensors TEXT[] NOT NULL)') # Create rules table if it doesn't exist
        cur.execute(f'SELECT create_hypertable(\'{collection_name}\', \'id\')') # Create hypertable if it doesn't exist
        cur.execute(f'CREATE INDEX IF NOT EXISTS {collection_name}_id_idx ON {collection_name} (id DESC) ') # Create the rule index
        postgres.conn.commit()
  except Exception as e:
    raise e

def load_rules(rule_list: List[Rule]):
  postgres = Postgres()
  
  rule_list = [(rule.id, rule.name, rule.description, rule.sensors_required) for rule in rule_list]
  query = "INSERT INTO rules (id, name, description, sensors) VALUES (%s, %s, %s, %s)"
  try:
    with postgres.cursor() as cur:
      cur.executemany(query, rule_list)
      cur.execute('COMMIT')
      logging.info('Rule successfully loaded. ')
  except Exception as e:
    raise e

def main():
  # set up anomalies table in postgres
  setup_anomalies_table()
  setup_rules_table()
  
  # load co2 rule into rules table in postgres
  co2Rule = Rule(name='CO2 Too High', id=1, description='ppm above 1000', sensors_required=[URIRef("https://brickschema.org/schema/Brick#CO2_Sensor")])
  rule = [co2Rule]
  load_rules(rule)
  
  # loading in device data to dataframe
  facility_uri = 'https://syyclops.com/example/example'
  device_list = [{'device_name': 'VG21D16414', 'device_udid': '5e81563a-42ca-4137-9b36-f423a6f27a73'}, 
                 {'device_name': 'VG21D22031', 'device_udid': '9cdcab62-892c-46c8-b3d2-3d525512576a'}, 
                 {'device_name': 'VG21D15018', 'device_udid': '8493663d-21bf-4fa7-ba8a-163308655319'}]
  
  graph_dataframe = load_graph(facility_uri=facility_uri, device_list=device_list)
  logging.info(graph_dataframe)

  # running anomaly detect every 30 minutes
  while True:
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(minutes=30)
    end_time = end_time.isoformat(timespec='seconds')
    start_time = start_time.isoformat(timespec='seconds')
    logging.info(f'start time: {start_time} \nend time: {end_time}')
    brick_class_co2 = "https://brickschema.org/schema/Brick#CO2_Sensor"

    # load timeseries data for co2 sensors
    co2_list = load_timeseries(graphInfoDF=graph_dataframe, start_time=start_time, end_time=end_time, brick_class=brick_class_co2)
    logging.info(co2_list)
    print(co2_list)
    # find anomalies in said data and put in list of tuples
    anomaly_list = analyze_data(ts_data_list=co2_list, graphInfoDF=graph_dataframe, rule=co2Rule, rule_func=co2_too_high)
    logging.info('analyzing done')

    # append anomalies to anomalies table in postgres
    append_anomalies(anomaly_list)

    time.sleep(1800)

if __name__ == '__main__':
  main()