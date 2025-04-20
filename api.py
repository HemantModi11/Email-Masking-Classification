# api.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils import mask_pii
from models import predict_category

router = APIRouter()

class EmailRequest(BaseModel):
    email_body: str

@router.post("/classify")
def classify_email(payload: EmailRequest):
    try:
        # 1. Mask PII
        result = mask_pii(payload.email_body)

        # 2. Classify
        category = predict_category(result["masked_email"], model_path="best_model.pkl")

        # 3. Add category to result
        result["category_of_the_email"] = category

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))