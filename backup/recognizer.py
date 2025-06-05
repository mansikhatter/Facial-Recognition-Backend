import face_recognition
import cv2
import pickle
import numpy as np
import pandas as pd
from logger import logger

result = []

class ImageEncoder():

    def __init__(self) -> None:
        pass

    def encode(self,image):
        rgb = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_encodings(rgb, boxes)
        print(encodings)
        return encodings
    
class FaceAuthenticator:

    def __init__(self):
        self.pkl_path = "encodings.pkl"

    def load_encodings(self):
        with open(self.pkl_path,'rb') as f:
            encodings_dict = pickle.load(f)
        return encodings_dict
    
    try:
        def authenticate(self,input_encodings):
            encodings_dict = self.load_encodings()
            min_dist = float('inf')
            name = ""
            for key,value in encodings_dict.items():
                for enc in value:
                    dist=np.linalg.norm(enc-input_encodings)
                    if dist<min_dist:
                        min_dist=dist
                        name=key

            print("Name",name)
            logger.info(f"Detected Name > {name}")
            return name
        
    except Exception as error:

        logger.error(f"Error in recognizer.py > /FaceAuthenticator > authenticate > {error}")
        print(f'Error in recognizer.py > /FaceAuthenticator > authenticate > {error}')