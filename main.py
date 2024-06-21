from rdflib import URIRef, Literal
from typing import List
import pandas as pd
import time
import datetime
from logger import logger

from timescale import TimeseriesData
from anomaly import Anomaly
from rule import Rule
from anomaly_ops import load_graph, load_timeseries, append_anomalies
from rule_functions import co2_too_high
from setup import *

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
        logger.info(anomaly_list)
  logger.info('finished going through data')
  return anomaly_list

def main():
  # set up anomalies table in postgres
  setup_anomalies_table()
  setup_rules_table()
  
  # load co2 rule into rules table in postgres
  co2Rule = Rule(name='CO2 Too High', id=1, description='ppm above 1000', sensors_required=[URIRef("https://brickschema.org/schema/Brick#CO2_Sensor")])
  rule = [co2Rule]
  load_rules(rule)
  
  # # loading in device data to dataframe
  # facility_uri = 'https://syyclops.com/example/example'
  # device_list = [{'device_name': 'VG21D16414', 'device_udid': '5e81563a-42ca-4137-9b36-f423a6f27a73'}, 
  #                {'device_name': 'VG21D22031', 'device_udid': '9cdcab62-892c-46c8-b3d2-3d525512576a'}, 
  #                {'device_name': 'VG21D15018', 'device_udid': '8493663d-21bf-4fa7-ba8a-163308655319'}]
  
  graph_dataframe = load_graph(devices='kaiterra_example.ttl')
  logger.info(graph_dataframe)

  # running anomaly detect every 30 minutes
  while True:
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(minutes=30)
    end_time = end_time.isoformat(timespec='seconds')
    start_time = start_time.isoformat(timespec='seconds')
    logger.info(f'start time: {start_time} \nend time: {end_time}')
    brick_class_co2 = "https://brickschema.org/schema/Brick#CO2_Sensor"

    # load timeseries data for co2 sensors
    co2_list = load_timeseries(graphInfoDF=graph_dataframe, start_time=start_time, end_time=end_time, brick_class=brick_class_co2)
    logger.info(co2_list)
    print(co2_list)
    # find anomalies in said data and put in list of tuples
    anomaly_list = analyze_data(ts_data_list=co2_list, graphInfoDF=graph_dataframe, rule=co2Rule, rule_func=co2_too_high)
    logger.info('analyzing done')

    # append anomalies to anomalies table in postgres
    append_anomalies(anomaly_list)

    time.sleep(1800)

if __name__ == '__main__':
  main()