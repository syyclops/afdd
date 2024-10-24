import pandas as pd
from afdd.utils import load_graph, round_time
from afdd.db import load_timeseries, append_anomalies
from afdd.main import analyze_data
from afdd.models import Rule, Condition, Metric, Severity, Anomaly, Metadata
import psycopg
import os
from afdd.logger import logger
from datetime import timedelta
from typing import List
from rdflib import URIRef


def main():
    combo_rule = Rule(
        rule_id=5,
        name="pm rule",
        component_type="IAQ sensor",
        sensor_types=["PM25_Level_Sensor", "PM10_Level_Sensor"],
        description="Triggers when pm10 counts and pm2.5 counts combined average over 70 micrograms per cubic meter for 1 minute",
        condition=Condition(
            equation="cc",
            metric=Metric.AVERAGE,
            duration=60,
            sleep_time=60,
            severity=Severity.HIGH,
        ),
    )

    co2_rule = Rule(
        rule_id=1,
        name="co2 too high",
        component_type="IAQ sensor",
        sensor_types=["CO2_Sensor"],
        description="Triggers when pm10 counts and pm2.5 counts combined average over 70 micrograms per cubic meter for 1 minute",
        condition=Condition(
            equation="1500 > CO2_Sensor > 1000",
            metric=Metric.AVERAGE,
            duration=60,
            sleep_time=60,
            severity=Severity.HIGH,
        ),
    )

    sensor_list = co2_rule.sensor_types

    postgres_conn_string = os.environ["POSTGRES_CONNECTION_STRING"]
    print(postgres_conn_string)
    conn = psycopg.connect(postgres_conn_string)

    graph = load_graph(devices="kaiterra_dcoffice.ttl")

    ts_data = load_timeseries(
        conn=conn,
        graphInfoDF=graph,
        start_time="2024-07-25T17:55:00",
        end_time="2024-07-25T18:00:00",
        brick_list=sensor_list,
    )

    list = analyze_data(
        graph=graph,
        timeseries_data=ts_data,
        rule=co2_rule,
        start_time="2024-07-25T17:55:00",
    )
    logger.info(f"anomaly list:\n{list}")

    append_anomalies(conn=conn, anomaly_list=list)


if __name__ == "__main__":
    main()
