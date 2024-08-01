### Rule
Represents a rule. Contains a `to_dict()` method to easily make it into a json object. Each rule has a unique rule_id, which links the Postgres `rules` and `anomalies` table. It acts as the primary key to the `rules` table and foreign key to `anomalies` table. `component_type`, `sensor_type`, and `equation` should all use only the Brick label and not the entire URI. Here is an example of our current rules table: 

rule_id | name         | component_type | sensor_types | description                                                    | condition
--------|--------------|-|------------|----------------------------------------------------------------|------------------------------------------------------------------------------------------------------
1       | CO2 Too High | IAQ_Sensor_Equipment | ['CO2_Sensor']  | Triggers when average CO2 level is between 1000 and 1500 ppm for 5 minutes | {"equation": "1000 < CO2_Sensor < 1500", metric": "average", "duration": 300, "severity": "high"}
2 | PM Sum Test Rule | IAQ_Sensor_Equipment | ['PM10_Level_Sensor', 'PM25_Level_Sensor']  | Triggers when sum of PM10 and PM2.5 sensor readings exceeds 60 ppm | {"equation": "PM10_Level_Sensor + PM25_Level_Sensor < 60", "metric": "average", "duration": 300, "severity": "critical"}

### Metric
An enum class for defining different ways to sample our timeseries data according to specific rule. For example, setting the metric to `AVERAGE` will calculate the average of every window of data of length `rule.condition.duration` before analyzing it. `AVERAGE` is the only metric currently implemented.

### Severity
An enum class for defining different severity levels of rules. For example, a rule checking for CO2 levels of over 1000 ppm might have a severity of HIGH, while a rule checking for over 1500 ppm might have a severity level of CRITICAL.

### Condition
Represents the specific details of a rule. Contains a `to_dict()` method to easily make it into a json object. 
* equation: an inequality representing the threhold of the rule, can include multiple operators
* sleep_time: how often the rule is run
* duration: the window size of the rolling average, the length of time that is considered an anomaly

### Metadata
Represents metadata about anomalies. Device and component should both be URIs.

### Anomaly
Represents an anomaly. Contains a `to_tuple()` method to easily format and insert into Postgres table:

start_time              |        end_time        | rule_id | anomaly_id   |               points               | metadata
------------------------|------------------------|---------|------|------------------------------------------|----------
 2024-06-27 14:05:19+00 | 2024-06-27 14:06:19+00 |       2 |        235 | ["https://syyclops.com/setty/dcoffice/point/5e81563a-42ca-4137-9b36-f423a6f27a73-co2"] | {"device": "https://syyclops.com/setty/dcoffice/device/5e81563a-42ca-4137-9b36-f423a6f27a73", "component": "https://syyclops.com/setty/dcoffice/component/kaiterrasensedgemini3"}
 2024-06-27 14:04:19+00 | 2024-06-27 14:05:19+00 |       1 |        234 | ["https://syyclops.com/setty/dcoffice/point/9cdcab62-892c-46c8-b3d2-3d525512576a-co2"] | {"device": "https://syyclops.com/setty/dcoffice/device/9cdcab62-892c-46c8-b3d2-3d525512576a, "component": "https://syyclops.com/setty/dcoffice/component/kaiterrasensedgemini4"}
 2024-06-27 13:58:19+00 | 2024-06-27 13:59:19+00 |       2 |        233 | ["https://syyclops.com/setty/dcoffice/point/8493663d-21bf-4fa7-ba8a-163308655319-co2"] | {"device": "https://syyclops.com/setty/dcoffice/device/8493663d-21bf-4fa7-ba8a-163308655319", "component": "https://syyclops.com/setty/dcoffice/component/kaiterrasensedgemini"}

 `anomaly_id` is not an attribute of the Anomaly class, but it is automatically generated and stored in the Postgres table. It is the primary key of the `anomalies` table.

### PointReading
Defines the format of individual timeseries data being inserted into the Postgres `timeseries` table. Only used for creating sample data.