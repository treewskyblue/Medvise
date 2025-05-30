from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pickle
import numpy as np
import pandas as pd
import sys
import os
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

logger.debug(f"Python version: {sys.version}")
logger.debug(f"Current working directory: {os.getcwd()}")
logger.debug(f"Directory contents: {os.listdir('.')}")

try:
    # RandomForest Model Load
    logger.debug("Attempting to load model...")
    model_path = "/app/model.pkl"
    logger.debug(f"Model path exists : {os.path.exists(model_path)}")

    if os.path.exists(model_path):
        with open(model_path, "rb") as model_file:
            model = pickle.load(model_file)
        logger.debug("Model loaded successfully")
    else:
        logger.error(f"Model file not found at {model_path}")
        raise FileNotFoundError(f"Model file not found at {model_path}")
    
    # StandardScaler Load
    logger.debug("Attempting to load scaler...")
    scaler_path = "/app/scaler.pkl"
    logger.debug(f"Scaler path exists : {os.path.exists(scaler_path)}")

    if os.path.exists(scaler_path):
        with open(scaler_path, "rb") as scaler_file:
            scaler = pickle.load(scaler_file)
        logger.debug("Scaler loaded successfully")
    else:
        logger.error(f"Scaler file not found at {scaler_path}")
        raise FileNotFoundError(f"Scaler file not found at {scaler_path}")
    
except Exception as e:
    logger.error(f"Error during initialization: {str(e)}")
    logger.exception("Stack trace:")
    raise



output_columns = ["TPNCALCULATEDGLUCOSE", "TPNCALCULATEDPROTEIN", "TPNCALCULATEDLIPID", "TPNCALCULATEDCALORI"]

class PredictionInput(BaseModel):
    data: list

@app.post("/predict")
async def predict(input_data: PredictionInput):
    try:
        logger.debug(f"Received input data: {input_data}")
        df = pd.DataFrame(input_data.data)
        logger.debug(f"Created DataFrame with shape: {df.shape}")

        scaled_data = scaler.transform(df)
        logger.debug("Data scaled successfully")

        predictions = model.predict(scaled_data)
        logger.debug("Predictions made successfully")

        result_df = pd.DataFrame(predictions, columns=output_columns)
        logger.debug(f"Result Dataframe created with shape: {result_df.shape}")

        return result_df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}")
        logger.exception("Stack trace")
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/test")
async def test_endpoint():
    """
    단순 테스트 앤드포인트 - API가 응답하는지 확인
    """
    logger.debug("Test endpoint called")
    return {
        "status": "ok",
        "message": "API is responding",
        "model_loaded": model is not None,
        "scaler_loaded": scaler is not None
    }
    