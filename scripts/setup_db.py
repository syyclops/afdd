import psycopg
import os
from dotenv import load_dotenv

def main():
  env_files = {
  'local': '.env',
  'dev': '.env.dev'
  }
  load_dotenv()

  try:
    env_file = env_files[os.environ['ENV']]
  except KeyError as e:
    env_file = env_files['local']

  load_dotenv(env_file, override=True)

  postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
  
  conn = psycopg.connect(postgres_conn_string)
  
  create_rules_query = """CREATE TABLE IF NOT EXISTS rules (
  rule_id INT PRIMARY KEY,
  name TEXT NOT NULL,
  sensor_type TEXT NOT NULL,
  description TEXT NOT NULL,
  condition jsonb NOT NULL
  )"""
  create_anomalies_query = """CREATE TABLE IF NOT EXISTS anomalies (
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ NOT NULL,
  rule_id INT,
  anomaly_id INT GENERATED ALWAYS AS IDENTITY,
  value FLOAT NOT NULL,
  timeseriesid TEXT NOT NULL,
  PRIMARY KEY(anomaly_id),
  CONSTRAINT fk_rules
    FOREIGN KEY(rule_id) 
      REFERENCES rules(rule_id)
  );"""

  try:
    with conn.cursor() as cur:
      cur.execute(create_rules_query)
      cur.execute(create_anomalies_query)
      conn.commit()

  except Exception as e:
    raise e

if __name__ == "__main__":
    main()