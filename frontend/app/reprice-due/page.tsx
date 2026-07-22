"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { RepriceDueRow, Store } from "@/lib/types";

export default function RepriceDuePage() {
  const { user } = useAuth();
  const [options, setOptions] = useState<{ store: Store; type: string }[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [rows, setRows] = useState<RepriceDueRow[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) return;
    api.get<Store[]>("/stores").then((stores) => {
      const opts: { store: Store; type: string }[] = [];
      for (const store of stores) {
        for (const type of ["new", "used"] as const) {
          const offers = type === "new" ? store.offers_new : store.offers_used;
          const hasScope = user.scopes.some((s) => s.store_id === store.id && (s.store_type === null || s.store_type === type));
          if (offers && hasScope) opts.push({ store, type });
        }
      }
      setOptions(opts);
      if (opts.length) setSelected(`${opts[0].store.id}:${opts[0].type}`);
    });
  }, [user]);

  useEffect(() => {
    if (!selected) return;
    const [storeId, type] = selected.split(":");
    setLoading(true);
    api
      .get<RepriceDueRow[]>(`/reprice/due?store_id=${storeId}&store_type=${type}`)
      .then(setRows)
      .finally(() => setLoading(false));
  }, [selected]);

  return (
    <div className="p-6">
      <h1 className="text-lg font-semibold mb-1">Reprice Due</h1>
      <p className="text-sm text-neutral-500 mb-4">
        Vehicles that have crossed a reprice-plan day threshold (per the company-wide rank-based strategy) without a
        price change since.
      </p>

      <select value={selected} onChange={(e) => setSelected(e.target.value)} className="border rounded px-2 py-1 text-sm mb-4">
        {options.map((o) => (
          <option key={`${o.store.id}:${o.type}`} value={`${o.store.id}:${o.type}`}>
            {o.store.name} {o.type}
          </option>
        ))}
      </select>

      {loading ? (
        <div className="text-sm text-neutral-500">Loading...</div>
      ) : (
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-neutral-100 text-left">
              <th className="border px-2 py-1">Stock #</th>
              <th className="border px-2 py-1">Vehicle</th>
              <th className="border px-2 py-1">Rank</th>
              <th className="border px-2 py-1">Age (days)</th>
              <th className="border px-2 py-1">Due Plan</th>
              <th className="border px-2 py-1">Guidance</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.vehicle_id}>
                <td className="border px-2 py-1">{r.stock_number}</td>
                <td className="border px-2 py-1">{[r.year, r.make, r.model].filter(Boolean).join(" ")}</td>
                <td className="border px-2 py-1">{r.price_rank}</td>
                <td className="border px-2 py-1">{r.age_days}</td>
                <td className="border px-2 py-1 font-medium">{r.due_plan}</td>
                <td className="border px-2 py-1">{r.guidance}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={6} className="border px-2 py-4 text-center text-neutral-400">
                  Nothing currently due.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
