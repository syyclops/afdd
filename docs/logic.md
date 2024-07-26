# How it works

### Set Up

* If you're running docker compose with a local database:

    If there is no existing database, Postgres will automatically initialize the timeseries, anomalies, and rules tables. The timeseries database will be populated with sample data of random values for three different CO2 sensors. It sends up data every fifteen seconds.

* If you're running with a hosted postgres database:
    
    At the moment, the anomalies and rules tables need to be created by running the `setup_db.py` script, which can be found in the `scripts` directory. More information on running scripts can be found [here](scripts.md).

- Example Timeseries Table:

    | timeseriesid                                     | value | ts                    |
    | -------------------------------------------------| ----- | ----------------------|
    | 8493663d-21bf-4fa7-ba8a-163308655319-co2         |   949 | 2024-06-26 20:16:37+00|
    | 9cdcab62-892c-46c8-b3d2-3d525512576a-temperature |    13 | 2024-06-26 20:16:37+00|
    | 5e81563a-42ca-4137-9b36-f423a6f27a73-temperature |     6 | 2024-06-26 20:16:37+00|
    | 9cdcab62-892c-46c8-b3d2-3d525512576a-co2         |   206 | 2024-06-26 20:16:37+00|
    |5e81563a-42ca-4137-9b36-f423a6f27a73-co2          |   990 | 2024-06-26 20:16:37+00|
    |8493663d-21bf-4fa7-ba8a-163308655319-temperature  |    67 | 2024-06-26 20:16:37+00|

- A json file that contains two rules that detect high CO2 at different severities are loaded into the rules table in Postgres.

- Graph of components corresponding to a certain class (e.g. IAQ) is loaded into a dataframe from neo4j.


point |class| timeseriesid | deviceURI | componentURI
------|-----|--------------|-----------|------------------------
https://syyclops.com/setty/dcoffice/point/5e81563a-42ca-4137-9b36-f423a6f27a73-co2| https://brickschema.org/schema/Brick#CO2_Sensor |5e81563a-42ca-4137-9b36-f423a6f27a73-co2 | https://syyclops.com/setty/dcoffice/device/5e81563a-42ca-4137-9b36-f423a6f27a73 | https://syyclops.com/setty/dcoffice/component/examplekaiterrasensedge
https://syyclops.com/setty/dcoffice/point/5e81563a-42ca-4137-9b36-f423a6f27a73-pm10 | https://brickschema.org/schema/Brick#PM10_Level_Sensor  | 5e81563a-42ca-4137-9b36-f423a6f27a73-pm10 | https://syyclops.com/setty/dcoffice/device/5e81563a-42ca-4137-9b36-f423a6f27a73 | https://syyclops.com/setty/dcoffice/component/examplekaiterrasensedge


### Anomaly Detection

Each rule has a `sleep_time` attribute which determines how often the rule is run against the set of timeseries data from that past `sleep_time` cycle.

After the first iteration, each rule is on its own timer. This is implemented using `async`, so the rules don't truly run in parallel, but it allows them to have independent sleep timers. Every time a rule runs, the following procedure occurs:

- Gets timeseries data from the past cycle from all the sensors that match the rule's `sensor_type` and puts it into a dataframe. Each column corresponds with one sensor's data and is labeled its timeseries id, and the timestamp is the index:

   | ts                | 5e81563a-42ca-4137-9b36-f423a6f27a73-co2 |8493663d-21bf-4fa7-ba8a-163308655319-co2 |
    | -----------------------| ----- | ------|
    | 2024-06-26 20:16:37+00 |   949 | NaN|
    | 2024-06-26 20:16:37+15 |    NaN | 245|
    | 2024-06-26 20:16:42+00 |     6 | NaN|
    | 2024-06-26 20:16:42+15 |   NaN | 206|
    |2024-06-26 20:16:47+00  |   990 | NaN|
    |2024-06-26 20:16:47+15  |    NaN | 67|


- Analyzes data
    - If `metric = AVERAGE`, data is analyzed using rolling means.
        - `AVERAGE` is the only metric currently implemented.
        - When a rule is run, `start_time = now - sleep_time - overlap` so that all values are accounted for in rolling averages.
    - Normalizes timestamps of timeseries data to intervals of one fourth of rule's `duration`.
        - For example, during the analysis of a rule with `duration` 600 seconds (10 minutes), the data will be resampled to intervals of 150 seconds (2.5 minutes). Given the resampled timestamps to be 12:30:00, 12:32:50, 12:35:00, datapoints at 12:31:20 and 12:34:15 would be resampled to 12:30:00 and 12:35:00 respectively, and 12:32:30 would be filled with a NaN value.
    - Takes rolling averages of length `duration` for all of the ids.
        - The first few rolling means after start time that are calculated from partial windows are removed from the dataframe so that they are not analyzed.
    - Goes through each id column and compares the means to the rule's threshold. This makes a new column called results full of booleans representing whether the data violated the threshold.

        | ts                | 5e81563a-42ca-4137-9b36-f423a6f27a73-co2 |results
        | -----------------------| ------ | ------|
        | 2024-06-26 12:30:00+00 |   1200 |   True|
        | 2024-06-26 12:32:30+00 |   1300 |   True|
        | 2024-06-26 12:35:00:+00|    990 |  False|

    - Puts the true rows into a dataframe called `anomaly_df`.
    - Goes through each row in `anomaly_df` and combines anomalies with overlapping times so that only one anomaly gets logged. When anomalies are combined, the weighted average of the values of the anomalies is taken based on how long the anomalies were.
    - Appends anomalies from anomaly dataframe to a list.
- Append the list of anomalies found to the Postgres anomalies table.