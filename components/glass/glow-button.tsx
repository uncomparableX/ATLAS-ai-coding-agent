"use client";

import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { ReactNode } from "react";

interface GlowButtonProps {
  children: ReactNode;
  className?: string;
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md" | "lg";
  onClick?: () => void;
  disabled?: boolean;
}

export function GlowButton({
  children,
  className,
  variant = "primary",
  size = "md",
  onClick,
  disabled,
}: GlowButtonProps) {
  const variants = {
    primary: "bg-accent/10 text-accent border-accent/20 hover:bg-accent/20 hover:border-accent/40 hover:shadow-[0_0_20px_rgba(34,211,238,0.2)]",
    secondary: "bg-white/5 text-foreground border-white/10 hover:bg-white/10 hover:border-white/20",
    ghost: "bg-transparent text-muted-foreground border-transparent hover:text-foreground hover:bg-white/5",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "relative rounded-lg border font-medium transition-all duration-300 backdrop-blur-sm",
        variants[variant],
        sizes[size],
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
    >
      {variant === "primary" && (
        <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-accent/20 to-accent-secondary/20 opacity-0 blur-xl transition-opacity group-hover:opacity-100" />
      )}
      <span className="relative z-10 flex items-center gap-2">{children}</span>
    </motion.button>
  );
}
