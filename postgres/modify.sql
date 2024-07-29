ALTER TABLE rules
ADD component_type TEXT NOT NULL DEFAULT 'IAQ_Sensor_Equipment'

ALTER TABLE rules
ADD sensor_types JSONB NOT NULL DEFAULT '[]';

update rules
set sensor_types = CASE
    WHEN sensor_type = 'CO2_Sensor' THEN '["CO2_Sensor"]'::jsonb
    WHEN sensor_type = 'PM10_Level_Sensor' THEN '["PM10_Level_Sensor"]'::jsonb 
    WHEN sensor_type = 'PM25_Level_Sensor' THEN '["PM25_Level_Sensor"]'::jsonb 
    ELSE sensor_types
END;

ALTER TABLE rules
DROP COLUMN sensor_type;

update rules
set condition = CASE
    WHEN rule_id = 1 THEN '{
         "equation": "1000 < CO2_Sensor < 1500",
         "metric": "average",
         "duration": 600,
         "sleep_time": 1800,
         "severity": "high"
      }'::jsonb
    WHEN rule_id = 2 THEN '{
         "equation": "CO2_Sensor > 1500",
         "metric": "average",
         "duration": 600,
         "sleep_time": 1800,
         "severity": "critical"
      }'::jsonb
    WHEN rule_id = 3 THEN '{
         "equation": "PM10_Level_Sensor > 150",
         "metric": "average",
         "duration": 86400,
         "sleep_time": 86400,
         "severity": "high"
      }'::jsonb  
    WHEN rule_id = 4 THEN '{
         "equation": "PM25_Level_Sensor > 35",
         "metric": "average",
         "duration": 86400,
         "sleep_time": 86400,
         "severity": "high"
      }'::jsonb  
END;

ALTER TABLE anomalies
DROP COLUMN value;

ALTER TABLE anomalies
ADD points JSONB NOT NULL DEFAULT '[]';

UPDATE anomalies
SET points = CASE
    WHEN timeseriesid = '8493663d-21bf-4fa7-ba8a-163308655319-co2' THEN '["https://syyclops.com/setty/dcoffice/point/8493663d-21bf-4fa7-ba8a-163308655319-co2"]'::jsonb
    WHEN timeseriesid = '5e81563a-42ca-4137-9b36-f423a6f27a73-co2' THEN '["https://syyclops.com/setty/dcoffice/point/5e81563a-42ca-4137-9b36-f423a6f27a73-co2"]'::jsonb
    WHEN timeseriesid = 'e4848531-911e-41f3-8b7a-4895a871e49b-co2' THEN '["https://syyclops.com/setty/dcoffice/point/e4848531-911e-41f3-8b7a-4895a871e49b-co2"]'::jsonb
    WHEN timeseriesid = '9cdcab62-892c-46c8-b3d2-3d525512576a-co2' THEN '["https://syyclops.com/setty/dcoffice/point/9cdcab62-892c-46c8-b3d2-3d525512576a-co2"]'::jsonb
    WHEN timeseriesid = '9cdcab62-892c-46c8-b3d2-3d525512576a-pm25' THEN '["https://syyclops.com/setty/dcoffice/point/9cdcab62-892c-46c8-b3d2-3d525512576a-pm25"]'::jsonb
END;

ALTER TABLE anomalies
DROP COLUMN timeseriesid;