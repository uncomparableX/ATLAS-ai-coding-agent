"use client";

import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { ReactNode } from "react";

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glow?: boolean;
  delay?: number;
}

export function GlassCard({
  children,
  className,
  hover = true,
  glow = false,
  delay = 0,
}: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.23, 1, 0.32, 1] }}
      className={cn(
        "glass-panel relative overflow-hidden",
        hover && "transition-all duration-300 hover:bg-white/[0.05] hover:border-white/20 hover:shadow-lg hover:shadow-accent/5",
        glow && "after:absolute after:inset-0 after:bg-gradient-to-r after:from-accent/10 after:to-accent-secondary/10 after:opacity-0 hover:after:opacity-100 after:transition-opacity",
        className
      )}
    >
      {children}
    </motion.div>
  );
}
