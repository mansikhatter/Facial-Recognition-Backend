import pickle
import os

pkl_path = "encodings.pkl"

def create_pickle_file():
    if not os.path.exists(pkl_path):
        with open(pkl_path, "wb") as f:
            pickle.dump({}, f)
        print(f"{pkl_path} created with empty dictionary.")
    else:
        print(f"{pkl_path} already exists.")

if __name__ == "__main__":
    create_pickle_file()
