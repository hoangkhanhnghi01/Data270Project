# -*- coding: utf-8 -*-
"""Data Cleaning - Weather Dataset from raw.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/122R89lx4pZUa_OT_Ycw_K6GwW7q47dE6
"""

from google.colab import drive

import sqlite3

import os

import math
import geopy.distance

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns

from datetime import datetime

drive.mount('/content/drive')

!ls "/content/drive/MyDrive/SJSU/aaa DATA 270/Data 270 project/Data"

"""## Load Dataset"""

def create_df(table_name, column_names, col_names_str = "*", condition = ""):
    cur.execute(f'SELECT {col_names_str} FROM {table_name} {condition}')
    data = cur.fetchall()
    df = pd.DataFrame(np.array(data), columns = column_names)
    return df

def checkdb(db):
    if os.path.exists(db)==True:
        conn=sqlite3.connect(db)
        con=conn.cursor()
        return con
    else:
        print(".Db does not exist")

directory = "/content/drive/MyDrive/SJSU/aaa DATA 270/Data 270 project/Data"
db = r'/270Database.db'

# check if the db still in the directory folder.
checkdb(directory + db)

# connect sql
con = sqlite3.connect(directory + db)
cur = con.cursor()

# weather table parameters
# weather_table_name = "weather_data_project"
weather_table_name = "weather_data"
weather_col_names = ["STATION", "NAME", "LATITUDE", "LONGITUDE", "DATE", "PRCP", "TAVG", "TMAX", "TMIN"]
weather_col_names_str = "STATION, NAME, LATITUDE, LONGITUDE, DATE, PRCP, TAVG, TMAX, TMIN"

# connect to weather table
weather_df = create_df(weather_table_name, weather_col_names, weather_col_names_str)

# convert data type from string to number
weather_df['LATITUDE'] = pd.to_numeric(weather_df['LATITUDE'])
weather_df['LONGITUDE'] = pd.to_numeric(weather_df['LONGITUDE'])
weather_df['PRCP'] = pd.to_numeric(weather_df['PRCP'])
weather_df['TAVG'] = pd.to_numeric(weather_df['TAVG'])
weather_df['TMIN'] = pd.to_numeric(weather_df['TMIN'])
weather_df['TMAX'] = pd.to_numeric(weather_df['TMAX'])

weather_df

print(f"""
There are {len(weather_df.index)} rows in total.
""")

weather_df.describe().transpose()

"""## Select station that's within the 50mi range."""

def generate_circle(lat, lon, radius, n_points = 100):
    """
    radius - meter
    """
    ls_points = []
    for n in range(n_points):
        # define which of the n_points point we are calculating 
        angle = math.pi * 2 * n / n_points
        
        # x and y axis on 0 centered graph 
        x = math.cos(angle) * radius
        y = math.sin(angle) * radius

        # point = {}
        # point['lat'] = lat + (180 / math.pi) * (y/6378137) # equatorial radius (WGS84)- 6378137 m
        # point['lon'] = lon + (180 / math.pi) * (x/6378137) / math.cos(lat * math.pi / 180)

        point = (lat + (180 / math.pi) * (y/6378137), lon + (180 / math.pi) * (x/6378137) / math.cos(lat * math.pi / 180))

        ls_points.append(point)

    return ls_points

# def calculate_distance(pt1, pt2):
#     x1 = pt1[0]
#     y1 = pt1[1]

#     x2 = pt2[0]
#     y2 = pt2[1]
#     dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
#     return dist

radius = 80467 # in meter (50mi)
san_luis_coords = (37.05721, -121.11608)
san_luis_lat = 37.05721
san_luis_lon = -121.11608
san_luis_circle = generate_circle(san_luis_lat, san_luis_lon, radius, n_points = 200)

san_luis_circle_df = pd.DataFrame(np.array(san_luis_circle), columns = ["latitude", "longitude"])

plot = plt.figure()
plot.set_figwidth(6)
plot.set_figheight(6)
for lat, lon in san_luis_circle:
    plt.scatter(lat, lon)
print("We will select the stations within the range below:")
print()
plt.scatter(san_luis_lat, san_luis_lon)

