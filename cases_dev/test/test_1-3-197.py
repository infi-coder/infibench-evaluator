import pandas as pd
import numpy as np
def f(df, cName, newCol):
    df[cName] = newCol
    return df


df = pd.DataFrame(np.random.randint(0,100,size=(5,4)),columns=list('ABCD'))

assert f(df, 'B', [1, 2, 3, 4, 5]) == fillColumn(df, 'B', [1, 2, 3, 4, 5])