import datetime
import enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .db import Base


class Role(str, enum.Enum):
    full_edit = "full_edit"
    manager = "manager"
    sales_rep = "sales_rep"


class StoreType(str, enum.Enum):
    new = "new"
    used = "used"


class UserStoreScope(Base):
    """A user's edit/view scope. store_type=None means 'all types this store offers'.

    Full-edit users are scoped to specific (store, type) pairs — e.g. Charles has
    Chevy New only, Brandon has Chevy Used + SARs but not Chevy New. Manager/sales_rep
    rows are typically store_type=None (whichever types that role covers).
    """

    __tablename__ = "user_store_scope"

    id = Column(Integer, Sequence("user_store_scope_id_seq", optional=True), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    store_type = Column(String, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "store_id", "store_type", name="uq_user_store_scope"),)


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, Sequence("stores_id_seq", optional=True), primary_key=True)
    slug = Column(String, unique=True, nullable=False)  # chevy, subaru, sars
    name = Column(String, nullable=False)
    offers_new = Column(Boolean, default=False)
    offers_used = Column(Boolean, default=False)
    stock_prefix = Column(String, nullable=True)  # C, S, R

    vehicles = relationship("Vehicle", back_populates="current_store", foreign_keys="Vehicle.current_store_id")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, Sequence("users_id_seq", optional=True), primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # Role enum value
    is_active = Column(Boolean, default=True)

    scopes = relationship("UserStoreScope", backref="user", cascade="all, delete-orphan")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, Sequence("vehicles_id_seq", optional=True), primary_key=True)
    stock_number = Column(String, nullable=True, index=True)
    vin_tail = Column(String, nullable=True)

    originating_store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    current_store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    store_type = Column(String, nullable=False)  # StoreType enum value

    year = Column(Integer, nullable=True)
    make = Column(String, nullable=True)
    model = Column(String, nullable=True)
    trim_details = Column(String, nullable=True)
    mileage = Column(Integer, nullable=True)

    price_rank = Column(Integer, nullable=True)  # 1, 2, 3
    status = Column(String, nullable=False)
    bucket = Column(String, nullable=False)

    price = Column(Float, nullable=True)
    cost = Column(Float, nullable=True)
    sold_price = Column(Float, nullable=True)
    sold_cost = Column(Float, nullable=True)
    sold_date = Column(Date, nullable=True)

    reserved = Column(Boolean, default=False)
    reserved_sales_rep = Column(String, nullable=True)
    reserved_guest_name = Column(String, nullable=True)

    unwound = Column(Boolean, default=False)

    tag_otd_special = Column(Boolean, default=False)

    inventory_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    updated_by = Column(String, nullable=True)

    current_store = relationship("Store", back_populates="vehicles", foreign_keys=[current_store_id])
    price_history = relationship("PriceHistory", back_populates="vehicle", cascade="all, delete-orphan")
    store_transfers = relationship("StoreTransfer", back_populates="vehicle", cascade="all, delete-orphan")
    unwind_events = relationship("UnwindEvent", back_populates="vehicle", cascade="all, delete-orphan")

    @property
    def available_gross(self):
        if self.price is None or self.cost is None:
            return None
        return self.price - self.cost

    @property
    def sold_gross(self):
        if self.sold_price is None or self.sold_cost is None:
            return None
        return self.sold_price - self.sold_cost