def select_range(original_df, range):
    """
    range - in miles
    """
    coords_ls = original_df.loc[:, ["LATITUDE", "LONGITUDE"]].values.tolist()

    def is_within_range(pt):
        if geopy.distance.distance(pt, san_luis_coords).mi <= range:
            return True
        else:
            return False

    within_range_bool = list(map(is_within_range, coords_ls))
    return weather_df[[x == True for x in within_range_bool]]

# selecting range. 50mi radius
within_range_df = select_range(weather_df, 50)
within_range_df = within_range_df.reset_index(drop = True)

# formatting DATE column
weather_date = within_range_df["DATE"].tolist()
for i in range(len(weather_date)):
    date_str = weather_date[i].split("/")
    if len(date_str) == 3 :
        if len(date_str[0]) == 1:
            date_str[0] = "0" + date_str[0]
        if len(date_str[1]) == 1:
            date_str[1] = "0" + date_str[1]
        weather_date[i] = date_str[2] + "-" + date_str[0] + "-" + date_str[1] 
within_range_df["DATE"] = weather_date


# sort by station then date.
within_range_df = within_range_df.sort_values(["STATION", "DATE"]).reset_index(drop = True)
within_range_df

"""## Descriptions of within_range_df"""

within_range_df.describe().transpose()

size = within_range_df.groupby(["STATION","NAME"]).size()
size_ls = size.tolist()

station_ls = within_range_df["STATION"].unique().tolist()
print(f"""
There are in total of {len(size)} stations within the range of 50mi of San Luis.

{size}

""")

len(size_ls) == len(station_ls)

"""### Exploration - within_range_df"""

sns.set(rc={"figure.figsize":(25, 10)})
bar_station = sns.histplot(within_range_df["NAME"])
plt.xticks(rotation=90)
bar_station.set_ylabel("days of data count")
bar_station.set_xlabel("Station Names")

print("""
As we can see from the histogram above, there are quite some stations within range of 50mi of San Luis Reservoir that doesn't have a lot of days of data recorded.
One station even has more days of data recorded than it should (3016 days of data, from 01/01/2014 to 04/04/2022). 
Because having many days of missing data in a station will jeopardize the accuracy of our prediction, we are going to eliminate stations that are below a completed rate and only 
keep those that are above the complete rate.
""")

g = sns.PairGrid(within_range_df, hue="NAME")
g.map_diag(sns.histplot)
g.map_offdiag(sns.scatterplot)
g.add_legend()







"""## Selecting stations that have acceptable amount of missing values"""

valid_station_ls = []

total_days = 3016
tmax_completed_rate = 0.9
tmin_completed_rate = 0.9
prcp_completed_rate = 0.9

for i in size_ls:
    # date_strs = final_weather_df[final_weather_df["STATION"] == station_ls[size_ls.index(i)]]["DATE"].tolist()
    # dates = [datetime.strptime(d, "%Y-%m-%d") for d in date_strs]
    # date_ints = [d.toordinal() for d in dates]
    # if len(date_ints) != 0:
    #     if max(date_ints) - min(date_ints) == len(date_ints) - 1:
    if i/total_days >= 0.9: # check date
        if 1 - within_range_df[within_range_df["STATION"] == station_ls[size_ls.index(i)]]["TMAX"].isna().sum()/total_days >= tmax_completed_rate: 
            if 1 - within_range_df[within_range_df["STATION"] == station_ls[size_ls.index(i)]]["TMIN"].isna().sum()/total_days >= tmin_completed_rate:
                if 1 - within_range_df[within_range_df["STATION"] == station_ls[size_ls.index(i)]]["PRCP"].isna().sum()/total_days >= prcp_completed_rate:
                    valid_station_ls.append(station_ls[size_ls.index(i)])

print(f"""
To select a completed rate, we chose {tmax_completed_rate*100}% for TMAX, {tmin_completed_rate*100}% for TMIN, and {prcp_completed_rate*100}% for PRCP. 
The reason being it it's because there's in total of 3016 days from 01/01/2014 to 04/04/2022, {tmin_completed_rate*100}% of completed rate will give us at least 2714 days of data. 
In other words, we will only have at most 301 days  missing data, meaning in average we will have about 3.5 days of missing data per month which would not 
affect the result of our prediction much.
""")

