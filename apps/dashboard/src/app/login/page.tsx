"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Shield, Lock, Mail, Loader2 } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    // Simulate login for foundation preview
    setTimeout(() => {
      if (email && password) {
        // Set local indicator
        localStorage.setItem("authenticated", "true");
        localStorage.setItem("aates_token", "mock_token_value_for_local_dev");
        router.push("/");
      } else {
        setError("Please enter both email and password.");
      }
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="glass-panel w-full max-w-md rounded-2xl p-8 shadow-2xl transition-all duration-300 hover:shadow-violet-500/10">
        <div className="mb-8 flex flex-col items-center">
          <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-violet-600 to-pink-500 text-white shadow-lg">
            <Shield className="h-7 w-7 animate-pulse" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent">
            AATES
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Autonomous AI Tamil Entertainment Studio
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute top-3.5 left-3.5 h-4 w-4 text-slate-400" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="operator@aates.com"
                className="w-full rounded-xl border border-slate-700/50 bg-slate-900/50 py-3 pr-4 pl-11 text-sm text-white placeholder-slate-500 outline-none transition-all focus:border-violet-500 focus:bg-slate-900"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute top-3.5 left-3.5 h-4 w-4 text-slate-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-xl border border-slate-700/50 bg-slate-900/50 py-3 pr-4 pl-11 text-sm text-white placeholder-slate-500 outline-none transition-all focus:border-violet-500 focus:bg-slate-900"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center rounded-xl bg-gradient-to-r from-violet-600 to-pink-500 py-3 font-semibold text-white shadow-lg transition-all hover:opacity-90 active:scale-[0.98] disabled:opacity-50"
          >
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              "Sign In to AATES"
            )}
          </button>
        </form>

        <div className="mt-8 text-center text-xs text-slate-500">
          AATES Cloud Operating Platform v1.0.0
        </div>
      </div>
    </div>
  );
}
