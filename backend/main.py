from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import re
import os

app = FastAPI(
    title="Fake Job Detector API",
    description="ML-powered fake job detection",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # change to your Vercel URL after deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = "model/model.pkl"
pipeline   = None


@app.on_event("startup")
def load_model():
    global pipeline
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Model not found at {MODEL_PATH}. Run training/train.py first.")
    pipeline = joblib.load(MODEL_PATH)
    print("Model loaded successfully.")


class JobInput(BaseModel):
    title:        str = ""
    company:      str = ""
    location:     str = ""
    salary:       str = ""
    description:  str = ""
    requirements: str = ""
    benefits:     str = ""


class PredictionOutput(BaseModel):
    prediction:  str
    confidence:  float
    label:       str
    message:     str


def clean_text(text: str) -> str:
    if not text:
        return ''
    text = text.lower()
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


@app.get("/")
def root():
    return {"status": "running", "model": "loaded" if pipeline else "not loaded"}


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": pipeline is not None}


@app.post("/predict", response_model=PredictionOutput)
def predict(job: JobInput):
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not job.title.strip() and not job.description.strip():
        raise HTTPException(status_code=400, detail="Title or description required")

    combined = clean_text(
        f"{job.title} {job.company} {job.location} {job.salary} "
        f"{job.description} {job.requirements} {job.benefits}"
    )

    prediction  = pipeline.predict([combined])[0]
    probability = pipeline.predict_proba([combined])[0]

    is_fake    = bool(prediction == 1)
    confidence = float(probability[1] if is_fake else probability[0])

    return PredictionOutput(
        prediction = "fake" if is_fake else "real",
        confidence = round(confidence, 4),
        label      = "Fake Job" if is_fake else "Real Job",
        message    = (
            "This job posting shows signs of being fraudulent."
            if is_fake else
            "This job posting appears to be legitimate."
        )
    )