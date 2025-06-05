import pickle
import pandas as pd

pkl_path = "encodings.pkl"

def update_encodings(encodings_dict):

    data = pd.read_pickle(pkl_path)
    data.update(encodings_dict)

    with open(pkl_path,"wb") as f:
        pickle.dump(data,f)

encodings_dict = {}