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
