CREATE TABLE timeseries (
  timeseriesid TEXT NOT NULL,
  value FLOAT NOT NULL,
  ts TIMESTAMPTZ NOT NULL
);

CREATE TABLE anomalies (
  ts TIMESTAMPTZ NOT NULL,
  rule INT NOT NULL,
  name TEXT NOT NULL,
  device TEXT NOT NULL,
  point TEXT NOT NULL,
  value FLOAT NOT NULL
);

CREATE TABLE rules (
  id INT NOT NULL,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  sensors TEXT[] NOT NULL,
)