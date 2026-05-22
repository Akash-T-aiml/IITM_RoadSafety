import React from "react";
import { cn } from "@/lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input: React.FC<InputProps> = ({ className, label, error, ...props }) => {
  return (
    <div className="flex flex-col gap-1.5 w-full">
      {label && (
        <label className="text-xs font-semibold text-text-secondary/80 uppercase tracking-wider select-none">
          {label}
        </label>
      )}
      <input
        className={cn(
          "w-full px-4 py-2.5 bg-background/50 border border-border-custom rounded-xl text-text-primary placeholder:text-text-secondary/40 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all duration-300 text-sm focus:bg-white shadow-inner shadow-black/[0.005]",
          error && "border-emergency focus:ring-emergency/20 focus:border-emergency bg-emergency/[0.02]",
          className
        )}
        {...props}
      />
      {error && <span className="text-xs text-emergency font-medium px-1">{error}</span>}
    </div>
  );
};
