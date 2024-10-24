# Anomaly and Fault Detection and Diagnostics

This AFDD system detects unusual patterns (anomalies) from IoT sensors and records them in a PostgreSQL database. Anomalies happen when sensor data goes outside set limits, which are defined by Rules.

## Project Structure

```
- afdd/                         # core application
- neo4j/                        # neo4j setup
- postgres/                     # postgres setup
- sample_data/                  # randomly generates sensor data
- scripts/
    - past_data_analysis.py     # script for analyzing past data within time frame for one rule
    - setup_db.py               # initializes postgres tables for hosted db
- tests/
- kaiterra_example.ttl          # contains an example graph of device and sensor info
- kaiterra_dcoffice.ttl         # contains a graph of device and sensor info for kaiterra devices in the dc office
- Brick.ttl                     # contains Brick schema ontology
```

### Setup:

Create .env file

```
# postgres
POSTGRES_CONNECTION_STRING=<>

# neo4j
NEO4J_URL=
```

### You can use docker to start postgres and neo4j services locally

_This also starts a service to insert sample data into the databases._

```bash
docker compose up
```

### How to run

```bash
poetry install
poetry run afdd
```

## Creating Rules

A rule defines when certain conditions happen, like if sensors detect high CO2 levels. It uses [Brick Schema](https://brickschema.org/) to standardize and track these conditions.

Add rules by editing the [rules.json](./rules.json)

### Structure of a rule

- rule_id: A unique identifier for each rule.
- name: Descriptive name of the rule.
- component_type: The equipment type associated with the sensor, typically Indoor Air Quality (IAQ) sensors.
- sensor_types: List of sensor types involved in the rule.
- description: A brief explanation of when the rule will trigger.
- condition:
  - equation: The mathematical expression for the rule condition, indicating thresholds for sensor readings.
  - metric: Type of calculation, usually "average."
  - duration: The time period over which the sensor readings are averaged, in seconds.
  - sleep_time: The time period before the rule can be re-triggered, in seconds.
