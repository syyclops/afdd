from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
import os
import psycopg
import pandas as pd
import os
from enum import Enum
from typing import List
import numpy as np
from afdd.utils import load_graph
from dotenv import load_dotenv
from afdd.db import load_timeseries, load_rules, get_rules
import neo4j
from neo4j import GraphDatabase
from afdd.utils import load_graph
from dotenv import load_dotenv

# Define the start time and the number of intervals
start_time = pd.Timestamp('2024-07-30 00:00:00')
num_intervals = 8  # Number of time intervals you want

# Create a list of timestamps at 2.5 minute intervals
timestamps = pd.date_range(start=start_time, periods=num_intervals, freq='2.5T')

# Generate random integer CO2 values
# Assuming CO2 values range from 300 to 600 for example
co2_values = [100, np.nan, 200, np.nan, 300, np.nan, 400, np.nan]

# Create the DataFrame
df = pd.DataFrame({
    'CO2': co2_values
}, index=timestamps)

print(f"df: {df}")

rolling_mean = df.rolling(window=2).mean()
print(f"after rolling: {rolling_mean}")