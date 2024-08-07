CREATE TABLE timeseries (
  timeseriesid TEXT NOT NULL,
  value FLOAT NOT NULL,
  ts TIMESTAMPTZ NOT NULL
);

CREATE TABLE rules (
  rule_id INT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  condition JSONB NOT NULL,
  component_type TEXT NOT NULL,
  sensor_types JSONB NOT NULL
);

CREATE TABLE anomalies (
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ NOT NULL,
  rule_id INT,
  anomaly_id INT GENERATED ALWAYS AS IDENTITY,
  metadata JSONB NOT NULL,
  points JSONB NOT NULL,
  PRIMARY KEY(anomaly_id),
  CONSTRAINT fk_rules
    FOREIGN KEY(rule_id) 
      REFERENCES rules(rule_id)
);

