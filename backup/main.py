from fastapi import FastAPI,Request,File,UploadFile,Form
import numpy as np
import cv2
import datetime
import os
import pickle
from recognizer import ImageEncoder,FaceAuthenticator
from data_update import update_encodings
import pandas as pd
import face_recognition
from logger import logger

encoder = ImageEncoder()
auth = FaceAuthenticator()
app = FastAPI()

pkl_path = "encodings.pkl"

@app.post("register")
async def register_face(name: str, imagefile:UploadFile(...)):
    try:
        timestamp = datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p")
        content_assignment = await imagefile.read()
        image_np = np.frombuffer(content_assignment, np.uint8)
        img_np = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        encodings = encoder.encode(img_np)
        str_encodings = ' '.join([str(x) for x in encodings[0]])

        encode = {name:encodings}

        update_encodings(encode)

        output = {"message":"Encodings created successfully",
                  "encodings":str_encodings,
                  "output":True}
        
        logger.info(f"{timestamp}:{output}")

        return output
    
    except Exception as error:
        print("Error in main.py > /register > register_face --> ",error)
        logger.error(f"{timestamp} : {error}")


@app.post("/recognition")
async def recognize_face(imagefile: UploadFile=File(...)):
    try:
        content_assignment = await imagefile.read()
        image_np = np.frombuffer(content_assignment, np.uint8)
        img_np = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        encodings = encoder.encode(img_np)[0]

        result = auth.authenticate(encodings)

        output = {
            "message": "Recognition completed",
            "result": result
        }

        logger.info(f"Output Generated - > {output}")
        return output
    
    except Exception as error:
        logger.error(f"Error - > {output}")
        print(f"Error in main.py > /recognition > recognize_face > {error}")
    
