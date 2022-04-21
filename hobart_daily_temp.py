# -*- coding: utf-8 -*-
"""
Created on Mon Apr 11 15:36:33 2022

@author: vivia
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
import statsmodels.api as sm
import statsmodels.formula.api as smf

sns.set_context("paper")
sns.set_style("darkgrid")

ellserie_rd_file = "IDCJAC0010_094029_1800/IDCJAC0010_094029_1800_Data.csv"

#Read in the data and format the datetime component
df = pd.read_csv(ellserie_rd_file)
dates = [datetime.datetime(i.Year,i.Month,i.Day) for idx,i in df.iterrows()]
df.index = dates



temp = df['Maximum temperature (Degree C)']
df['temp'] = temp

plt.plot(temp)
plt.xlabel("Time")
plt.ylabel("Daily average maximum temperature (C)")

df["time"] = np.arange(len(df))/365.25
df["season"] = np.cos(2 * np.pi * (df.time - 15/365.25))

model = smf.ols(formula="temp ~ time + season", data=df)

result = model.fit()

pred = result.predict(df)

plt.plot(pred)