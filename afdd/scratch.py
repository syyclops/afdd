import pandas as pd
# import datetime

df = pd.DataFrame([[1, True], [4, False], [7, True]],
                  index=['cobra', 'viper', 'sidewinder'],
                  columns=['max_speed', 'shield'])

row = df.tail(1)
print(type(row))

# print(df)

# for index, row in df.iterrows():
#     df.loc[index, "max_speed"] = 100
#     print(f"current df: {df}")
#     print(f"current row: {row}")


# anom_df = df.loc[df["shield"] == True, ['max_speed']]
# anom_df['start_time'] = 100


# print(anom_df)
# print(type(anom_df))

# date1 = datetime.datetime.now()
# date2 = datetime.datetime(2023, 7, 3, 13)

# print(date1, date2)
# delta = date2-date1
# print(type(delta))
# convert = delta.seconds
# print(convert, type(convert))

if 4 <= 8 <= 10:
    print('true')