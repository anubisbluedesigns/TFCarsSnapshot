"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
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
  const [showAdd, setShowAdd] = useState(false);
  const [loading, setLoading] = useState(true);
  const [focusStock, setFocusStock] = useState<string>("");

  useEffect(() => {
    if (!user) return;
    api.get<Store[]>("/stores").then((stores) => {
      const s = stores.find((st) => st.slug === storeSlug) ?? null;
      setStore(s);
    });
  }, [user, storeSlug]);

  const refresh = useMemo(
    () => async () => {
      if (!store) return;
      setLoading(true);
      const [v, so] = await Promise.all([
        api.get<Vehicle[]>(`/vehicles?store_id=${store.id}&store_type=${storeType}`),
        api.get<StatusOption[]>(`/status-options?store_id=${store.id}&store_type=${storeType}`),
      ]);
      setVehicles(v);
      setStatusOptions(so);
      setLoading(false);
      try {
        const colors = await api.get<Record<string, string>>(
          `/settings/status-colors?store_id=${store.id}&store_type=${storeType}`
        );
        setStatusColors(colors);
      } catch {
        setStatusColors({});
      }
    },
    [store, storeType]
  );

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (!user) return null;
  if (!store) return <div className="p-6 text-sm text-neutral-500">Loading store...</div>;

  const buckets = Array.from(new Set(vehicles.map((v) => v.bucket))).sort();
  const filtered = activeBucket === "__all__" ? vehicles : vehicles.filter((v) => v.bucket === activeBucket);
  const fullEdit = canEditStore(store.id, storeType);

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-3 print:hidden">
        <h1 className="text-lg font-semibold">
          {store.name} — {storeType === "new" ? "New" : "Used"} Inventory
        </h1>
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
            onClick={() => setActiveBucket(b)}
            className={`text-sm px-3 py-1 rounded border ${activeBucket === b ? "bg-blue-600 text-white border-blue-600" : "bg-white border-neutral-300"}`}
          >
            {b} ({vehicles.filter((v) => v.bucket === b).length})
          </button>
        ))}
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
