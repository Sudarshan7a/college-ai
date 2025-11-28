"use client";

import { motion } from "framer-motion";

export const LoadingSkeleton = () => {
  return (
    <div className="flex justify-start">
      <div className="bg-muted px-4 py-3 rounded-2xl">
        <div className="flex gap-1">
          <motion.span
            className="w-2 h-2 bg-foreground/40 rounded-full"
            animate={{
              y: [0, -5, 0],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 0,
            }}
          />
          <motion.span
            className="w-2 h-2 bg-foreground/40 rounded-full"
            animate={{
              y: [0, -5, 0],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 0.2,
            }}
          />
          <motion.span
            className="w-2 h-2 bg-foreground/40 rounded-full"
            animate={{
              y: [0, -5, 0],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 0.4,
            }}
          />
        </div>
      </div>
    </div>
  );
};
