"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import type { Store } from "@/lib/types";

export default function NavBar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [stores, setStores] = useState<Store[]>([]);

  useEffect(() => {
    if (!user) return;
    api
      .get<Store[]>("/stores")
      .then(setStores)
      .catch(() => setStores([]));
  }, [user]);

  if (pathname === "/login" || !user) return null;

  const links: { href: string; label: string }[] = [];
  for (const store of stores) {
    for (const type of ["new", "used"] as const) {
      const offers = type === "new" ? store.offers_new : store.offers_used;
      const hasScope = user.scopes.some((s) => s.store_id === store.id && (s.store_type === null || s.store_type === type));
      if (offers && hasScope) {
        links.push({ href: `/inventory/${store.slug}/${type}`, label: `${store.name} ${type === "new" ? "New" : "Used"}` });
      }
    }
  }

  return (
    <header className="border-b border-neutral-200 bg-white px-4 py-2 flex items-center gap-4 flex-wrap print:hidden">
      <span className="font-semibold text-sm">Inventory Snapshot</span>
      <nav className="flex gap-3 flex-wrap text-sm">
        {links.map((l) => (
          <Link key={l.href} href={l.href} className={`hover:underline ${pathname.startsWith(l.href) ? "font-semibold text-blue-700" : "text-neutral-700"}`}>
            {l.label}
          </Link>
        ))}
        <Link href="/reprice-due" className="text-neutral-700 hover:underline">Reprice Due</Link>
        <Link href="/reserved" className="text-neutral-700 hover:underline">Reserved</Link>
        {user.role === "full_edit" && (
          <Link href="/settings" className="text-neutral-700 hover:underline">Settings</Link>
        )}
      </nav>
      <div className="ml-auto flex items-center gap-2 text-sm text-neutral-600">
        <span>{user.name} ({user.role})</span>
        <button onClick={logout} className="text-red-600 hover:underline">Log out</button>
      </div>
    </header>
  );
}
