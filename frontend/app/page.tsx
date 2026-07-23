"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import type { Store } from "@/lib/types";

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    api
      .get<Store[]>("/stores")
      .then((stores) => {
        for (const store of stores) {
          for (const type of ["used", "new"] as const) {
            const offers = type === "new" ? store.offers_new : store.offers_used;
            const hasScope = user.scopes.some(
              (s) => s.store_id === store.id && (s.store_type === null || s.store_type === type)
            );
            if (offers && hasScope) {
              router.replace(`/dashboard/${store.slug}/${type}`);
              return;
            }
          }
        }
      })
      .catch(() => {});
  }, [user, loading, router]);

  return <div className="p-6 text-sm text-neutral-500">Loading...</div>;
}
