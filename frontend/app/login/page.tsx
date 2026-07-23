"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth, devLogin, googleLogin } from "@/lib/auth";
import GoogleSignInButton from "@/components/GoogleSignInButton";

const SHOW_DEV_LOGIN = process.env.NEXT_PUBLIC_SHOW_DEV_LOGIN === "true";

export default function LoginPage() {
  const { loginWithToken } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleGoogleToken(idToken: string) {
    setError(null);
    try {
      const res = await googleLogin(idToken);
      loginWithToken(res.access_token, res.user);
      router.push("/");
    } catch {
      setError("This Google account isn't set up for the app yet.");
    }
  }

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
      <p className="text-sm text-neutral-500 mb-6">Sign in with your work Google account.</p>

      <GoogleSignInButton onToken={handleGoogleToken} />
      {error && <p className="text-sm text-red-600 mt-3">{error}</p>}

      {SHOW_DEV_LOGIN && (
        <form onSubmit={handleDevLogin} className="space-y-3 mt-6 pt-4 border-t border-neutral-200">
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
          <button
            type="submit"
            disabled={busy}
            className="w-full bg-neutral-700 text-white rounded py-1.5 text-sm font-medium disabled:opacity-50"
          >
            {busy ? "Signing in..." : "Dev sign in (bypasses Google)"}
          </button>
        </form>
      )}
    </div>
  );
}
