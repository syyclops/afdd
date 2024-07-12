## How to Run
Create .env file

```
ENV=<the env file you want to use (i.e. local, dev)> # optional: defaults to local (.env)
POSTGRES_CONNECTION_STRING=<>
```

Make sure you're running the script from the same folder that your .env files are in.

## Running with alternative .env files

### Command prompt
```cmd
SET ENV=dev 
python ./scripts/setup_db.py
```
### Bash
```bash
ENV=dev ./scripts/setup_db.py
```

## past_data_analysis.py
This script runs a specified rule on timeseries data within a given timeframe and logs the anomalies into the anomalies Postgres. 

Arguments:

* --start_time: a string in iso format (i.e. "2024-06-20T12:35:00")
* --end_time: a string in iso format
* --rule_id: an integer representing the rule to be run
* --graph: a string representing the .ttl filename of the devices

## setup_db.py
This script initializes the rules and anomalies tables in a hosted database. If you are setting up a new database, this script should be run once bbefore running the main application.