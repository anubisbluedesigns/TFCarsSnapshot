"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Store, Vehicle } from "@/lib/types";

export default function ReservedPage() {
  const { user, canToggleReserved } = useAuth();
  const [reserved, setReserved] = useState<(Vehicle & { storeName: string })[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    api.get<Store[]>("/stores").then(async (allStores) => {
      const results: (Vehicle & { storeName: string })[] = [];
      for (const store of allStores) {
        for (const type of ["new", "used"] as const) {
          const offers = type === "new" ? store.offers_new : store.offers_used;
          const hasScope = user.scopes.some((s) => s.store_id === store.id && (s.store_type === null || s.store_type === type));
          if (!offers || !hasScope) continue;
          try {
            const vs = await api.get<Vehicle[]>(`/vehicles?store_id=${store.id}&store_type=${type}`);
            for (const v of vs) if (v.reserved) results.push({ ...v, storeName: `${store.name} ${type}` });
          } catch {
            // skip
          }
        }
      }
      setReserved(results);
      setLoading(false);
    });
  }, [user]);

  async function unreserve(v: Vehicle) {
    await api.post(`/vehicles/${v.id}/reserve`, { reserved: false });
    setReserved((r) => r.filter((x) => x.id !== v.id));
  }

  if (loading) return <div className="p-6 text-sm text-neutral-500">Loading...</div>;

  return (
    <div className="p-6">
      <h1 className="text-lg font-semibold mb-4">Reserved / Pre-Sold Units</h1>
      <p className="text-sm text-neutral-500 mb-4">
        In-transit and on-lot units already spoken for — kept visible to staff so a guest shopping for one of
        these isn&apos;t sent elsewhere.
      </p>
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-neutral-100 text-left">
            <th className="border px-2 py-1">Store</th>
            <th className="border px-2 py-1">Stock #</th>
            <th className="border px-2 py-1">Vehicle</th>
            <th className="border px-2 py-1">Sales Rep</th>
            <th className="border px-2 py-1">Guest</th>
            <th className="border px-2 py-1"></th>
          </tr>
        </thead>
        <tbody>
          {reserved.map((v) => (
            <tr key={v.id}>
              <td className="border px-2 py-1">{v.storeName}</td>
              <td className="border px-2 py-1">{v.stock_number ?? v.vin_tail}</td>
              <td className="border px-2 py-1">{[v.year, v.make, v.model].filter(Boolean).join(" ")}</td>
              <td className="border px-2 py-1">{v.reserved_sales_rep}</td>
              <td className="border px-2 py-1">{v.reserved_guest_name}</td>
              <td className="border px-2 py-1">
                {canToggleReserved(v.current_store_id, v.store_type) && (
                  <button onClick={() => unreserve(v)} className="text-red-600 text-xs hover:underline">
                    Release
                  </button>
                )}
              </td>
            </tr>
          ))}
          {reserved.length === 0 && (
            <tr>
              <td colSpan={6} className="border px-2 py-4 text-center text-neutral-400">
                No reserved units right now.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
