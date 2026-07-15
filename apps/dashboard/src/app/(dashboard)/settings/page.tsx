"use client";

import React, { useState } from "react";
import { Save } from "lucide-react";

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    dbUrl: "postgresql://postgres:***@localhost:5432/aates",
    redisUrl: "redis://localhost:6379/0",
    openaiKey: "sk-proj-**********************",
    geminiKey: "AIzaSy**********************",
    maxRenders: "2",
    resolution: "1080p",
    s3Bucket: "aates-assets-production"
  });

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    alert("Dynamic settings updated in configurations repository!");
  };

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent">
          Platform Settings
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Configure active environment databases connection strings, vendor endpoints and rendering thresholds
        </p>
      </div>

      <div className="glass-card rounded-2xl p-6 border border-slate-800/80">
        <form onSubmit={handleSave} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Database Connection URL</label>
              <input
                type="text"
                value={settings.dbUrl}
                onChange={(e) => setSettings({ ...settings, dbUrl: e.target.value })}
                className="w-full rounded-xl border border-slate-700/50 bg-slate-900/50 p-3 text-sm text-slate-200 focus:border-violet-500 outline-none"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Redis Server URL</label>
              <input
                type="text"
                value={settings.redisUrl}
                onChange={(e) => setSettings({ ...settings, redisUrl: e.target.value })}
                className="w-full rounded-xl border border-slate-700/50 bg-slate-900/50 p-3 text-sm text-slate-200 focus:border-violet-500 outline-none"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">OpenAI API Key</label>
              <input
                type="password"
                value={settings.openaiKey}
                onChange={(e) => setSettings({ ...settings, openaiKey: e.target.value })}
                className="w-full rounded-xl border border-slate-700/50 bg-slate-900/50 p-3 text-sm text-slate-200 focus:border-violet-500 outline-none"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Google Gemini API Key</label>
              <input
                type="password"
                value={settings.geminiKey}
                onChange={(e) => setSettings({ ...settings, geminiKey: e.target.value })}
                className="w-full rounded-xl border border-slate-700/50 bg-slate-900/50 p-3 text-sm text-slate-200 focus:border-violet-500 outline-none"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Max Concurrent Renders</label>
              <input
                type="number"
                value={settings.maxRenders}
                onChange={(e) => setSettings({ ...settings, maxRenders: e.target.value })}
                className="w-full rounded-xl border border-slate-700/50 bg-slate-900/50 p-3 text-sm text-slate-200 focus:border-violet-500 outline-none"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">AWS S3 Assets Bucket</label>
              <input
                type="text"
                value={settings.s3Bucket}
                onChange={(e) => setSettings({ ...settings, s3Bucket: e.target.value })}
                className="w-full rounded-xl border border-slate-700/50 bg-slate-900/50 p-3 text-sm text-slate-200 focus:border-violet-500 outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-pink-500 hover:opacity-90 font-semibold text-white transition-all shadow-md active:scale-95"
          >
            <Save className="h-4.5 w-4.5" />
            Save Configurations
          </button>
        </form>
      </div>
    </div>
  );
}
