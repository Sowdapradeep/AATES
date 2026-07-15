"use client";

import React, { useState } from "react";
import { User } from "lucide-react";

export default function ProfilePage() {
  const [profile] = useState({
    email: "operator@aates.com",
    role: "System Operator",
    joined: "July 2026",
    status: "Active"
  });

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent">
          User Profile
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Manage your account settings, credentials, and access control capabilities
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card rounded-2xl p-6 border border-slate-800/80 flex flex-col items-center justify-center text-center">
          <div className="h-20 w-20 rounded-full bg-violet-600/20 border border-violet-500/30 flex items-center justify-center mb-4">
            <User className="h-10 w-10 text-violet-400" />
          </div>
          <h2 className="text-lg font-semibold text-slate-200">{profile.email}</h2>
          <p className="text-xs text-violet-400 font-semibold uppercase mt-1">{profile.role}</p>
        </div>

        <div className="md:col-span-2 glass-card rounded-2xl p-6 border border-slate-800/80 space-y-6">
          <h3 className="text-md font-semibold text-slate-200 border-b border-slate-800/60 pb-3">Account Details</h3>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Email Address</span>
              <span className="text-sm text-slate-300">{profile.email}</span>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">System Role</span>
              <span className="text-sm text-slate-300">{profile.role}</span>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Account Status</span>
              <span className="text-sm text-emerald-400">{profile.status}</span>
            </div>
            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Joined Date</span>
              <span className="text-sm text-slate-300">{profile.joined}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
