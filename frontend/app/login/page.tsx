"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth, devLogin } from "@/lib/auth";

export default function LoginPage() {
  const { loginWithToken } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleDevLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await devLogin(email);
      loginWithToken(res.access_token, res.user);
      router.push("/");
    } catch {
      setError("No matching active user for that email.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-24 p-6 border border-neutral-200 rounded-lg bg-white">
      <h1 className="text-lg font-semibold mb-1">Dealership Inventory Snapshot</h1>
      <p className="text-sm text-neutral-500 mb-6">Sign in to continue.</p>

      {/* Production: replace with Google Identity Services sign-in button
          (NEXT_PUBLIC_GOOGLE_CLIENT_ID), posting the id_token to /auth/login. */}
      <form onSubmit={handleDevLogin} className="space-y-3">
        <label className="block text-sm">
          Work email (dev login)
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="brandonw@twinfalls-chevy.com"
            className="mt-1 w-full border border-neutral-300 rounded px-2 py-1.5 text-sm"
          />
        </label>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={busy}
          className="w-full bg-blue-600 text-white rounded py-1.5 text-sm font-medium disabled:opacity-50"
        >
          {busy ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}
