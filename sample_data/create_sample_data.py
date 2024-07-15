import datetime
import random
import psycopg
import os
import asyncio
import logging

from afdd.models import PointReading
from afdd.db import insert_timeseries

timeseriesid_co2_1 = ['8493663d-21bf-4fa7-ba8a-163308655319-co2', '9cdcab62-892c-46c8-b3d2-3d525512576a-co2', '5e81563a-42ca-4137-9b36-f423a6f27a73-co2']
timeseriesid_pm10 = ['8493663d-21bf-4fa7-ba8a-163308655319-pm10']
timeseriesid_pm25 = ['8493663d-21bf-4fa7-ba8a-163308655319-pm25']

# Connect to the database
postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
conn = psycopg.connect(postgres_conn_string)

async def append_sample_data(id_list, time, min, max):
  """
  Inserts random values between min and max to a timeseries table every [time] seconds for the given ids in id_list
  """
  while True:
    point_reading_list = []
    for id in id_list:
      point_reading_list.append(PointReading(ts=datetime.datetime.now().isoformat(timespec='seconds'), value=random.randint(min, max), timeseriesid=id))
    insert_timeseries(conn, point_reading_list)
    logging.info(f"successfully appended at {datetime.datetime.now()} for the {time} second loop")
    await asyncio.sleep(time)

async def start():
  coro_list = []
  coro_list.append(append_sample_data(timeseriesid_co2_1, 10, 40, 60))
  coro_list.append(append_sample_data(timeseriesid_pm10, 10, 40, 60))
  coro_list.append(append_sample_data(timeseriesid_pm25, 10, 15, 30))

  await asyncio.gather(*coro_list)

def main():
  asyncio.run(start())