import pandas as pd
import pytz
from copy import deepcopy
def f(df):
    df['date'] = df['date'].dt.tz_localize(None)
    return df

ny_tz = pytz.timezone('America/New_York')
datetimes = [pd.Timestamp("2023-10-31 12:00:00", tz=ny_tz), pd.Timestamp("2023-11-01 15:30:00", tz=ny_tz)]

# 创建 DataFrame
df = pd.DataFrame({'date': datetimes})

assert removeTimezone(deepcopy(df)).equals(f(deepcopy(df)))