"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { StatusOption } from "@/lib/types";

interface Props {
  storeId: number;
  storeType: string;
  buckets: string[];
  statusOptions: StatusOption[];
  onClose: () => void;
  onCreated: () => void;
}

export default function AddVehicleForm({ storeId, storeType, buckets, statusOptions, onClose, onCreated }: Props) {
  const [form, setForm] = useState({
    stock_number: "",
    vin_tail: "",
    year: "",
    make: "",
    model: "",
    trim_details: "",
    mileage: "",
    price_rank: "",
    status: statusOptions[0]?.value ?? "",
    bucket: buckets[0] ?? "New",
    price: "",
    cost: "",
    inventory_date: new Date().toISOString().slice(0, 10),
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.post("/vehicles", {
        originating_store_id: storeId,
        current_store_id: storeId,
        store_type: storeType,
        stock_number: form.stock_number || null,
        vin_tail: form.vin_tail || null,
        year: form.year ? Number(form.year) : null,
        make: form.make || null,
        model: form.model || null,
        trim_details: form.trim_details || null,
        mileage: form.mileage ? Number(form.mileage) : null,
        price_rank: form.price_rank ? Number(form.price_rank) : null,
        status: form.status,
        bucket: form.bucket,
        price: form.price ? Number(form.price) : null,
        cost: form.cost ? Number(form.cost) : null,
        inventory_date: form.inventory_date || null,
      });
      onCreated();
    } catch {
      setError("Could not create vehicle — check required fields.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 print:hidden">
      <form onSubmit={submit} className="bg-white rounded-lg p-5 w-full max-w-lg space-y-3 max-h-[85vh] overflow-y-auto">
        <h2 className="font-semibold text-base">Add Vehicle</h2>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <label>
            Stock # / VIN tail
            <input className="w-full border rounded px-2 py-1 mt-0.5" value={form.stock_number} onChange={(e) => set("stock_number", e.target.value)} />
          </label>
          <label>
            VIN tail (if pre-stock)
            <input className="w-full border rounded px-2 py-1 mt-0.5" value={form.vin_tail} onChange={(e) => set("vin_tail", e.target.value)} />
          </label>
          <label>
            Year
            <input className="w-full border rounded px-2 py-1 mt-0.5" value={form.year} onChange={(e) => set("year", e.target.value)} />
          </label>
          <label>
            Make
            <input className="w-full border rounded px-2 py-1 mt-0.5" value={form.make} onChange={(e) => set("make", e.target.value)} />
          </label>
          <label>
            Model
            <input className="w-full border rounded px-2 py-1 mt-0.5" value={form.model} onChange={(e) => set("model", e.target.value)} />
          </label>
          <label className="col-span-2">
            Trim / Details
            <input className="w-full border rounded px-2 py-1 mt-0.5" value={form.trim_details} onChange={(e) => set("trim_details", e.target.value)} />
          </label>
          <label>
            Mileage
            <input className="w-full border rounded px-2 py-1 mt-0.5" value={form.mileage} onChange={(e) => set("mileage", e.target.value)} />
          </label>
          <label>
            Price Rank
            <select className="w-full border rounded px-2 py-1 mt-0.5" value={form.price_rank} onChange={(e) => set("price_rank", e.target.value)}>
              <option value="">-</option>
              <option value="1">1 — common</option>
              <option value="2">2 — moderate</option>
              <option value="3">3 — rare</option>
            </select>
          </label>
          <label>
            Status
            <select className="w-full border rounded px-2 py-1 mt-0.5" value={form.status} onChange={(e) => set("status", e.target.value)}>
              {statusOptions.map((s) => (
                <option key={s.id} value={s.value}>{s.value}</option>
              ))}
            </select>
          </label>
          <label>
            Bucket
            <select className="w-full border rounded px-2 py-1 mt-0.5" value={form.bucket} onChange={(e) => set("bucket", e.target.value)}>
              {buckets.map((b) => (
                <option key={b} value={b}>{b}</option>
              ))}
            </select>
          </label>
          <label>
            Price
            <input className="w-full border rounded px-2 py-1 mt-0.5" value={form.price} onChange={(e) => set("price", e.target.value)} />
          </label>
          <label>
            Cost
            <input className="w-full border rounded px-2 py-1 mt-0.5" value={form.cost} onChange={(e) => set("cost", e.target.value)} />
          </label>
          <label>
            Inventory Date
            <input type="date" className="w-full border rounded px-2 py-1 mt-0.5" value={form.inventory_date} onChange={(e) => set("inventory_date", e.target.value)} />
          </label>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" onClick={onClose} className="text-sm px-3 py-1.5 rounded border">Cancel</button>
          <button type="submit" disabled={saving} className="text-sm px-3 py-1.5 rounded bg-blue-600 text-white disabled:opacity-50">
            {saving ? "Saving..." : "Create"}
          </button>
        </div>
      </form>
    </div>
  );
}
