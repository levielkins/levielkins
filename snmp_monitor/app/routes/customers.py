from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Customer

router = APIRouter(prefix="/customers")
templates = Jinja2Templates(directory="app/templates")


@router.get("/new")
def new_customer_form(request: Request):
    return templates.TemplateResponse(request, "customer_form.html")


@router.post("/new")
def create_customer(
    name: str = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    name = name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Customer name is required")

    customer = Customer(name=name, notes=notes.strip())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return RedirectResponse(url=f"/customers/{customer.id}", status_code=303)


@router.get("/{customer_id}")
def customer_detail(customer_id: int, request: Request, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    return templates.TemplateResponse(
        request, "customer_detail.html", {"customer": customer}
    )


@router.post("/{customer_id}/delete")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    db.delete(customer)
    db.commit()
    return RedirectResponse(url="/?msg=Customer+deleted", status_code=303)
