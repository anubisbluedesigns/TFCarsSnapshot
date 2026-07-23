import calendar
import datetime
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import CurrentUser, get_current_user
from ..db import get_db
from ..models import MonthlyBucketGoal, MonthlyInventoryGoal, MonthlySnapshotBaseline, Vehicle
from ..schemas import MonthlyBucketGoalUpsert

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

SOLD_LIKE = {"SOLD", "Sold", "sold"}


def _current_month() -> str:
    return datetime.date.today().strftime("%Y-%m")


def _month_bounds(month: str) -> tuple[datetime.date, int]:
    year, mon = (int(x) for x in month.split("-"))
    days_in_month = calendar.monthrange(year, mon)[1]
    return datetime.date(year, mon, 1), days_in_month


def _require_view(user: CurrentUser, store_id: int, store_type: str):
    if not user.can_view_store(store_id, store_type):
        raise HTTPException(status_code=403, detail="Not authorized")


@router.get("")
def get_dashboard(
    store_id: int = Query(...),
    store_type: str = Query(...),
    month: str = Query(default_factory=_current_month),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Computed replica of the original workbooks' Snapshot tab: per-bucket
    sales-forecast-vs-actual with pace tracking, inventory summary, trade
    summary with aged buckets, and top volume segments. Everything here is
    read-only/computed except the manager-entered goals (separate endpoints)."""
    _require_view(user, store_id, store_type)

    month_start, days_in_month = _month_bounds(month)
    today = datetime.date.today()
    is_current_month = month == _current_month()
    days_elapsed = today.day if is_current_month else days_in_month

    def pace(actual: float) -> float | None:
        if not days_elapsed:
            return None
        return round(actual / days_elapsed * days_in_month, 2)

    vehicles = db.query(Vehicle).filter(
        Vehicle.current_store_id == store_id, Vehicle.store_type == store_type
    ).all()

    # --- Per-bucket sales forecast vs MTD actuals ---
    goals = {
        g.bucket: g
        for g in db.query(MonthlyBucketGoal).filter(
            MonthlyBucketGoal.store_id == store_id,
            MonthlyBucketGoal.store_type == store_type,
            MonthlyBucketGoal.month == month,
        )
    }
    by_bucket: dict[str, list[Vehicle]] = defaultdict(list)
    for v in vehicles:
        by_bucket[v.bucket].append(v)

    bucket_rows = []
    totals = {"sales_forecast": 0, "inventory_needed": 0, "plan_for_total_gross": 0.0, "mtd_sales": 0, "mtd_gross": 0.0}
    for bucket in sorted(set(by_bucket) | set(goals)):
        bvs = by_bucket.get(bucket, [])
        mtd_sold = [
            v for v in bvs
            if (v.status or "").upper() == "SOLD" and v.sold_date and v.sold_date >= month_start
            and v.sold_date < datetime.date(month_start.year, month_start.month, days_in_month) + datetime.timedelta(days=1)
        ]
        mtd_sales = len(mtd_sold)
        mtd_gross = sum((v.sold_gross or 0) for v in mtd_sold)
        avg_gross = round(mtd_gross / mtd_sales, 2) if mtd_sales else None

        g = goals.get(bucket)
        sales_forecast = g.sales_forecast if g else None
        inventory_needed = g.inventory_needed if g else None
        plan_per_vehicle = g.plan_per_vehicle if g else None
        plan_for_total_gross = (
            round(sales_forecast * plan_per_vehicle, 2) if sales_forecast is not None and plan_per_vehicle is not None else None
        )

        bucket_rows.append(
            {
                "bucket": bucket,
                "sales_forecast": sales_forecast,
                "inventory_needed": inventory_needed,
                "plan_per_vehicle": plan_per_vehicle,
                "plan_for_total_gross": plan_for_total_gross,
                "mtd_sales": mtd_sales,
                "mtd_gross": round(mtd_gross, 2),
                "avg_gross": avg_gross,
                "mtd_sales_tracking": pace(mtd_sales),
                "mtd_gross_tracking": pace(mtd_gross),
            }
        )
        totals["sales_forecast"] += sales_forecast or 0
        totals["inventory_needed"] += inventory_needed or 0
        totals["plan_for_total_gross"] += plan_for_total_gross or 0
        totals["mtd_sales"] += mtd_sales
        totals["mtd_gross"] += mtd_gross

    totals["avg_gross"] = round(totals["mtd_gross"] / totals["mtd_sales"], 2) if totals["mtd_sales"] else None
    totals["mtd_sales_tracking"] = pace(totals["mtd_sales"])
    totals["mtd_gross_tracking"] = pace(totals["mtd_gross"])
    totals["mtd_gross"] = round(totals["mtd_gross"], 2)
    totals["plan_for_total_gross"] = round(totals["plan_for_total_gross"], 2)

    # --- Inventory summary ---
    not_sold = [v for v in vehicles if (v.status or "").upper() != "SOLD"]
    wholesale_units = sum(1 for v in not_sold if "wholesale" in (v.bucket or "").lower())
    on_lot_units = len(not_sold) - wholesale_units
    aged45_units = sum(
        1 for v in not_sold if v.inventory_date and (today - v.inventory_date).days >= 45
    )
    available_gross = round(sum((v.available_gross or 0) for v in not_sold), 2)
    internet_must_have_units = sum(1 for v in not_sold if (v.bucket or "").lower() == "internet")
    on_display_units = on_lot_units  # closest available proxy; see chat notes

    baseline = (
        db.query(MonthlySnapshotBaseline)
        .filter(
            MonthlySnapshotBaseline.store_id == store_id,
            MonthlySnapshotBaseline.store_type == store_type,
            MonthlySnapshotBaseline.month == month,
        )
        .first()
    )
    if not baseline and is_current_month:
        baseline = MonthlySnapshotBaseline(
            store_id=store_id,
            store_type=store_type,
            month=month,
            on_lot_units=on_lot_units,
            wholesale_units=wholesale_units,
            aged45_units=aged45_units,
            available_gross=available_gross,
            internet_must_have_units=internet_must_have_units,
            on_display_units=on_display_units,
        )
        db.add(baseline)
        db.commit()

    inv_goal = (
        db.query(MonthlyInventoryGoal)
        .filter(
            MonthlyInventoryGoal.store_id == store_id,
            MonthlyInventoryGoal.store_type == store_type,
            MonthlyInventoryGoal.month == month,
        )
        .first()
    )

    def inv_row(key: str, current: float, goal_attr: str):
        return {
            "first_of_month": getattr(baseline, key, None) if baseline else None,
            "current": current,
            "goal": getattr(inv_goal, goal_attr, None) if inv_goal else None,
        }

    inventory = {
        "on_lot": inv_row("on_lot_units", on_lot_units, "on_lot_goal"),
        "wholesale": inv_row("wholesale_units", wholesale_units, "wholesale_goal"),
        "aged45": inv_row("aged45_units", aged45_units, "aged45_goal"),
        "available_gross": inv_row("available_gross", available_gross, "available_gross_goal"),
        "internet_must_have": inv_row("internet_must_have_units", internet_must_have_units, "internet_must_have_goal"),
        "on_display": inv_row("on_display_units", on_display_units, "on_display_goal"),
    }

    # --- Trade summary (New + Used, both at this store, per original layout) ---
    def trade_summary_for(s_type: str):
        vs = db.query(Vehicle).filter(Vehicle.current_store_id == store_id, Vehicle.store_type == s_type).all()
        mtd_sales = sum(
            1 for v in vs
            if (v.status or "").upper() == "SOLD" and v.sold_date and v.sold_date >= month_start
        )
        mtd_trades = sum(
            1 for v in vs
            if "trade" in (v.bucket or "").lower() and v.inventory_date and v.inventory_date >= month_start
        )
        pct = round(mtd_trades / mtd_sales * 100, 1) if mtd_sales else None
        not_sold_v = [v for v in vs if (v.status or "").upper() != "SOLD" and v.inventory_date]
        aged = {
            "90": sum(1 for v in not_sold_v if (today - v.inventory_date).days >= 90),
            "75": sum(1 for v in not_sold_v if (today - v.inventory_date).days >= 75),
            "60": sum(1 for v in not_sold_v if (today - v.inventory_date).days >= 60),
        }
        return {"mtd_sales": mtd_sales, "mtd_trades": mtd_trades, "pct": pct, "aged": aged}

    trade_summary = {"new": trade_summary_for("new"), "used": trade_summary_for("used")}

    # --- Top 4 volume segments (by model, MTD units sold) ---
    model_counts: dict[str, int] = defaultdict(int)
    for v in vehicles:
        if (v.status or "").upper() == "SOLD" and v.sold_date and v.sold_date >= month_start and v.model:
            model_counts[v.model] += 1
    top_volume_segments = [
        {"model": m, "units": c} for m, c in sorted(model_counts.items(), key=lambda x: -x[1])[:4]
    ]

    return {
        "month": month,
        "days_elapsed": days_elapsed,
        "days_in_month": days_in_month,
        "as_of": today.isoformat(),
        "buckets": bucket_rows,
        "totals": totals,
        "inventory": inventory,
        "trade_summary": trade_summary,
        "top_volume_segments": top_volume_segments,
    }


@router.get("/bucket-goals")
def list_bucket_goals(
    store_id: int = Query(...),
    store_type: str = Query(...),
    month: str = Query(default_factory=_current_month),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_view(user, store_id, store_type)
    rows = db.query(MonthlyBucketGoal).filter(
        MonthlyBucketGoal.store_id == store_id,
        MonthlyBucketGoal.store_type == store_type,
        MonthlyBucketGoal.month == month,
    ).all()
    return [
        {
            "bucket": r.bucket,
            "sales_forecast": r.sales_forecast,
            "inventory_needed": r.inventory_needed,
            "plan_per_vehicle": r.plan_per_vehicle,
        }
        for r in rows
    ]


@router.put("/bucket-goals")
def upsert_bucket_goal(
    payload: MonthlyBucketGoalUpsert,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if not user.can_edit_store(payload.store_id, payload.store_type):
        raise HTTPException(status_code=403, detail="Full-edit access required")
    row = db.query(MonthlyBucketGoal).filter(
        MonthlyBucketGoal.store_id == payload.store_id,
        MonthlyBucketGoal.store_type == payload.store_type,
        MonthlyBucketGoal.bucket == payload.bucket,
        MonthlyBucketGoal.month == payload.month,
    ).first()
    if row:
        row.sales_forecast = payload.sales_forecast
        row.inventory_needed = payload.inventory_needed
        row.plan_per_vehicle = payload.plan_per_vehicle
    else:
        row = MonthlyBucketGoal(**payload.model_dump())
        db.add(row)
    db.commit()
    return {"ok": True}


@router.get("/inventory-goals")
def get_inventory_goals(
    store_id: int = Query(...),
    store_type: str = Query(...),
    month: str = Query(default_factory=_current_month),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_view(user, store_id, store_type)
    row = db.query(MonthlyInventoryGoal).filter(
        MonthlyInventoryGoal.store_id == store_id,
        MonthlyInventoryGoal.store_type == store_type,
        MonthlyInventoryGoal.month == month,
    ).first()
    if not row:
        return None
    return {
        "on_lot_goal": row.on_lot_goal,
        "wholesale_goal": row.wholesale_goal,
        "aged45_goal": row.aged45_goal,
        "available_gross_goal": row.available_gross_goal,
        "internet_must_have_goal": row.internet_must_have_goal,
        "on_display_goal": row.on_display_goal,
    }


@router.put("/inventory-goals")
def upsert_inventory_goals(
    store_id: int,
    store_type: str,
    month: str,
    on_lot_goal: int | None = None,
    wholesale_goal: int | None = None,
    aged45_goal: int | None = None,
    available_gross_goal: float | None = None,
    internet_must_have_goal: int | None = None,
    on_display_goal: int | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if not user.can_edit_store(store_id, store_type):
        raise HTTPException(status_code=403, detail="Full-edit access required")
    row = db.query(MonthlyInventoryGoal).filter(
        MonthlyInventoryGoal.store_id == store_id,
        MonthlyInventoryGoal.store_type == store_type,
        MonthlyInventoryGoal.month == month,
    ).first()
    if not row:
        row = MonthlyInventoryGoal(store_id=store_id, store_type=store_type, month=month)
        db.add(row)
    row.on_lot_goal = on_lot_goal
    row.wholesale_goal = wholesale_goal
    row.aged45_goal = aged45_goal
    row.available_gross_goal = available_gross_goal
    row.internet_must_have_goal = internet_must_have_goal
    row.on_display_goal = on_display_goal
    db.commit()
    return {"ok": True}
