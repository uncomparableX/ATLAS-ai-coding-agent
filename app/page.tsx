"use client";

import { motion } from "framer-motion";
import { AIActivityViz } from "@/components/agent/ai-activity-viz";
import { GlassCard } from "@/components/glass/glass-card";
import { GlowButton } from "@/components/glass/glow-button";
import { RobotMascot } from "@/components/agent/robot-mascot";
import {
  ArrowRight,
  Bot,
  Code2,
  GitBranch,
  Zap,
  Shield,
  Workflow,
  Terminal,
} from "lucide-react";

const features = [
  {
    icon: Bot,
    title: "Autonomous AI Agents",
    description:
      "Deploy AI agents that plan, code, debug, test, and execute complex engineering workflows autonomously.",
  },
  {
    icon: GitBranch,
    title: "GitHub Native",
    description:
      "Connect repositories, create branches, generate pull requests, and automate reviews directly.",
  },
  {
    icon: Zap,
    title: "Real-Time Execution",
    description:
      "Watch tasks execute live with logs, streamed reasoning, status updates, and live progress tracking.",
  },
  {
    icon: Shield,
    title: "Sandboxed & Secure",
    description:
      "Every execution runs inside isolated secure environments with resource and access controls.",
  },
  {
    icon: Workflow,
    title: "Multi-Agent Orchestration",
    description:
      "Planner, coder, reviewer, and executor agents work together in coordinated workflows.",
  },
  {
    icon: Terminal,
    title: "Developer-First UX",
    description:
      "Built for engineers with logs, terminals, dashboards, observability, and deployment workflows.",
  },
];

const steps = [
  { num: "01", title: "Connect", desc: "Connect repositories, APIs, models, and infrastructure" },
  { num: "02", title: "Assign", desc: "Describe a task in natural language" },
  { num: "03", title: "Execute", desc: "Watch ATLAS plan and run autonomously" },
  { num: "04", title: "Deploy", desc: "Ship production-ready results with confidence" },
];

