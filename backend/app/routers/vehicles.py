import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import CurrentUser, get_current_user
from ..db import get_db
from ..models import (
    PriceHistory,
    StatusOption,
    Store,
    StoreTransfer,
    UnwindEvent,
    Vehicle,
)
from ..schemas import (
    BucketMoveRequest,
    PriceChangeRequest,
    ReserveRequest,
    UnwindRequest,
    VehicleCreate,
    VehicleOut,
    VehicleUpdate,
)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def _require_view(user: CurrentUser, store_id: int, store_type: str):
    if not user.can_view_store(store_id, store_type):
        raise HTTPException(status_code=403, detail="Not authorized to view this store/type")


def _get_vehicle_or_404(db: Session, vehicle_id: int) -> Vehicle:
    v = db.get(Vehicle, vehicle_id)
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return v


@router.get("", response_model=list[VehicleOut])
def list_vehicles(
    store_id: int = Query(...),
    store_type: str = Query(...),
    bucket: Optional[str] = Query(None),
    status_value: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_view(user, store_id, store_type)
    q = db.query(Vehicle).filter(
        Vehicle.current_store_id == store_id, Vehicle.store_type == store_type
    )
    if bucket:
        q = q.filter(Vehicle.bucket == bucket)
    if status_value:
        q = q.filter(Vehicle.status == status_value)
    return q.order_by(Vehicle.bucket, Vehicle.stock_number).all()


@router.post("", response_model=VehicleOut)
def create_vehicle(
    payload: VehicleCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if not user.can_edit_store(payload.current_store_id, payload.store_type):
        raise HTTPException(status_code=403, detail="Full-edit access required for this store/type")
    v = Vehicle(**payload.model_dump(), updated_by=user.email)
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.patch("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(
    vehicle_id: int,
    payload: VehicleUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    v = _get_vehicle_or_404(db, vehicle_id)
    data = payload.model_dump(exclude_unset=True)

    # status-only edit is allowed for managers too; anything else requires full edit
    status_only = set(data.keys()) <= {"status"}
    if status_only and data:
        if not user.can_edit_status(v.current_store_id, v.store_type):
            raise HTTPException(status_code=403, detail="Status-edit access required")
    else:
        if not user.can_edit_store(v.current_store_id, v.store_type):
            raise HTTPException(status_code=403, detail="Full-edit access required for this store/type")

    for k, val in data.items():
        setattr(v, k, val)
    v.updated_by = user.email
    v.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(v)
    return v


@router.post("/{vehicle_id}/price-change", response_model=VehicleOut)
def change_price(
    vehicle_id: int,
    payload: PriceChangeRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    v = _get_vehicle_or_404(db, vehicle_id)
    if not user.can_edit_store(v.current_store_id, v.store_type):
        raise HTTPException(status_code=403, detail="Full-edit access required for this store/type")

    db.add(
        PriceHistory(
            vehicle_id=v.id,
            old_price=v.price,
            new_price=payload.new_price,
            changed_by=user.email,
        )
    )
    v.price = payload.new_price
    v.updated_by = user.email
    v.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(v)
    return v


@router.post("/{vehicle_id}/bucket-move", response_model=VehicleOut)
def move_bucket(
    vehicle_id: int,
    payload: BucketMoveRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    v = _get_vehicle_or_404(db, vehicle_id)
    if not user.can_edit_store(v.current_store_id, v.store_type):
        raise HTTPException(status_code=403, detail="Full-edit access required for this store/type")

    if payload.to_store_id and payload.to_store_id != v.current_store_id:
        to_store = db.get(Store, payload.to_store_id)
        if not to_store:
            raise HTTPException(status_code=404, detail="Destination store not found")
        db.add(
            StoreTransfer(
                vehicle_id=v.id,
                from_store_id=v.current_store_id,
                to_store_id=payload.to_store_id,
                transferred_by=user.email,
            )
        )
        v.current_store_id = payload.to_store_id

    v.bucket = payload.bucket
    v.updated_by = user.email
    v.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(v)
    return v


@router.post("/{vehicle_id}/reserve", response_model=VehicleOut)
def toggle_reserved(
    vehicle_id: int,
    payload: ReserveRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    v = _get_vehicle_or_404(db, vehicle_id)
    if not user.can_toggle_reserved(v.current_store_id, v.store_type):
        raise HTTPException(status_code=403, detail="Not authorized to reserve units at this store")

    v.reserved = payload.reserved
    v.reserved_sales_rep = payload.reserved_sales_rep if payload.reserved else None
    v.reserved_guest_name = payload.reserved_guest_name if payload.reserved else None
    v.updated_by = user.email
    v.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(v)
    return v


@router.post("/{vehicle_id}/unwind", response_model=VehicleOut)
def unwind_vehicle(
    vehicle_id: int,
    payload: UnwindRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Reverts a SOLD unit back to available inventory instead of manual re-entry.

    Restores status to the store/type's canonical "Lot" status option and clears
    the sold fields, while logging an UnwindEvent so unwind frequency is trackable
    (user reported ~12/store/month for the two main stores).
    """
    v = _get_vehicle_or_404(db, vehicle_id)
    if not user.can_edit_store(v.current_store_id, v.store_type):
        raise HTTPException(status_code=403, detail="Full-edit access required for this store/type")

    if not payload.unwind:
        v.unwound = False
        db.commit()
        db.refresh(v)
        return v

    lot_status = (
        db.query(StatusOption)
        .filter(
            StatusOption.store_id == v.current_store_id,
            StatusOption.store_type == v.store_type,
            StatusOption.value.ilike("lot"),
        )
        .first()
    )
    restore_status = lot_status.value if lot_status else "LOT"

    db.add(
        UnwindEvent(
            vehicle_id=v.id,
            prior_sold_price=v.sold_price,
            unwound_by=user.email,
        )
    )
    v.unwound = True
    v.status = restore_status
    v.sold_price = None
    v.sold_cost = None
    v.sold_date = None
    v.updated_by = user.email
    v.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(v)
    return v


@router.delete("/{vehicle_id}")
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    v = _get_vehicle_or_404(db, vehicle_id)
    if not user.can_edit_store(v.current_store_id, v.store_type):
        raise HTTPException(status_code=403, detail="Full-edit access required for this store/type")
    db.delete(v)
    db.commit()
    return {"ok": True}
