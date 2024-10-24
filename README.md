# Anomaly Fault Detection and Diagnostics

## Get Started

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
