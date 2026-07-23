"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Store } from "@/lib/types";
import type { DashboardData, BucketRow } from "@/lib/dashboardTypes";

function fmtMoney(n: number | null | undefined) {
  if (n == null) return "-";
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}
function fmtNum(n: number | null | undefined) {
  if (n == null) return "-";
  return n.toLocaleString();
}

export default function DashboardPage() {
  const params = useParams<{ storeSlug: string; storeType: string }>();
  const { storeSlug, storeType } = params;
  const { user, canEditStore } = useAuth();

  const [store, setStore] = useState<Store | null>(null);
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const month = new Date().toISOString().slice(0, 7);

  useEffect(() => {
    if (!user) return;
    api.get<Store[]>("/stores").then((stores) => {
      const match = stores.find((s) => s.slug === storeSlug) ?? null;
      setStore(match);
      if (!match) setError("You don't have access to this store.");
    });
  }, [user, storeSlug]);

  const refresh = useCallback(async () => {
    if (!store) return;
    setLoading(true);
    setError(null);
    try {
      const d = await api.get<DashboardData>(`/dashboard?store_id=${store.id}&store_type=${storeType}&month=${month}`);
      setData(d);
    } catch (e) {
      setError(
        e instanceof ApiError && e.status === 403
          ? "You don't have access to this store/type. Try logging out and back in, or check with an admin."
          : "Couldn't load the dashboard right now."
      );
    } finally {
      setLoading(false);
    }
  }, [store, storeType, month]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (!user) return null;
  if (error) return <div className="p-6 text-sm text-red-600">{error}</div>;
  if (!store || loading || !data) return <div className="p-6 text-sm text-neutral-500">Loading dashboard...</div>;

  const fullEdit = canEditStore(store.id, storeType);

  async function saveBucketGoal(bucket: string, field: keyof BucketRow, value: string) {
    if (!store) return;
    const existing = data!.buckets.find((b) => b.bucket === bucket)!;
    const parsed = value === "" ? null : Number(value);
    await api.put("/dashboard/bucket-goals", {
      store_id: store.id,
      store_type: storeType,
      bucket,
      month,
      sales_forecast: field === "sales_forecast" ? parsed : existing.sales_forecast,
      inventory_needed: field === "inventory_needed" ? parsed : existing.inventory_needed,
      plan_per_vehicle: field === "plan_per_vehicle" ? parsed : existing.plan_per_vehicle,
    });
    refresh();
  }

  async function saveInventoryGoal(key: string, value: string) {
    if (!store) return;
    const g = data!.inventory;
    const goals: Record<string, number | null> = {
      on_lot_goal: g.on_lot.goal,
      wholesale_goal: g.wholesale.goal,
      aged45_goal: g.aged45.goal,
      available_gross_goal: g.available_gross.goal,
      internet_must_have_goal: g.internet_must_have.goal,
      on_display_goal: g.on_display.goal,
    };
    goals[key] = value === "" ? null : Number(value);
    const qs = new URLSearchParams({
      store_id: String(store.id),
      store_type: storeType,
      month,
      ...Object.fromEntries(Object.entries(goals).map(([k, v]) => [k, v == null ? "" : String(v)])),
    });
    await api.put(`/dashboard/inventory-goals?${qs.toString()}`);
    refresh();
  }

  const inv = data.inventory;
  const invRows: { label: string; key: keyof typeof inv; goalKey: string; money?: boolean }[] = [
    { label: "On Lot Inventory (units owned)", key: "on_lot", goalKey: "on_lot_goal" },
    { label: "Wholesale Inventory (units owned)", key: "wholesale", goalKey: "wholesale_goal" },
    { label: "Inventory Older Than 45 Days", key: "aged45", goalKey: "aged45_goal" },
    { label: "Internet Must-Have", key: "internet_must_have", goalKey: "internet_must_have_goal" },
    { label: "Available Gross (w/ wholesale)", key: "available_gross", goalKey: "available_gross_goal", money: true },
    { label: "On Display", key: "on_display", goalKey: "on_display_goal" },
  ];

  return (
    <div className="p-4 max-w-6xl">
      <div className="flex items-center justify-between mb-1 print:hidden">
        <h1 className="text-lg font-semibold">
          {store.name} Snapshot — {storeType === "new" ? "New" : "Used"}
        </h1>
        <Link href={`/inventory/${storeSlug}/${storeType}`} className="text-sm text-blue-700 hover:underline">
          Go to inventory grid →
        </Link>
      </div>
      <p className="text-sm text-neutral-500 mb-4">
        Plan for month of {month} — Day {data.days_elapsed} of {data.days_in_month} — as of {data.as_of}
      </p>

      <h2 className="font-semibold text-sm bg-neutral-800 text-white px-2 py-1 mt-4">Vehicle Game Plan</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-neutral-100 text-left">
              <th className="border px-2 py-1">Sales Forecast</th>
              <th className="border px-2 py-1">Inventory Needed</th>
              <th className="border px-2 py-1">Category</th>
              <th className="border px-2 py-1">Plan / Vehicle</th>
              <th className="border px-2 py-1">Plan Total Gross</th>
              <th className="border px-2 py-1">MTD Sales</th>
              <th className="border px-2 py-1">MTD Gross</th>
              <th className="border px-2 py-1">Avg Gross</th>
              <th className="border px-2 py-1">Sales Pace</th>
              <th className="border px-2 py-1">Gross Pace</th>
            </tr>
          </thead>
          <tbody>
            {data.buckets.map((b) => (
              <tr key={b.bucket}>
                <td className="border px-2 py-1">
                  {fullEdit ? (
                    <input
                      type="number"
                      defaultValue={b.sales_forecast ?? ""}
                      onBlur={(e) => saveBucketGoal(b.bucket, "sales_forecast", e.target.value)}
                      className="w-16 border rounded px-1"
                    />
                  ) : (
                    fmtNum(b.sales_forecast)
                  )}
                </td>
                <td className="border px-2 py-1">
                  {fullEdit ? (
                    <input
                      type="number"
                      defaultValue={b.inventory_needed ?? ""}
                      onBlur={(e) => saveBucketGoal(b.bucket, "inventory_needed", e.target.value)}
                      className="w-16 border rounded px-1"
                    />
                  ) : (
                    fmtNum(b.inventory_needed)
                  )}
                </td>
                <td className="border px-2 py-1 font-medium">{b.bucket}</td>
                <td className="border px-2 py-1">
                  {fullEdit ? (
                    <input
                      type="number"
                      defaultValue={b.plan_per_vehicle ?? ""}
                      onBlur={(e) => saveBucketGoal(b.bucket, "plan_per_vehicle", e.target.value)}
                      className="w-20 border rounded px-1"
                    />
                  ) : (
                    fmtMoney(b.plan_per_vehicle)
                  )}
                </td>
                <td className="border px-2 py-1">{fmtMoney(b.plan_for_total_gross)}</td>
                <td className="border px-2 py-1 font-medium">{b.mtd_sales}</td>
                <td className="border px-2 py-1">{fmtMoney(b.mtd_gross)}</td>
                <td className="border px-2 py-1">{fmtMoney(b.avg_gross)}</td>
                <td className="border px-2 py-1">{b.mtd_sales_tracking ?? "-"}</td>
                <td className="border px-2 py-1">{fmtMoney(b.mtd_gross_tracking)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="font-semibold bg-neutral-50">
              <td className="border px-2 py-1">{fmtNum(data.totals.sales_forecast)}</td>
              <td className="border px-2 py-1">{fmtNum(data.totals.inventory_needed)}</td>
              <td className="border px-2 py-1">TOTAL</td>
              <td className="border px-2 py-1"></td>
              <td className="border px-2 py-1">{fmtMoney(data.totals.plan_for_total_gross)}</td>
              <td className="border px-2 py-1">{data.totals.mtd_sales}</td>
              <td className="border px-2 py-1">{fmtMoney(data.totals.mtd_gross)}</td>
              <td className="border px-2 py-1">{fmtMoney(data.totals.avg_gross)}</td>
              <td className="border px-2 py-1">{data.totals.mtd_sales_tracking ?? "-"}</td>
              <td className="border px-2 py-1">{fmtMoney(data.totals.mtd_gross_tracking)}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
        <div>
          <h2 className="font-semibold text-sm bg-neutral-800 text-white px-2 py-1">Inventory Summary</h2>
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="bg-neutral-100 text-left">
                <th className="border px-2 py-1"></th>
                <th className="border px-2 py-1">1st of Month</th>
                <th className="border px-2 py-1">Current</th>
                <th className="border px-2 py-1">Goal</th>
              </tr>
            </thead>
            <tbody>
              {invRows.map((row) => {
                const r = inv[row.key];
                return (
                  <tr key={row.key}>
                    <td className="border px-2 py-1">{row.label}</td>
                    <td className="border px-2 py-1">{row.money ? fmtMoney(r.first_of_month) : fmtNum(r.first_of_month)}</td>
                    <td className="border px-2 py-1 font-medium">{row.money ? fmtMoney(r.current) : fmtNum(r.current)}</td>
                    <td className="border px-2 py-1">
                      {fullEdit ? (
                        <input
                          type="number"
                          defaultValue={r.goal ?? ""}
                          onBlur={(e) => saveInventoryGoal(row.goalKey, e.target.value)}
                          className="w-20 border rounded px-1"
                        />
                      ) : row.money ? (
                        fmtMoney(r.goal)
                      ) : (
                        fmtNum(r.goal)
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div>
          <h2 className="font-semibold text-sm bg-neutral-800 text-white px-2 py-1">Top Volume Segments (MTD)</h2>
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="bg-neutral-100 text-left">
                <th className="border px-2 py-1">Model</th>
                <th className="border px-2 py-1">Units Sold</th>
              </tr>
            </thead>
            <tbody>
              {data.top_volume_segments.map((s) => (
                <tr key={s.model}>
                  <td className="border px-2 py-1">{s.model}</td>
                  <td className="border px-2 py-1">{s.units}</td>
                </tr>
              ))}
              {data.top_volume_segments.length === 0 && (
                <tr>
                  <td colSpan={2} className="border px-2 py-4 text-center text-neutral-400">
                    No sales recorded yet this month.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <h2 className="font-semibold text-sm bg-neutral-800 text-white px-2 py-1 mt-6">Trade Summary</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(["new", "used"] as const).map((t) => {
          const side = data.trade_summary[t];
          return (
            <table key={t} className="w-full text-xs border-collapse">
              <thead>
                <tr className="bg-neutral-100 text-left">
                  <th className="border px-2 py-1" colSpan={2}>
                    {t === "new" ? "New Vehicles" : "Used Vehicles"}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="border px-2 py-1">MTD Sales</td>
                  <td className="border px-2 py-1">{side.mtd_sales}</td>
                </tr>
                <tr>
                  <td className="border px-2 py-1">MTD Trades</td>
                  <td className="border px-2 py-1">{side.mtd_trades}</td>
                </tr>
                <tr>
                  <td className="border px-2 py-1">Trade %</td>
                  <td className="border px-2 py-1">{side.pct != null ? `${side.pct}%` : "-"}</td>
                </tr>
                <tr>
                  <td className="border px-2 py-1">Aged 90+</td>
                  <td className={`border px-2 py-1 ${side.aged["90"] > 0 ? "bg-red-200" : ""}`}>{side.aged["90"]}</td>
                </tr>
                <tr>
                  <td className="border px-2 py-1">Aged 75+</td>
                  <td className={`border px-2 py-1 ${side.aged["75"] > 0 ? "bg-orange-200" : ""}`}>{side.aged["75"]}</td>
                </tr>
                <tr>
                  <td className="border px-2 py-1">Aged 60+</td>
                  <td className={`border px-2 py-1 ${side.aged["60"] > 0 ? "bg-yellow-100" : ""}`}>{side.aged["60"]}</td>
                </tr>
              </tbody>
            </table>
          );
        })}
      </div>
    </div>
  );
}
