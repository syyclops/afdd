from timescale import Timescale, TimeseriesData, PointReading
import time
import datetime
import random
from postgres import Postgres

timeseriesid_co2 = ['5e81563a-42ca-4137-9b36-f423a6f27a73-co2', '8493663d-21bf-4fa7-ba8a-163308655319-co2', '9cdcab62-892c-46c8-b3d2-3d525512576a-co2']
timeseriesid_temp = ['5e81563a-42ca-4137-9b36-f423a6f27a73-temperature', '8493663d-21bf-4fa7-ba8a-163308655319-temperature', '9cdcab62-892c-46c8-b3d2-3d525512576a-temperature']

timescale = Timescale(postgres=Postgres())

while True:
  point_reading_list = []
  for id in timeseriesid_co2:
      point_reading_list.append(PointReading(datetime.datetime.now().isoformat(timespec='seconds'), random.randint(0, 2000), id))
  for id in timeseriesid_temp:
      point_reading_list.append(PointReading(datetime.datetime.now().isoformat(timespec='seconds'), random.randint(0, 100), id))
  timescale.insert_timeseries(point_reading_list)
  time.sleep(60)