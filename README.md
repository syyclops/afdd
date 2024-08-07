# Anomaly Fault Detection and Diagnostics

## How to run:

### Setup:

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
### To Run Locally:
The local environment generates random values for timeseries data.

```shell
docker compose -f docker-compose.local.yml up --build
```

### To Run in Development Environment:
The development environment uses a hosted database of timeseries data. It requires an .env.dev file.

```shell
docker compose -f docker-compose.dev.yml up --build
```

### With Poetry
```
poetry run afdd
```
If you want to use env files other than local (.env) or dev (.env.dev), add the mapping to the env_files dictionary.

### Running with alternative env variables (e.g. setting ENV in the command line)
### Command prompt
```cmd
SET ENV=dev
poetry run afdd
```
### Bash
```bash
ENV=dev poetry run afdd
```
