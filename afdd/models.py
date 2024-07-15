from dataclasses import dataclass
from typing import List
from typing import TypedDict
from enum import Enum

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
  metric: Metric
  threshold: int | tuple
  operator: str
  duration: int # in seconds
  sleep_time: int # in seconds
  severity: Severity
  
  def to_dict(self):
    condition_dict = {'metric': self.metric, 
                      'threshold': self.threshold, 
                      'operator': self.operator, 
                      'duration': self.duration,
                      'sleep_time': self.sleep_time,
                      'severity': self.severity}
    return condition_dict

@dataclass
class Metadata:
  """ this class defines attributes that describe metadata about Anomalies """
  device: str
  component: str

  def to_dict(self):
    metadata = {
      'device': self.device,
      'component': self.component}
    return metadata


@dataclass
class Anomaly:
  start_time: str
  end_time: str
  rule_id: int
  value: float
  timeseriesid: str
  metadata: Metadata

  def to_tuple(self):
    anomaly_tuple = (self.start_time, 
                     self.end_time, 
                     self.rule_id, 
                     self.value, 
                     self.timeseriesid, 
                     self.metadata.to_dict())
    return anomaly_tuple
  
@dataclass
class Rule:
  rule_id: int
  name: str
  sensor_type: str
  description: str
  condition: Condition
  
  def to_dict(self):
    rule_dict = {'rule_id': self.rule_id, 
            'name': self.name, 
            'sensor_type': self.sensor_type,
            'description': self.description, 
            'condition': self.condition.to_dict()}
    return rule_dict
  
@dataclass
class PointReading:
  ts: str
  value: float
  timeseriesid: str