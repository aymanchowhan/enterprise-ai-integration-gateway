import os
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

app = FastAPI(title="Enterprise AI Integration Gateway")
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

INTERNAL_API_KEY = os.environ.get("GATEWAY_API_KEY", "dev-secret-key")

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

# --- Mock "ERP" data (stand-in for a real SAP/backend system) ---
PURCHASE_ORDERS = {
    "PO-1001": {"vendor": "Acme Supplies", "amount": 15000, "status": "Pending Approval"},
    "PO-1002": {"vendor": "Globex Corp", "amount": 4200, "status": "Approved"},
    "PO-1003": {"vendor": "Initech", "amount": 32000, "status": "Pending Approval"},
}

def get_purchase_order(po_id: str) -> dict:
    """Look up a purchase order by its ID and return its details."""
    return PURCHASE_ORDERS.get(po_id, {"error": "Purchase order not found"})

# --- FastAPI endpoints ---
@app.get("/")
def root():
    return {"status": "ok", "message": "Gateway is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

class ChatRequest(BaseModel):
    message: str

class PurchaseOrderResponse(BaseModel):
    po_id: str
    vendor: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    summary: str

@app.post("/chat", response_model=PurchaseOrderResponse, dependencies=[Depends(verify_api_key)])
def chat(request: ChatRequest):
    # Pass 1: let Gemini use the tool to get real, grounded facts
    grounding_response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=request.message,
        config=types.GenerateContentConfig(
            tools=[get_purchase_order]
        ),
    )
    grounded_text = grounding_response.text

    # Pass 2: force that grounded answer into our fixed schema
    structured_response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"Extract the purchase order details from this text into the required fields:\n\n{grounded_text}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PurchaseOrderResponse,
        ),
    )
    return structured_response.parsed