# null values in the first selected station 
within_range_df[within_range_df["STATION"] == valid_station_ls[0]].isna().sum()

# creating df for the selected stations
final_weather_df = within_range_df[within_range_df['STATION'].isin(valid_station_ls)].reset_index(drop = True)
final_weather_df

final_size = final_weather_df.groupby("STATION").size()
print(f"""There are {len(final_size)} stations valid station that meet the following criteria:
missing values of TMAX no more than {round(1-tmax_completed_rate, 2)*100}%
missing values of TMIN no more than {round(1-tmin_completed_rate, 2)*100}%
missing values of PRCP no more than {round(1-prcp_completed_rate, 2)*100}%
""")

# before replacing values: 
final_weather_df.isna().sum()

"""## Final_weather_df description and exploration"""

final_weather_df.describe().transpose()

for i in final_weather_df["NAME"].unique():
    print(i)

sns.set(rc={"figure.figsize":(25, 10)})
bar_station = sns.histplot(final_weather_df["NAME"])
# plt.xticks(rotation=45)
bar_station.set_ylabel("days of data count")
bar_station.set_xlabel("Station Names")

print("""
After we narrowed the stations down, we have 6 valid stations that each of them doesn't have a high rate missing days of data as shown in chart above.
Now, we are going to take a look at each attribute in details.
""")

final_name_ls = final_weather_df["NAME"].unique().tolist()
final_station_ls = final_weather_df["STATION"].unique().tolist()

sns.set_style('darkgrid')
plt.rcParams['figure.figsize']=[15, 15]
j = 1
for i in final_station_ls:
    for col in final_weather_df.columns[5:]:
        plt.subplot(4,2,j)
        sns.lineplot(final_weather_df[final_weather_df["STATION"] == i]['DATE'], final_weather_df[final_weather_df["STATION"] == i][col])
        plt.xlabel(final_name_ls[final_station_ls.index(i)])
        plt.ylabel(col)
        if j + 1 == 9:
            break
        j += 1
plt.show()

final_weather_df[final_weather_df["STATION"] == 'USC00045118']['DATE']

