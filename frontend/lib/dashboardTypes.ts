export interface BucketRow {
  bucket: string;
  sales_forecast: number | null;
  inventory_needed: number | null;
  plan_per_vehicle: number | null;
  plan_for_total_gross: number | null;
  mtd_sales: number;
  mtd_gross: number;
  avg_gross: number | null;
  mtd_sales_tracking: number | null;
  mtd_gross_tracking: number | null;
}

export interface InventoryRow {
  first_of_month: number | null;
  current: number;
  goal: number | null;
}

export interface TradeSummarySide {
  mtd_sales: number;
  mtd_trades: number;
  pct: number | null;
  aged: { "90": number; "75": number; "60": number };
}

export interface DashboardData {
  month: string;
  days_elapsed: number;
  days_in_month: number;
  as_of: string;
  buckets: BucketRow[];
  totals: BucketRow & { bucket?: string };
  inventory: {
    on_lot: InventoryRow;
    wholesale: InventoryRow;
    aged45: InventoryRow;
    available_gross: InventoryRow;
    internet_must_have: InventoryRow;
    on_display: InventoryRow;
  };
  trade_summary: { new: TradeSummarySide; used: TradeSummarySide };
  top_volume_segments: { model: string; units: number }[];
}