class StatusOption(Base):
    __tablename__ = "status_options"
    __table_args__ = (UniqueConstraint("store_id", "store_type", "value", name="uq_status_option"),)

    id = Column(Integer, Sequence("status_options_id_seq", optional=True), primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    store_type = Column(String, nullable=False)
    value = Column(String, nullable=False)
    sort_order = Column(Integer, default=0)


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, Sequence("price_history_id_seq", optional=True), primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    old_price = Column(Float, nullable=True)
    new_price = Column(Float, nullable=True)
    changed_at = Column(DateTime, default=datetime.datetime.utcnow)
    changed_by = Column(String, nullable=True)

    vehicle = relationship("Vehicle", back_populates="price_history")


class StoreTransfer(Base):
    __tablename__ = "store_transfers"

    id = Column(Integer, Sequence("store_transfers_id_seq", optional=True), primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    from_store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    to_store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    transferred_at = Column(DateTime, default=datetime.datetime.utcnow)
    transferred_by = Column(String, nullable=True)

    vehicle = relationship("Vehicle", back_populates="store_transfers")


class UnwindEvent(Base):
    __tablename__ = "unwind_events"

    id = Column(Integer, Sequence("unwind_events_id_seq", optional=True), primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    unwound_at = Column(DateTime, default=datetime.datetime.utcnow)
    prior_sold_price = Column(Float, nullable=True)
    unwound_by = Column(String, nullable=True)

    vehicle = relationship("Vehicle", back_populates="unwind_events")


class StoreGoal(Base):
    __tablename__ = "store_goals"

    id = Column(Integer, Sequence("store_goals_id_seq", optional=True), primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    store_type = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    map_value = Column(Float, nullable=True)
    par_value = Column(Float, nullable=True)
    target_value = Column(Float, nullable=True)


class StatusColorMap(Base):
    __tablename__ = "status_color_map"
    __table_args__ = (UniqueConstraint("store_id", "store_type", "status_value", name="uq_status_color"),)

    id = Column(Integer, Sequence("status_color_map_id_seq", optional=True), primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    store_type = Column(String, nullable=False)
    status_value = Column(String, nullable=False)
    color_hex = Column(String, nullable=False)


class BucketColorMap(Base):
    __tablename__ = "bucket_color_map"
    __table_args__ = (UniqueConstraint("store_id", "bucket_value", name="uq_bucket_color"),)

    id = Column(Integer, Sequence("bucket_color_map_id_seq", optional=True), primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    bucket_value = Column(String, nullable=False)
    color_hex = Column(String, nullable=False)


class AgeBandConfig(Base):
    __tablename__ = "age_band_config"

    id = Column(Integer, Sequence("age_band_config_id_seq", optional=True), primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)  # null = global default
    min_days = Column(Integer, nullable=False)
    max_days = Column(Integer, nullable=True)  # null = open-ended (60+)
    color_hex = Column(String, nullable=False)
    sort_order = Column(Integer, default=0)


class GrossHeatmapConfig(Base):
    __tablename__ = "gross_heatmap_config"

    id = Column(Integer, Sequence("gross_heatmap_config_id_seq", optional=True), primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True)  # null = global default
    low_threshold = Column(Float, nullable=False)
    high_threshold = Column(Float, nullable=False)
    low_color = Column(String, nullable=False)
    mid_color = Column(String, nullable=False)
    high_color = Column(String, nullable=False)


class ReportTitle(Base):
    __tablename__ = "report_titles"
    __table_args__ = (UniqueConstraint("store_id", "month", name="uq_report_title"),)

    id = Column(Integer, Sequence("report_titles_id_seq", optional=True), primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    month = Column(String, nullable=False)  # "2026-07"
    title = Column(String, nullable=False)


class RepricePolicy(Base):
    """Company-wide reprice strategy, keyed by price_rank (1/2/3) and day-plan step."""

    __tablename__ = "reprice_policy"
    __table_args__ = (UniqueConstraint("price_rank", "day_threshold", name="uq_reprice_policy"),)

    id = Column(Integer, Sequence("reprice_policy_id_seq", optional=True), primary_key=True)
    price_rank = Column(Integer, nullable=False)  # 1, 2, 3
    day_threshold = Column(Integer, nullable=False)  # 1, 15, 30, 45, 60
    plan_label = Column(String, nullable=False)  # "1st Price", "15 Day Plan", ...
    guidance_text = Column(String, nullable=False)  # "Reprice to 98% of Market"


class MonthlyBucketGoal(Base):
    """Manager-entered monthly plan per bucket, replicating the Snapshot tab's
    Sales Forecast / Inventory Needed / Plan Per Vehicle columns."""

    __tablename__ = "monthly_bucket_goal"
    __table_args__ = (
        UniqueConstraint("store_id", "store_type", "bucket", "month", name="uq_monthly_bucket_goal"),
    )

    id = Column(Integer, Sequence("monthly_bucket_goal_id_seq", optional=True), primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    store_type = Column(String, nullable=False)
    bucket = Column(String, nullable=False)
    month = Column(String, nullable=False)  # "2026-07"
    sales_forecast = Column(Integer, nullable=True)
    inventory_needed = Column(Integer, nullable=True)
    plan_per_vehicle = Column(Float, nullable=True)


class MonthlySnapshotBaseline(Base):
    """Auto-captured on first dashboard load of a new month — the "1st of Month"
    figures the old Snapshot tab showed. We have no history before this app
    existed, so the first month's baseline is just whatever the numbers are
    when first captured, and it gets more meaningful every month after."""

    __tablename__ = "monthly_snapshot_baseline"
    __table_args__ = (UniqueConstraint("store_id", "store_type", "month", name="uq_monthly_snapshot_baseline"),)

    id = Column(Integer, Sequence("monthly_snapshot_baseline_id_seq", optional=True), primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    store_type = Column(String, nullable=False)
    month = Column(String, nullable=False)
    on_lot_units = Column(Integer, nullable=True)
    wholesale_units = Column(Integer, nullable=True)
    aged45_units = Column(Integer, nullable=True)
    available_gross = Column(Float, nullable=True)
    internet_must_have_units = Column(Integer, nullable=True)
    on_display_units = Column(Integer, nullable=True)
    captured_at = Column(DateTime, default=datetime.datetime.utcnow)


class MonthlyInventoryGoal(Base):
    """Manager-entered inventory targets for the dashboard's summary block."""

    __tablename__ = "monthly_inventory_goal"
    __table_args__ = (UniqueConstraint("store_id", "store_type", "month", name="uq_monthly_inventory_goal"),)

    id = Column(Integer, Sequence("monthly_inventory_goal_id_seq", optional=True), primary_key=True)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    store_type = Column(String, nullable=False)
    month = Column(String, nullable=False)
    on_lot_goal = Column(Integer, nullable=True)
    wholesale_goal = Column(Integer, nullable=True)
    aged45_goal = Column(Integer, nullable=True)
    available_gross_goal = Column(Float, nullable=True)
    internet_must_have_goal = Column(Integer, nullable=True)
    on_display_goal = Column(Integer, nullable=True)
