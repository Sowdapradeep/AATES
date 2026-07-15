"use client";

import React, { useState } from "react";
import { Clock, Play, Plus } from "lucide-react";

export default function JobsPage() {
  const [jobs, setJobs] = useState([
    { id: "job-1", name: "Daily Video Publishing Check", trigger: "cron", expression: "0 9 * * *", status: "Active", last_run: "2026-07-15 09:00:00" },
    { id: "job-2", name: "Universe Story Continuity Scan", trigger: "interval", expression: "300", status: "Active", last_run: "2026-07-15 17:40:00" },
    { id: "job-3", name: "Budget Usage Sweep", trigger: "cron", expression: "*/30 * * * *", status: "Active", last_run: "2026-07-15 17:30:00" }
  ]);

  const triggerJob = (jobId: string) => {
    alert(`Triggered job ${jobId} manually! Action sent to SchedulerProvider.`);
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-400 to-pink-400 bg-clip-text text-transparent">
            Scheduler Tasks & Jobs
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Trigger, reschedule, and monitor recurring workflow execution timers
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2.5 text-xs font-semibold rounded-xl bg-gradient-to-r from-violet-600 to-pink-500 hover:opacity-90 transition-all text-white shadow-md active:scale-95">
          <Plus className="h-4 w-4" />
          Schedule New Job
        </button>
      </div>

      <div className="glass-card rounded-2xl border border-slate-800/80 p-6 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-800/60 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                <th className="pb-4">Job Name</th>
                <th className="pb-4">Trigger</th>
                <th className="pb-4">Expression</th>
                <th className="pb-4">Status</th>
                <th className="pb-4">Last Execution</th>
                <th className="pb-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40">
              {jobs.map((job) => (
                <tr key={job.id} className="text-slate-300">
                  <td className="py-4 pr-4">
                    <div className="font-semibold text-slate-200">{job.name}</div>
                    <div className="text-[10px] text-slate-500 font-mono mt-0.5">{job.id}</div>
                  </td>
                  <td className="py-4 uppercase text-xs font-bold text-violet-400">{job.trigger}</td>
                  <td className="py-4 font-mono text-xs">{job.expression}</td>
                  <td className="py-4">
                    <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded">
                      {job.status}
                    </span>
                  </td>
                  <td className="py-4 text-xs text-slate-400">{job.last_run}</td>
                  <td className="py-4 text-right">
                    <button
                      onClick={() => triggerJob(job.id)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-violet-500/30 text-xs font-semibold text-slate-300 hover:text-white transition-all active:scale-95"
                    >
                      <Play className="h-3 w-3 fill-slate-300" />
                      Run Now
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
