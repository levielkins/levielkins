from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Customer

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    customers = db.query(Customer).order_by(Customer.name).all()

    summaries = []
    for customer in customers:
        devices = customer.devices
        up = sum(1 for d in devices if d.latest_result and d.latest_result.is_up)
        down = sum(
            1 for d in devices if d.latest_result and not d.latest_result.is_up
        )
        unknown = sum(1 for d in devices if d.latest_result is None)
        summaries.append(
            {
                "customer": customer,
                "total": len(devices),
                "up": up,
                "down": down,
                "unknown": unknown,
            }
        )

    return templates.TemplateResponse(
        request, "dashboard.html", {"summaries": summaries}
    )
