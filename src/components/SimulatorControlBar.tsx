"use client";

import React from "react";
import { useSimulation, UserRole } from "@/context/SimulationContext";
import { Button } from "./ui/button";
import {
  Activity,
  AlertTriangle,
  RefreshCw,
  User,
  Shield,
  Truck,
  Building2,
  Lock,
  Compass,
  Heart,
  RotateCcw,
  LogOut,
} from "lucide-react";
import { motion } from "framer-motion";

export const SimulatorControlBar: React.FC = () => {
  const {
    activeRole,
    setActiveRole,
    isLoggedIn,
    setIsLoggedIn,
    emergencyState,
    telemetry,
    triggerEmergency,
    triggerSevereImpact,
    clearHospitalBeds,
    resetSimulation,
  } = useSimulation();

  // Color mappings for emergency pipeline display
  const statusColors = {
    idle: "bg-success/10 text-success border-success/20",
    countdown: "bg-warning/10 text-warning border-warning/20 animate-pulse",
    triggered: "bg-emergency/10 text-emergency border-emergency/20",
    accepted: "bg-primary/10 text-primary border-primary/20",
    transporting: "bg-accent/10 text-primary border-accent/20",
    resolved: "bg-success/10 text-success border-success/20",
  };

  const statusLabels = {
    idle: "System Active & Monitoring",
    countdown: `CRASH TRIGGERED! Auto-Alert in...`,
    triggered: "Broadcast Broadcasted",
    accepted: "Ambulance En Route",
    transporting: "Transit to Hospital",
    resolved: "Emergency Resolved",
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setActiveRole("guest");
    resetSimulation();
  };

  return (
    <div className="fixed top-4 left-0 right-0 z-50 px-4 flex flex-col items-center pointer-events-none select-none">
      {/* Simulation status pill */}
      <motion.div
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 100 }}
        className="glass-card px-4 py-2 rounded-full border border-border-custom shadow-soft flex items-center gap-3 text-xs font-medium mb-3 backdrop-blur-lg pointer-events-auto"
      >
        <span className="flex items-center gap-1.5 text-text-secondary">
          <Activity className="w-3.5 h-3.5 text-primary animate-pulse" />
          Simulator:
        </span>
        <span
          className={`px-2.5 py-0.5 rounded-full border text-[10px] uppercase font-bold tracking-wider ${statusColors[emergencyState]}`}
        >
          {emergencyState === "countdown" ? "Countdown running" : emergencyState}
        </span>
        <div className="w-[1px] h-3 bg-border-custom" />
        <span className="text-text-secondary flex items-center gap-1">
          <Heart className="w-3.5 h-3.5 text-emergency animate-pulse" /> {telemetry.heartRate} BPM
        </span>
        <div className="w-[1px] h-3 bg-border-custom" />
        <span className="text-text-secondary">
          G-Force: <strong className={telemetry.accelerometer.gForce > 5 ? "text-emergency" : ""}>{telemetry.accelerometer.gForce}G</strong>
        </span>
      </motion.div>

      {/* Main floating control center */}
      <motion.div
        initial={{ y: -60, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 100, delay: 0.1 }}
        className="glass-card px-6 py-3 rounded-2xl border border-border-custom shadow-premium flex flex-wrap items-center justify-center gap-4 max-w-5xl backdrop-blur-xl pointer-events-auto"
      >
        {/* Logo and Brand */}
        <div className="flex items-center gap-2 pr-2 border-r border-border-custom">
          <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20">
            <Shield className="w-4 h-4 text-primary" />
          </div>
          <div className="hidden sm:block text-left">
            <h1 className="text-sm font-bold tracking-tight text-text-primary">SmartRescue AI</h1>
            <p className="text-[10px] text-text-secondary leading-none">Simulation Hub</p>
          </div>
        </div>

        {/* Role switching buttons */}
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-semibold text-text-secondary uppercase tracking-wider mr-1 hidden md:inline">
            Views:
          </span>
          
          {(["user", "driver", "hospital"] as UserRole[]).map((role) => {
            const isActive = activeRole === role;
            const icons = {
              user: <User className="w-4 h-4" />,
              driver: <Truck className="w-4 h-4" />,
              hospital: <Building2 className="w-4 h-4" />,
              guest: <Lock className="w-4 h-4" />,
            };

            const labels = {
              user: "Citizen Profile",
              driver: "Ambulance Driver",
              hospital: "Hospital ER",
              guest: "Portal",
            };

            return (
              <Button
                key={role}
                variant={isActive ? "primary" : "ghost"}
                size="sm"
                onClick={() => {
                  if (isLoggedIn) {
                    setActiveRole(role);
                  } else {
                    setActiveRole(role);
                    // Force logged in for demo switching if they bypass role portal
                    setIsLoggedIn(true);
                  }
                }}
                className={`flex items-center gap-1.5 ${
                  isActive ? "bg-primary text-white" : "hover:bg-secondary text-text-secondary"
                }`}
              >
                {icons[role]}
                <span className="capitalize">{labels[role]}</span>
              </Button>
            );
          })}
        </div>

        <div className="w-[1px] h-6 bg-border-custom hidden md:block" />

        {/* Simulated Incident Injection Tools */}
        <div className="flex items-center gap-1.5">
          <span className="text-[10px] font-semibold text-text-secondary uppercase tracking-wider mr-1 hidden md:inline">
            Inject Events:
          </span>

          <Button
            variant="warning"
            size="sm"
            onClick={triggerEmergency}
            disabled={emergencyState !== "idle"}
            className="flex items-center gap-1 text-[11px] font-semibold"
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            Trigger Alarm
          </Button>

          <Button
            variant="emergency"
            size="sm"
            onClick={triggerSevereImpact}
            disabled={emergencyState !== "idle"}
            className="flex items-center gap-1 text-[11px] font-semibold text-white"
          >
            <Activity className="w-3.5 h-3.5" />
            15G Impact
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={clearHospitalBeds}
            className="flex items-center gap-1 text-[11px] font-semibold"
          >
            <Building2 className="w-3.5 h-3.5" />
            Clear ER Beds
          </Button>

          <Button
            variant="default"
            size="sm"
            onClick={resetSimulation}
            className="flex items-center justify-center p-2 rounded-xl text-text-secondary hover:text-text-primary"
            title="Reset Simulation"
          >
            <RotateCcw className="w-4 h-4" />
          </Button>
        </div>

        {/* Logout (to return to role select) */}
        {isLoggedIn && (
          <div className="pl-2 border-l border-border-custom">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="text-emergency hover:bg-emergency/10 flex items-center justify-center px-2 py-2 rounded-xl"
              title="Log Out & Lock Portal"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        )}
      </motion.div>
    </div>
  );
};
