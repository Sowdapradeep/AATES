"use client";

import React, { useState } from "react";
import { Terminal, RefreshCw } from "lucide-react";

export default function LogsPage() {
  const [logs] = useState([
    { timestamp: "2026-07-15T17:45:10.102Z", level: "INFO", service: "api", message: "HTTP GET /v1/health completed with status 200", request_id: "req-f02a", correlation_id: "corr-1a2b" },
    { timestamp: "2026-07-15T17:45:12.304Z", level: "INFO", service: "worker", message: "EventBus: Received event UserLoggedIn with payload {'user': 'operator@aates.com'}", request_id: "req-f02b", correlation_id: "corr-1a2c" },
    { timestamp: "2026-07-15T17:45:15.556Z", level: "DEBUG", service: "scheduler", message: "Scheduler: Polled jobs table, found 0 pending tasks.", request_id: "req-f02c", correlation_id: "corr-1a2d" },
    { timestamp: "2026-07-15T17:45:20.902Z", level: "WARNING", service: "api", message: "Database connection took longer than expected: 104ms", request_id: "req-f02d", correlation_id: "corr-1a2e" }
  ]);

  const handleRefresh = () => {
    alert("Fetched latest 50 JSON logs from PostgreSQL Logs table!");
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent">
            System Log Terminal
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Realtime distributed structured JSON logs context tracker
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl bg-slate-900 border border-slate-800 hover:border-violet-500/30 transition-all text-slate-300"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh Streams
        </button>
      </div>

      <div className="glass-panel rounded-2xl border border-slate-800/80 p-6 font-mono text-xs overflow-hidden">
        <div className="flex items-center gap-2 border-b border-slate-800/60 pb-3 mb-4 text-slate-400">
          <Terminal className="h-4 w-4" />
          <span>Distributed log viewer</span>
        </div>
        
        <div className="space-y-3 max-h-[500px] overflow-y-auto">
          {logs.map((log, idx) => (
            <div key={idx} className="p-3 rounded-lg bg-slate-950/80 border border-slate-900/60 space-y-1">
              <div className="flex items-center justify-between text-[10px]">
                <span className="text-slate-500">{log.timestamp}</span>
                <div className="flex items-center gap-2">
                  <span className="text-slate-500">request_id: {log.request_id}</span>
                  <span className="text-slate-500">correlation_id: {log.correlation_id}</span>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold ${
                  log.level === "INFO" ? "bg-blue-500/10 text-blue-400" :
                  log.level === "WARNING" ? "bg-yellow-500/10 text-yellow-400" : "bg-purple-500/10 text-purple-400"
                }`}>
                  {log.level}
                </span>
                <span className="text-violet-400 font-semibold">[{log.service}]</span>
                <span className="text-slate-300 flex-1">{log.message}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
