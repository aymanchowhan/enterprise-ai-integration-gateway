from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

class ApprovalState(TypedDict):
    po_id: str
    amount: float
    vendor_id: str
    vendor_rating: Optional[float]
    decision: Optional[str]
    explanation: Optional[str]

def check_vendor(state: ApprovalState) -> ApprovalState:
    from main import VENDORS
    vendor = VENDORS.get(state["vendor_id"], {})
    state["vendor_rating"] = vendor.get("rating", 0)
    return state

def route_decision(state: ApprovalState) -> str:
    """This is the router: it doesn't change the state, it just decides which node to go to next."""
    if state["amount"] > 10000 and state["vendor_rating"] < 4.0:
        return "flag_review"
    return "auto_approve"

def auto_approve(state: ApprovalState) -> ApprovalState:
    state["decision"] = "Auto-Approved"
    state["explanation"] = (
        f"PO {state['po_id']} meets auto-approval criteria "
        f"(amount ${state['amount']}, vendor rating {state['vendor_rating']})."
    )
    return state

def flag_review(state: ApprovalState) -> ApprovalState:
    state["decision"] = "Flagged for Review"
    state["explanation"] = (
        f"PO {state['po_id']} is ${state['amount']} with a vendor rating of "
        f"{state['vendor_rating']}, below our 4.0 threshold for high-value orders."
    )
    return state

workflow = StateGraph(ApprovalState)
workflow.add_node("check_vendor", check_vendor)
workflow.add_node("auto_approve", auto_approve)
workflow.add_node("flag_review", flag_review)

workflow.set_entry_point("check_vendor")
workflow.add_conditional_edges(
    "check_vendor",
    route_decision,
    {"auto_approve": "auto_approve", "flag_review": "flag_review"},
)
workflow.add_edge("auto_approve", END)
workflow.add_edge("flag_review", END)

approval_graph = workflow.compile()