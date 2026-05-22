"use client";

import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "primary" | "secondary" | "emergency" | "warning" | "ghost" | "outline";
  size?: "sm" | "md" | "lg";
  animate?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = "default",
  size = "md",
  animate = true,
  ...props
}) => {
  const baseStyles =
    "inline-flex items-center justify-center font-medium rounded-xl transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary/40 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer";

  const sizeStyles = {
    sm: "px-3 py-1.5 text-xs rounded-lg",
    md: "px-4 py-2 text-sm rounded-xl",
    lg: "px-6 py-3 text-base rounded-2xl",
  };

  const variantStyles = {
    default: "bg-white text-text-primary border border-border-custom shadow-soft hover:bg-secondary/50",
    primary: "bg-primary text-white hover:bg-primary/95 shadow-premium hover:shadow-primary/20",
    secondary: "bg-secondary text-primary hover:bg-secondary/80 border border-primary/10",
    emergency: "bg-emergency text-white hover:bg-emergency/90 shadow-lg hover:shadow-emergency/30",
    warning: "bg-warning text-text-primary hover:bg-warning/90 shadow-md",
    ghost: "bg-transparent text-text-secondary hover:text-text-primary hover:bg-secondary/50",
    outline: "bg-transparent text-text-primary border border-border-custom hover:bg-secondary/30",
  };

  const Component = animate ? motion.button : "button";
  const motionProps = animate
    ? {
        whileHover: { scale: 1.02 },
        whileTap: { scale: 0.98 },
      }
    : {};

  return (
    // @ts-expect-error motion components can have different props but compile fine
    <Component
      className={cn(baseStyles, sizeStyles[size], variantStyles[variant], className)}
      {...motionProps}
      {...props}
    >
      {children}
    </Component>
  );
};
