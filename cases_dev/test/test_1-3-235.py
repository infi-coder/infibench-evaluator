
import pandas as pd
def f(data_h_df):
    data_h_df['year'] = data_h_df['year'].astype(float).astype(int)

    return data_h_df


data_h_df = pd.DataFrame({'year':['2020.1','2015.8',
                                  '1999.8', '2000.12', '1889.6']})
#print(f1(data_h_df))
from copy import deepcopy

assert all(f(deepcopy(data_h_df)) == transformation(deepcopy(data_h_df)))
