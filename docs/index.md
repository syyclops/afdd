# Anomaly and Fault Detection and Diagnostics

This AFDD system detects unusual patterns (anomalies) from IoT sensors and records them in a PostgreSQL database. Anomalies happen when sensor data goes outside set limits, which are defined by Rules.

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

A rule defines when certain conditions happen, like if sensors detect high CO2 levels. It uses [Brick Schema](https://brickschema.org/) to standardize and track these conditions, as well as COBie and BACnet.

Add rules by editing the [rules.json](./rules.json)

### Structure of a rule

- rule_id: A unique identifier for each rule.
- name: Name of the rule.
- component_type: The Brick class that represents the equipment type
- sensor_types: List of Brick classes for the points that are needed for this rule
- description: A brief explanation of when the rule will trigger.
- condition:
  - equation: The mathematical expression for the rule condition, indicating thresholds for sensor readings.
  - metric: "average", "max", "min"
  - duration: The time period over which the sensor readings are averaged, in seconds.
  - sleep_time: The time period before the rule can be re-triggered, in seconds.

#### Example Rule

```json
{
  "rule_id": 1,
  "name": "High CO2",
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
```
