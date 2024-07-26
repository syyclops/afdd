from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
import os
import psycopg
import pandas as pd
import os
from enum import Enum
from typing import List
import numpy as np
from afdd.utils import load_graph
from dotenv import load_dotenv
from afdd.db import load_timeseries, load_rules, get_rules

@dataclass
class Metric(Enum):
  AVERAGE = 'average'
  MAX = 'max'
  MIN = 'min'

@dataclass
class Severity(Enum):
  CRITICAL = 'critical'
  HIGH = 'high'
  LOW = 'low'

@dataclass
class Condition():
  equation: str
  metric: Metric
  duration: int # in seconds
  sleep_time: int # in seconds
  severity: Severity
  
  def to_dict(self):
    condition_dict = {'metric': self.metric, 
                      'equation': self.equation, 
                      'duration': self.duration,
                      'sleep_time': self.sleep_time,
                      'severity': self.severity}
    return condition_dict

@dataclass
class Rule:
  rule_id: int
  name: str
  component_type: str
  sensor_types: List[str]
  description: str
  condition: Condition

  def to_dict(self):
    rule_dict = {'rule_id': self.rule_id, 
                'name': self.name, 
                'component_type': self.component_type,
                'sensor_type': self.sensor_types,
                'description': self.description, 
                'condition': self.condition.to_dict()}
    return rule_dict

combo_rule = Rule(
  rule_id=5,
  name="pm rule",
  component_type="IAQ sensor",
  sensor_types=["PM25_Level_Sensor", "PM10_Level_Sensor"],
  description="Triggers when pm10 counts and pm2.5 counts combined average over 100 micrograms per cubic meter for 1 minute",
  condition=Condition(
    equation="(PM25_Level_Sensor + PM10_Level_Sensor) > 100",
    metric=Metric.AVERAGE,
    duration=60,
    sleep_time=60,
    severity=Severity.HIGH
  )
)


# Example data
# componentURI = ['Component A', 'Component B', 'Component A', 'Component B', 'Component A', 'Component B', 'Component A', 'Component B', 'Component A', 'Component B']
# timestamps = pd.date_range('2024-01-01', periods=10, freq='D')
# pm25_values = np.array([10, 10, 20, 20, 30, 30, 40, 40, 50, 50])
# pm10_values = np.array([1, 1, 2, 2, 3, 3, 4, 4, 5, 5])


# # df = pd.DataFrame({'PM25_Level_Sensor': pm25_values, 'PM10_Level_Sensor': pm10_values}, index=[componentURI, timestamps])
# df = pd.DataFrame({"componentURI": componentURI, "timestamps": timestamps, 'PM25_Level_Sensor': pm25_values, 'PM10_Level_Sensor': pm10_values})
# df.set_index(['componentURI', 'timestamps'], inplace=True)
# df.sort_index(level=0, inplace=True)

# print(f"df before resampling: {df}")
# grouped = df.groupby(level=0).resample('4d', level=1).mean()  
# print(f"df after resampling: {grouped}")

# rolling_mean = grouped.groupby(level=0, group_keys=False).rolling(window=2).sum()
# rolling_mean = rolling_mean.droplevel(level=0)

# print(f"df after rolling: {rolling_mean}")

# cutoff_time = pd.Timestamp('2024-01-03')

# # Filter out rows where timestamp is before cutoff_time
# filtered_df = rolling_mean.loc[rolling_mean.index.get_level_values('timestamps') >= cutoff_time]

# print(f"df after throwing away: {filtered_df}")

# rolling_mean = rolling_mean.xs(pd.to_datetime("2024-01-03", format='%Y-%m-%d'), level=1)

# # Example assuming 'rolling_mean' has a multi-index with levels ['componentURI', 'timestamps']
# selected_date = pd.to_datetime("2024-01-03", format='%Y-%m-%d')
# subset = rolling_mean.xs(selected_date, level='timestamps')


postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
# logger.info(f"Postgres connection string: {postgres_conn_string}")
conn = psycopg.connect(postgres_conn_string)

# Loads rules.json into postgres then gets rules from postgres
load_rules(conn=conn, rules_json='rules.json')
