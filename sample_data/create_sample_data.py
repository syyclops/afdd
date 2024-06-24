import time
import datetime
import random
import psycopg
import os

from afdd.models import PointReading
from afdd.utils import insert_timeseries

timeseriesid_co2 = ['5e81563a-42ca-4137-9b36-f423a6f27a73-co2', '8493663d-21bf-4fa7-ba8a-163308655319-co2', '9cdcab62-892c-46c8-b3d2-3d525512576a-co2']
timeseriesid_temp = ['5e81563a-42ca-4137-9b36-f423a6f27a73-temperature', '8493663d-21bf-4fa7-ba8a-163308655319-temperature', '9cdcab62-892c-46c8-b3d2-3d525512576a-temperature']

# Connect to the database
postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
conn = psycopg.connect(postgres_conn_string)

def main():
  while True:
    point_reading_list = []
    for id in timeseriesid_co2:
        point_reading_list.append(PointReading(ts=datetime.datetime.now().isoformat(timespec='seconds'), value=random.randint(0, 2000), timeseriesid=id))
    for id in timeseriesid_temp:
        point_reading_list.append(PointReading(ts=datetime.datetime.now().isoformat(timespec='seconds'), value=random.randint(0, 100), timeseriesid=id))
    insert_timeseries(conn, point_reading_list)
    time.sleep(60)