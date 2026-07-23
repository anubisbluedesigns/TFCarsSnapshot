"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";

interface DealRow {
  stock_number: string;
  customer_name: string | null;
  vehicle: string | null;
  sales_1: string | null;
  sales_2: string | null;
  deal_type: string | null;
  deal_date: string;
}

interface Props {
  storeId: number;
  storeType: string;
  storeSlug: string;
  onFocusStock: (stockNumber: string) => void;
}

export default function SoldNotUpdated({ storeId, storeType, storeSlug, onFocusStock }: Props) {
  const [rows, setRows] = useState<DealRow[] | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .get<DealRow[]>(`/sold-not-updated?store_id=${storeId}&store_type=${storeType}&store_slug=${storeSlug}`)
      .then((r) => {
        if (!cancelled) setRows(r);
      })
      .catch((e) => {
        if (cancelled) return;
        if (e instanceof ApiError && e.status === 503) setUnavailable(true);
        setRows([]);
      });
    return () => {
      cancelled = true;
    };
  }, [storeId, storeType, storeSlug]);

  if (unavailable || rows === null || rows.length === 0) return null;

  return (
    <div className="mb-3 border border-amber-300 bg-amber-50 rounded print:hidden">
      <div className="px-3 py-2 border-b border-amber-300 font-semibold text-sm text-amber-900">
        Sold Not Updated ({rows.length}) — these show sold in the sold log but aren&apos;t marked SOLD here yet
      </div>
      <div className="max-h-48 overflow-y-auto divide-y divide-amber-200">
        {rows.map((r) => (
          <button
            key={r.stock_number}
            onClick={() => onFocusStock(r.stock_number)}
            className="w-full text-left px-3 py-1.5 text-sm hover:bg-amber-100 flex justify-between items-center gap-2"
          >
            <span className="font-medium">{r.stock_number}</span>
            <span className="text-neutral-600 truncate flex-1">{r.vehicle}</span>
            <span className="text-neutral-500 text-xs">{r.customer_name}</span>
            <span className="text-neutral-400 text-xs">{r.sales_1}{r.sales_2 ? ` / ${r.sales_2}` : ""}</span>
            <span className="text-neutral-400 text-xs">{r.deal_date}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
