from dataclasses import dataclass

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