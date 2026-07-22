from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import CurrentUser, get_current_user
from ..db import get_db
from ..models import Store
from ..schemas import StoreOut

router = APIRouter(prefix="/stores", tags=["stores"])


@router.get("", response_model=list[StoreOut])
def list_stores(db: Session = Depends(get_db), user: CurrentUser = Depends(get_current_user)):
    store_ids = set(user.store_ids)
    stores = db.query(Store).all()
    return [s for s in stores if s.id in store_ids]
