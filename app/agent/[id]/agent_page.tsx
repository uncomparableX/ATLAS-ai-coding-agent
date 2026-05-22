"use client";

import { Shell } from "@/components/layout/shell";
import { Sidebar } from "@/components/layout/sidebar";
import { Terminal } from "@/components/terminal/terminal";
import { GlassCard } from "@/components/glass/glass-card";
import { StatusIndicator } from "@/components/agent/status-indicator";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { LogEntry } from "@/types";
import {
  RotateCcw,
  Square,
  Play,
  Container,
  Cpu,
  HardDrive,
  Timer,
  CheckCircle2,
  Loader2,
} from "lucide-react";

export default function AgentPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<
    "running" | "paused" | "failed" | "complete"
  >("running");

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((p) => Math.min(p + 2, 100));

      setLogs((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          timestamp: new Date(),
          level: Math.random() > 0.8 ? "debug" : "info",
          message: `Executing step ${prev.length + 1}: ${
            [
              "Analyzing context",
              "Generating code",
              "Running tests",
              "Validating output",
            ][Math.floor(Math.random() * 4)]
          }`,
          source: "executor",
        },
      ]);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const mockSandbox = {
    containerId: "container_7f3a9d2e",
    status: "running",
    resources: {
      cpu: 45,
      memory: 62,
      disk: 23,
    },
    uptime: 734,
  };

  return (
    <Shell>
      <Sidebar />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="h-14 border-b border-border flex items-center justify-between px-6 bg-background/50 backdrop-blur-sm">
          <div className="flex items-center gap-4">
            <StatusIndicator
              status={{
                state:
                  status === "running"
                    ? "coding"
                    : status === "failed"
                    ? "error"
                    : "idle",
                progress,
                lastActivity: new Date(),
              }}
              showLabel
            />

            <span className="text-sm text-muted-foreground">
              Live Agent Execution
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() =>
                setStatus(status === "running" ? "paused" : "running")
              }
              className="p-2 rounded-lg hover:bg-white/5 transition-colors"
            >
              {status === "running" ? (
                <Square className="w-4 h-4" />
              ) : (
                <Play className="w-4 h-4" />
              )}
            </button>

            <button className="p-2 rounded-lg hover:bg-white/5 transition-colors">
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Progress */}
        <div className="px-6 py-3 border-b border-border">
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-2">
            <span>Execution Progress</span>
            <span>{progress}%</span>
          </div>

          <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-accent rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Main */}
        <div className="flex-1 overflow-auto p-6 grid grid-cols-3 gap-6">
          {/* Logs */}
          <div className="col-span-2">
            <Terminal
              logs={logs}
              live
              title="execution.log"
              className="h-full"
            />
          </div>

          {/* Sandbox */}
          <div className="space-y-4">
            <GlassCard className="p-4">
              <div className="flex items-center gap-3 mb-4">
                <Container className="w-5 h-5 text-accent" />

                <div>
                  <div className="text-sm font-medium">
                    {mockSandbox.containerId}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Uptime: {mockSandbox.uptime}s
                  </div>
                </div>

                <span className="ml-auto text-xs text-green-400">
                  {mockSandbox.status}
                </span>
              </div>

              <div className="space-y-3">
                {[
                  {
                    label: "CPU",
                    value: mockSandbox.resources.cpu,
                    icon: Cpu,
                  },
                  {
                    label: "Memory",
                    value: mockSandbox.resources.memory,
                    icon: HardDrive,
                  },
                  {
                    label: "Disk",
                    value: mockSandbox.resources.disk,
                    icon: Timer,
                  },
                ].map((metric) => (
                  <div key={metric.label}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="flex items-center gap-1.5 text-muted-foreground">
                        <metric.icon className="w-3 h-3" />
                        {metric.label}
                      </span>
                      <span>{metric.value}%</span>
                    </div>

                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-accent rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${metric.value}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>

            <GlassCard className="p-4">
              <h4 className="text-sm font-medium mb-3">Execution Steps</h4>

              <div className="space-y-2">
                {[
                  { status: "complete", label: "Initialize environment" },
                  { status: "complete", label: "Clone repository" },
                  { status: "complete", label: "Analyze codebase" },
                  { status: "running", label: "Generate code" },
                  { status: "pending", label: "Run tests" },
                  { status: "pending", label: "Create PR" },
                ].map((step, i) => (
                  <div key={i} className="flex items-center gap-3">
                    {step.status === "complete" ? (
                      <CheckCircle2 className="w-4 h-4 text-green-400 shrink-0" />
                    ) : step.status === "running" ? (
                      <Loader2 className="w-4 h-4 text-accent animate-spin shrink-0" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-white/20 shrink-0" />
                    )}

                    <span className="text-sm">{step.label}</span>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
        </div>
      </div>
    </Shell>
  );
}
