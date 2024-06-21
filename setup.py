from postgres import Postgres
from typing import List
from rule import Rule
from logger import logger

# creating a postgres table for anomalies data
def setup_anomalies_table():
  postgres = Postgres()
  collection_name = 'anomalies'
  """Make sure the timescaledb extension is enabled, the table and indexes are created"""
  try:
    with postgres.cursor() as cur:
      # Create timescaledb extension
      cur.execute('CREATE EXTENSION IF NOT EXISTS timescaledb') 

      # Check if anomalies table exists
      cur.execute(f'SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = \'{collection_name}\')') 
      if not cur.fetchone()[0]: 
        cur.execute(f'CREATE TABLE {collection_name} (ts timestamptz NOT NULL, rule INT NOT NULL, name TEXT NOT NULL, device TEXT NOT NULL, point TEXT NOT NULL, value FLOAT NOT NULL)') # Create anomalies table if it doesn't exist
        cur.execute(f'SELECT create_hypertable(\'{collection_name}\', \'ts\')') # Create hypertable if it doesn't exist
        cur.execute(f'CREATE INDEX {collection_name}_rule_ts_idx ON {collection_name} (rule, ts DESC)') # Create the rule index
        postgres.conn.commit()
  except Exception as e:
    raise e

def setup_rules_table():
  postgres = Postgres()
  collection_name = 'rules'
  """Make sure the timescaledb extension is enabled, the table and indexes are created"""
  try:
    with postgres.cursor() as cur:
      # Create timescaledb extension
      cur.execute('CREATE EXTENSION IF NOT EXISTS timescaledb') 

      # Check if rules table exists
      cur.execute(f'SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = \'{collection_name}\')') 
      if not cur.fetchone()[0]: 
        cur.execute(f'CREATE TABLE {collection_name} (id INT NOT NULL, name TEXT NOT NULL, description TEXT NOT NULL, sensors TEXT[] NOT NULL)') # Create rules table if it doesn't exist
        cur.execute(f'SELECT create_hypertable(\'{collection_name}\', \'id\')') # Create hypertable if it doesn't exist
        cur.execute(f'CREATE INDEX IF NOT EXISTS {collection_name}_id_idx ON {collection_name} (id DESC) ') # Create the rule index
        postgres.conn.commit()
  except Exception as e:
    raise e
  
def load_rules(rule_list: List[Rule]):
  postgres = Postgres()
  
  rule_list = [(rule.id, rule.name, rule.description, rule.sensors_required) for rule in rule_list]
  query = "INSERT INTO rules (id, name, description, sensors) VALUES (%s, %s, %s, %s)"
  try:
    with postgres.cursor() as cur:
      cur.executemany(query, rule_list)
      cur.execute('COMMIT')
      logger.info('Rule successfully loaded. ')
  except Exception as e:
    raise e