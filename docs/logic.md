## How it works

The application currently consists of 3 containers: postgres, sample_data, and afdd. 

### Set Up

* Postgres is initialized and sets up the timeseries, anomalies, and rules tables. The anomalies and rules tables associate anomaly and rule objects by the rule_id key.

* Sample data is randomly generated with random values every 15 seconds for 6 sensors (3 CO2 and 3 temperature) and inserted into the PostgreSQL timeseries table.

    - Example Timeseries Table:

        | timeseriesid                                     | value | ts                    |
        | -------------------------------------------------| ----- | ----------------------|
        | 8493663d-21bf-4fa7-ba8a-163308655319-co2         |   949 | 2024-06-26 20:16:37+00|
        | 9cdcab62-892c-46c8-b3d2-3d525512576a-temperature |    13 | 2024-06-26 20:16:37+00|
        | 5e81563a-42ca-4137-9b36-f423a6f27a73-temperature |     6 | 2024-06-26 20:16:37+00|
        | 9cdcab62-892c-46c8-b3d2-3d525512576a-co2         |   206 | 2024-06-26 20:16:37+00|
        |5e81563a-42ca-4137-9b36-f423a6f27a73-co2          |   990 | 2024-06-26 20:16:37+00|
        |8493663d-21bf-4fa7-ba8a-163308655319-temperature  |    67 | 2024-06-26 20:16:37+00|

- Two rule objects that detect high CO2 at different severities are created, loaded into json, and loaded into the rules table in Postgres. 

- A dataframe of the points' information, such as the associated devices, timeseries ids, and classes, is generated from the graph of kaiterra_example.ttl and Brick.ttl.

### Anomaly Detection

Every minute, the main program detects anomalies in the past minute of sample timeseries data. After loading rules and a dataframe of points, the program enters the following loop:

- Gets timeseries data from the last minute that matches the CO2 brick class and puts it into a dataframe. Each column corresponds with one sensor's data and is labeled its timeseries id. 
    - Note: This works now because all devices sends up data at the same interval. 
- Analyzes data

    ```
    for each column in the timeseries dataframe:
        for each rule in the list of rules:
            data sample value is calculated according to the rule's metric (i.e. average, min, or max)
            then compared using specified operation to the threshold predefined in the rule's model
            if anomaly found, add it to a list of anomalies
    ```

- Append the list of anomalies found to the Postgres anomalies table
