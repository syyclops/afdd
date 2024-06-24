from dataclasses import dataclass
from typing import List
from typing import TypedDict

@dataclass
class Anomaly:
  name: str
  rule: int
  timestamp: str
  device: str
  point: str
  value: float

  def to_dict(self):
    anomaly_dict = {'timestamp': self.timestamp,
                    'rule': self.rule,
                    'name': self.name, 
                    'device': self.device, 
                    'point': self.point,
                    'value': self.value}
    return anomaly_dict
  
  def to_tuple(self):
    anomaly_tuple = (self.timestamp, self.rule, self.name, self.device, self.point, self.value)
    return anomaly_tuple
  
@dataclass
class Rule:
  name: str
  id: int
  description: str
  sensors_required: List[str]
  
  def to_dict(self):
    dict = {'id': self.id, 
            'name': self.name, 
            'description': self.description, 
            'sensors': self.sensors_required}
    return dict
  
@dataclass
class PointReading:
  ts: str
  value: float
  timeseriesid: str

class TimeseriesData(TypedDict):
  data: List[PointReading]
  timeseriesid: str