export default function LandingPage() {
  return (
    <main className="relative min-h-screen bg-background overflow-hidden">
      <AIActivityViz />
      <RobotMascot />

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-background/50 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-gradient-to-br from-accent to-accent-secondary flex items-center justify-center">
              <span className="text-white font-bold text-xs">A</span>
            </div>
            <span className="font-semibold text-foreground">ATLAS</span>
          </div>

          <div className="flex items-center gap-6">
            <a
              href="#features"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Features
            </a>
            <a
              href="#architecture"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Architecture
            </a>
            <a href="/dashboard">
              <GlowButton variant="primary" size="sm">
                Launch ATLAS <ArrowRight className="w-3 h-3" />
              </GlowButton>
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-6xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-6"
          >
            <span className="gradient-text">ATLAS</span>
            <br />
            <span className="text-foreground">Autonomous AI Engineering</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-xl text-muted-foreground max-w-3xl mx-auto mb-10"
          >
            Build, orchestrate, deploy, and manage autonomous AI agents that
            understand your codebase, execute engineering tasks, and ship
            production-grade software.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="flex items-center justify-center gap-4"
          >
            <GlowButton variant="primary" size="lg">
              Launch ATLAS <ArrowRight className="w-4 h-4" />
            </GlowButton>
            <GlowButton variant="secondary" size="lg">
              Explore Platform
            </GlowButton>
          </motion.div>
        </div>

        {/* Hero Visual */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.8 }}
          className="max-w-6xl mx-auto mt-20"
        >
          <GlassCard className="p-1" glow>
            <div className="bg-black/40 rounded-lg overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
                <div className="w-3 h-3 rounded-full bg-red-500/80" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                <div className="w-3 h-3 rounded-full bg-green-500/80" />
                <span className="ml-2 text-xs text-muted-foreground font-mono">
                  ATLAS — live execution
                </span>
              </div>

              <div className="p-6 font-mono text-sm space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="w-3.5 h-3.5 text-accent" />
                  </div>

                  <div className="space-y-2">
                    <p className="text-foreground">
                      Planning architecture, generating code, validating tests,
                      and preparing deployment...
                    </p>

                    <div className="flex gap-2">
                      <span className="px-2 py-1 rounded bg-white/5 text-xs text-muted-foreground">
                        planning
                      </span>
                      <span className="px-2 py-1 rounded bg-white/5 text-xs text-muted-foreground">
                        execution
                      </span>
                    </div>
                  </div>
                </div>

                <div className="pl-9 space-y-2">
                  <div className="flex items-center gap-2 text-terminal-green text-xs">
                    <span>✓</span>
                    <span>Repository analyzed</span>
                  </div>
                  <div className="flex items-center gap-2 text-terminal-green text-xs">
                    <span>✓</span>
                    <span>Execution plan generated</span>
                  </div>
                  <div className="flex items-center gap-2 text-accent text-xs animate-pulse">
                    <span>◈</span>
                    <span>Running autonomous engineering workflow...</span>
                  </div>
                </div>
              </div>
            </div>
          </GlassCard>
        </motion.div>
      </section>

      {/* How it Works */}
      <section className="py-24 px-6 relative">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">How ATLAS Works</h2>
            <p className="text-muted-foreground">
              From task to production in four steps
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            {steps.map((step, i) => (
              <GlassCard key={step.num} delay={i * 0.1} className="p-6">
                <span className="text-4xl font-bold text-accent/20">
                  {step.num}
                </span>
                <h3 className="text-lg font-semibold mt-4 mb-2">
                  {step.title}
                </h3>
                <p className="text-sm text-muted-foreground">{step.desc}</p>
              </GlassCard>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Engineering-Grade AI</h2>
            <p className="text-muted-foreground">
              Built for teams that ship
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <GlassCard
                key={feature.title}
                delay={i * 0.1}
                className="p-6 group"
              >
                <div className="w-10 h-10 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <feature.icon className="w-5 h-5 text-accent" />
                </div>

                <h3 className="text-lg font-semibold mb-2">
                  {feature.title}
                </h3>

                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </GlassCard>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section id="architecture" className="py-24 px-6 relative">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">ATLAS Architecture</h2>
            <p className="text-muted-foreground">
              Specialized AI agents working together
            </p>
          </div>

          <GlassCard className="p-8">
            <div className="grid md:grid-cols-3 gap-8">
              {[
                {
                  title: "Planner",
                  desc: "Breaks down tasks and creates execution plans",
                },
                {
                  title: "Builder",
                  desc: "Writes, edits, and executes engineering workflows",
                },
                {
                  title: "Reviewer",
                  desc: "Tests, validates, and ensures production quality",
                },
              ].map((agent) => (
                <div
                  key={agent.title}
                  className="p-6 rounded-xl border border-white/10 bg-white/5"
                >
                  <div className="w-12 h-12 rounded-lg bg-accent/10 flex items-center justify-center mb-4">
                    <Code2 className="w-6 h-6 text-accent" />
                  </div>

                  <h3 className="text-xl font-bold mb-2">{agent.title}</h3>
                  <p className="text-sm text-muted-foreground">
                    {agent.desc}
                  </p>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <GlassCard className="p-12" glow>
            <h2 className="text-4xl font-bold mb-4">
              Ready to build with ATLAS?
            </h2>
            <p className="text-muted-foreground mb-8">
              Launch autonomous AI engineering workflows at scale.
            </p>

            <GlowButton variant="primary" size="lg">
              Get Started <ArrowRight className="w-4 h-4" />
            </GlowButton>
          </GlassCard>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 px-6">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-accent to-accent-secondary flex items-center justify-center">
              <span className="text-white font-bold text-[10px]">A</span>
            </div>
            <span className="text-sm font-medium">ATLAS</span>
          </div>

          <p className="text-sm text-muted-foreground">
            © 2026 ATLAS. All rights reserved.
          </p>
        </div>
      </footer>
    </main>
  );
}
