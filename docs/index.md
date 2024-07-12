# Anomaly and Fault Detection and Diagnostics

## Description

The anomaly and fault detection and diagnostics (AFDD) system detects anomalies in the incoming IoT devices and logs them in a PostgreSQL database. Anomalies are defined as events that violate predefined thresholds, which are modeled by Rules.

### What is an anomaly and fault detection and diagnostics system?
Many AFDD systems use artificial intelligence or pattern matching to look for patterns in sensor data in order to identify deviations from normal sensor activity, which are classified as "anomalies." This system uses a simple thresholding technique, meaning data is compared to thresholds. For example, a threshold may be defined as 1000 parts per million (ppm) for a rule checking for high carbon dioxide (CO2) levels. With this rule, incoming data from a CO2 sensor would be compared to a threshold of 1000 ppm, and it if exceeds the threshold for longer than a predefined duration, then it will be recorded in a database.

## Project Structure

```
- afdd/                         # core application
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

## How to run

### Setup

Create .env file

```
ENV=<the env file you want to use (i.e. local, dev)> # optional: defaults to local (.env)
POSTGRES_CONNECTION_STRING=<>
```

Install dependencies
```
poetry install
```

### With Docker
[Install Docker](https://docs.docker.com/install) on your local environment
#### To Run Locally
The local environment generates random values for timeseries data.

```shell
docker compose -f docker-compose.local.yml up --build
```

#### To Run in Development Environment
The development environment uses a hosted database of timeseries data. It requires an .env.dev file.

```shell
docker compose -f docker-compose.dev.yml up --build
```

### With Poetry
```
pip install poetry
poetry run afdd
```

### Running with alternative env variables (e.g. setting ENV in the command line)

#### Command prompt
```cmd
SET ENV=dev && poetry run afdd
```
#### Bash
```bash
ENV=dev poetry run afdd
```
If you want to use env files other than local (.env) or dev (.env.dev), add the mapping to the env_files dictionary.