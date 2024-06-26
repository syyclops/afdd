## Anomaly Fault Detection and Diagnostics

### Description

The anomaly fault detection and diagnostics system detects anomalies in the incoming IoT data and logs them in a PostgreSQL database. Anomalies are defined as events that violate predefined thresholds, which are modeled as Rules. 

### Project Structure

```
- afdd/                     # actual whole program.
- postgres/                 # postgres setup
- sample_data/              # randomly generates sensor data
- tests/
- kaiterra_example.ttl      # contains device and sensor info
- Brick.ttl                 # contains Brick schema ontology
```

### Local Development with Docker

1. Install poetry by running
```pip install poetry``` in your command line

1. [Install Docker](https://docs.docker.com/install) on your local environment

2. Set the required environment variable in .env file,
```POSTGRES_CONNECTION_STRING=<your_connection_string>```

#### RUN

```shell
docker compose build
docker compose up
```
or run the condensed syntax with the daemon

```
docker compose up -d --build
```
