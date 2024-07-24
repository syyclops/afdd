import pandas as pd
from afdd.utils import load_graph
from afdd.db import load_timeseries
from afdd.main import analyze_data
from afdd.models import Rule, Condition, Metric, Severity
import psycopg
import os
from afdd.logger import logger
from datetime import timedelta
from typing import List

def analyze_data2(graph: pd.DataFrame, timeseries_data: pd.DataFrame, rule: Rule, start_time: str) -> List[tuple]:
  rolling_mean = timeseries_data.rolling(2).sum()
  print("new_df after rolling: \n", rolling_mean)
  # print("new df indices: ", df.index.to_list())

  # Evaluate the equation
  rolling_mean['results'] = rolling_mean.eval(rule.condition.equation)
  print("new_df with results column:\n", rolling_mean)

  # Put Trues in anomaly_df
  anomaly_df = rolling_mean.loc[rolling_mean["results"] == True]
  anomaly_df = anomaly_df.drop(columns=['results'])
  print("anomaly_df:\n", anomaly_df)


  anomaly_df.reset_index(level='ts', inplace=True)  # to make the index 'ts' a column
  anomaly_df.rename(columns={"ts" : "end_time"}, inplace=True) 
  print("anomaly_df after resetting end_time index:\n", anomaly_df)

  anomaly_df["start_time"] = anomaly_df['end_time'] - timedelta(minutes=60)
  anomaly_df["start_time"] = pd.to_datetime(anomaly_df["start_time"])
  print("anomaly_df after adding start_time:\n", anomaly_df)

  for component, new_df in anomaly_df.groupby(level=0):
    # new_df = new_df[throwaway::]
    print("component: ", component)
    print("component df:\n", new_df)
    combine_mask = (new_df['start_time'] <= new_df['end_time'].shift(1))

    group_key = (~combine_mask).cumsum()
    grouped = new_df.groupby(group_key).agg({
        'start_time': 'min',
        'end_time': 'max'
    }).reset_index(drop=True)
    print("new_df after combining:\n", grouped)

def main():
    combo_rule = Rule(
    rule_id=5,
    name="pm rule",
    component_type="IAQ sensor",
    sensor_types=["PM25_Level_Sensor", "PM10_Level_Sensor"],
    description="Triggers when pm10 counts and pm2.5 counts combined average over 70 micrograms per cubic meter for 1 minute",
    condition=Condition(
        equation="(PM25_Level_Sensor + PM10_Level_Sensor) > 70",
        metric=Metric.AVERAGE,
        duration=60,
        sleep_time=60,
        severity=Severity.HIGH
        )
    )

    sensor_list = ["PM10_Level_Sensor", "PM25_Level_Sensor"]

    postgres_conn_string = os.environ(['POSTGRES_CONNECTION_STRING'])
    conn = psycopg.connect(postgres_conn_string)

    graph = load_graph(devices='kaiterra_dcoffice.ttl')

    ts_data = load_timeseries(conn=conn, graphInfoDF=graph, start_time='2024-07-24T15:46:00', end_time='2024-07-24T15:50:00', brick_list=sensor_list)

    list = analyze_data(graph_info_df=graph, timeseries_data=ts_data, rule=combo_rule, start_time='2024-07-24T15:46:00')

if __name__ == "__main__":
   main()