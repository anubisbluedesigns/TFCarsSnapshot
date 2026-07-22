from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import CurrentUser, get_current_user
from ..db import get_db
from ..models import StatusOption
from ..schemas import StatusOptionOut

router = APIRouter(prefix="/status-options", tags=["status-options"])


@router.get("", response_model=list[StatusOptionOut])
def list_status_options(
    store_id: int = Query(...),
    store_type: str = Query(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if not user.can_view_store(store_id, store_type):
        raise HTTPException(status_code=403, detail="Not authorized to view this store/type")
    return (
        db.query(StatusOption)
        .filter(StatusOption.store_id == store_id, StatusOption.store_type == store_type)
        .order_by(StatusOption.sort_order)
        .all()
    )


@router.post("", response_model=StatusOptionOut)
def add_status_option(
    store_id: int,
    store_type: str,
    value: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    if not user.can_edit_store(store_id, store_type):
        raise HTTPException(status_code=403, detail="Full-edit access required for this store/type")
    max_sort = (
        db.query(StatusOption)
        .filter(StatusOption.store_id == store_id, StatusOption.store_type == store_type)
        .count()
    )
    opt = StatusOption(store_id=store_id, store_type=store_type, value=value, sort_order=max_sort)
    db.add(opt)
    db.commit()
    db.refresh(opt)
    return opt


@router.delete("/{option_id}")
def delete_status_option(
    option_id: int, db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)
):
    opt = db.get(StatusOption, option_id)
    if not opt:
        raise HTTPException(status_code=404, detail="Not found")
    if not user.can_edit_store(opt.store_id, opt.store_type):
        raise HTTPException(status_code=403, detail="Full-edit access required for this store/type")
    db.delete(opt)
    db.commit()
    return {"ok": True}
