import pytest
import json
import psycopg
from unittest.mock import Mock, mock_open, patch
from contextlib import contextmanager

from afdd.models import Rule, Metric, Severity
from afdd.db import load_rules, get_rules

# Test data
SAMPLE_RULES_JSON = """[
    {
        "rule_id": 1,
        "name": "CO2 High",
        "component_type": "IAQ_Sensor_Equipment",
        "sensor_types": ["CO2_Sensor"],
        "description": "Triggers when average CO2 level is between 1000 and 1500 ppm for 10 minutes",
        "condition": {
            "equation": "1000 < CO2_Sensor < 1500",
            "metric": "average",
            "duration": 600,
            "sleep_time": 1800,
            "severity": "high"
        }
    }
]"""

@pytest.fixture
def mock_connection():
    """Create a mock database connection with proper context manager handling"""
    conn = Mock()
    cursor = Mock()
    
    @contextmanager
    def cursor_context():
        yield cursor
    
    conn.cursor.return_value = cursor
    conn.cursor.side_effect = cursor_context
    return conn, cursor

def test_load_rules_new_rule(mock_connection):
    """Test loading a new rule that doesn't exist in the database"""
    conn, cursor = mock_connection
    
    # Mock cursor.fetchall() to return empty list (rule doesn't exist)
    cursor.fetchall.return_value = []
    
    # Mock open() to return our sample JSON
    with patch('builtins.open', mock_open(read_data=SAMPLE_RULES_JSON)):
        load_rules(conn=conn, rules_json="dummy_path.json")
    
    # Verify that INSERT query was called with correct parameters
    insert_calls = cursor.execute.call_args_list
    assert len(insert_calls) >= 2  # One for SELECT, one for INSERT
    
    # Check the INSERT query parameters
    insert_query = insert_calls[1][0][0]
    insert_params = insert_calls[1][0][1]
    assert "INSERT INTO rules" in insert_query
    assert insert_params[0] == 1  # rule_id
    assert insert_params[1] == "CO2 High"  # name
    assert insert_params[2] == "IAQ_Sensor_Equipment"  # component_type
    assert json.loads(insert_params[3]) == ["CO2_Sensor"]  # sensor_types

def test_load_rules_existing_rule(mock_connection):
    """Test loading a rule that already exists in the database"""
    conn, cursor = mock_connection
    
    # Mock cursor.fetchall() to return existing rule
    cursor.fetchall.return_value = [(1,)]
    
    # Mock open() to return our sample JSON
    with patch('builtins.open', mock_open(read_data=SAMPLE_RULES_JSON)):
        load_rules(conn=conn, rules_json="dummy_path.json")
    
    # Verify that only SELECT was called, not INSERT
    insert_calls = cursor.execute.call_args_list
    assert len(insert_calls) == 1
    assert "SELECT * FROM rules WHERE rule_id = 1" in insert_calls[0][0][0]

def test_load_rules_invalid_json(mock_connection):
    """Test loading invalid JSON data"""
    conn, _ = mock_connection
    
    with pytest.raises(json.JSONDecodeError):
        with patch('builtins.open', mock_open(read_data="invalid json")):
            load_rules(conn=conn, rules_json="dummy_path.json")

def test_get_rules_success(mock_connection):
    """Test successfully retrieving rules from the database"""
    conn, cursor = mock_connection
    
    # Mock the database response
    cursor.fetchall.return_value = [(
        1,  # rule_id
        "CO2 High",  # name
        "Triggers when average CO2 level is between 1000 and 1500 ppm for 10 minutes",  # description
        {  # condition
            "equation": "1000 < CO2_Sensor < 1500",
            "metric": "average",
            "duration": 600,
            "sleep_time": 1800,
            "severity": "high"
        },
        "IAQ_Sensor_Equipment",  # component_type
        ["CO2_Sensor"]  # sensor_types
    )]
    
    rules = get_rules(conn=conn)
    
    assert len(rules) == 1
    assert isinstance(rules[0], Rule)
    assert rules[0].rule_id == 1
    assert rules[0].name == "CO2 High"
    assert rules[0].component_type == "IAQ_Sensor_Equipment"
    assert rules[0].condition.equation == "1000 < CO2_Sensor < 1500"
    assert rules[0].condition.metric == Metric.AVERAGE
    assert rules[0].condition.severity == Severity.HIGH

def test_get_rules_database_error(mock_connection):
    """Test handling of database errors when retrieving rules"""
    conn, cursor = mock_connection
    
    # Mock a database error
    cursor.execute.side_effect = psycopg.Error("Database error")
    
    with pytest.raises(psycopg.Error):
        get_rules(conn=conn)

def test_get_rules_empty_database(mock_connection):
    """Test retrieving rules from an empty database"""
    conn, cursor = mock_connection
    
    # Mock an empty database response
    cursor.fetchall.return_value = []
    
    rules = get_rules(conn=conn)
    
    assert len(rules) == 0
    assert isinstance(rules, list)