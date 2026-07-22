"use client";

import { useCallback, useMemo, useState } from "react";
import { AgGridReact } from "ag-grid-react";
import {
  AllCommunityModule,
  ModuleRegistry,
  type CellClassParams,
  type ColDef,
  type ValueGetterParams,
} from "ag-grid-community";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-quartz.css";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { StatusOption, Vehicle } from "@/lib/types";

ModuleRegistry.registerModules([AllCommunityModule]);

interface Props {
  vehicles: Vehicle[];
  statusOptions: StatusOption[];
  statusColors: Record<string, string>;
  bucketOptions: string[];
  storeId: number;
  storeType: string;
  onChanged: () => void;
  quickFilterText?: string;
}

function ageDays(inventoryDate: string | null): number | null {
  if (!inventoryDate) return null;
  const d = new Date(inventoryDate);
  return Math.floor((Date.now() - d.getTime()) / (1000 * 60 * 60 * 24));
}

function ageColor(age: number | null): string {
  if (age === null) return "";
  if (age < 15) return "";
  if (age < 30) return "bg-yellow-100";
  if (age < 45) return "bg-orange-200";
  if (age < 60) return "bg-orange-300";
  return "bg-red-300";
}

export default function InventoryGrid({ vehicles, statusOptions, statusColors, bucketOptions, storeId, storeType, onChanged, quickFilterText }: Props) {
  const { canEditStore, canEditStatus } = useAuth();
  const fullEdit = canEditStore(storeId, storeType);
  const statusEdit = canEditStatus(storeId, storeType);
  const [saving, setSaving] = useState<number | null>(null);

  const statusValues = useMemo(() => statusOptions.map((s) => s.value), [statusOptions]);

  const commit = useCallback(
    async (vehicleId: number, field: string, value: unknown) => {
      setSaving(vehicleId);
      try {
        if (field === "price") {
          await api.post(`/vehicles/${vehicleId}/price-change`, { new_price: Number(value) });
        } else {
          await api.patch(`/vehicles/${vehicleId}`, { [field]: value });
        }
        onChanged();
      } finally {
        setSaving(null);
      }
    },
    [onChanged]
  );

  const columnDefs = useMemo<ColDef<Vehicle>[]>(
    () => [
      { field: "stock_number", headerName: "Stock #", pinned: "left", width: 130, editable: fullEdit },
      { field: "year", headerName: "Year", width: 85, editable: fullEdit },
      { field: "make", headerName: "Make", width: 110, editable: fullEdit },
      { field: "model", headerName: "Model", width: 140, editable: fullEdit },
      { field: "trim_details", headerName: "Trim / Details", width: 220, editable: fullEdit },
      { field: "mileage", headerName: "Mileage", width: 100, editable: fullEdit, valueFormatter: (p) => (p.value != null ? p.value.toLocaleString() : "") },
      {
        field: "price_rank",
        headerName: "Rank",
        width: 80,
        editable: fullEdit,
        cellEditor: "agSelectCellEditor",
        cellEditorParams: { values: [1, 2, 3] },
      },
      {
        field: "status",
        headerName: "Status",
        width: 120,
        editable: fullEdit || statusEdit,
        cellEditor: "agSelectCellEditor",
        cellEditorParams: { values: statusValues },
        cellStyle: (p: CellClassParams<Vehicle>) => {
          const color = statusColors[p.value as string];
          return color ? { backgroundColor: color } : null;
        },
      },
      {
        field: "bucket",
        headerName: "Bucket",
        width: 160,
        editable: fullEdit,
        cellEditor: "agSelectCellEditor",
        cellEditorParams: { values: bucketOptions },
      },
      {
        headerName: "Age",
        width: 70,
        valueGetter: (p: ValueGetterParams<Vehicle>) => ageDays(p.data?.inventory_date ?? null),
        cellClass: (p: CellClassParams<Vehicle>) => ageColor(p.value),
      },
      { field: "price", headerName: "Price", width: 110, editable: fullEdit, valueFormatter: (p) => (p.value != null ? `$${p.value.toLocaleString()}` : "") },
      { field: "cost", headerName: "Cost", width: 110, editable: fullEdit, valueFormatter: (p) => (p.value != null ? `$${p.value.toLocaleString()}` : "") },
      {
        field: "available_gross",
        headerName: "Avail. Gross",
        width: 120,
        valueFormatter: (p) => (p.value != null ? `$${p.value.toLocaleString()}` : ""),
        cellClass: (p: CellClassParams<Vehicle>) => {
          if (p.value == null) return "";
          if (p.value < 0) return "bg-red-200";
          if (p.value > 3000) return "bg-green-200";
          return "bg-yellow-50";
        },
      },
      { field: "reserved", headerName: "Reserved", width: 90 },
      { field: "reserved_sales_rep", headerName: "Rep", width: 110 },
      { field: "reserved_guest_name", headerName: "Guest", width: 130 },
      { field: "unwound", headerName: "Unwind", width: 90, editable: fullEdit },
      { field: "tag_otd_special", headerName: "OTD Special", width: 100, editable: fullEdit },
    ],
    [fullEdit, statusEdit, statusValues, statusColors, bucketOptions]
  );

  return (
    <div className="ag-theme-quartz" style={{ height: "70vh", width: "100%" }}>
      <AgGridReact<Vehicle>
        theme="legacy"
        rowData={vehicles}
        columnDefs={columnDefs}
        quickFilterText={quickFilterText}
        getRowId={(p) => String(p.data.id)}
        onCellValueChanged={(e) => {
          if (!e.colDef.field) return;
          if (e.colDef.field === "unwound") {
            api.post(`/vehicles/${e.data.id}/unwind`, { unwind: e.newValue }).then(onChanged);
            return;
          }
          if (e.colDef.field === "bucket") {
            api.post(`/vehicles/${e.data.id}/bucket-move`, { bucket: e.newValue }).then(onChanged);
            return;
          }
          commit(e.data.id, e.colDef.field, e.newValue);
        }}
        loadingOverlayComponentParams={{ loadingMessage: saving ? "Saving..." : undefined }}
      />
    </div>
  );
}
