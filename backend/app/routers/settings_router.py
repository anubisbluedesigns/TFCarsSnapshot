from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import CurrentUser, get_current_user
from ..db import get_db
from ..models import (
    AgeBandConfig,
    BucketColorMap,
    GrossHeatmapConfig,
    ReportTitle,
    StatusColorMap,
    StoreGoal,
)
from ..schemas import (
    ColorMapUpsert,
    ReportTitleOut,
    ReportTitleUpsert,
    StoreGoalOut,
    StoreGoalUpsert,
)

router = APIRouter(prefix="/settings", tags=["settings"])


def _require_full_edit(user: CurrentUser, store_id: int, store_type: str | None = None):
    if not user.can_edit_store(store_id, store_type):
        raise HTTPException(status_code=403, detail="Full-edit access required for this store")


@router.get("/status-colors")
def get_status_colors(
    store_id: int = Query(...),
    store_type: str = Query(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if not user.can_view_store(store_id, store_type):
        raise HTTPException(status_code=403, detail="Not authorized")
    rows = (
        db.query(StatusColorMap)
        .filter(StatusColorMap.store_id == store_id, StatusColorMap.store_type == store_type)
        .all()
    )
    return {r.status_value: r.color_hex for r in rows}


@router.put("/status-colors")
def set_status_color(
    payload: ColorMapUpsert, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    _require_full_edit(user, payload.store_id, payload.store_type)
    row = (
        db.query(StatusColorMap)
        .filter(
            StatusColorMap.store_id == payload.store_id,
            StatusColorMap.store_type == payload.store_type,
            StatusColorMap.status_value == payload.key_value,
        )
        .first()
    )
    if row:
        row.color_hex = payload.color_hex
    else:
        row = StatusColorMap(
            store_id=payload.store_id,
            store_type=payload.store_type,
            status_value=payload.key_value,
            color_hex=payload.color_hex,
        )
        db.add(row)
    db.commit()
    return {"ok": True}


@router.get("/bucket-colors")
def get_bucket_colors(
    store_id: int = Query(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if not user.can_view_store(store_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    rows = db.query(BucketColorMap).filter(BucketColorMap.store_id == store_id).all()
    return {r.bucket_value: r.color_hex for r in rows}


@router.put("/bucket-colors")
def set_bucket_color(
    payload: ColorMapUpsert, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    _require_full_edit(user, payload.store_id)
    row = (
        db.query(BucketColorMap)
        .filter(BucketColorMap.store_id == payload.store_id, BucketColorMap.bucket_value == payload.key_value)
        .first()
    )
    if row:
        row.color_hex = payload.color_hex
    else:
        row = BucketColorMap(
            store_id=payload.store_id, bucket_value=payload.key_value, color_hex=payload.color_hex
        )
        db.add(row)
    db.commit()
    return {"ok": True}


@router.get("/age-bands")
def get_age_bands(
    store_id: int | None = Query(None), db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    rows = db.query(AgeBandConfig).filter(AgeBandConfig.store_id == store_id).order_by(AgeBandConfig.sort_order).all()
    if not rows:
        # fall back to global defaults (store_id is NULL)
        rows = db.query(AgeBandConfig).filter(AgeBandConfig.store_id.is_(None)).order_by(AgeBandConfig.sort_order).all()
    return [
        {"min_days": r.min_days, "max_days": r.max_days, "color_hex": r.color_hex} for r in rows
    ]


@router.get("/report-title", response_model=ReportTitleOut | None)
def get_report_title(
    store_id: int = Query(...),
    month: str = Query(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if not user.can_view_store(store_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    return (
        db.query(ReportTitle)
        .filter(ReportTitle.store_id == store_id, ReportTitle.month == month)
        .first()
    )


@router.put("/report-title", response_model=ReportTitleOut)
def set_report_title(
    payload: ReportTitleUpsert, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    _require_full_edit(user, payload.store_id)
    row = (
        db.query(ReportTitle)
        .filter(ReportTitle.store_id == payload.store_id, ReportTitle.month == payload.month)
        .first()
    )
    if row:
        row.title = payload.title
    else:
        row = ReportTitle(store_id=payload.store_id, month=payload.month, title=payload.title)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/store-goals", response_model=list[StoreGoalOut])
def list_store_goals(
    store_id: int = Query(...),
    store_type: str = Query(...),
    year: int = Query(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if not user.can_view_store(store_id, store_type):
        raise HTTPException(status_code=403, detail="Not authorized")
    return (
        db.query(StoreGoal)
        .filter(StoreGoal.store_id == store_id, StoreGoal.store_type == store_type, StoreGoal.year == year)
        .order_by(StoreGoal.quarter)
        .all()
    )


@router.put("/store-goals", response_model=StoreGoalOut)
def upsert_store_goal(
    payload: StoreGoalUpsert, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    _require_full_edit(user, payload.store_id, payload.store_type)
    row = (
        db.query(StoreGoal)
        .filter(
            StoreGoal.store_id == payload.store_id,
            StoreGoal.store_type == payload.store_type,
            StoreGoal.year == payload.year,
            StoreGoal.quarter == payload.quarter,
        )
        .first()
    )
    if row:
        row.map_value = payload.map_value
        row.par_value = payload.par_value
        row.target_value = payload.target_value
    else:
        row = StoreGoal(**payload.model_dump())
        db.add(row)
    db.commit()
    db.refresh(row)
    return row
