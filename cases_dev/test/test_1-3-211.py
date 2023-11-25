import pandas as pd
import numpy as np
def f(df):
    df.loc[df["type"]=="deposit", "balance"] = df.loc[df["type"]=="deposit"].groupby("exchange", sort=False)["value"].apply(np.cumsum)
    df = df.fillna(method='ffill')
    return df

df1=pd.DataFrame()
df1['exchange'] = [1, 1, 1, 2, 3]
df1['type'] = ['deposit', 'deposit', 'trade', 'deposit', 'deposit']
df1['value'] = [10, 10, 30, 40, 100]

df2=pd.DataFrame()
df2['exchange'] = [1, 1, 1, 2, 3]
df2['type'] = ['deposit', 'deposit', 'deposit', 'deposit', 'deposit']
df2['value'] = [10, 10, 30, 40, 100]

df3=pd.DataFrame()
df3['exchange'] = [1, 1, 1, 1, 1]
df3['type'] = ['deposit', 'deposit', 'deposit', 'deposit', 'deposit']
df3['value'] = [10, 50, 30, 40, 100]

df4=pd.DataFrame()
df4['exchange'] = [2, 1, 2, 1, 2]
df4['type'] = ['deposit', 'deposit', 'trade', 'deposit', 'deposit']
df4['value'] = [110, 50, 30, 40, 100]

assert all(f(df1) == aggregation(df1))
assert all(f(df2) == aggregation(df2))
assert all(f(df3) == aggregation(df3))
assert all(f(df4) == aggregation(df4))