"use client";

import React from "react";
import { SimulationProvider, useSimulation } from "@/context/SimulationContext";
import { RoleSelection } from "@/components/RoleSelection";
import { SimulatorControlBar } from "@/components/SimulatorControlBar";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Activity,
  Heart,
  Compass,
  Zap,
  Shield,
  Clock,
  CheckCircle,
  Truck,
  Building2,
  Users,
  HardDrive,
  Cpu,
  AlertTriangle,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import dynamic from "next/dynamic";

const LeafletMap = dynamic(() => import("@/components/LeafletMap"), { ssr: false });

function AppContent() {
  const {
    activeRole,
    isLoggedIn,
    loginEmail,
    emergencyState,
    countdownValue,
    telemetry,
    ambulance,
    hospitals,
    cancelEmergency,
    acceptEmergencyByDriver,
    resolveEmergency,
    resetSimulation,
  } = useSimulation();

  if (!isLoggedIn || activeRole === "guest") {
    return <RoleSelection />;
  }

  // Dashboard content renderings
  const renderDashboardPlaceholder = () => {
    switch (activeRole) {
      case "user":
        return (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Header info */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-4 border-b border-border-custom">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-primary">Citizen Terminal</span>
                <h2 className="text-2xl font-black text-text-primary">Medical & Telemetry Hub</h2>
                <p className="text-xs text-text-secondary">Synced with wearables and vehicle sensors.</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-success animate-ping" />
                <span className="text-xs font-medium text-text-secondary">Live Monitoring Active</span>
              </div>
            </div>

            {/* Simulated telemetry cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card glass className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-emergency/10 flex items-center justify-center border border-emergency/20 text-emergency">
                  <Heart className="w-5 h-5 animate-pulse" />
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-text-secondary">Heart Rate</span>
                  <p className="text-lg font-black text-text-primary font-mono">{telemetry.heartRate} bpm</p>
                </div>
              </Card>

              <Card glass className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20 text-primary">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-text-secondary">G-Force (Impact)</span>
                  <p className="text-lg font-black text-text-primary font-mono">{telemetry.accelerometer.gForce} G</p>
                </div>
              </Card>

              <Card glass className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20 text-indigo-500">
                  <Compass className="w-5 h-5 animate-spin-slow" />
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-text-secondary">Smartwatch link</span>
                  <p className="text-lg font-black text-text-primary">
                    {telemetry.smartwatchConnected ? "Connected" : "Disconnected"}
                  </p>
                </div>
              </Card>

              <Card glass className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-teal-500/10 flex items-center justify-center border border-teal-500/20 text-teal-500">
                  <Zap className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-text-secondary">GPS Coordinates</span>
                  <p className="text-xs font-mono font-bold text-text-primary">
                    {telemetry.gps.lat.toFixed(5)}, {telemetry.gps.lng.toFixed(5)}
                  </p>
                </div>
              </Card>
            </div>

            {/* Emergency flow test */}
            <Card className="bg-gradient-to-r from-secondary/50 to-white border border-primary/10 p-6 rounded-3xl relative overflow-hidden">
              <div className="absolute right-0 top-0 w-32 h-32 bg-primary/5 rounded-full blur-xl pointer-events-none" />
              <div className="max-w-xl">
                <h3 className="text-lg font-extrabold text-text-primary flex items-center gap-2">
                  <Shield className="w-5 h-5 text-primary" /> Emergency Alarm Flow Simulation
                </h3>
                <p className="text-xs text-text-secondary mt-1">
                  Triggering the emergency state starts a countdown on the device, notifying emergency vehicles nearby upon expiration.
                </p>

                {emergencyState === "idle" && (
                  <div className="mt-6 flex flex-wrap gap-3">
                    <p className="text-xs text-text-secondary self-center">No emergencies currently active.</p>
                  </div>
                )}

                {emergencyState === "countdown" && (
                  <div className="mt-6 bg-warning/10 border border-warning/20 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <span className="text-xs font-bold text-warning flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-warning animate-ping" />
                        CRASH ALARM COUNTDOWN
                      </span>
                      <p className="text-sm font-semibold text-text-primary mt-0.5">
                        Auto-broadcasting coordinates in <strong className="text-warning text-base font-mono">{countdownValue}s</strong>
                      </p>
                    </div>
                    <Button variant="outline" size="sm" onClick={cancelEmergency}>
                      Cancel Alarm
                    </Button>
                  </div>
                )}

                {(emergencyState === "triggered" ||
                  emergencyState === "accepted" ||
                  emergencyState === "transporting") && (
                  <div className="mt-6 bg-emergency/5 border border-emergency/15 rounded-2xl p-4">
                    <span className="text-xs font-bold text-emergency uppercase tracking-wider flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-emergency animate-pulse" />
                      SOS BROADCAST TRANSMITTING
                    </span>
                    <div className="mt-2 text-xs text-text-secondary space-y-1">
                      <p>
                        <strong>Patient:</strong> Dharshan (O+)
                      </p>
                      <p>
                        <strong>Status:</strong> {emergencyState === "triggered" ? "Awaiting dispatch acceptance" : "Ambulance en route"}
                      </p>
                      {emergencyState !== "triggered" && (
                        <p className="text-primary font-bold">
                          Ambulance Vehicle: {ambulance.vehicleNumber} (ETA: {ambulance.eta} mins)
                        </p>
                      )}
                    </div>
                    {emergencyState === "triggered" && (
                      <div className="mt-3 flex gap-2">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => acceptEmergencyByDriver(true)}
                          className="bg-primary/15 text-primary border-primary/20 hover:bg-primary/20"
                        >
                          Simulate Driver Acceptance
                        </Button>
                        <Button variant="ghost" size="sm" onClick={cancelEmergency}>
                          Dismiss
                        </Button>
                      </div>
                    )}
                  </div>
                )}

                {emergencyState === "resolved" && (
                  <div className="mt-6 bg-success/10 border border-success/20 rounded-2xl p-4 flex items-center justify-between">
                    <div>
                      <span className="text-xs font-bold text-success flex items-center gap-1.5">
                        <CheckCircle className="w-4 h-4" />
                        PATIENT SECURED
                      </span>
                      <p className="text-xs text-text-secondary mt-0.5">
                        Delivered successfully to Fortis Trauma Center. All systems reset.
                      </p>
                    </div>
                    <Button variant="outline" size="sm" onClick={resetSimulation}>
                      Reset App
                    </Button>
                  </div>
                )}
              </div>
            </Card>

            {/* Notice */}
            <div className="p-4 rounded-2xl bg-secondary/30 border border-border-custom text-xs text-text-secondary">
              <strong>Phase 1 System Note:</strong> You are view-locked to the citizen sensor hub. Telemetries fluctuate locally. You can use the top control bar to switch dashboard views and verify interaction pipelines.
            </div>
          </motion.div>
        );

      case "driver":
        return (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Header info */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-4 border-b border-border-custom">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-indigo-500">
                  Ambulance Mobile Terminal
                </span>
                <h2 className="text-2xl font-black text-text-primary">Operator Despatch Console</h2>
                <p className="text-xs text-text-secondary">Vehicle: {ambulance.vehicleNumber} | Operator: {ambulance.driverName}</p>
              </div>
              <span className="px-2.5 py-1 rounded-lg bg-indigo-500/10 text-indigo-600 text-xs font-bold border border-indigo-500/20">
                GPS Operational
              </span>
            </div>

            {/* Active dispatches block */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-4">
                <h3 className="text-sm font-extrabold text-text-primary uppercase tracking-wider">Incoming Dispatch Alerts</h3>
                
                {emergencyState === "idle" && (
                  <Card glass className="p-8 text-center text-text-secondary">
                    <Truck className="w-10 h-10 text-text-secondary/40 mx-auto mb-3" />
                    <p className="text-sm font-semibold">No active rescue alerts in your region.</p>
                    <p className="text-xs text-text-secondary/70 mt-0.5">Standalone patrol mode active. System listening for crash signals.</p>
                  </Card>
                )}

                {emergencyState === "countdown" && (
                  <Card glass className="p-8 text-center text-text-secondary animate-pulse border-warning/30">
                    <Activity className="w-10 h-10 text-warning mx-auto mb-3" />
                    <p className="text-sm font-bold text-text-primary">Pre-Collision Pulse Signal Detected</p>
                    <p className="text-xs mt-0.5">A citizen device registered high-G impacts. Analyzing safety status...</p>
                  </Card>
                )}

                {emergencyState === "triggered" && (
                  <Card className="border border-emergency/30 bg-emergency/[0.02] p-6 rounded-3xl">
                    <div className="flex justify-between items-start gap-4 flex-wrap">
                      <div>
                        <span className="px-2 py-0.5 rounded-full bg-emergency text-white text-[10px] font-extrabold uppercase tracking-wide">
                          Accident Alert
                        </span>
                        <h4 className="text-lg font-extrabold text-text-primary mt-2">IITM Hostel Zone (15G Crash)</h4>
                        <p className="text-xs text-text-secondary mt-0.5">Patient Name: Dharshan | Blood Group: O+</p>
                        <p className="text-xs text-text-secondary mt-0.5 font-bold">Vitals Relay: Heart Rate {telemetry.heartRate} bpm</p>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="primary" size="sm" onClick={() => acceptEmergencyByDriver(true)} className="bg-indigo-500 hover:bg-indigo-600 shadow-indigo-500/10">
                          Accept Callout
                        </Button>
                        <Button variant="ghost" size="sm" className="text-text-secondary">
                          Decline
                        </Button>
                      </div>
                    </div>
                  </Card>
                )}

                {(emergencyState === "accepted" || emergencyState === "transporting") && (
                  <Card className="border border-primary/20 bg-primary/[0.01] p-6 rounded-3xl">
                    <div className="flex justify-between items-start gap-4 flex-wrap">
                      <div>
                        <span className="px-2.5 py-0.5 rounded-full bg-primary text-white text-[10px] font-extrabold uppercase tracking-wide">
                          {emergencyState === "accepted" ? "En Route to Accident" : "Transporting Patient to Hospital"}
                        </span>
                        <h4 className="text-lg font-extrabold text-text-primary mt-2">IITM Campus Rescue Run</h4>
                        <p className="text-xs text-text-secondary mt-1">
                          <strong>Route Target:</strong> {emergencyState === "accepted" ? "IIT Hostel Road" : "Fortis Malar Hospital"}
                        </p>
                        <p className="text-xs text-text-secondary">
                          <strong>Active ETA:</strong> <strong className="text-primary font-mono">{ambulance.eta} mins</strong>
                        </p>
                      </div>
                      {emergencyState === "transporting" ? (
                        <Button variant="primary" size="sm" onClick={resolveEmergency}>
                          Arrived at ER Hospital
                        </Button>
                      ) : (
                        <p className="text-xs text-text-secondary italic">Navigating to site...</p>
                      )}
                    </div>
                  </Card>
                )}

                {emergencyState === "resolved" && (
                  <Card glass className="p-8 text-center text-success border-success/20">
                    <CheckCircle className="w-10 h-10 text-success mx-auto mb-3" />
                    <p className="text-sm font-bold text-text-primary">Dispatch Run Successfully Completed</p>
                    <p className="text-xs text-text-secondary mt-0.5">Patient safely delivered and checked into Fortis Hospital.</p>
                  </Card>
                )}

                {/* Live Routing Map */}
                <div className="mt-6 pt-4 border-t border-border-custom">
                  <h4 className="text-sm font-extrabold text-text-primary uppercase tracking-wider mb-3">Live Navigation & Dispatch Route</h4>
                  <LeafletMap />
                </div>
              </div>

              {/* Status panel */}
              <div className="space-y-4">
                <h3 className="text-sm font-extrabold text-text-primary uppercase tracking-wider">Device & GPS status</h3>
                <Card glass className="space-y-4">
                  <div className="flex justify-between text-xs pb-2 border-b border-border-custom">
                    <span className="text-text-secondary">MDT Signal</span>
                    <span className="font-bold text-success">Excellent (4G LTE)</span>
                  </div>
                  <div className="flex justify-between text-xs pb-2 border-b border-border-custom">
                    <span className="text-text-secondary">Live Location</span>
                    <span className="font-mono text-text-primary">
                      {ambulance.lat.toFixed(5)}, {ambulance.lng.toFixed(5)}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-text-secondary">Job status</span>
                    <span className="font-bold text-text-primary capitalize">{emergencyState}</span>
                  </div>
                </Card>
              </div>
            </div>
          </motion.div>
        );

      case "hospital":
        return (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-6"
          >
            {/* Header info */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pb-4 border-b border-border-custom">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-teal-600">
                  Hospital ER Operations Center
                </span>
                <h2 className="text-2xl font-black text-text-primary">Operations Desk</h2>
                <p className="text-xs text-text-secondary">Connected hospitals: Apollo Adyar & Fortis Malar Trauma Center</p>
              </div>
              <span className="px-2.5 py-1 rounded-lg bg-teal-500/10 text-teal-600 text-xs font-bold border border-teal-500/20">
                System Connected
              </span>
            </div>

            {/* Main panels */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Recommendations and facilities */}
              <div className="lg:col-span-2 space-y-4">
                <h3 className="text-sm font-extrabold text-text-primary uppercase tracking-wider">
                  AI Facility Comparison & Recommendations
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {hospitals.map((h) => {
                    const isRecommended = h.score >= 90;
                    return (
                      <Card
                        key={h.hospitalName}
                        className={`flex flex-col justify-between p-5 border rounded-3xl ${
                          isRecommended ? "border-primary bg-primary/[0.01]" : "border-border-custom bg-white"
                        }`}
                      >
                        <div>
                          <div className="flex justify-between items-start gap-2">
                            <h4 className="text-sm font-black text-text-primary">{h.hospitalName}</h4>
                            {isRecommended && (
                              <span className="px-2 py-0.5 bg-primary text-white text-[9px] font-extrabold rounded-full uppercase tracking-wider">
                                Best AI Choice
                              </span>
                            )}
                          </div>

                          <div className="mt-4 space-y-2 text-xs">
                            <div className="flex justify-between">
                              <span className="text-text-secondary">Available Beds:</span>
                              <span className="font-bold text-text-primary">
                                {h.availableBeds} / {h.totalBeds}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-text-secondary">ICU Availability:</span>
                              <span className="font-bold text-text-primary">
                                {h.availableIcu} / {h.totalIcu}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-text-secondary">Trauma Support:</span>
                              <span className={`font-bold ${h.traumaReady ? "text-success" : "text-text-secondary"}`}>
                                {h.traumaReady ? "Fully Equipped" : "Limited"}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="mt-6 pt-3 border-t border-border-custom flex justify-between items-center text-xs">
                          <span className="text-text-secondary">AI Dispatch Score:</span>
                          <span className="font-black text-primary">{h.score}% match</span>
                        </div>
                      </Card>
                    );
                  })}
                </div>

                {/* Live Transit Tracking Map */}
                <div className="mt-6 pt-4 border-t border-border-custom">
                  <h4 className="text-sm font-extrabold text-text-primary uppercase tracking-wider mb-3">Live Emergency Transit Map</h4>
                  <LeafletMap />
                </div>
              </div>

              {/* Transit tracking */}
              <div className="space-y-4">
                <h3 className="text-sm font-extrabold text-text-primary uppercase tracking-wider">Incoming Transits</h3>
                
                {emergencyState === "idle" && (
                  <Card glass className="p-6 text-center text-text-secondary">
                    <Clock className="w-8 h-8 text-text-secondary/40 mx-auto mb-2" />
                    <p className="text-xs font-semibold">No incoming ambulance dispatches detected.</p>
                  </Card>
                )}

                {emergencyState === "countdown" && (
                  <Card glass className="p-6 text-center text-text-secondary border-warning/20">
                    <Activity className="w-8 h-8 text-warning mx-auto mb-2 animate-pulse" />
                    <p className="text-xs font-bold text-text-primary">Pending Crash Incident...</p>
                  </Card>
                )}

                {emergencyState === "triggered" && (
                  <Card glass className="p-6 text-center text-emergency border-emergency/20">
                    <AlertTriangle className="w-8 h-8 text-emergency mx-auto mb-2 animate-bounce" />
                    <p className="text-xs font-bold text-text-primary">Crash Alert Awaiting Driver Acceptance...</p>
                  </Card>
                )}

                {(emergencyState === "accepted" || emergencyState === "transporting") && (
                  <Card className="border-primary bg-primary/[0.02] p-5 rounded-2xl space-y-4">
                    <div>
                      <span className="px-2 py-0.5 rounded bg-primary text-white text-[9px] font-bold uppercase tracking-wider">
                        {emergencyState === "accepted" ? "En Route to Site" : "Transporting Patient"}
                      </span>
                      <h4 className="text-sm font-extrabold text-text-primary mt-2">Ambulance {ambulance.vehicleNumber}</h4>
                      <p className="text-xs text-text-secondary mt-0.5">Operator: {ambulance.driverName}</p>
                    </div>

                    <div className="space-y-1.5 text-xs border-t border-border-custom pt-3">
                      <div className="flex justify-between">
                        <span className="text-text-secondary">Patient:</span>
                        <span className="font-bold text-text-primary">Dharshan (O+)</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-text-secondary">Wearable Vitals:</span>
                        <span className="font-mono font-bold text-emergency animate-pulse">{telemetry.heartRate} bpm</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-text-secondary">Expected Arrival:</span>
                        <span className="font-black text-primary font-mono">{ambulance.eta} mins</span>
                      </div>
                    </div>
                  </Card>
                )}

                {emergencyState === "resolved" && (
                  <Card glass className="p-6 text-center text-success border-success/20">
                    <CheckCircle className="w-8 h-8 text-success mx-auto mb-2" />
                    <p className="text-xs font-bold text-text-primary">Patient Transferred Successfully</p>
                    <p className="text-[10px] text-text-secondary/70">ER Check-in logged at Fortis Malar Center.</p>
                  </Card>
                )}
              </div>
            </div>
          </motion.div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-background relative pt-36 md:pt-28 pb-12 px-4 sm:px-6 lg:px-8">
      {/* Simulation control bar */}
      <SimulatorControlBar />

      <main className="max-w-6xl mx-auto mt-6">
        {/* Workspace Card Container */}
        <div className="glass-card p-6 sm:p-8 rounded-3xl border border-border-custom shadow-premium relative overflow-hidden">
          {/* Decorative ambient blur background */}
          <div className="absolute top-0 right-0 w-80 h-80 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
          
          <AnimatePresence mode="wait">
            {renderDashboardPlaceholder()}
          </AnimatePresence>
        </div>

        {/* Global architectural review card */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card glass className="p-5 flex gap-4">
            <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary shrink-0 border border-primary/20">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-extrabold text-text-primary">Phase 1 Context Synced</h4>
              <p className="text-xs text-text-secondary mt-1 leading-relaxed">
                Roles share real-time state flags. Actions (like 15G Impact) trigger automatic response cycles across all terminals.
              </p>
            </div>
          </Card>

          <Card glass className="p-5 flex gap-4">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-500 shrink-0 border border-indigo-500/20">
              <HardDrive className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-extrabold text-text-primary">Light Day Palette Installed</h4>
              <p className="text-xs text-text-secondary mt-1 leading-relaxed">
                Built strictly with `#F5F7FB` backdrop variables, pure glass cards, and calm visual elements matching healthcare requirements.
              </p>
            </div>
          </Card>

          <Card glass className="p-5 flex gap-4">
            <div className="w-10 h-10 rounded-xl bg-teal-500/10 flex items-center justify-center text-teal-500 shrink-0 border border-teal-500/20">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-extrabold text-text-primary">Modular Components Built</h4>
              <p className="text-xs text-text-secondary mt-1 leading-relaxed">
                Base structure contains decoupled Context APIs, reusable UI components, and authentication routes ready for full page integrations.
              </p>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}

export default function Home() {
  return (
    <SimulationProvider>
      <AppContent />
    </SimulationProvider>
  );
}
