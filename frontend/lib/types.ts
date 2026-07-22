export interface Scope {
  store_id: number;
  store_type: string | null;
}

export interface User {
  id: number;
  email: string;
  name: string;
  role: "full_edit" | "manager" | "sales_rep";
  scopes: Scope[];
}

export interface Store {
  id: number;
  slug: string;
  name: string;
  offers_new: boolean;
  offers_used: boolean;
  stock_prefix: string | null;
}

export interface Vehicle {
  id: number;
  stock_number: string | null;
  vin_tail: string | null;
  originating_store_id: number;
  current_store_id: number;
  store_type: string;
  year: number | null;
  make: string | null;
  model: string | null;
  trim_details: string | null;
  mileage: number | null;
  price_rank: number | null;
  status: string;
  bucket: string;
  price: number | null;
  cost: number | null;
  available_gross: number | null;
  sold_price: number | null;
  sold_cost: number | null;
  sold_gross: number | null;
  sold_date: string | null;
  reserved: boolean;
  reserved_sales_rep: string | null;
  reserved_guest_name: string | null;
  unwound: boolean;
  tag_otd_special: boolean;
  inventory_date: string | null;
  updated_at: string | null;
  updated_by: string | null;
}

export interface StatusOption {
  id: number;
  store_id: number;
  store_type: string;
  value: string;
  sort_order: number;
}

export interface RepriceDueRow {
  vehicle_id: number;
  stock_number: string | null;
  year: number | null;
  make: string | null;
  model: string | null;
  price_rank: number;
  age_days: number;
  due_plan: string;
  guidance: string;
}
