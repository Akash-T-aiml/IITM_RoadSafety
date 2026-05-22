import React from "react";
import { cn } from "@/lib/utils";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  glass?: boolean;
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  glass = false,
  hoverable = false,
  ...props
}) => {
  return (
    <div
      className={cn(
        "rounded-2xl border border-border-custom bg-card text-text-primary shadow-soft p-5 transition-all duration-300",
        glass && "glass-card",
        hoverable && "hover:shadow-premium hover:-translate-y-1 hover:border-primary/20",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
