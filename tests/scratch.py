from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
import os
import psycopg
import pandas as pd
import os
from enum import Enum
from typing import List
import neo4j
from neo4j import GraphDatabase
import numpy as np
from afdd.utils import load_graph
from dotenv import load_dotenv

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
components = ['Component A', 'Component B', 'Component A', 'Component B', 'Component A', 'Component B', 'Component A', 'Component B', 'Component A', 'Component B']
timestamps = pd.date_range('2024-01-01', periods=10, freq='D')
pm25_values = np.array([10, 10, 20, 20, 30, 30, 40, 40, 50, 50])
pm10_values = np.array([10, 10, 20, 20, 30, 30, 40, 40, 50, 50])

df = pd.DataFrame({'components': components, 'PM25_Level_Sensor': pm25_values, 'PM10_Level_Sensor': pm10_values}, index=timestamps)
print("new_df before rolling: \n", df)
df = df.groupby('components').rolling(2).sum()
print("new_df after rolling: \n", df)
print("new df indices: ", df.index.to_list())

# Evaluate the equation
df['results'] = df.eval(combo_rule.condition.equation)
print("new_df with results column:\n", df)