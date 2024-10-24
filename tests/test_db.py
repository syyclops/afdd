import pytest
import psycopg
from neo4j import GraphDatabase
import pandas as pd
from afdd.db import (
    insert_timeseries,
    load_rules,
    get_rules,
    load_timeseries,
)
from afdd.models import PointReading
import json
from datetime import datetime
from urllib.parse import urlparse

# Fixtures for PostgreSQL and Neo4j connections
@pytest.fixture(scope="session")
def pg_conn():
    postgres_conn_string = "postgresql://postgres:postgres@localhost:5432/postgres"
    conn = psycopg.connect(postgres_conn_string)
    conn.autocommit = True  # Enable autocommit mode
    yield conn
    conn.close()

@pytest.fixture(scope="function", autouse=True)
def clean_pg(pg_conn):
    with pg_conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE timeseries CASCADE;")
        cur.execute("TRUNCATE TABLE anomalies CASCADE;")
        cur.execute("TRUNCATE TABLE rules CASCADE;")

@pytest.fixture(scope="function")
def neo4j_driver():
    neo4j_conn_string = urlparse("bolt://neo4j:neo4j-password@localhost:7687")
    driver = GraphDatabase.driver(
        f"{neo4j_conn_string.scheme}://{neo4j_conn_string.hostname}:{neo4j_conn_string.port}",
        auth=(neo4j_conn_string.username, neo4j_conn_string.password),
        max_connection_lifetime=200,
    )
    yield driver
    # Teardown: Clean up data
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    driver.close()

def test_insert_timeseries(pg_conn):
    # Arrange
    data = [
        PointReading(ts='2024-10-24T12:00:00', value=100.0, timeseriesid='ts1'),
        PointReading(ts='2024-10-24T12:01:00', value=101.0, timeseriesid='ts1'),
    ]
    # Act
    insert_timeseries(pg_conn, data)
    # Assert
    with pg_conn.cursor() as cur:
        cur.execute("SELECT ts, value, timeseriesid FROM timeseries ORDER BY ts")
        results = cur.fetchall()
    expected_results = [
        (datetime.fromisoformat('2024-10-24T12:00:00+00:00'), 100.0, 'ts1'),
        (datetime.fromisoformat('2024-10-24T12:01:00+00:00'), 101.0, 'ts1'),
    ]
    assert results == expected_results

def test_load_rules(pg_conn, tmp_path):
    # Arrange
    rules_json_path = tmp_path / "rules.json"
    rules_data = [
        {
            "rule_id": 1,
            "name": "Test Rule",
            "component_type": "TestComponent",
            "sensor_types": ["SensorType1"],
            "description": "Test description",
            "condition": {
                "equation": "value > 100",
                "metric": "average",
                "duration": 600,
                "sleep_time": 1800,
                "severity": "high"
            }
        }
    ]
    rules_json_path.write_text(json.dumps(rules_data))
    # Act
    load_rules(pg_conn, str(rules_json_path))
    # Assert
    with pg_conn.cursor() as cur:
        cur.execute("SELECT * FROM rules")
        results = cur.fetchall()
    assert len(results) == 1
    rule_row = results[0]
    assert rule_row[0] == 1  # rule_id
    assert rule_row[1] == "Test Rule"  # name

def test_get_rules(pg_conn):
    # Arrange
    with pg_conn.cursor() as cur:
        cur.execute("""
        INSERT INTO rules (rule_id, name, component_type, sensor_types, description, condition)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            1,
            "Test Rule",
            "TestComponent",
            json.dumps(["SensorType1"]),
            "Test description",
            json.dumps({
                "equation": "value > 100",
                "metric": "average",
                "duration": 600,
                "sleep_time": 1800,
                "severity": "high"
            }),
        ))
    # Act
    rules = get_rules(pg_conn)
    # Assert
    assert len(rules) == 1
    rule = rules[0]
    assert rule.rule_id == 1
    assert rule.name == "Test Rule"

def test_load_timeseries(pg_conn):
    # Arrange
    with pg_conn.cursor() as cur:
        cur.execute("""
        INSERT INTO timeseries (ts, value, timeseriesid)
        VALUES (%s, %s, %s), (%s, %s, %s)
        """, (
            '2024-10-24T12:10:00', 100.0, 'ts1',
            '2024-10-24T12:20:00', 101.0, 'ts1',
        ))
    graph = pd.DataFrame({
        "class": ["SensorType1"],
        "timeseriesid": ["ts1"],
        "componentURI": ["component1"],
    })
    start_time = "2024-10-24T12:00:00"
    end_time = "2024-10-24T13:00:00"
    brick_list = ["SensorType1"]
    # Act
    df_pivoted = load_timeseries(pg_conn, graph, start_time, end_time, brick_list)
    # Assert
    assert isinstance(df_pivoted, pd.DataFrame)
    assert not df_pivoted.empty
    expected_columns = ["SensorType1"]
    assert list(df_pivoted.columns.get_level_values(0)) == expected_columns
