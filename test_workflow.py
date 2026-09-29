from workflow import approval_graph

result = approval_graph.invoke({
    "po_id": "PO-1003",
    "amount": 32000,
    "vendor_id": "V-003",
    "vendor_rating": None,
    "decision": None,
    "explanation": None,
})

print(result)