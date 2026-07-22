"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Store, StatusOption, Scope } from "@/lib/types";

export default function SettingsPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [stores, setStores] = useState<Store[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [statusOptions, setStatusOptions] = useState<StatusOption[]>([]);
  const [colors, setColors] = useState<Record<string, string>>({});
  const [title, setTitle] = useState("");
  const [savedMsg, setSavedMsg] = useState("");

  useEffect(() => {
    if (user && user.role !== "full_edit") router.replace("/");
  }, [user, router]);

  const fullEditScopes: (Scope & { store?: Store })[] =
    user?.role === "full_edit" ? user.scopes : [];

  useEffect(() => {
    if (!user) return;
    api.get<Store[]>("/stores").then((s) => {
      setStores(s);
      const first = fullEditScopes[0];
      if (first) {
        const store = s.find((st) => st.id === first.store_id);
        const type = first.store_type ?? (store?.offers_used ? "used" : "new");
        setSelected(`${first.store_id}:${type}`);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  useEffect(() => {
    if (!selected) return;
    const [storeId, type] = selected.split(":");
    api.get<StatusOption[]>(`/status-options?store_id=${storeId}&store_type=${type}`).then(setStatusOptions);
    api.get<Record<string, string>>(`/settings/status-colors?store_id=${storeId}&store_type=${type}`).then(setColors);
    const month = new Date().toISOString().slice(0, 7);
    api
      .get<{ title: string } | null>(`/settings/report-title?store_id=${storeId}&month=${month}`)
      .then((r) => setTitle(r?.title ?? ""))
      .catch(() => setTitle(""));
  }, [selected]);

  if (!user || user.role !== "full_edit") return null;

  const [storeId, storeType] = selected ? selected.split(":") : ["", ""];

  async function saveColor(status: string, color: string) {
    setColors((c) => ({ ...c, [status]: color }));
    await api.put("/settings/status-colors", {
      store_id: Number(storeId),
      store_type: storeType,
      key_value: status,
      color_hex: color,
    });
  }

  async function saveTitle() {
    const month = new Date().toISOString().slice(0, 7);
    await api.put("/settings/report-title", { store_id: Number(storeId), month, title });
    setSavedMsg("Saved!");
    setTimeout(() => setSavedMsg(""), 1500);
  }

  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-lg font-semibold mb-4">Settings</h1>

      <label className="block text-sm mb-4">
        Store / Type
        <select value={selected} onChange={(e) => setSelected(e.target.value)} className="mt-1 border rounded px-2 py-1 block w-full max-w-xs">
          {fullEditScopes.map((s) => {
            const store = stores.find((st) => st.id === s.store_id);
            if (!store) return null;
            const types = s.store_type ? [s.store_type] : ["new", "used"].filter((t) => (t === "new" ? store.offers_new : store.offers_used));
            return types.map((t) => (
              <option key={`${s.store_id}:${t}`} value={`${s.store_id}:${t}`}>
                {store.name} {t}
              </option>
            ));
          })}
        </select>
      </label>

      {selected && (
        <>
          <section className="mb-6">
            <h2 className="font-medium text-sm mb-2">Monthly Report Title</h2>
            <p className="text-xs text-neutral-500 mb-2">
              The fun rotating name (e.g. &quot;Pole Line Palace Round 14&quot;) — printed at the top of the weekly rollup.
            </p>
            <div className="flex gap-2">
              <input value={title} onChange={(e) => setTitle(e.target.value)} className="border rounded px-2 py-1 text-sm flex-1" />
              <button onClick={saveTitle} className="bg-blue-600 text-white text-sm px-3 py-1 rounded">Save</button>
              {savedMsg && <span className="text-xs text-green-600 self-center">{savedMsg}</span>}
            </div>
          </section>

          <section>
            <h2 className="font-medium text-sm mb-2">Status Colors</h2>
            <div className="space-y-2">
              {statusOptions.map((s) => (
                <div key={s.id} className="flex items-center gap-3">
                  <span className="text-sm w-40">{s.value}</span>
                  <input
                    type="color"
                    value={colors[s.value] ?? "#ffffff"}
                    onChange={(e) => saveColor(s.value, e.target.value)}
                  />
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
