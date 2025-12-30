import pandas as pd
import numpy as np
# scales data to a specific format
from sklearn.preprocessing import MinMaxScaler

# read in movies data from csv
movies_df = pd.read_csv("movies.csv")

# scaling popularity to be between 0 and 1
scaler = MinMaxScaler()
#.fit_transform needs 2D array so we pass in [["popularity"]] and [["vote_avg"]]
popularity_scaled = scaler.fit_transform(movies_df[["popularity"]])
movies_df["popularity"] = popularity_scaled
vote_avg_scaled = scaler.fit_transform(movies_df[["vote_avg"]])
movies_df["vote_avg"] = vote_avg_scaled

# export as new csv with the scaled data
movies_df.to_csv("movies.csv", index=False)
