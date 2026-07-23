from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..auth import CurrentUser, get_current_user
from ..db import engine, get_db
from ..models import Vehicle

router = APIRouter(prefix="/sold-not-updated", tags=["sold-not-updated"])

# Maps our store slugs to the literal `store` value used in the external
# TFCarsSoldDash sold-log table (DEALERSHIP.PUBLIC.DEALS).
DEALS_STORE_NAME = {
    "chevy": "Chevy",
    "subaru": "Subaru",
    "sars": "SARs",
}

# deals.inventory_type is "N" (new) or "U" (used) — must match our store_type
# or a used-car sale will look like an unmatched "new" vehicle (and vice versa)
# since that stock number never existed in the other type's inventory at all.
DEALS_INVENTORY_TYPE = {"new": "N", "used": "U"}


@router.get("")
def sold_not_updated(
    store_id: int = Query(...),
    store_type: str = Query(...),
    store_slug: str = Query(..., description="chevy | subaru | sars"),
    months_back: int = Query(2, ge=1, le=12),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Cross-references the sold log (DEALERSHIP.PUBLIC.DEALS, read-only) against
    our vehicles table. Returns stock numbers the sold log shows as sold in the
    last `months_back` months that this system hasn't been marked SOLD for yet.

    Purely informational — nothing here writes anything. A manager still has to
    open the vehicle and mark it sold themselves (they have sold price and other
    details the sold log doesn't carry).
    """
    if not user.can_view_store(store_id, store_type):
        raise HTTPException(status_code=403, detail="Not authorized")

    deals_store = DEALS_STORE_NAME.get(store_slug)
    if not deals_store:
        raise HTTPException(status_code=400, detail=f"Unknown store_slug: {store_slug}")

    already_sold = {
        (v.stock_number or "").upper()
        for v in db.query(Vehicle.stock_number).filter(
            Vehicle.current_store_id == store_id,
            Vehicle.store_type == store_type,
            Vehicle.status == "SOLD",
        )
    }

    deals_inventory_type = DEALS_INVENTORY_TYPE.get(store_type)
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT stock_number, customer_name, vehicle, sales_1, sales_2,
                           deal_type, tab_year, tab_month
                    FROM DEALERSHIP.PUBLIC.DEALS
                    WHERE store = :store
                      AND inventory_type = :inventory_type
                      AND stock_number IS NOT NULL
                      AND (tab_year * 12 + tab_month) >=
                          (YEAR(CURRENT_DATE()) * 12 + MONTH(CURRENT_DATE()) - :months_back)
                    ORDER BY tab_year DESC, tab_month DESC
                    """
                ),
                {"store": deals_store, "inventory_type": deals_inventory_type, "months_back": months_back},
            ).fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Sold log not reachable yet (grant INVENTORY_APP_ROLE access to DEALERSHIP.PUBLIC.DEALS first): {e}",
        )

    seen = set()
    results = []
    for row in rows:
        stock = (row.stock_number or "").upper()
        if not stock or stock in seen or stock in already_sold:
            continue
        seen.add(stock)
        results.append(
            {
                "stock_number": row.stock_number,
                "customer_name": row.customer_name,
                "vehicle": row.vehicle,
                "sales_1": row.sales_1,
                "sales_2": row.sales_2,
                "deal_type": row.deal_type,
                "tab_year": row.tab_year,
                "tab_month": row.tab_month,
            }
        )
    return results
