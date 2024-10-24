from dataclasses import dataclass
from typing import List
from enum import Enum
import json
import numpy as np


@dataclass
class Metric(Enum):
    AVERAGE = "average"
    MAX = "max"
    MIN = "min"


@dataclass
class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    LOW = "low"


@dataclass
class Condition:
    equation: str
    metric: Metric
    duration: int  # in seconds
    sleep_time: int  # in seconds
    severity: Severity

    def to_dict(self):
        condition_dict = {
            "metric": self.metric,
            "equation": self.equation,
            "duration": self.duration,
            "sleep_time": self.sleep_time,
            "severity": self.severity,
        }
        return condition_dict


@dataclass
class Metadata:
    """this class defines attributes that describe metadata about Anomalies"""

    device: str
    component: str

    def to_dict(self):
        metadata = {"device": self.device, "component": self.component}
        return metadata


@dataclass
class Anomaly:
    start_time: str
    end_time: str
    rule_id: int
    points: np.ndarray
    metadata: Metadata

    def to_tuple(self):
        anomaly_tuple = (
            self.start_time,
            self.end_time,
            self.rule_id,
            json.dumps(self.points.tolist()),
            json.dumps(self.metadata.to_dict()),
        )
        return anomaly_tuple


@dataclass
class Rule:
    rule_id: int
    name: str
    component_type: str
    sensor_types: List[str]
    description: str
    condition: Condition

    def to_dict(self):
        rule_dict = {
            "rule_id": self.rule_id,
            "name": self.name,
            "component_type": self.component_type,
            "sensor_type": self.sensor_types,
            "description": self.description,
            "condition": self.condition.to_dict(),
        }
        return rule_dict


@dataclass
class PointReading:
    ts: str
    value: float
    timeseriesid: str
