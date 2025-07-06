from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os

#uvicorn main_old:app --reload

app = FastAPI()

# Enable CORS so the React frontend can access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specify ["http://localhost:5173"] for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FOLDER = "data"

@app.get("/data/{symbol}")
def get_data(symbol: str, bar_size: str = "1_hour"):
    duration = "5_D"
    # Convert "1 hour" to "1_hour" format for filename
    bar_size_formatted = bar_size.replace(" ", "_")
    filename = f"{symbol.upper()}_{bar_size_formatted}.csv"
    filepath = os.path.join(DATA_FOLDER, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="CSV not found")

    df = pd.read_csv(filepath, parse_dates=["date"])
    df["time"] = df["date"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    result = df[["time", "open", "high", "low", "close", "volume"]].to_dict(orient="records")
    return result

@app.get("/metadata")
def get_metadata():
    metadata_path = os.path.join(DATA_FOLDER, "metadata.json")
    if not os.path.exists(metadata_path):
        return {}

    with open(metadata_path, "r") as f:
        metadata = pd.read_json(f)
    
    return metadata.to_dict(orient="records")