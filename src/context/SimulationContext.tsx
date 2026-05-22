"use client";

import React, { createContext, useContext, useState, useEffect, useRef } from "react";

export type UserRole = "guest" | "user" | "driver" | "hospital";
export type EmergencyState = "idle" | "countdown" | "triggered" | "accepted" | "transporting" | "resolved";

export interface Telemetry {
  heartRate: number;
  accelerometer: { x: number; y: number; z: number; gForce: number };
  gyroscope: { alpha: number; beta: number; gamma: number };
  gps: { lat: number; lng: number; accuracy: number };
  smartwatchConnected: boolean;
  orientation: string;
}

export interface UserProfile {
  name: string;
  bloodGroup: string;
  phone: string;
  emergencyContact: string;
  emergencyPhone: string;
  profileCompleted: boolean;
}

export interface AmbulanceState {
  driverName: string;
  driverPhone: string;
  vehicleNumber: string;
  eta: number; // in minutes
  lat: number;
  lng: number;
  acceptedByMe: boolean; // For the current driver view
  attendedByOther: boolean; // If another driver accepted it
}

export interface HospitalStatus {
  hospitalName: string;
  availableBeds: number;
  totalBeds: number;
  availableIcu: number;
  totalIcu: number;
  traumaReady: boolean;
  surgeryReady: boolean;
  score: number; // Dynamic recommendation score (0-100)
}

interface SimulationContextType {
  // Authentication & Role
  activeRole: UserRole;
  setActiveRole: (role: UserRole) => void;
  isLoggedIn: boolean;
  setIsLoggedIn: (val: boolean) => void;
  loginEmail: string;
  setLoginEmail: (email: string) => void;
  
  // User Profile
  userProfile: UserProfile;
  setUserProfile: React.Dispatch<React.SetStateAction<UserProfile>>;
  locationPermission: "prompt" | "granted" | "denied";
  setLocationPermission: (status: "prompt" | "granted" | "denied") => void;

  // Emergency pipeline
  emergencyState: EmergencyState;
  setEmergencyState: (state: EmergencyState) => void;
  countdownValue: number;
  setCountdownValue: (val: number) => void;

  // Sensor telemetries
  telemetry: Telemetry;
  setTelemetry: React.Dispatch<React.SetStateAction<Telemetry>>;

  // Dispatch states
  ambulance: AmbulanceState;
  setAmbulance: React.Dispatch<React.SetStateAction<AmbulanceState>>;
  hospitals: HospitalStatus[];
  setHospitals: React.Dispatch<React.SetStateAction<HospitalStatus[]>>;

  // Actions
  triggerEmergency: () => void;
  triggerSevereImpact: () => void;
  cancelEmergency: () => void;
  acceptEmergencyByDriver: (byMe: boolean) => void;
  resolveEmergency: () => void;
  clearHospitalBeds: () => void;
  resetSimulation: () => void;
}

const SimulationContext = createContext<SimulationContextType | undefined>(undefined);

// Initial Positions (IIT Madras Area)
const USER_COORDS = { lat: 12.9915, lng: 80.2302 }; // Hostel zone
const AMBULANCE_START_COORDS = { lat: 12.9984, lng: 80.2418 }; // IIT Main Gate
const HOSPITAL_A_COORDS = { lat: 13.0065, lng: 80.2205 }; // Hospital A
const HOSPITAL_B_COORDS = { lat: 12.9882, lng: 80.2450 }; // Hospital B

// Waypoint Tracks for simulation & LeafletMap overlay
export const ROUTE_TO_PATIENT = [
  { lat: 12.9984, lng: 80.2418 }, // IIT Main Gate
  { lat: 12.9968, lng: 80.2396 },
  { lat: 12.9948, lng: 80.2372 },
  { lat: 12.9930, lng: 80.2351 },
  { lat: 12.9918, lng: 80.2338 }, // Gajendra Circle
  { lat: 12.9912, lng: 80.2320 },
  { lat: 12.9915, lng: 80.2302 }, // Hostel Zone (Patient Location)
];

