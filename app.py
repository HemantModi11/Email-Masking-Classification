# app.py
from fastapi import FastAPI
from api import router

app = FastAPI(
    title="Email Classification API",
    description="Classifies support emails and masks PII entities.",
    version="1.0.0"
)

app.include_router(router)