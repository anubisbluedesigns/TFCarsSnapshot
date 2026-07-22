import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class StoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    name: str
    offers_new: bool
    offers_used: bool
    stock_prefix: Optional[str] = None


class ScopeOut(BaseModel):
    store_id: int
    store_type: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    name: str
    role: str
    scopes: list[ScopeOut] = []


class VehicleBase(BaseModel):
    stock_number: Optional[str] = None
    vin_tail: Optional[str] = None
    originating_store_id: int
    current_store_id: int
    store_type: str
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    trim_details: Optional[str] = None
    mileage: Optional[int] = None
    price_rank: Optional[int] = None
    status: str
    bucket: str
    price: Optional[float] = None
    cost: Optional[float] = None
    sold_price: Optional[float] = None
    sold_cost: Optional[float] = None
    sold_date: Optional[datetime.date] = None
    reserved: bool = False
    reserved_sales_rep: Optional[str] = None
    reserved_guest_name: Optional[str] = None
    unwound: bool = False
    tag_otd_special: bool = False
    inventory_date: Optional[datetime.date] = None


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    stock_number: Optional[str] = None
    vin_tail: Optional[str] = None
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None
    trim_details: Optional[str] = None
    mileage: Optional[int] = None
    price_rank: Optional[int] = None
    status: Optional[str] = None
    bucket: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    sold_price: Optional[float] = None
    sold_cost: Optional[float] = None
    sold_date: Optional[datetime.date] = None
    tag_otd_special: Optional[bool] = None


class VehicleOut(VehicleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    available_gross: Optional[float] = None
    sold_gross: Optional[float] = None
    updated_at: Optional[datetime.datetime] = None
    updated_by: Optional[str] = None


class PriceChangeRequest(BaseModel):
    new_price: float


class BucketMoveRequest(BaseModel):
    bucket: str
    to_store_id: Optional[int] = None  # set if the move crosses stores (e.g. into SARs)


class ReserveRequest(BaseModel):
    reserved: bool
    reserved_sales_rep: Optional[str] = None
    reserved_guest_name: Optional[str] = None


class UnwindRequest(BaseModel):
    unwind: bool = True


class StatusOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    store_id: int
    store_type: str
    value: str
    sort_order: int


class StoreGoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    store_id: int
    store_type: str
    year: int
    quarter: int
    map_value: Optional[float] = None
    par_value: Optional[float] = None
    target_value: Optional[float] = None


class StoreGoalUpsert(BaseModel):
    store_id: int
    store_type: str
    year: int
    quarter: int
    map_value: Optional[float] = None
    par_value: Optional[float] = None
    target_value: Optional[float] = None


class ReportTitleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    store_id: int
    month: str
    title: str


class ReportTitleUpsert(BaseModel):
    store_id: int
    month: str
    title: str


class ColorMapUpsert(BaseModel):
    store_id: int
    store_type: Optional[str] = None
    key_value: str  # status value or bucket value
    color_hex: str


class LoginRequest(BaseModel):
    id_token: str


class LoginResponse(BaseModel):
    access_token: str
    user: UserOut
