import face_recognition
import cv2
import pickle
import numpy as np
from logger import logger

class ImageEncoder:
    def __init__(self) -> None:
        pass

    def encode(self, image):
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, boxes)
        return encodings


class FaceAuthenticator:
    def __init__(self):
        self.pkl_path = "encodings.pkl"
        self.threshold = 0.5  # distance threshold for recognition

    def load_encodings(self):
        with open(self.pkl_path, 'rb') as f:
            return pickle.load(f)

    def authenticate(self, input_encoding):
        try:
            encodings_dict = self.load_encodings()
            min_dist = float('inf')
            name = "Unknown"

            for key, enc_list in encodings_dict.items():
                for stored_enc in enc_list:
                    dist = np.linalg.norm(input_encoding - stored_enc)
                    if dist < min_dist:
                        min_dist = dist
                        name = key

            logger.info(f"Detected: {name} with distance {min_dist}")

            if min_dist <= self.threshold:
                return {
                    "name": name,
                    "score": round(1 - min_dist, 4)  # score: closer to 1 is better
                }
            else:
                return {
                    "name": "Unknown",
                    "score": round(1 - min_dist, 4)
                }

        except Exception as error:
            logger.error(f"Error in recognizer.py > authenticate > {error}")
            return {
                "name": "Error",
                "score": None
            }
