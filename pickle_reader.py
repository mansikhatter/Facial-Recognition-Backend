# read_encodings_pickle.py

import pickle
import numpy as np

PKL_PATH = "encodings.pkl"

def read_pickle_file(path):
    try:
        with open(path, 'rb') as f:
            data = pickle.load(f)
            return data
    except Exception as e:
        print(f"Error reading pickle file: {e}")
        return {}

if __name__ == "__main__":
    encodings_data = read_pickle_file(PKL_PATH)

    if not encodings_data:
        print("No data found in pickle file.")
    else:
        print("Encodings in pickle file:")
        for emp_id, info in encodings_data.items():
            print(f"Employee ID: {emp_id}")
            print(f"Name: {info.get('name')}")
            print(f"Encoding (first 5 values): {np.array(info.get('encoding'))[:5]}")
            print("-" * 50)
