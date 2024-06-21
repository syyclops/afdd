from dataclasses import dataclass
from typing import List

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