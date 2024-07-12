### Rule
Represents a rule. Contains a `to_dict()` method to easily make it into a json object. Each rule has a unique rule_id, which links the Postgres `rules` and `anomalies` table. It acts as the primary key to the `rules` table and foreign key to `anomalies` table. Here is an example of our current rules table: 

rule_id | name         | sensor_type | description                                                    | condition
--------|--------------|-------------|----------------------------------------------------------------|------------------------------------------------------------------------------------------------------
1       | CO2 Too High | CO2_Sensor  | Triggers when average CO2 level exceeds 1000 ppm for 5 minutes | {"metric": "average", "duration": 300, "operator": "in", "severity": "high", "threshold": [1000, 1500]}
2 | CO2 Critical | CO2_Sensor  | Triggers when average CO2 level exceeds 1500 ppm for 5 minutes | {"metric": "average", "duration": 300, "operator": ">", "severity": "critical", "threshold": 1500}

### Metric
An enum class for defining different ways to sample our timeseries data according to specific rule. For example, setting the metric to `AVERAGE` will calculate the average of every window of data of length `rule.duration` before analyzing it. `AVERAGE` is the only metric currently implemented.

### Severity
An enum class for defining different severity levels of rules. For example, a rule checking for CO2 levels of over 1000 ppm might have a severity of HIGH, while a rule checking for over 1500 ppm might have a severity level of CRITICAL.

### Condition
Represents the specific details of a rule. Contains a `to_dict()` method to easily make it into a json object. 
* Threshold: can either be an integer or a tuple containing two integers that represent a range. 
* sleep_time: how often the rule is run
* duration: the window size of the rolling average, the length of time that is considered an anomaly
the length of time from which the average is calculated from 

### Anomaly
Represents an anomaly. Contains a `to_tuple()` method to easily format and insert into Postgres table:

start_time              |        end_time        | rule_id | anomaly_id |  value  |               timeseriesid               
------------------------|------------------------|---------|------------|---------|------------------------------------------
 2024-06-27 14:05:19+00 | 2024-06-27 14:06:19+00 |       2 |        235 | 1577.25 | 5e81563a-42ca-4137-9b36-f423a6f27a73-co2
 2024-06-27 14:04:19+00 | 2024-06-27 14:05:19+00 |       1 |        234 |    1207 | 9cdcab62-892c-46c8-b3d2-3d525512576a-co2
 2024-06-27 13:58:19+00 | 2024-06-27 13:59:19+00 |       2 |        233 |  1525.5 | 8493663d-21bf-4fa7-ba8a-163308655319-co2
 2024-06-27 13:56:19+00 | 2024-06-27 13:57:19+00 |       1 |        232 |    1486 | 8493663d-21bf-4fa7-ba8a-163308655319-co2
 2024-06-27 13:55:19+00 | 2024-06-27 13:56:19+00 |       2 |        231 |    1563 | 8493663d-21bf-4fa7-ba8a-163308655319-co2
 2024-06-27 13:54:19+00 | 2024-06-27 13:55:19+00 |       1 |        230 |    1252 | 5e81563a-42ca-4137-9b36-f423a6f27a73-co2

 `anomaly_id` is not an attribute of the Anomaly class, but it is automatically generated and stored in the Postgres table. It is the primary key of the `anomalies` table.

### PointReading
Defines the format of individual timeseries data being inserted into the Postgres `timeseries` table. Only used for creating sample data.