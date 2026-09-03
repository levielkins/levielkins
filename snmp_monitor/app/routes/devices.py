from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Customer, Device
from ..poller import poll_and_record

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/customers/{customer_id}/devices/new")
def new_device_form(customer_id: int, request: Request, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return templates.TemplateResponse(
        request, "device_form.html", {"customer": customer}
    )


@router.post("/customers/{customer_id}/devices/new")
def create_device(
    customer_id: int,
    name: str = Form(...),
    ip_address: str = Form(...),
    port: int = Form(161),
    snmp_version: str = Form("2c"),
    community: str = Form("public"),
    poll_interval_seconds: int = Form(300),
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    name = name.strip()
    ip_address = ip_address.strip()
    if not name or not ip_address:
        raise HTTPException(status_code=400, detail="Name and IP address are required")
    if snmp_version not in ("1", "2c"):
        raise HTTPException(status_code=400, detail="SNMP version must be 1 or 2c")
    if not (1 <= port <= 65535):
        raise HTTPException(status_code=400, detail="Port must be between 1 and 65535")
    if poll_interval_seconds < 15:
        raise HTTPException(
            status_code=400, detail="Poll interval must be at least 15 seconds"
        )

    device = Device(
        customer_id=customer.id,
        name=name,
        ip_address=ip_address,
        port=port,
        snmp_version=snmp_version,
        community=community.strip() or "public",
        poll_interval_seconds=poll_interval_seconds,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return RedirectResponse(url=f"/devices/{device.id}", status_code=303)


@router.get("/devices/{device_id}")
def device_detail(device_id: int, request: Request, db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    history = device.poll_results[:50]
    return templates.TemplateResponse(
        request, "device_detail.html", {"device": device, "history": history}
    )


@router.post("/devices/{device_id}/poll")
async def poll_now(device_id: int, db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    await poll_and_record(device_id)
    return RedirectResponse(url=f"/devices/{device_id}?msg=Poll+complete", status_code=303)


@router.post("/devices/{device_id}/toggle")
def toggle_device(device_id: int, db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    device.enabled = not device.enabled
    db.commit()
    return RedirectResponse(url=f"/devices/{device_id}", status_code=303)


@router.post("/devices/{device_id}/delete")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    customer_id = device.customer_id
    db.delete(device)
    db.commit()
    return RedirectResponse(url=f"/customers/{customer_id}?msg=Device+deleted", status_code=303)
