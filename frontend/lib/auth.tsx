"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, clearToken, getToken, setToken } from "./api";
import type { Scope, User } from "./types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  loginWithToken: (token: string, user: User) => void;
  logout: () => void;
  canEditStore: (storeId: number, storeType?: string | null) => boolean;
  canEditStatus: (storeId: number, storeType?: string | null) => boolean;
  canToggleReserved: (storeId: number, storeType?: string | null) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function scopeMatches(scopes: Scope[], storeId: number, storeType?: string | null) {
  return scopes.some(
    (s) => s.store_id === storeId && (s.store_type === null || !storeType || s.store_type === storeType)
  );
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const stored = window.localStorage.getItem("user");
    const token = getToken();
    if (stored && token) {
      setUser(JSON.parse(stored));
    }
    setLoading(false);
  }, []);

  function loginWithToken(token: string, u: User) {
    setToken(token);
    window.localStorage.setItem("user", JSON.stringify(u));
    setUser(u);
  }

  function logout() {
    clearToken();
    window.localStorage.removeItem("user");
    setUser(null);
    router.push("/login");
  }

  const value: AuthContextValue = {
    user,
    loading,
    loginWithToken,
    logout,
    canEditStore: (storeId, storeType) =>
      !!user && user.role === "full_edit" && scopeMatches(user.scopes, storeId, storeType),
    canEditStatus: (storeId, storeType) =>
      !!user &&
      (user.role === "full_edit" || user.role === "manager") &&
      scopeMatches(user.scopes, storeId, storeType),
    canToggleReserved: (storeId, storeType) => !!user && scopeMatches(user.scopes, storeId, storeType),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export async function devLogin(email: string) {
  return api.get<{ access_token: string; user: User }>(`/auth/dev-login?email=${encodeURIComponent(email)}`);
}

export async function googleLogin(idToken: string) {
  return api.post<{ access_token: string; user: User }>("/auth/login", { id_token: idToken });
}
