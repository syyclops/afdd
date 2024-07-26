from dotenv import load_dotenv
import os
from neo4j import GraphDatabase
from afdd.db import load_graph_neo4j

env_files = {
  'local': '.env',
  'dev': '.env.dev'
}
load_dotenv()
try:
  env_file = env_files[os.environ['ENV']]
except Exception:
  env_file = env_files['local']  

load_dotenv(env_file, override=True)

neo4j_uri = os.environ['NEO4J_URI']
neo4j_user = os.environ['NEO4J_USER']
neo4j_password = os.environ['NEO4J_PASSWORD']

neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password), max_connection_lifetime=200)
neo4j_driver.verify_connectivity()

df = load_graph_neo4j(neo4j_driver, "IAQ_Sensor_Equipment")
print(type(df["class"].to_list()[0]))
print(df.to_string())