export const ROUTE_TO_HOSPITAL = [
  { lat: 12.9915, lng: 80.2302 }, // Hostel Zone
  { lat: 12.9912, lng: 80.2320 },
  { lat: 12.9918, lng: 80.2338 }, // Gajendra Circle
  { lat: 12.9930, lng: 80.2351 },
  { lat: 12.9948, lng: 80.2372 },
  { lat: 12.9968, lng: 80.2396 },
  { lat: 12.9984, lng: 80.2418 }, // Out of IIT Gate
  { lat: 12.9960, lng: 80.2458 },
  { lat: 12.9924, lng: 80.2492 },
  { lat: 12.9882, lng: 80.2450 }, // Hospital B (Fortis Malar)
];

const initialUserProfile: UserProfile = {
  name: "Dharshan",
  bloodGroup: "O+",
  phone: "+91 98765 43210",
  emergencyContact: "Anitha (Mother)",
  emergencyPhone: "+91 98765 43211",
  profileCompleted: true,
};

const initialHospitals: HospitalStatus[] = [
  {
    hospitalName: "Apollo Emergency Care (Adyar)",
    availableBeds: 2,
    totalBeds: 20,
    availableIcu: 0,
    totalIcu: 5,
    traumaReady: false,
    surgeryReady: true,
    score: 65,
  },
  {
    hospitalName: "Fortis Malar Trauma Center",
    availableBeds: 14,
    totalBeds: 30,
    availableIcu: 4,
    totalIcu: 8,
    traumaReady: true,
    surgeryReady: true,
    score: 98, // Recommended
  },
];