sns.set_style('darkgrid')
plt.rcParams['figure.figsize']=[23, 23]
j=1
for i in final_weather_df.columns[5:]:
    plt.subplot(4,2,j)
    sns.histplot(final_weather_df[i])
    plt.xlabel(i,fontsize=15)
    plt.ylabel('Density',fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    j+=1
plt.show()

print("""
According to the bar chart above, PRCP appears to be exponentially distributed. 
TMIN, and TAVG appear to be about normally distributed while TMAX seems bimodal distributed.
""")

sns.set_style('darkgrid')
plt.rcParams['figure.figsize']=[23, 23]
j=1
for i in final_weather_df.columns[5:]:
    plt.subplot(4,2,j)
    sns.boxplot(final_weather_df[i])
    plt.xlabel(i,fontsize=15)
    plt.xticks(fontsize=15)
    plt.yticks(fontsize=15)
    j+=1
plt.show()

print("""
Box plot for each attributes also look good. There's in fact some outliers but they are all within the acceptable range.
""")

final_weather_df["STATION"]

# check if dates are consecutive

# date_strs = final_weather_df[final_weather_df["STATION"] == "USC00045933"]["DATE"].tolist()
# dates = [datetime.strptime(d, "%Y-%m-%d") for d in date_strs]

# date_ints = [d.toordinal() for d in dates]

# if len(date_ints) == 1:
#     print("unique")
# elif max(date_ints) - min(date_ints) == len(date_ints) - 1:
#     print("consecutive")
# else:
#     print("not consecutive")

final_station_ls = final_weather_df["STATION"].unique().tolist()
final_size

final_weather_df.isna().sum()

final_weather_df_pivot = final_weather_df.pivot(index = "DATE", columns = "STATION", values = ["PRCP", "TAVG", "TMAX", "TMIN"])
final_weather_df_pivot["TMAX"] = final_weather_df_pivot["TMAX"].interpolate(method ='linear', limit_direction ='forward')
final_weather_df_pivot["PRCP"] = final_weather_df_pivot["PRCP"].interpolate(method ='linear', limit_direction ='forward')
final_weather_df_pivot["TMIN"] = final_weather_df_pivot["TMIN"].interpolate(method ='linear', limit_direction ='forward')

final_weather_df_pivot.isna().sum()

# replace null values linearly.
tavg_dict = {}
for station in final_weather_df_pivot["TAVG"].columns:
    tavg_values = []
    for i in range(3016):
        tavg_values.append((final_weather_df_pivot["TMAX"][station][i]+final_weather_df_pivot["TMIN"][station][i])/2)
    tavg_dict[station] = tavg_values

for key, values in tavg_dict.items():
    final_weather_df_pivot["TAVG"][key] = values

final_weather_df_pivot.isna().sum()

final_weather_df_pivot

# for index, row in final_weather_df.iterrows():
#     next_index = index + 1 
#     next_next_index = next_index + 1
#     fourth_index = next_next_index +1
#     fifth_index = fourth_index + 1
#     sixth_index = fifth_index + 1
#     seventh_index = sixth_index + 1

#     last_index = index - 1

#     if np.isnan(row[7]): # the value is null
#         if np.isnan(final_weather_df.iloc[next_index, 7]) == True: # the next value is null
#             if np.isnan(final_weather_df.iloc[next_next_index, 7]) == True: # the 3rd value is null
#                 if np.isnan(final_weather_df.iloc[fourth_index, 7]) == True: # the 4th values is null
#                     if np.isnan(final_weather_df.iloc[fifth_index, 7]) == True: # 5 consecutive nulls
#                         if np.isnan(final_weather_df.iloc[sixth_index, 7]) == True: # 6 consecutive nulls
#                             average = (final_weather_df.iloc[last_index, 7] + final_weather_df.iloc[seventh_index, 7])/2 
#                             final_weather_df.iloc[index, 7] = average
#                             final_weather_df.iloc[next_index, 7] = average
#                             final_weather_df.iloc[next_next_index, 7] = average
#                             final_weather_df.iloc[fourth_index, 7] = average
#                             final_weather_df.iloc[fifth_index, 7] = average
#                             final_weather_df.iloc[sixth_index, 7] = average
#                         else: #5 null values
#                             average = (final_weather_df.iloc[last_index, 7] + final_weather_df.iloc[sixth_index, 7])/2 
#                             final_weather_df.iloc[index, 7] = average
#                             final_weather_df.iloc[next_index, 7] = average
#                             final_weather_df.iloc[next_next_index, 7] = average
#                             final_weather_df.iloc[fourth_index, 7] = average
#                             final_weather_df.iloc[fifth_index, 7] = average
#                     else: # 4 null values
#                         average = (final_weather_df.iloc[last_index, 7] + final_weather_df.iloc[fifth_index, 7])/2 
#                         final_weather_df.iloc[index, 7] = average
#                         final_weather_df.iloc[next_index, 7] = average
#                         final_weather_df.iloc[next_next_index, 7] = average
#                         final_weather_df.iloc[fourth_index, 7] = average
#                 else: # 3 null values
#                     average = (final_weather_df.iloc[last_index, 7] + final_weather_df.iloc[fourth_index, 7])/2 
#                     final_weather_df.iloc[index, 7] = average
#                     final_weather_df.iloc[next_index, 7] = average
#                     final_weather_df.iloc[next_next_index, 7] = average
#             else: # there's 2 consecutive nulls
#                 average = (final_weather_df.iloc[last_index, 7] + final_weather_df.iloc[next_next_index, 7])/2
#                 final_weather_df.iloc[index, 7] = (average + final_weather_df.iloc[last_index, 7])/2
#                 final_weather_df.iloc[next_index, 7] = (average + final_weather_df.iloc[next_next_index, 7])/2
#         else: # there's 1 null, no consecutive nulls
#             final_weather_df.iloc[index, 7] = (final_weather_df.iloc[last_index, 7] + final_weather_df.iloc[next_index, 7])/2
        



#     if np.isnan(row[8]): # the value is null
#         if np.isnan(final_weather_df.iloc[next_index, 8]) == True: # the next value is null
#             if np.isnan(final_weather_df.iloc[next_next_index, 8]) == True: # the 3rd value is null
#                 if np.isnan(final_weather_df.iloc[fourth_index, 8]) == True: # the 4th values is null
#                     if np.isnan(final_weather_df.iloc[fifth_index, 8]) == True: # 5 consecutive nulls
#                         if np.isnan(final_weather_df.iloc[sixth_index, 8]) == True: # 6 consecutive nulls
#                             average = (final_weather_df.iloc[last_index, 8] + final_weather_df.iloc[seventh_index, 8])/2 
#                             final_weather_df.iloc[index, 8] = average
#                             final_weather_df.iloc[next_index, 8] = average
#                             final_weather_df.iloc[next_next_index, 8] = average
#                             final_weather_df.iloc[fourth_index, 8] = average
#                             final_weather_df.iloc[fifth_index, 8] = average
#                             final_weather_df.iloc[sixth_index, 8] = average
#                         else: #5 null values
#                             average = (final_weather_df.iloc[last_index, 8] + final_weather_df.iloc[sixth_index, 8])/2 
#                             final_weather_df.iloc[index, 8] = average
#                             final_weather_df.iloc[next_index, 8] = average
#                             final_weather_df.iloc[next_next_index, 8] = average
#                             final_weather_df.iloc[fourth_index, 8] = average
#                             final_weather_df.iloc[fifth_index, 8] = average
#                     else: # 4 null values
#                         average = (final_weather_df.iloc[last_index, 8] + final_weather_df.iloc[fifth_index, 8])/2 
#                         final_weather_df.iloc[index, 8] = average
#                         final_weather_df.iloc[next_index, 8] = average
#                         final_weather_df.iloc[next_next_index, 8] = average
#                         final_weather_df.iloc[fourth_index, 8] = average
#                 else: # 3 null values
#                     average = (final_weather_df.iloc[last_index, 8] + final_weather_df.iloc[fourth_index, 8])/2 
#                     final_weather_df.iloc[index, 8] = average
#                     final_weather_df.iloc[next_index, 8] = average
#                     final_weather_df.iloc[next_next_index, 8] = average
#             else: # there's 2 consecutive nulls
#                 average = (final_weather_df.iloc[last_index, 8] + final_weather_df.iloc[next_next_index, 8])/2
#                 final_weather_df.iloc[index, 8] = (average + final_weather_df.iloc[last_index, 8])/2
#                 final_weather_df.iloc[next_index, 8] = (average + final_weather_df.iloc[next_next_index, 8])/2
#         else: # there's 1 null, no consecutive nulls
#             final_weather_df.iloc[index, 8] = (final_weather_df.iloc[last_index, 8] + final_weather_df.iloc[next_index, 8])/2
#     final_weather_df.iloc[index, 6] = (final_weather_df.iloc[index, 7] + final_weather_df.iloc[index, 8]) / 2


#     if np.isnan(row[5]): # the value is null
#         if np.isnan(final_weather_df.iloc[next_index, 5]) == True: # the next value is null
#             if np.isnan(final_weather_df.iloc[next_next_index, 5]) == True: # the 3rd value is null
#                 if np.isnan(final_weather_df.iloc[fourth_index, 5]) == True: # the 4th values is null
#                     if np.isnan(final_weather_df.iloc[fifth_index, 5]) == True: # 5 consecutive nulls
#                         if np.isnan(final_weather_df.iloc[sixth_index, 5]) == True: # 6 consecutive nulls
#                             average = (final_weather_df.iloc[last_index, 5] + final_weather_df.iloc[seventh_index, 5])/2 
#                             final_weather_df.iloc[index, 5] = average
#                             final_weather_df.iloc[next_index, 5] = average
#                             final_weather_df.iloc[next_next_index, 5] = average
#                             final_weather_df.iloc[fourth_index, 5] = average
#                             final_weather_df.iloc[fifth_index, 5] = average
#                             final_weather_df.iloc[sixth_index, 5] = average
#                         else: # 5 null values
#                             average = (final_weather_df.iloc[last_index, 5] + final_weather_df.iloc[sixth_index, 5])/2 
#                             final_weather_df.iloc[index, 5] = average
#                             final_weather_df.iloc[next_index, 5] = average
#                             final_weather_df.iloc[next_next_index, 5] = average
#                             final_weather_df.iloc[fourth_index, 5] = average
#                             final_weather_df.iloc[fifth_index, 5] = average
#                     else: # 4 null values
#                         average = (final_weather_df.iloc[last_index, 5] + final_weather_df.iloc[fifth_index, 5])/2 
#                         final_weather_df.iloc[index, 5] = average
#                         final_weather_df.iloc[next_index, 5] = average
#                         final_weather_df.iloc[next_next_index, 5] = average
#                         final_weather_df.iloc[fourth_index, 5] = average
#                 else: # 3 null values
#                     average = (final_weather_df.iloc[last_index, 5] + final_weather_df.iloc[fourth_index, 5])/2 
#                     final_weather_df.iloc[index, 5] = average
#                     final_weather_df.iloc[next_index, 5] = average
#                     final_weather_df.iloc[next_next_index, 5] = average
#             else: # there's 2 consecutive nulls
#                 average = (final_weather_df.iloc[last_index, 5] + final_weather_df.iloc[next_next_index, 5])/2
#                 final_weather_df.iloc[index, 5] = (average + final_weather_df.iloc[last_index, 5])/2
#                 final_weather_df.iloc[next_index, 5] = (average + final_weather_df.iloc[next_next_index, 5])/2
#         else: # there's 1 null, no consecutive nulls
#             final_weather_df.iloc[index, 5] = (final_weather_df.iloc[last_index, 5] + final_weather_df.iloc[next_index, 5])/2











# # to replace the rest of the null
# a = final_weather_df.iloc[14734:14765,:]
# avg_tmin = a["TMIN"].mean()
# avg_tmax = a["TMAX"].mean()
# final_weather_df['TMIN'] = final_weather_df['TMIN'].replace(np.nan, avg_tmin)
# final_weather_df['TMAX'] = final_weather_df['TMAX'].replace(np.nan, avg_tmax)
# final_weather_df.iloc[14744:14755, :]["TAVG"] = (final_weather_df.iloc[14744:14755, :]["TMAX"] + final_weather_df.iloc[14744:14755, :]["TMIN"])/2

# final_weather_df.isna().sum()

# sns.set_style('darkgrid')
# plt.rcParams['figure.figsize']=[23, 23]
# j=1
# for i in final_weather_df.columns[5:]:
#     plt.subplot(4,2,j)
#     sns.boxplot(final_weather_df[i])
#     plt.xlabel(i,fontsize=15)
#     plt.xticks(fontsize=15)
#     plt.yticks(fontsize=15)
#     j+=1
# plt.show()

# g = sns.PairGrid(final_weather_df, hue="NAME")
# g.map_diag(sns.histplot)
# g.map_offdiag(sns.scatterplot)
# g.add_legend()



"""## Combined table"""

# combined_df = pd.read_csv(directory + "/COMBINED_DATA.csv")

# combined_df

# g = sns.PairGrid(combined_df)
# g.map_diag(sns.histplot)
# g.map_offdiag(sns.scatterplot)
# g.add_legend()

# from sklearn.decomposition import PCA
# from sklearn.preprocessing import StandardScaler, Normalizer

# x = combined_df.iloc[:, 1:].values
# # standardization, 
# x = StandardScaler().fit_transform(x)

# pca = PCA(n_components = 4)
# principalComponents = pca.fit_transform(x)
# principalDf = pd.DataFrame(data = principalComponents
#              , columns = ['principal component 1', 'principal component 2', 'principal component 3', 'principal component 4'])

# principalDf

# pca.explained_variance_ratio_

# from functools import reduce

# round(reduce(lambda x, y: x + y, pca.explained_variance_ratio_.tolist()), 2)

# sns.lineplot(combined_df["DATE"], combined_df.iloc[:, 1:25])

# combined_df.iloc[:, 1:25]

