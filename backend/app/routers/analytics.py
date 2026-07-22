from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import CurrentUser, get_current_user
from ..db import get_db
from ..models import Vehicle

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/aging-summary")
def aging_summary(
    store_id: int = Query(...),
    store_type: str = Query(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if not user.can_view_store(store_id, store_type):
        raise HTTPException(status_code=403, detail="Not authorized")

    import datetime

    today = datetime.date.today()
    vehicles = (
        db.query(Vehicle)
        .filter(
            Vehicle.current_store_id == store_id,
            Vehicle.store_type == store_type,
            Vehicle.status.notin_(["SOLD", "Sold", "sold"]),
            Vehicle.inventory_date.isnot(None),
        )
        .all()
    )
    bands = {"0-14": 0, "15-29": 0, "30-44": 0, "45-59": 0, "60+": 0}
    for v in vehicles:
        age = (today - v.inventory_date).days
        if age < 15:
            bands["0-14"] += 1
        elif age < 30:
            bands["15-29"] += 1
        elif age < 45:
            bands["30-44"] += 1
        elif age < 60:
            bands["45-59"] += 1
        else:
            bands["60+"] += 1
    return bands


@router.get("/sold-price-by-model")
def sold_price_by_model(
    store_id: int = Query(...),
    store_type: str = Query(...),
    year: int | None = Query(None, description="Vehicle model year, not sale year"),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Average/min/max sold price grouped by year/make/model — the YMM trend
    tracking the user asked for, to help price new stock-ins correctly from day one."""
    if not user.can_view_store(store_id, store_type):
        raise HTTPException(status_code=403, detail="Not authorized")

    q = db.query(
        Vehicle.year,
        Vehicle.make,
        Vehicle.model,
        func.count(Vehicle.id).label("units_sold"),
        func.avg(Vehicle.sold_price).label("avg_sold_price"),
        func.min(Vehicle.sold_price).label("min_sold_price"),
        func.max(Vehicle.sold_price).label("max_sold_price"),
    ).filter(
        Vehicle.current_store_id == store_id,
        Vehicle.store_type == store_type,
        Vehicle.sold_price.isnot(None),
    )
    if year:
        q = q.filter(Vehicle.year == year)
    q = q.group_by(Vehicle.year, Vehicle.make, Vehicle.model)

    return [
        {
            "year": r.year,
            "make": r.make,
            "model": r.model,
            "units_sold": r.units_sold,
            "avg_sold_price": round(r.avg_sold_price, 2) if r.avg_sold_price else None,
            "min_sold_price": r.min_sold_price,
            "max_sold_price": r.max_sold_price,
        }
        for r in q.all()
    ]
