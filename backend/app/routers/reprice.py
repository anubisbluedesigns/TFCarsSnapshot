import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import CurrentUser, get_current_user
from ..db import get_db
from ..models import PriceHistory, RepricePolicy, Vehicle

router = APIRouter(prefix="/reprice", tags=["reprice"])

SOLD_LIKE = {"SOLD", "Sold", "sold"}


@router.get("/policy")
def get_policy(db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    rows = db.query(RepricePolicy).order_by(RepricePolicy.price_rank, RepricePolicy.day_threshold).all()
    return [
        {
            "price_rank": r.price_rank,
            "day_threshold": r.day_threshold,
            "plan_label": r.plan_label,
            "guidance_text": r.guidance_text,
        }
        for r in rows
    ]


@router.put("/policy")
def upsert_policy(
    price_rank: int,
    day_threshold: int,
    plan_label: str,
    guidance_text: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    # Reprice strategy is company-wide policy; any full_edit user may adjust it.
    if user.role != "full_edit":
        raise HTTPException(status_code=403, detail="Full-edit access required")
    row = (
        db.query(RepricePolicy)
        .filter(RepricePolicy.price_rank == price_rank, RepricePolicy.day_threshold == day_threshold)
        .first()
    )
    if row:
        row.plan_label = plan_label
        row.guidance_text = guidance_text
    else:
        row = RepricePolicy(
            price_rank=price_rank,
            day_threshold=day_threshold,
            plan_label=plan_label,
            guidance_text=guidance_text,
        )
        db.add(row)
    db.commit()
    return {"ok": True}


@router.get("/due")
def due_for_reprice(
    store_id: int = Query(...),
    store_type: str = Query(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Flags vehicles that should have hit their next reprice step by now.

    Rule: a threshold T (from the rank's policy) is "missed" if T <= current
    age-in-days AND the vehicle's last price change happened before it had
    reached T days old (i.e. no reprice has occurred since crossing T).
    """
    if not user.can_view_store(store_id, store_type):
        raise HTTPException(status_code=403, detail="Not authorized")

    today = datetime.date.today()
    vehicles = (
        db.query(Vehicle)
        .filter(
            Vehicle.current_store_id == store_id,
            Vehicle.store_type == store_type,
            ~Vehicle.status.in_(SOLD_LIKE),
        )
        .all()
    )
    policy_by_rank: dict[int, list[RepricePolicy]] = {}
    for row in db.query(RepricePolicy).order_by(RepricePolicy.day_threshold).all():
        policy_by_rank.setdefault(row.price_rank, []).append(row)

    results = []
    for v in vehicles:
        if not v.inventory_date or not v.price_rank:
            continue
        age_days = (today - v.inventory_date).days
        last_price_change = (
            db.query(PriceHistory)
            .filter(PriceHistory.vehicle_id == v.id)
            .order_by(PriceHistory.changed_at.desc())
            .first()
        )
        last_reprice_age_days = (
            (last_price_change.changed_at.date() - v.inventory_date).days if last_price_change else 0
        )

        thresholds = policy_by_rank.get(v.price_rank, [])
        missed = [t for t in thresholds if t.day_threshold <= age_days and last_reprice_age_days < t.day_threshold]
        if missed:
            next_due = max(missed, key=lambda t: t.day_threshold)
            results.append(
                {
                    "vehicle_id": v.id,
                    "stock_number": v.stock_number,
                    "year": v.year,
                    "make": v.make,
                    "model": v.model,
                    "price_rank": v.price_rank,
                    "age_days": age_days,
                    "due_plan": next_due.plan_label,
                    "guidance": next_due.guidance_text,
                }
            )
    return results
