import datetime
import random
import psycopg
import os
import asyncio
import logging

from afdd.models import PointReading
from afdd.utils import insert_timeseries

timeseriesid_co2_1 = ['8493663d-21bf-4fa7-ba8a-163308655319-co2', '9cdcab62-892c-46c8-b3d2-3d525512576a-co2', '5e81563a-42ca-4137-9b36-f423a6f27a73-co2']

# Connect to the database
postgres_conn_string = os.environ['POSTGRES_CONNECTION_STRING']
conn = psycopg.connect(postgres_conn_string)

async def append_co2(ids, time):
  while True:
    point_reading_list = []
    for id in ids:
      point_reading_list.append(PointReading(ts=datetime.datetime.now().isoformat(timespec='seconds'), value=random.randint(0, 2000), timeseriesid=id))
    insert_timeseries(conn, point_reading_list)
    logging.info(f"successfully appended at {datetime.datetime.now()} for the {time} second loop")
    await asyncio.sleep(time)

async def start():
  await asyncio.gather(append_co2(timeseriesid_co2_1, 10))

def main():
  asyncio.run(start())