import os
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, Depends, Query
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
VENDORS = {
    "V-001": {"name": "Acme Supplies", "country": "USA", "rating": 4.2},
    "V-002": {"name": "Globex Corp", "country": "Germany", "rating": 3.8},
    "V-003": {"name": "Initech", "country": "India", "rating": 4.5},
}

PURCHASE_ORDERS = {
    "PO-1001": {"vendor_id": "V-001", "vendor": "Acme Supplies", "amount": 15000, "status": "Pending Approval"},
    "PO-1002": {"vendor_id": "V-002", "vendor": "Globex Corp", "amount": 4200, "status": "Approved"},
    "PO-1003": {"vendor_id": "V-003", "vendor": "Initech", "amount": 32000, "status": "Pending Approval"},
    "PO-1004": {"vendor_id": "V-001", "vendor": "Acme Supplies", "amount": 8700, "status": "Approved"},
    "PO-1005": {"vendor_id": "V-002", "vendor": "Globex Corp", "amount": 21000, "status": "Rejected"},
}

# --- Tool functions (used by Gemini's tool-calling) ---
def get_purchase_order(po_id: str) -> dict:
    """Look up a purchase order by its ID and return its details."""
    return PURCHASE_ORDERS.get(po_id, {"error": "Purchase order not found"})

def search_purchase_orders(status: Optional[str] = None, min_amount: Optional[float] = None) -> list:
    """Search purchase orders, optionally filtering by status and/or a minimum amount."""
    results = []
    for po_id, po in PURCHASE_ORDERS.items():
        if status and po["status"] != status:
            continue
        if min_amount and po["amount"] < min_amount:
            continue
        results.append({"po_id": po_id, **po})
    return results

# --- Basic endpoints ---
@app.get("/")
def root():
    return {"status": "ok", "message": "Gateway is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# --- Request/response schemas ---
class ChatRequest(BaseModel):
    message: str

class PurchaseOrderItem(BaseModel):
    po_id: str
    vendor: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None

class PurchaseOrderResponse(BaseModel):
    results: list[PurchaseOrderItem]
    summary: str

# --- Chat endpoint (AI orchestration) ---
@app.post("/chat", response_model=PurchaseOrderResponse, dependencies=[Depends(verify_api_key)])
def chat(request: ChatRequest):
    # Pass 1: let Gemini use tools to get real, grounded facts
    grounding_response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=request.message,
        config=types.GenerateContentConfig(
            tools=[get_purchase_order, search_purchase_orders]
        ),
    )
    grounded_text = grounding_response.text

    # Pass 2: force that grounded answer into our fixed schema
    structured_response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"Extract all purchase orders mentioned in this text into a list of results, plus a short summary:\n\n{grounded_text}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PurchaseOrderResponse,
        ),
    )
    return structured_response.parsed

# --- OData-style query endpoint ---
def parse_odata_filter(filter_str: str, data: dict) -> dict:
    """Very small OData $filter parser: supports 'field eq value', 'field gt value',
    'field lt value', joined by 'and'. Good enough to demonstrate the pattern."""
    if not filter_str:
        return data

    conditions = filter_str.split(" and ")
    result = {}

    for po_id, po in data.items():
        matches = True
        for cond in conditions:
            parts = cond.strip().split(" ", 2)
            if len(parts) != 3:
                continue
            field, op, value = parts
            value = value.strip("'")  # OData strings are single-quoted

            actual = po.get(field)
            if actual is None:
                matches = False
                break

            if op == "eq" and str(actual) != value:
                matches = False
            elif op == "gt" and not (isinstance(actual, (int, float)) and actual > float(value)):
                matches = False
            elif op == "lt" and not (isinstance(actual, (int, float)) and actual < float(value)):
                matches = False

        if matches:
            result[po_id] = po

    return result

@app.get("/odata/PurchaseOrders")
def odata_purchase_orders(
    filter: Optional[str] = Query(None, alias="$filter"),
    select: Optional[str] = Query(None, alias="$select"),
    top: Optional[int] = Query(None, alias="$top"),
    expand: Optional[str] = Query(None, alias="$expand"),
):
    data = parse_odata_filter(filter, PURCHASE_ORDERS) if filter else PURCHASE_ORDERS

    results = []
    for po_id, po in data.items():
        row = {"po_id": po_id, **po}

        if expand and "Vendor" in expand:
            vendor_id = row.get("vendor_id")
            row["Vendor"] = VENDORS.get(vendor_id)

        if select:
            fields = ["po_id"] + [f.strip() for f in select.split(",")]
            row = {k: v for k, v in row.items() if k in fields}

        results.append(row)

    if top:
        results = results[:top]

    return {"value": results}