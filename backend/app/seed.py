"""One-time seed script: stores, canonical status vocab, users/scopes, reprice
policy, and default color config. Run with `python -m app.seed` from backend/.
"""

from .db import Base, SessionLocal, engine
from .models import (
    AgeBandConfig,
    GrossHeatmapConfig,
    RepricePolicy,
    Store,
    StatusOption,
    User,
    UserStoreScope,
)

STATUS_LISTS = {
    ("chevy", "new"): ["WIP", "LOT", "SOLD", "In Transit", "Dealer Trade", "Ordered", "STOP SALE", "Recall", "DRAC", "RENTAL"],
    ("chevy", "used"): ["-", "WIP", "Lot", "SOLD", "Wholesale", "STOP SALE", "VALUE LOT", "Title SS", "NOT HERE", "NEED W.S."],
    ("subaru", "new"): ["WIP", "LOT", "SOLD", "In Transit", "Dealer Trade", "Ordered", "SSLP", "Lease Special", "Costco"],
    ("subaru", "used"): ["WIP", "LOT", "SOLD", "In Trans", "WHOLE SALE", "Detail", "title hold", "ARB"],
    ("sars", "used"): ["-", "WIP", "Lot", "SOLD", "Wholesale", "STOP SALE", "NSS", "NOT HERE", "NEED W.S."],
}

# (price_rank, day_threshold, plan_label, guidance_text) — from the company-wide
# "Reprice Strategy Based on Vehicle Rank 1,2,3s" table found in every workbook.
REPRICE_POLICY = [
    (1, 1, "1st Price", "Minimum $500 over cost"),
    (1, 15, "15 Day Plan", "Check VDPs, reprice to 100% of market"),
    (1, 30, "30 Day Plan", "Reprice to 98% of market; sales person drive sheet"),
    (1, 45, "45 Day Plan", "Reprice to 95% of market; manager drive sheet"),
    (1, 60, "60 Day Plan", "Reprice to 95% of market; move to sheet 2"),
    (2, 1, "1st Price", "$4,000 over cost"),
    (2, 15, "15 Day Plan", "No change"),
    (2, 30, "30 Day Plan", "Reduce gross by 25%; sales person drive sheet"),
    (2, 45, "45 Day Plan", "Reduce gross by 50%; manager drive sheet"),
    (2, 60, "60 Day Plan", "$0 remaining gross; move to sheet 2"),
    (3, 1, "1st Price", "$6,000 over cost"),
    (3, 15, "15 Day Plan", "No change"),
    (3, 30, "30 Day Plan", "Check VDPs; sales person drive sheet"),
    (3, 45, "45 Day Plan", "Reprice; manager drive sheet"),
    (3, 60, "60 Day Plan", "Reprice; move to sheet 2"),
]

AGE_BANDS = [
    (0, 14, "#FFFFFF"),
    (15, 29, "#FFF3B0"),
    (30, 44, "#FFC46B"),
    (45, 59, "#FF8A65"),
    (60, None, "#E53935"),
]

# Full-edit users confirmed directly by the client. store_type=None means the
# scope covers every type that store offers (used for Nick/Tedy's Chevy-wide
# access and for SARs, which is used-only anyway).
FULL_EDIT_USERS = [
    ("Brandon Welsh", "brandonw@twinfalls-chevy.com", [("chevy", "used"), ("sars", None)]),
    ("Charles Durbin", "charles@twinfalls-chevy.com", [("chevy", "new")]),
    ("Nick Watson", "nick@twinfalls-chevy.com", [("chevy", None), ("sars", None)]),
    ("Tedy Pelligrini-Ramseyer", "tedy@twinfalls-chevy.com", [("chevy", None), ("sars", None)]),
    # NOTE: email domain assumed to be twinfalls-subaru.com — confirm before go-live (per plan).
    ("Riley Fraser", "riley@twinfalls-subaru.com", [("subaru", "used")]),
    ("Steven Henson", "steven@twinfalls-subaru.com", [("subaru", "new")]),
    ("JT", "jt@twinfalls-subaru.com", [("subaru", None)]),
    # Owner/admin — full control across every store and type.
    ("Christian", "christian@twinfallscars.com", [("chevy", None), ("subaru", None), ("sars", None)]),
    ("Rob", "rob@twinfallscars.com", [("chevy", None), ("subaru", None), ("sars", None)]),
]

# Ops managers — view everything, can update status, but can't touch price,
# bucket moves, or settings (that stays with the full_edit users above).
MANAGER_USERS = [
    ("Weston", "weston@twinfallscars.com", [("chevy", None), ("subaru", None), ("sars", None)]),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        stores_by_slug = {}
        for slug, name, offers_new, offers_used, prefix in [
            ("chevy", "Twin Falls Chevy", True, True, "C"),
            ("subaru", "Twin Falls Subaru", True, True, "S"),
            ("sars", "Pole Line Palace (SARs)", False, True, "R"),
        ]:
            store = db.query(Store).filter(Store.slug == slug).first()
            if not store:
                store = Store(
                    slug=slug, name=name, offers_new=offers_new, offers_used=offers_used, stock_prefix=prefix
                )
                db.add(store)
                db.flush()
            stores_by_slug[slug] = store
        db.commit()

        for (slug, store_type), values in STATUS_LISTS.items():
            store = stores_by_slug[slug]
            existing = {
                s.value
                for s in db.query(StatusOption)
                .filter(StatusOption.store_id == store.id, StatusOption.store_type == store_type)
                .all()
            }
            for i, value in enumerate(values):
                if value not in existing:
                    db.add(StatusOption(store_id=store.id, store_type=store_type, value=value, sort_order=i))
        db.commit()

        if db.query(RepricePolicy).count() == 0:
            for rank, day, label, guidance in REPRICE_POLICY:
                db.add(RepricePolicy(price_rank=rank, day_threshold=day, plan_label=label, guidance_text=guidance))
            db.commit()

        if db.query(AgeBandConfig).filter(AgeBandConfig.store_id.is_(None)).count() == 0:
            for i, (lo, hi, color) in enumerate(AGE_BANDS):
                db.add(AgeBandConfig(store_id=None, min_days=lo, max_days=hi, color_hex=color, sort_order=i))
            db.commit()

        if db.query(GrossHeatmapConfig).filter(GrossHeatmapConfig.store_id.is_(None)).count() == 0:
            db.add(
                GrossHeatmapConfig(
                    store_id=None,
                    low_threshold=-1000,
                    high_threshold=3000,
                    low_color="#E53935",
                    mid_color="#FFF3B0",
                    high_color="#43A047",
                )
            )
            db.commit()

        def _seed_users(user_list, role):
            for name, email, scopes in user_list:
                user = db.query(User).filter(User.email == email).first()
                if not user:
                    user = User(name=name, email=email, role=role, is_active=True)
                    db.add(user)
                    db.flush()
                existing_scopes = {(s.store_id, s.store_type) for s in user.scopes}
                for slug, store_type in scopes:
                    store = stores_by_slug[slug]
                    if (store.id, store_type) not in existing_scopes:
                        db.add(UserStoreScope(user_id=user.id, store_id=store.id, store_type=store_type))

        _seed_users(FULL_EDIT_USERS, "full_edit")
        _seed_users(MANAGER_USERS, "manager")
        db.commit()

        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
