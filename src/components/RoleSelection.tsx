"use client";

import React, { useState } from "react";
import { useSimulation, UserRole } from "@/context/SimulationContext";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { motion, AnimatePresence } from "framer-motion";
import { User, Truck, Building2, ShieldCheck, ArrowLeft, Loader2, Sparkles } from "lucide-react";

export const RoleSelection: React.FC = () => {
  const { setActiveRole, setIsLoggedIn, setLoginEmail } = useSimulation();
  
  const [selectedRole, setSelectedRole] = useState<UserRole | null>(null);
  const [step, setStep] = useState<"select_role" | "login_form">("select_role");
  
  // Form fields
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [phone, setPhone] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [isLoading, setIsLoading] = useState(false);

  const roleDetails = [
    {
      id: "user" as UserRole,
      title: "Normal Citizen / User",
      subtitle: "Profile telemetry, monitor sensors, report emergencies automatically.",
      icon: <User className="w-8 h-8 text-primary" />,
      color: "from-primary/10 to-accent/10 border-primary/20",
    },
    {
      id: "driver" as UserRole,
      title: "Ambulance Operator",
      subtitle: "Receive dispatch updates, route maps, and accident live status tracking.",
      icon: <Truck className="w-8 h-8 text-indigo-500" />,
      color: "from-indigo-500/10 to-primary/10 border-indigo-500/20",
    },
    {
      id: "hospital" as UserRole,
      title: "Hospital Agent Center",
      subtitle: "Manage emergency beds, review patient telemetry and ETAs in real-time.",
      icon: <Building2 className="w-8 h-8 text-teal-500" />,
      color: "from-teal-500/10 to-accent/10 border-teal-500/20",
    },
  ];

  const handleRoleSelect = (role: UserRole) => {
    setSelectedRole(role);
    setStep("login_form");
  };

  const handleBack = () => {
    setStep("select_role");
    setErrors({});
  };

  const handleLoginSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Simple Validation
    const newErrors: { email?: string; password?: string } = {};
    if (!email) {
      newErrors.email = "Gmail address is required";
    } else if (!email.endsWith("@gmail.com")) {
      newErrors.email = "Email must end with @gmail.com";
    }
    
    if (!password) {
      newErrors.password = "Password is required";
    } else if (password.length < 6) {
      newErrors.password = "Password must be at least 6 characters";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsLoading(true);
    
    // Simulate premium login spinner and transition
    setTimeout(() => {
      setIsLoading(false);
      if (selectedRole) {
        setLoginEmail(email);
        setIsLoggedIn(true);
        setActiveRole(selectedRole);
      }
    }, 1500);
  };

  // Outer container animations
  const containerVariants: any = {
    hidden: { opacity: 0, scale: 0.98 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: { duration: 0.5, ease: "easeOut" },
    },
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center py-12 px-4 sm:px-6 lg:px-8 relative bg-gradient-to-tr from-background via-background to-secondary/30">
      {/* Decorative premium floating shapes */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/5 rounded-full blur-3xl pointer-events-none" />
      
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="w-full max-w-4xl text-center z-10"
      >
        <AnimatePresence mode="wait">
          {step === "select_role" ? (
            <motion.div
              key="select-role"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.4 }}
              className="flex flex-col items-center"
            >
              {/* Header */}
              <div className="flex items-center gap-2 mb-3 px-4 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold">
                <Sparkles className="w-3.5 h-3.5" />
                AI-Powered Response Engine
              </div>
              <h2 className="text-4xl font-extrabold text-text-primary tracking-tight max-w-2xl">
                SmartRescue <span className="text-primary font-bold">AI</span>
              </h2>
              <p className="mt-3 text-lg text-text-secondary max-w-xl">
                Choose your operations hub access portal below to initialize telemetry streams.
              </p>

              {/* Cards Grid */}
              <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
                {roleDetails.map((role) => (
                  <motion.div
                    key={role.id}
                    whileHover={{ y: -8, scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => handleRoleSelect(role.id)}
                    className="cursor-pointer flex"
                  >
                    <Card
                      glass
                      className={`flex flex-col items-center text-center p-8 rounded-3xl border border-border-custom bg-gradient-to-b ${role.color} h-full justify-between glass-card-hover shadow-soft`}
                    >
                      <div className="flex flex-col items-center">
                        <div className="w-16 h-16 rounded-2xl bg-white border border-border-custom flex items-center justify-center shadow-soft mb-6 transition-all duration-300">
                          {role.icon}
                        </div>
                        <h3 className="text-lg font-bold text-text-primary mb-2 select-none">
                          {role.title}
                        </h3>
                        <p className="text-xs text-text-secondary leading-relaxed select-none">
                          {role.subtitle}
                        </p>
                      </div>

                      <div className="mt-8 w-full">
                        <span className="inline-flex items-center gap-1 text-xs font-bold text-primary hover:text-primary/85">
                          Launch Interface
                          <ArrowLeft className="w-3 h-3 rotate-180" />
                        </span>
                      </div>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="auth-form"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.4 }}
              className="flex justify-center w-full"
            >
              <Card glass className="w-full max-w-md p-8 rounded-3xl shadow-premium text-left">
                {/* Back button */}
                <button
                  onClick={handleBack}
                  className="flex items-center gap-1.5 text-xs font-bold text-text-secondary hover:text-text-primary transition-colors mb-6 cursor-pointer"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  Change Role
                </button>

                <div className="flex items-center gap-2 mb-2">
                  <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
                    {selectedRole === "user" && <User className="w-5 h-5 text-primary" />}
                    {selectedRole === "driver" && <Truck className="w-5 h-5 text-indigo-500" />}
                    {selectedRole === "hospital" && <Building2 className="w-5 h-5 text-teal-500" />}
                  </div>
                  <div>
                    <h3 className="text-xl font-extrabold text-text-primary">
                      {selectedRole === "user" && "Citizen Portal Login"}
                      {selectedRole === "driver" && "Ambulance MDT Sync"}
                      {selectedRole === "hospital" && "Hospital Ops Login"}
                    </h3>
                    <p className="text-xs text-text-secondary">
                      Access code dispatch systems
                    </p>
                  </div>
                </div>

                <form onSubmit={handleLoginSubmit} className="mt-8 space-y-5">
                  <Input
                    label="Gmail Address"
                    type="email"
                    placeholder="name@gmail.com"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (errors.email) setErrors((prev) => ({ ...prev, email: undefined }));
                    }}
                    error={errors.email}
                  />

                  <Input
                    label="Access Password"
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (errors.password) setErrors((prev) => ({ ...prev, password: undefined }));
                    }}
                    error={errors.password}
                  />

                  <Input
                    label="Mobile Number (Optional)"
                    type="tel"
                    placeholder="+91 99999 99999"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                  />

                  <Button
                    type="submit"
                    variant="primary"
                    className="w-full py-3 mt-6 flex items-center justify-center gap-2"
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Synchronizing Telemetry...
                      </>
                    ) : (
                      <>
                        <ShieldCheck className="w-4 h-4" />
                        Sync Identity
                      </>
                    )}
                  </Button>
                </form>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};
