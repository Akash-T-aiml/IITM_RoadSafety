"use client";

import React, { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useSimulation, ROUTE_TO_PATIENT, ROUTE_TO_HOSPITAL } from "@/context/SimulationContext";

export default function LeafletMap() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const ambulanceMarkerRef = useRef<L.Marker | null>(null);
  const routePolylineRef = useRef<L.Polyline | null>(null);

  const { emergencyState, ambulance } = useSimulation();

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Center on IIT Madras / Adyar area
    const map = L.map(mapContainerRef.current, {
      zoomControl: false,
      attributionControl: false,
    }).setView([12.9935, 80.2380], 14);

    // CartoDB Voyager Tile Layer (Light, elegant, clean maps matching the light day theme)
    L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
      maxZoom: 19,
    }).addTo(map);

    // Add zoom control at bottom right
    L.control.zoom({ position: "bottomright" }).addTo(map);

    mapRef.current = map;

    // Draw static markers
    // Hospital (Fortis Malar) - green cross beacon
    const hospitalIcon = L.divIcon({
      html: `<div class="relative w-8 h-8 flex items-center justify-center">
               <div class="absolute inset-0 rounded-full bg-success/20 animate-pulse"></div>
               <div class="absolute w-5 h-5 rounded-full bg-success border-2 border-white flex items-center justify-center shadow-md">
                 <span class="text-white text-xs font-bold leading-none select-none">+</span>
               </div>
             </div>`,
      className: "",
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });
    L.marker([12.9882, 80.2450], { icon: hospitalIcon }).addTo(map);

    // Patient site (IIT Hostel Zone) - pulsing emergency red locator
    const patientIcon = L.divIcon({
      html: `<div class="relative w-8 h-8 flex items-center justify-center">
               <div class="absolute inset-0 rounded-full bg-emergency/35 animate-ping"></div>
               <div class="absolute w-5 h-5 rounded-full bg-emergency border-2 border-white flex items-center justify-center shadow-md">
                 <div class="w-1.5 h-1.5 rounded-full bg-white"></div>
               </div>
             </div>`,
      className: "",
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    });
    L.marker([12.9915, 80.2302], { icon: patientIcon }).addTo(map);

    // Create Ambulance Marker at initial coordinates
    const ambulanceIcon = L.divIcon({
      html: `<div class="relative w-10 h-10 flex items-center justify-center">
               <div class="absolute inset-0 rounded-full bg-primary/25 animate-pulse"></div>
               <div class="absolute w-6 h-6 rounded-full bg-primary border-2 border-white flex items-center justify-center shadow-md text-white">
                 <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
                   <polygon points="5 3 19 12 5 21 5 3"/>
                 </svg>
               </div>
             </div>`,
      className: "",
      iconSize: [40, 40],
      iconAnchor: [20, 20],
    });
    const ambMarker = L.marker([ambulance.lat, ambulance.lng], { icon: ambulanceIcon }).addTo(map);
    ambulanceMarkerRef.current = ambMarker;

    // Draw complete background routes as reference lines (subtle dashed grey)
    const backgroundCoords = [...ROUTE_TO_PATIENT, ...ROUTE_TO_HOSPITAL].map(c => L.latLng(c.lat, c.lng));
    L.polyline(backgroundCoords, {
      color: "rgba(108, 140, 255, 0.15)",
      weight: 4,
      dashArray: "6, 6",
    }).addTo(map);

    // Dynamic routing line
    const activeRouteLine = L.polyline([], {
      color: "#6C8CFF",
      weight: 5,
      opacity: 0.85,
    }).addTo(map);
    routePolylineRef.current = activeRouteLine;

    // Clean up on unmount
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  // Sync positions and paths
  useEffect(() => {
    if (!mapRef.current || !ambulanceMarkerRef.current || !routePolylineRef.current) return;

    // 1. Move ambulance marker
    ambulanceMarkerRef.current.setLatLng([ambulance.lat, ambulance.lng]);

    // 2. Draw path polyline based on active state
    if (emergencyState === "accepted") {
      const activePath = ROUTE_TO_PATIENT.map(c => L.latLng(c.lat, c.lng));
      routePolylineRef.current.setLatLngs(activePath);
      routePolylineRef.current.setStyle({ color: "#6C8CFF" }); // Indigo route to patient
      
      const bounds = L.latLngBounds(activePath);
      mapRef.current.fitBounds(bounds, { padding: [50, 50] });

    } else if (emergencyState === "transporting") {
      const activePath = ROUTE_TO_HOSPITAL.map(c => L.latLng(c.lat, c.lng));
      routePolylineRef.current.setLatLngs(activePath);
      routePolylineRef.current.setStyle({ color: "#4ADE80" }); // Success green route to hospital
      
      const bounds = L.latLngBounds(activePath);
      mapRef.current.fitBounds(bounds, { padding: [50, 50] });

    } else if (emergencyState === "resolved") {
      routePolylineRef.current.setLatLngs([]);
      mapRef.current.setView([12.9882, 80.2450], 15.5); // Focus hospital ER

    } else {
      routePolylineRef.current.setLatLngs([]);
      mapRef.current.setView([12.9935, 80.2380], 14); // General view
    }
  }, [emergencyState, ambulance.lat, ambulance.lng]);

  return (
    <div className="w-full h-full rounded-2xl overflow-hidden border border-border-custom shadow-inner min-h-[320px] md:min-h-[400px] relative">
      <div className="absolute top-3 left-3 z-[1000] glass-card px-3 py-1.5 rounded-xl border border-border-custom text-[10px] font-bold shadow-soft flex items-center gap-1.5 select-none pointer-events-none">
        <span className="w-2 h-2 rounded-full bg-success animate-ping" />
        OSM Live Routing Active
      </div>
      <div ref={mapContainerRef} className="w-full h-full min-h-[320px] md:min-h-[400px] bg-[#F5F7FB]" />
    </div>
  );
}
