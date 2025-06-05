from fastapi import FastAPI, UploadFile, File, Form
import numpy as np
import cv2
import datetime
import os
from recognizer import ImageEncoder, FaceAuthenticator
from data_update import update_encodings
from logger import logger

encoder = ImageEncoder()
auth = FaceAuthenticator()
app = FastAPI()

pkl_path = "encodings.pkl"

@app.post("/register")
async def register_face(name: str = Form(...), imagefile: UploadFile = File(...)):
    timestamp = datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p")
    try:
        content = await imagefile.read()
        image_np = np.frombuffer(content, np.uint8)
        img_np = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        encodings = encoder.encode(img_np)
        if not encodings:
            raise ValueError("No face detected in the image.")

        encode = {name: encodings}
        update_encodings(encode)

        str_encodings = ' '.join([str(x) for x in encodings[0]])

        output = {
            "message": "Encodings created successfully",
            "encodings": str_encodings,
            "output": True
        }

        logger.info(f"{timestamp}: {output}")
        return output

    except Exception as error:
        logger.error(f"{timestamp} : Error in /register -> {error}")
        return {
            "message": f"Error occurred during registration: {str(error)}",
            "output": False
        }


@app.post("/recognition")
async def recognize_face(imagefile: UploadFile = File(...)):
    timestamp = datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p")
    try:
        content = await imagefile.read()
        image_np = np.frombuffer(content, np.uint8)
        img_np = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        encodings = encoder.encode(img_np)
        if not encodings:
            raise ValueError("No face detected in the image.")

        result = auth.authenticate(encodings[0])

        output = {
            "message": "Recognition completed",
            "result": result
        }

        logger.info(f"{timestamp} : Output -> {output}")
        return output

    except Exception as error:
        logger.error(f"{timestamp} : Error in /recognition -> {error}")
        return {
            "message": f"Error occurred during recognition: {str(error)}",
            "result": None
        }
