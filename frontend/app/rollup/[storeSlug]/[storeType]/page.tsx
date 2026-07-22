"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Store, Vehicle } from "@/lib/types";

export default function RollupPage() {
  const params = useParams<{ storeSlug: string; storeType: string }>();
  const { storeSlug, storeType } = params;
  const { user } = useAuth();

  const [store, setStore] = useState<Store | null>(null);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [title, setTitle] = useState<string>("");

  useEffect(() => {
    if (!user) return;
    api.get<Store[]>("/stores").then((stores) => {
      setStore(stores.find((s) => s.slug === storeSlug) ?? null);
    });
  }, [user, storeSlug]);

  useEffect(() => {
    if (!store) return;
    api.get<Vehicle[]>(`/vehicles?store_id=${store.id}&store_type=${storeType}`).then(setVehicles);
    const month = new Date().toISOString().slice(0, 7);
    api
      .get<{ title: string } | null>(`/settings/report-title?store_id=${store.id}&month=${month}`)
      .then((r) => setTitle(r?.title ?? `${store.name} ${storeType === "new" ? "New" : "Used"} Snapshot`))
      .catch(() => setTitle(`${store.name} ${storeType === "new" ? "New" : "Used"} Snapshot`));
  }, [store, storeType]);

  if (!store) return <div className="p-6 text-sm text-neutral-500">Loading...</div>;

  const buckets = Array.from(new Set(vehicles.map((v) => v.bucket))).sort();

  return (
    <div className="p-6 print:p-2">
      <div className="flex items-center justify-between mb-4 print:hidden">
        <h1 className="text-lg font-semibold">{title}</h1>
        <button onClick={() => window.print()} className="text-sm px-3 py-1.5 rounded bg-blue-600 text-white">
          Print
        </button>
      </div>
      <h1 className="hidden print:block text-xl font-bold mb-4">{title}</h1>

      {buckets.map((bucket) => {
        const rows = vehicles.filter((v) => v.bucket === bucket);
        const available = rows.filter((v) => v.status.toUpperCase() !== "SOLD");
        const sold = rows.filter((v) => v.status.toUpperCase() === "SOLD");
        const availGross = available.reduce((sum, v) => sum + (v.available_gross ?? 0), 0);

        return (
          <div key={bucket} className="mb-6 break-inside-avoid">
            <h2 className="font-semibold text-sm bg-neutral-800 text-white px-2 py-1">{bucket}</h2>
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="bg-neutral-100 text-left">
                  <th className="border px-1 py-0.5">Stock #</th>
                  <th className="border px-1 py-0.5">Year</th>
                  <th className="border px-1 py-0.5">Make</th>
                  <th className="border px-1 py-0.5">Model</th>
                  <th className="border px-1 py-0.5">Status</th>
                  <th className="border px-1 py-0.5">Price</th>
                  <th className="border px-1 py-0.5">Cost</th>
                  <th className="border px-1 py-0.5">Avail. Gross</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((v) => (
                  <tr key={v.id}>
                    <td className="border px-1 py-0.5">{v.stock_number}</td>
                    <td className="border px-1 py-0.5">{v.year}</td>
                    <td className="border px-1 py-0.5">{v.make}</td>
                    <td className="border px-1 py-0.5">{v.model}</td>
                    <td className="border px-1 py-0.5">{v.status}</td>
                    <td className="border px-1 py-0.5">{v.price != null ? `$${v.price.toLocaleString()}` : ""}</td>
                    <td className="border px-1 py-0.5">{v.cost != null ? `$${v.cost.toLocaleString()}` : ""}</td>
                    <td className="border px-1 py-0.5">{v.available_gross != null ? `$${v.available_gross.toLocaleString()}` : ""}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="font-semibold bg-neutral-50">
                  <td className="border px-1 py-0.5" colSpan={4}>
                    Available: {available.length} · Sold this month: {sold.length}
                  </td>
                  <td className="border px-1 py-0.5" colSpan={4}>
                    Available Gross: ${availGross.toLocaleString()}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        );
      })}
    </div>
  );
}
