from __future__ import annotations
import os
import random
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

app = FastAPI(title="Internal Tracker (mock)")
DB: dict[str, dict] = {}
FAIL_ONCE: set[str] = set()


@app.get("/", response_class=HTMLResponse)
def home():
    rows = "".join(
        f"<tr><td>{v['invoice_id']}</td><td>{v['company']}</td>"
        f"<td>{v['amount']}</td><td>{v['due_date']}</td></tr>"
        for v in DB.values()
    )
    return f"""
    <html><head><title>Internal Tracker</title></head>
    <body>
      <h1>Internal Invoice Tracker</h1>
      <p><a href="/new">+ New Invoice</a></p>
      <table border=1 cellpadding=6>
        <tr><th>Invoice ID</th><th>Company</th><th>Amount</th><th>Due</th></tr>
        {rows}
      </table>
    </body></html>"""


@app.get("/new", response_class=HTMLResponse)
def new_form():
    return """
    <html><head><title>New Invoice</title></head>
    <body>
      <h1>New Invoice</h1>
      <form method="post" action="/invoices">
        <label>Invoice ID <input name="invoice_id" required></label><br>
        <label>Company    <input name="company" required></label><br>
        <label>Amount     <input name="amount" required></label><br>
        <label>Due date   <input name="due_date" required></label><br>
        <button type="submit">Save</button>
      </form>
    </body></html>"""


@app.post("/invoices")
def create_invoice(
    invoice_id: str = Form(...),
    company: str = Form(...),
    amount: str = Form(...),
    due_date: str = Form(...),
):
    fail_once_id = os.getenv("FAIL_ONCE_ID", "")
    if fail_once_id and invoice_id == fail_once_id and invoice_id not in FAIL_ONCE:
        FAIL_ONCE.add(invoice_id)
        return JSONResponse({"error": "temporarily unavailable"}, status_code=503)

    rate = float(os.getenv("FAIL_RATE", "0"))
    if rate and random.random() < rate:
        return JSONResponse({"error": "temporarily unavailable"}, status_code=503)

    DB[invoice_id] = {
        "invoice_id": invoice_id,
        "company": company,
        "amount": amount,
        "due_date": due_date,
    }
    return RedirectResponse(url=f"/invoices/{invoice_id}/saved", status_code=303)


@app.get("/invoices/{invoice_id}/saved", response_class=HTMLResponse)
def saved(invoice_id: str):
    return (f"<html><body><h1>Invoice {invoice_id} saved ✔</h1>"
            f"<p><a href='/'>Back</a></p></body></html>")


@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: str):
    if invoice_id not in DB:
        return JSONResponse({"error": "not found"}, status_code=404)
    return DB[invoice_id]