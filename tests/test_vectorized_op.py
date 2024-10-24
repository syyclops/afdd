import pandas as pd
import numpy as np

data = {"device_id_pm25": [25, 35, 46, 90], "device_id_pm10": [45, 50, 60, 43]}

date_range = pd.date_range("2024-07-01", periods=4, freq="H")

lambda_eq = lambda pm10, pm25: pm10 + pm25 > 100

df = pd.DataFrame(data, index=date_range)
print(df)

# equation = "np.add({pm10} + {pm25}) > 100"
pm10 = df["device_id_pm10"]
pm25 = df["device_id_pm25"]

equation = f"{pm10} + {pm25} > 100"

df["results"] = exec(equation)

# df['results'] = df.eval(equation.format(pm10="device_id_pm10", pm25="device_id_pm25"))

# equation.format(pm10=df["device_id_pm10"], pm25=df["device_id_pm25"]) # df["device_id_pm10"] + df["device_id_pm25"] > 100
print(df)

# thing that works
df["results"] = df["device_id_pm10"] + df["device_id_pm25"] > 100
