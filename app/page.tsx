"use client";

import { motion } from "framer-motion";
import { AIActivityViz } from "@/components/agent/ai-activity-viz";
import { GlassCard } from "@/components/glass/glass-card";
import { GlowButton } from "@/components/glass/glow-button";
import { RobotMascot } from "@/components/agent/robot-mascot";
import { StreamingText } from "@/components/motion/streaming-text";
import {
  ArrowRight,
  Bot,
  Code2,
  GitBranch,
  Zap,
  Shield,
  Workflow,
  Terminal,
  Sparkles,
} from "lucide-react";

const features = [
  {
    icon: Bot,
    title: "Autonomous Agents",
    description: "AI agents that plan, code, test, and deploy without human intervention.",
  },
  {
    icon: GitBranch,
    title: "GitHub Native",
    description: "Deep integration with your repositories. Branches, PRs, and reviews automated.",
  },
  {
    icon: Zap,
    title: "Real-time Execution",
    description: "Watch your agents work in real-time with live logs and streaming output.",
  },
  {
    icon: Shield,
    title: "Sandboxed & Secure",
    description: "Every agent runs in an isolated Docker sandbox with strict resource limits.",
  },
  {
    icon: Workflow,
    title: "Complex Workflows",
    description: "Multi-step planning with reflection, retry logic, and error recovery.",
  },
  {
    icon: Terminal,
    title: "Developer Experience",
    description: "Terminal aesthetics with modern UX. Built by engineers, for engineers.",
  },
];

const steps = [
  { num: "01", title: "Connect", desc: "Link your GitHub repository in seconds" },
  { num: "02", title: "Assign", desc: "Describe the task in natural language" },
  { num: "03", title: "Observe", desc: "Watch the AI agent plan and execute" },
  { num: "04", title: "Ship", desc: "Review the PR and merge with confidence" },
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
            <span className="font-semibold text-foreground">Agentic</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Features</a>
            <a href="#architecture" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Architecture</a>
            <a href="/dashboard">
              <GlowButton variant="primary" size="sm">
                Launch App <ArrowRight className="w-3 h-3" />
              </GlowButton>
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-accent text-sm mb-8"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Now with GPT-4o Agentic Coding</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="text-6xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-6"
          >
            <span className="gradient-text">Autonomous</span>
            <br />
            <span className="text-foreground">Software Engineering</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-xl text-muted-foreground max-w-2xl mx-auto mb-10"
          >
            AI agents that understand your codebase, plan complex changes, write production-quality code, and ship to production.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="flex items-center justify-center gap-4"
          >
            <GlowButton variant="primary" size="lg">
              Start Building <ArrowRight className="w-4 h-4" />
            </GlowButton>
            <GlowButton variant="secondary" size="lg">
              View Demo
            </GlowButton>
          </motion.div>
        </div>

        {/* Hero Visual */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7, duration: 0.8 }}
          className="max-w-6xl mx-auto mt-20"
        >
          <GlassCard className="p-1" glow>
            <div className="bg-black/40 rounded-lg overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
                <div className="w-3 h-3 rounded-full bg-red-500/80" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                <div className="w-3 h-3 rounded-full bg-green-500/80" />
                <span className="ml-2 text-xs text-muted-foreground font-mono">agentic — task #1842</span>
              </div>
              <div className="p-6 font-mono text-sm space-y-4">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="w-3.5 h-3.5 text-accent" />
                  </div>
                  <div className="space-y-2">
                    <p className="text-foreground">
                      <StreamingText text="Analyzing repository structure and planning implementation for OAuth2 authentication flow..." speed={20} />
                    </p>
                    <div className="flex gap-2">
                      <span className="px-2 py-1 rounded bg-white/5 text-xs text-muted-foreground">planning</span>
                      <span className="px-2 py-1 rounded bg-white/5 text-xs text-muted-foreground">src/auth/</span>
                    </div>
                  </div>
                </div>
                <div className="pl-9 space-y-2">
                  <div className="flex items-center gap-2 text-terminal-green text-xs">
                    <span>✓</span>
                    <span>Analyzed 47 files in src/auth/</span>
                  </div>
                  <div className="flex items-center gap-2 text-terminal-green text-xs">
                    <span>✓</span>
                    <span>Identified passport.js dependency</span>
                  </div>
                  <div className="flex items-center gap-2 text-accent text-xs animate-pulse">
                    <span>◈</span>
                    <span>Generating OAuth2 strategy implementation...</span>
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
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl font-bold mb-4">How it works</h2>
            <p className="text-muted-foreground">From task to production in four steps</p>
          </motion.div>

          <div className="grid md:grid-cols-4 gap-6">
            {steps.map((step, i) => (
              <GlassCard key={step.num} delay={i * 0.1} className="p-6">
                <span className="text-4xl font-bold text-accent/20">{step.num}</span>
                <h3 className="text-lg font-semibold mt-4 mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground">{step.desc}</p>
              </GlassCard>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl font-bold mb-4">Engineering-grade AI</h2>
            <p className="text-muted-foreground">Built for teams that ship</p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <GlassCard key={feature.title} delay={i * 0.1} className="p-6 group">
                <div className="w-10 h-10 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <feature.icon className="w-5 h-5 text-accent" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </GlassCard>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture Visualization */}
      <section id="architecture" className="py-24 px-6 relative">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl font-bold mb-4">Agent Architecture</h2>
            <p className="text-muted-foreground">Multi-agent system with specialized roles</p>
          </motion.div>

          <GlassCard className="p-8">
            <div className="grid md:grid-cols-3 gap-8 relative">
              {/* Connection lines */}
              <div className="hidden md:block absolute top-1/2 left-1/3 right-1/3 h-px bg-gradient-to-r from-accent/50 to-accent-secondary/50" />
              <div className="hidden md:block absolute top-1/2 left-2/3 right-0 h-px bg-gradient-to-r from-accent-secondary/50 to-transparent" />

              {[
                {
                  title: "Planner",
                  desc: "Decomposes tasks into executable steps with dependency analysis",
                  color: "from-cyan-500 to-blue-500",
                },
                {
                  title: "Coder",
                  desc: "Writes, edits, and refactors code with full context awareness",
                  color: "from-blue-500 to-violet-500",
                },
                {
                  title: "Reviewer",
                  desc: "Validates output, runs tests, and ensures quality standards",
                  color: "from-violet-500 to-fuchsia-500",
                },
              ].map((agent, i) => (
                <motion.div
                  key={agent.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.2 }}
                  className="relative z-10"
                >
                  <div className={`p-6 rounded-xl bg-gradient-to-br ${agent.color} bg-opacity-10 border border-white/10`}>
                    <div className="w-12 h-12 rounded-lg bg-white/10 flex items-center justify-center mb-4">
                      <Code2 className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">{agent.title}</h3>
                    <p className="text-sm text-white/70">{agent.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </GlassCard>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <GlassCard className="p-12" glow>
            <h2 className="text-4xl font-bold mb-4">Ready to ship faster?</h2>
            <p className="text-muted-foreground mb-8">
              Join the next generation of engineering teams using AI agents.
            </p>
            <GlowButton variant="primary" size="lg">
              Get Started Free <ArrowRight className="w-4 h-4" />
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
            <span className="text-sm font-medium">Agentic</span>
          </div>
          <p className="text-sm text-muted-foreground">
            © 2026 Agentic Labs. All rights reserved.
          </p>
        </div>
      </footer>
    </main>
  );
}
