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
import neo4j
from neo4j import GraphDatabase
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

# Use the sensor_map to format the equation string
formatted_equation = combo_rule.condition.equation.format(**column_name_map)
print(f"formatted equation: {formatted_equation}")

# # Evaluate the formatted equation
# df['results'] = df.eval(formatted_equation)

# # print(df)

env_files = {
'local': '.env',
'dev': '.env.dev'
}
load_dotenv()
try:
  env_file = env_files[os.environ['ENV']]
except Exception:
  env_file = env_files['local']  
load_dotenv(env_file, override=True)

# URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
URI = os.environ['NEO4J_URI']
AUTH = (os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD'])
print(f"URI: {URI}")

query = """
MATCH (c:Class) where c.uri contains "IAQ_Sensor_Equipment" 
    MATCH (c)-[:HAS_BRICK_CLASS]-(comp:Component)
    MATCH (comp)-[:hasPoint]-(p:Point)
    MATCH (comp)-[:isDeviceOf]-(d:Device)
    MATCH (p)-[:HAS_BRICK_CLASS]-(class: Class)
    MATCH (p)-[:hasExternalReference]-(t:TimeseriesReference)
    RETURN p.uri AS point, class.uri AS class, t.hasTimeseriesId AS timeseriesid, d.uri AS deviceURI, comp.uri AS componentURI
"""

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    df = driver.execute_query(query_=query, database_="neo4j", result_transformer_=neo4j.Result.to_df)
    print(df)

# print(load_graph("kaiterra_dcoffice.ttl")["point"])

"""
MATCH (c:Component)-[:hasPoint]-(p:Point)
            MATCH (c)-[:HAS_BRICK_CLASS]-(b:Class) where toLower(b.uri)contains "iaq"
            OPTIONAL MATCH (p)-[:hasUnit]->(u:Unit)
            OPTIONAL MATCH (p)-[:hasExternalReference]->(ts:TimeseriesReference)
            RETURN c as Component, p as Point, u, ts

MATCH (c:Class) where c.uri contains "IAQ_Sensor_Equipment" 
    MATCH (c)-[:HAS_BRICK_CLASS]-(comp:Component)
    MATCH (comp)-[:hasPoint]-(p:Point)
    MATCH (comp)-[:isDeviceOf]-(d:Device)
    MATCH (p)-[:HAS_BRICK_CLASS]-(class: Class)
    MATCH (p)-[:hasExternalReference]-(t:TimeseriesReference)
    RETURN p.uri AS point, class.uri AS class, t.hasTimeseriesId AS timeseriesid, d.uri AS deviceURI, comp.uri AS componentURI


"""
 