export const SimulationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeRole, setActiveRole] = useState<UserRole>("guest");
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [loginEmail, setLoginEmail] = useState<string>("");
  const [userProfile, setUserProfile] = useState<UserProfile>(initialUserProfile);
  const [locationPermission, setLocationPermission] = useState<"prompt" | "granted" | "denied">("prompt");
  
  const [emergencyState, setEmergencyState] = useState<EmergencyState>("idle");
  const [countdownValue, setCountdownValue] = useState<number>(5);

  const [telemetry, setTelemetry] = useState<Telemetry>({
    heartRate: 72,
    accelerometer: { x: 0.1, y: 0.2, z: 9.8, gForce: 1.0 },
    gyroscope: { alpha: 0.5, beta: -1.2, gamma: 0.1 },
    gps: { ...USER_COORDS, accuracy: 5 },
    smartwatchConnected: true,
    orientation: "Portrait Upright",
  });

  const [ambulance, setAmbulance] = useState<AmbulanceState>({
    driverName: "Karthik Raja",
    driverPhone: "+91 99887 76655",
    vehicleNumber: "TN-07-CS-1082",
    eta: 6,
    ...AMBULANCE_START_COORDS,
    acceptedByMe: false,
    attendedByOther: false,
  });

  const [hospitals, setHospitals] = useState<HospitalStatus[]>(initialHospitals);

  // References for intervals/simulation
  const countdownIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const telemetryIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const transitIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // 1. Simulating real-time sensor fluctuation
  useEffect(() => {
    telemetryIntervalRef.current = setInterval(() => {
      setTelemetry((prev) => {
        // Heart rate fluctuations
        let hrDelta = (Math.random() - 0.5) * 3;
        // Increase heart rate significantly if in distress/countdown/triggered
        let baseHr = 72;
        if (emergencyState !== "idle" && emergencyState !== "resolved") {
          baseHr = 118;
          hrDelta = (Math.random() - 0.3) * 4; // Tends upward
        }
        const nextHeartRate = Math.round(Math.max(60, Math.min(150, prev.heartRate + hrDelta)));

        // Micro-shaking of accelerometer (under 1.1G) unless severe impact is triggered
        let accX = prev.accelerometer.x;
        let accY = prev.accelerometer.y;
        let accZ = prev.accelerometer.z;
        let gForce = prev.accelerometer.gForce;

        if (gForce < 5) {
          accX = (Math.random() - 0.5) * 0.4;
          accY = (Math.random() - 0.5) * 0.4;
          accZ = 9.8 + (Math.random() - 0.5) * 0.4;
          gForce = parseFloat((Math.sqrt(accX ** 2 + accY ** 2 + accZ ** 2) / 9.8).toFixed(2));
        } else {
          // Decelerating crash peak back to normal over time
          accX = prev.accelerometer.x * 0.7;
          accY = prev.accelerometer.y * 0.7;
          accZ = 9.8 + (prev.accelerometer.z - 9.8) * 0.7;
          gForce = parseFloat((Math.sqrt(accX ** 2 + accY ** 2 + accZ ** 2) / 9.8).toFixed(2));
        }

        return {
          ...prev,
          heartRate: nextHeartRate,
          accelerometer: { x: accX, y: accY, z: accZ, gForce },
          gyroscope: {
            alpha: prev.gyroscope.alpha + (Math.random() - 0.5) * 0.2,
            beta: prev.gyroscope.beta + (Math.random() - 0.5) * 0.2,
            gamma: prev.gyroscope.gamma + (Math.random() - 0.5) * 0.2,
          },
        };
      });
    }, 1000);

    return () => {
      if (telemetryIntervalRef.current) clearInterval(telemetryIntervalRef.current);
    };
  }, [emergencyState]);

  // 2. Manage Countdown logic
  useEffect(() => {
    if (emergencyState === "countdown") {
      setCountdownValue(5);
      countdownIntervalRef.current = setInterval(() => {
        setCountdownValue((prev) => {
          if (prev <= 1) {
            if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
            setEmergencyState("triggered");
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (countdownIntervalRef.current) {
        clearInterval(countdownIntervalRef.current);
      }
    }

    return () => {
      if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
    };
  }, [emergencyState]);

  // 3. Simulating Ambulance Movement in Accepted & Transporting States via Waypoints
  useEffect(() => {
    if (emergencyState === "accepted") {
      if (transitIntervalRef.current) clearInterval(transitIntervalRef.current);

      let stepIdx = 0;
      setAmbulance((prev) => ({
        ...prev,
        eta: ROUTE_TO_PATIENT.length - 1,
        lat: ROUTE_TO_PATIENT[0].lat,
        lng: ROUTE_TO_PATIENT[0].lng,
      }));

      transitIntervalRef.current = setInterval(() => {
        stepIdx += 1;
        if (stepIdx >= ROUTE_TO_PATIENT.length) {
          if (transitIntervalRef.current) clearInterval(transitIntervalRef.current);
          setEmergencyState("transporting");
          return;
        }

        const point = ROUTE_TO_PATIENT[stepIdx];
        const remainingEta = Math.max(1, ROUTE_TO_PATIENT.length - 1 - stepIdx);

        setAmbulance((prev) => ({
          ...prev,
          lat: point.lat,
          lng: point.lng,
          eta: remainingEta,
        }));
      }, 1500); // Step coordinate every 1.5 seconds

    } else if (emergencyState === "transporting") {
      if (transitIntervalRef.current) clearInterval(transitIntervalRef.current);

      let stepIdx = 0;
      setAmbulance((prev) => ({
        ...prev,
        eta: ROUTE_TO_HOSPITAL.length - 1,
        lat: ROUTE_TO_HOSPITAL[0].lat,
        lng: ROUTE_TO_HOSPITAL[0].lng,
      }));

      transitIntervalRef.current = setInterval(() => {
        stepIdx += 1;
        if (stepIdx >= ROUTE_TO_HOSPITAL.length) {
          if (transitIntervalRef.current) clearInterval(transitIntervalRef.current);
          setEmergencyState("resolved");
          return;
        }

        const point = ROUTE_TO_HOSPITAL[stepIdx];
        const remainingEta = Math.max(1, ROUTE_TO_HOSPITAL.length - 1 - stepIdx);

        setAmbulance((prev) => ({
          ...prev,
          lat: point.lat,
          lng: point.lng,
          eta: remainingEta,
        }));
      }, 1500);
    } else if (emergencyState === "idle" || emergencyState === "resolved") {
      if (transitIntervalRef.current) {
        clearInterval(transitIntervalRef.current);
      }
    }

    return () => {
      if (transitIntervalRef.current) clearInterval(transitIntervalRef.current);
    };
  }, [emergencyState]);

  // ACTIONS
  const triggerEmergency = () => {
    setEmergencyState("countdown");
  };

  const triggerSevereImpact = () => {
    // Inject massive G-force
    setTelemetry((prev) => ({
      ...prev,
      accelerometer: { x: 14.8, y: -8.2, z: 2.1, gForce: 17.2 },
    }));
    // Instantly go to countdown
    setEmergencyState("countdown");
  };

  const cancelEmergency = () => {
    setEmergencyState("idle");
    setCountdownValue(5);
  };

  const acceptEmergencyByDriver = (byMe: boolean) => {
    setAmbulance((prev) => ({
      ...prev,
      acceptedByMe: byMe,
      attendedByOther: !byMe,
    }));
    setEmergencyState("accepted");
  };

  const resolveEmergency = () => {
    setEmergencyState("resolved");
    setAmbulance((prev) => ({
      ...prev,
      eta: 0,
      lat: HOSPITAL_B_COORDS.lat,
      lng: HOSPITAL_B_COORDS.lng,
    }));
  };

  const clearHospitalBeds = () => {
    setHospitals((prev) =>
      prev.map((h, i) =>
        i === 1
          ? { ...h, availableBeds: 28, availableIcu: 8, score: 99 } // Fortis Trauma
          : { ...h, availableBeds: 18, availableIcu: 4, score: 88 } // Apollo Adyar
      )
    );
  };

  const resetSimulation = () => {
    // Clear all states
    setEmergencyState("idle");
    setCountdownValue(5);
    setTelemetry({
      heartRate: 72,
      accelerometer: { x: 0.1, y: 0.2, z: 9.8, gForce: 1.0 },
      gyroscope: { alpha: 0.5, beta: -1.2, gamma: 0.1 },
      gps: { ...USER_COORDS, accuracy: 5 },
      smartwatchConnected: true,
      orientation: "Portrait Upright",
    });
    setAmbulance({
      driverName: "Karthik Raja",
      driverPhone: "+91 99887 76655",
      vehicleNumber: "TN-07-CS-1082",
      eta: 6,
      ...AMBULANCE_START_COORDS,
      acceptedByMe: false,
      attendedByOther: false,
    });
    setHospitals(initialHospitals);
  };

  return (
    <SimulationContext.Provider
      value={{
        activeRole,
        setActiveRole,
        isLoggedIn,
        setIsLoggedIn,
        loginEmail,
        setLoginEmail,
        userProfile,
        setUserProfile,
        locationPermission,
        setLocationPermission,
        emergencyState,
        setEmergencyState,
        countdownValue,
        setCountdownValue,
        telemetry,
        setTelemetry,
        ambulance,
        setAmbulance,
        hospitals,
        setHospitals,
        triggerEmergency,
        triggerSevereImpact,
        cancelEmergency,
        acceptEmergencyByDriver,
        resolveEmergency,
        clearHospitalBeds,
        resetSimulation,
      }}
    >
      {children}
    </SimulationContext.Provider>
  );
};

export const useSimulation = () => {
  const context = useContext(SimulationContext);
  if (!context) {
    throw new Error("useSimulation must be used within a SimulationProvider");
  }
  return context;
};
