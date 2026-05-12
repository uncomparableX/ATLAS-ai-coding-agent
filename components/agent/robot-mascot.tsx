"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

export function RobotMascot() {
  const [position, setPosition] = useState({ x: 100, y: 100 });
  const [isMoving, setIsMoving] = useState(false);

  useEffect(() => {
    const moveRobot = () => {
      setIsMoving(true);
      setPosition({
        x: Math.random() * (window.innerWidth - 100),
        y: Math.random() * (window.innerHeight - 100),
      });
      setTimeout(() => setIsMoving(false), 2000);
    };

    const interval = setInterval(moveRobot, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      className="fixed z-50 pointer-events-auto cursor-pointer"
      animate={{ x: position.x, y: position.y }}
      transition={{ type: "spring", stiffness: 50, damping: 20, duration: 2 }}
      whileHover={{ scale: 1.2 }}
      onClick={() => {
        setPosition({
          x: Math.random() * (window.innerWidth - 100),
          y: Math.random() * (window.innerHeight - 100),
        });
      }}
    >
      <div className="relative">
        {/* Glow effect */}
        <div className="absolute inset-0 bg-accent/20 blur-xl rounded-full" />
        
        {/* Robot body */}
        <motion.div
          animate={isMoving ? { y: [0, -10, 0] } : { y: [0, -5, 0] }}
          transition={{ duration: 0.5, repeat: Infinity }}
          className="relative w-12 h-12 bg-surface-elevated border border-accent/30 rounded-xl flex items-center justify-center shadow-lg shadow-accent/10"
        >
          {/* Eyes */}
          <div className="flex gap-1.5">
            <motion.div
              animate={{ scaleY: [1, 0.1, 1] }}
              transition={{ duration: 3, repeat: Infinity, repeatDelay: 2 }}
              className="w-2 h-2 bg-accent rounded-full"
            />
            <motion.div
              animate={{ scaleY: [1, 0.1, 1] }}
              transition={{ duration: 3, repeat: Infinity, repeatDelay: 2, delay: 0.1 }}
              className="w-2 h-2 bg-accent rounded-full"
            />
          </div>
          
          {/* Antenna */}
          <motion.div
            animate={{ rotate: [-10, 10, -10] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="absolute -top-2 left-1/2 -translate-x-1/2 w-0.5 h-3 bg-accent/50"
          >
            <div className="absolute -top-1 -left-1 w-2 h-2 bg-accent rounded-full animate-pulse" />
          </motion.div>
        </motion.div>

        {/* Speech bubble */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1 }}
          className="absolute -top-10 left-1/2 -translate-x-1/2 whitespace-nowrap glass-panel px-2 py-1 text-[10px] text-accent font-mono"
        >
          Processing...
        </motion.div>
      </div>
    </motion.div>
  );
}
