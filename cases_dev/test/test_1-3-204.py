
import pandas as pd
import numpy as np
from copy import deepcopy
def f(df):
    avg = df.groupby("t", sort=False)["p"].mean().reset_index(name="mean")
    return avg
df = pd.DataFrame({"t":[1,2,3,3,2,1,3,2,3,1],
                     "p":[1,2,3,4,5,6,7,8,9,10],
                        "x":[1,2,3,4,5,6,7,8,9,10],
                            "y":[1,2,3,4,5,6,7,8,9,10],
                                "z":[1,2,3,4,5,6,7,8,9,10]})

assert all(f(deepcopy(df)) == renameDataFrame(deepcopy(df)))