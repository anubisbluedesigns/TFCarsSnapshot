"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import InventoryGrid from "@/components/InventoryGrid";
import AddVehicleForm from "@/components/AddVehicleForm";
import SoldNotUpdated from "@/components/SoldNotUpdated";
import type { Store, StatusOption, Vehicle } from "@/lib/types";

export default function InventoryPage() {
  const params = useParams<{ storeSlug: string; storeType: string }>();
  const { storeSlug, storeType } = params;
  const { user, canEditStore } = useAuth();

  const [store, setStore] = useState<Store | null>(null);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [statusOptions, setStatusOptions] = useState<StatusOption[]>([]);
  const [statusColors, setStatusColors] = useState<Record<string, string>>({});
  const [activeBucket, setActiveBucket] = useState<string>("__all__");
  const [activeModel, setActiveModel] = useState<string>("__all__");
  const [showAdd, setShowAdd] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [focusStock, setFocusStock] = useState<string>("");

  useEffect(() => {
    if (!user) return;
    api.get<Store[]>("/stores").then((stores) => {
      const s = stores.find((st) => st.slug === storeSlug) ?? null;
      setStore(s);
      if (!s) setError("You don't have access to this store.");
    });
  }, [user, storeSlug]);

  const refresh = useMemo(
    () => async () => {
      if (!store) return;
      setLoading(true);
      setError(null);
      try {
        const [v, so] = await Promise.all([
          api.get<Vehicle[]>(`/vehicles?store_id=${store.id}&store_type=${storeType}`),
          api.get<StatusOption[]>(`/status-options?store_id=${store.id}&store_type=${storeType}`),
        ]);
        setVehicles(v);
        setStatusOptions(so);
        try {
          const colors = await api.get<Record<string, string>>(
            `/settings/status-colors?store_id=${store.id}&store_type=${storeType}`
          );
          setStatusColors(colors);
        } catch {
          setStatusColors({});
        }
      } catch (e) {
        setError(
          e instanceof ApiError && e.status === 403
            ? "You don't have access to this store/type. Try logging out and back in, or check with an admin."
            : "Couldn't load inventory right now."
        );
      } finally {
        setLoading(false);
      }
    },
    [store, storeType]
  );

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (!user) return null;
  if (error) return <div className="p-6 text-sm text-red-600">{error}</div>;
  if (!store) return <div className="p-6 text-sm text-neutral-500">Loading store...</div>;

  const buckets = Array.from(new Set(vehicles.map((v) => v.bucket))).sort();
  const byBucket = activeBucket === "__all__" ? vehicles : vehicles.filter((v) => v.bucket === activeBucket);
  const models = Array.from(new Set(byBucket.map((v) => v.model).filter((m): m is string => !!m))).sort();
  const filtered = activeModel === "__all__" ? byBucket : byBucket.filter((v) => v.model === activeModel);
  const fullEdit = canEditStore(store.id, storeType);

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-3 print:hidden">
        <div>
          <h1 className="text-lg font-semibold">
            {store.name} — {storeType === "new" ? "New" : "Used"} Inventory
          </h1>
          <Link href={`/dashboard/${storeSlug}/${storeType}`} className="text-sm text-blue-700 hover:underline">
            ← Back to dashboard
          </Link>
        </div>
        {fullEdit && (
          <button
            onClick={() => setShowAdd(true)}
            className="bg-blue-600 text-white text-sm px-3 py-1.5 rounded"
          >
            + Add Vehicle
          </button>
        )}
      </div>

      <SoldNotUpdated
        storeId={store.id}
        storeType={storeType}
        storeSlug={storeSlug}
        onFocusStock={(stock) => {
          setActiveBucket("__all__");
          setFocusStock(stock);
        }}
      />

      <div className="flex gap-2 mb-3 flex-wrap print:hidden">
        <button
          onClick={() => setActiveBucket("__all__")}
          className={`text-sm px-3 py-1 rounded border ${activeBucket === "__all__" ? "bg-blue-600 text-white border-blue-600" : "bg-white border-neutral-300"}`}
        >
          All ({vehicles.length})
        </button>
        {buckets.map((b) => (
          <button
            key={b}
            onClick={() => {
              setActiveBucket(b);
              setActiveModel("__all__");
            }}
            className={`text-sm px-3 py-1 rounded border ${activeBucket === b ? "bg-blue-600 text-white border-blue-600" : "bg-white border-neutral-300"}`}
          >
            {b} ({vehicles.filter((v) => v.bucket === b).length})
          </button>
        ))}
        {models.length > 1 && (
          <select
            value={activeModel}
            onChange={(e) => setActiveModel(e.target.value)}
            className="text-sm px-2 py-1 rounded border border-neutral-300 bg-white"
          >
            <option value="__all__">All Models</option>
            {models.map((m) => (
              <option key={m} value={m}>
                {m} ({byBucket.filter((v) => v.model === m).length})
              </option>
            ))}
          </select>
        )}
        {focusStock && (
          <button
            onClick={() => setFocusStock("")}
            className="text-sm px-3 py-1 rounded border bg-amber-100 border-amber-300"
          >
            Filtered: {focusStock} ✕
          </button>
        )}
      </div>

      {loading ? (
        <div className="text-sm text-neutral-500">Loading vehicles...</div>
      ) : (
        <InventoryGrid
          vehicles={filtered}
          statusOptions={statusOptions}
          statusColors={statusColors}
          bucketOptions={buckets}
          storeId={store.id}
          storeType={storeType}
          onChanged={refresh}
          quickFilterText={focusStock}
        />
      )}

      {showAdd && (
        <AddVehicleForm
          storeId={store.id}
          storeType={storeType}
          buckets={buckets}
          statusOptions={statusOptions}
          onClose={() => setShowAdd(false)}
          onCreated={() => {
            setShowAdd(false);
            refresh();
          }}
        />
      )}
    </div>
  );
}
