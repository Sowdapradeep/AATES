"use client";

import React from "react";
import { AgentWorkflowGraph } from "@/components/AgentWorkflowGraph";

export default function N8nLiveGraphPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 via-blue-400 to-violet-400 bg-clip-text text-transparent">
            Live Creation Pipeline
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time visual node-and-edge orchestration graph of all AI Council Agents during autonomous production cycles.
          </p>
        </div>
      </div>

      {/* n8n Live Agent Execution Node & Edge Graph */}
      <AgentWorkflowGraph />
    </div>
  );
}
