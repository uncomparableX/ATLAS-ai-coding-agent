"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { GlassCard } from "@/components/glass/glass-card";
import { Bot, Code2, Network, ShieldCheck } from "lucide-react";

const agents = [
  {
    name: "Planner Agent",
    icon: Network,
    desc: "Analyzes intent, browses codebase context, and creates step-by-step execution plans.",
    status: "Active"
  },
  {
    name: "Builder Agent",
    icon: Code2,
    desc: "Writes code, modifies files, and handles the core engineering task.",
    status: "Active"
  },
  {
    name: "Reviewer Agent",
    icon: ShieldCheck,
    desc: "Checks code quality, validates logic, and catches bugs before execution.",
    status: "Active"
  },
  {
    name: "Executor Agent",
    icon: Bot,
    desc: "Runs bash commands, tests, and streams output directly to the workspace terminal.",
    status: "Active"
  }
];

export default function AgentsPage() {
  return (
    <div className="flex h-screen w-full bg-background text-foreground overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 bg-background/50">
        <div className="h-14 border-b border-border flex items-center px-6 bg-background/50 backdrop-blur-sm">
          <Bot className="w-4 h-4 text-accent mr-2" />
          <h1 className="font-semibold tracking-wide">ATLAS Agents</h1>
        </div>

        <div className="p-6 max-w-5xl mx-auto w-full">
          <div className="mb-8 mt-4">
            <h2 className="text-2xl font-bold">Multi-Agent Swarm</h2>
            <p className="text-sm text-muted-foreground mt-1">ATLAS uses a dedicated swarm of specialized internal agents to handle complex workflows.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {agents.map((agent) => (
              <GlassCard key={agent.name} className="p-6 flex flex-col">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-accent/10 rounded-lg">
                      <agent.icon className="w-5 h-5 text-accent" />
                    </div>
                    <h3 className="font-semibold">{agent.name}</h3>
                  </div>
                  <span className="text-[10px] uppercase bg-terminal-green/10 text-terminal-green px-2 py-1 rounded">
                    {agent.status}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {agent.desc}
                </p>
              </GlassCard>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
