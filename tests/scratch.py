from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
import os
import psycopg
import pandas as pd
import os
from enum import Enum
from typing import List

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
  sensor_types=["PM2.5_Level_Sensor", "PM10_Level_Sensor"],
  description="Triggers when pm10 counts and pm2.5 counts combined average over 100 micrograms per cubic meter for 1 minute",
  condition=Condition(
    equation="({pm25} + {pm10}) > 100",
    metric=Metric.AVERAGE,
    duration=60,
    sleep_time=60,
    severity=Severity.HIGH
  )
)

data = {"device_id_pm25": [25, 35, 46, 90],
        "device_id_pm10": [45, 50, 60, 43]}

date_range = pd.date_range('2024-07-01', periods=4, freq='H')

# equation_str = "({PM2.5_Level_Sensor} + {PM10_Level_Sensor}) > 100"

df = pd.DataFrame(data, index=date_range)
print(f"df: \n{df}")

sensor_type_map = {"PM2.5_Level_Sensor": "pm25", "PM10_Level_Sensor": "pm10", "Temperature_Sensor": "temp", "CO2_Sensor": "co2", "TVOC_Level_Sensor": "tvoc", "Relative_Humidity_Sensor": "humidity"}

# Create a dictionary to map sensor types to column names
column_name_map = {sensor_type_map[sensor]: f"device_id_{sensor_type_map[sensor]}" for sensor in combo_rule.sensor_types}
hc_column_name_map = {
  "pm10":"device_id_pm10",
  "pm25":"device_id_pm25"
}
print(f"sensor map: {column_name_map}")

# Use the sensor_map to format the equation string
formatted_equation = combo_rule.condition.equation.format(**column_name_map)
print(f"formatted equation: {formatted_equation}")

# Evaluate the formatted equation
df['results'] = df.eval(formatted_equation)

print(df)

# name = 'jessica'
# x = 'print(f"my name is: {name}")'
# # exec(x, name)

# name = 'jessica'
# x = f'print(f"my name is: {name}")'
# exec(x)

# y = "print('my name is:', name)"
# exec(y)

# txt = "For only {price:.2f} dollars!"
# print(txt.format(price = 49))

# # temp = 200
# equation = "{temp} > 100"
# # if exec(equation.format(temp=temp)):
# #   print('anomaly!')

# exec("temp=500\nif equation.format(temp=temp):\n\tprint('anomaly!', temp)")

# string = ""
# for sensor in sensor_types:
#   string += f"{sensor} = \"device_id-{sensor}\","
  
# string = string[:-1]
# print(f"string: {string}")

# # Evaluate the equation string as a Python expression
# df['results'] = df.eval(equation_str.format(exec(string)))

# # df['results'] = df.eval(equation_str.format(pm10))

# print(df['results'])

