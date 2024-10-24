import pandas as pd
from afdd.main import analyze_data
from afdd.models import Rule, Condition, Metric, Severity
from datetime import datetime, timedelta, timezone

def test_analyze_data():
    graph = pd.DataFrame({
        "point": ["https://syyclops.com/point1", "https://syyclops.com/point2"],
        "class": ["CO2_Sensor", "Temperature_Sensor"],
        "timeseriesid": ["https://syyclops.com/ts1", "https://syyclops.com/ts2"],
        "deviceURI": ["https://syyclops.com/device1", "https://syyclops.com/device2"],
        "componentURI": ["https://syyclops.com/component1", "https://syyclops.com/component2"],
    })

    # Create timezone-aware timestamps
    tz = timezone.utc
    now = datetime.now(tz)
    timeseries_data = pd.DataFrame({
        "componentURI": ["https://syyclops.com/component1", "https://syyclops.com/component1", "https://syyclops.com/component2"],
        "ts": [
            now - timedelta(minutes=12),  # 12 minutes ago
            now - timedelta(minutes=11),  # 11 minutes ago
            now - timedelta(minutes=10),  # 10 minutes ago
        ],
        "value": [1200, 1300, 300]  # Values for CO2_Sensor and Temperature_Sensor
    }).set_index(["componentURI", "ts"])  # Create MultiIndex DataFrame

    # Define a rule that should trigger an anomaly when the CO2 levels are between 1000 and 1500
    rule = Rule(
        rule_id=1,
        name="CO2 High",
        component_type="CO2_Sensor_Equipment",
        sensor_types=["CO2_Sensor"],
        description="Triggers when average CO2 level is between 1000 and 1500 ppm for 10 minutes",
        condition=Condition(
            equation="1000 <= value <= 1500",  # Trigger when CO2 level is between 1000 and 1500
            metric=Metric.AVERAGE,
            duration=600,  # 10 minutes duration
            sleep_time=1800,
            severity=Severity.HIGH
        )
    )

    # Set start_time to a time before the timeseries data (e.g., 15 minutes ago)
    start_time = (now - timedelta(minutes=25)).strftime("%Y-%m-%dT%H:%M:%S")

    anomalies = analyze_data(graph=graph, timeseries_data=timeseries_data, rule=rule, start_time=start_time)

    # We expect 1 anomaly, as the CO2 levels were between 1000 and 1500
    assert len(anomalies) == 1


