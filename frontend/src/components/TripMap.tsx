// @ts-nocheck
'use client';

import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface MapStop {
  name: string;
  address: string;
  lat: number;
  lon: number;
  distance_from_last?: number;
}

interface TripMapProps {
  stops: MapStop[];
}

export default function TripMap({ stops }: TripMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // 1. Initialize map if not already done
    if (!mapRef.current) {
      mapRef.current = L.map(mapContainerRef.current, {
        zoomControl: true,
        scrollWheelZoom: true
      }).setView([44.1003, -70.2147], 8);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(mapRef.current);
      
      layerGroupRef.current = L.layerGroup().addTo(mapRef.current);
    }

    // 2. Clear old markers/polylines
    if (layerGroupRef.current) {
      layerGroupRef.current.clearLayers();
    }

    if (!stops || stops.length === 0) return;

    // 3. Add markers and draw polyline
    const latlngs: L.LatLngExpression[] = [];
    const bounds = L.latLngBounds([]);

    stops.forEach((stop, i) => {
      const isStart = i === 0;
      const isReturn = i === stops.length - 1 && stop.name === "Return to Start";
      
      const latlng: L.LatLngExpression = [stop.lat, stop.lon];
      latlngs.push(latlng);
      bounds.extend(latlng);

      // Define color schemes: Emerald for Start, Rose for Return, Indigo for standard stops
      let color = '#4f46e5'; // Indigo-600
      let labelText = `${i}`;
      
      if (isStart) {
        color = '#10b981'; // Emerald-500
        labelText = 'Start';
      } else if (isReturn) {
        color = '#f43f5e'; // Rose-500
        labelText = 'End';
      }

      // Custom marker icon with inline SVG wrapper to avoid Next.js image loading errors
      const customIcon = L.divIcon({
        className: 'custom-leaflet-marker',
        html: `
          <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            background-color: ${color};
            border: 2px solid #ffffff;
            border-radius: 50%;
            color: #ffffff;
            font-family: sans-serif;
            font-weight: 800;
            font-size: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
            text-align: center;
          ">
            ${labelText}
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
        popupAnchor: [0, -14]
      });

      const marker = L.marker(latlng, { icon: customIcon });
      
      const popupContent = `
        <div style="color: #1e293b; font-family: sans-serif; font-size: 12px; padding: 4px; max-width: 200px;">
          <h4 style="margin: 0 0 4px 0; font-weight: bold; font-size: 13px; color: #0f172a;">
            ${stop.name}
          </h4>
          <p style="margin: 0; color: #64748b; font-size: 11px;">
            ${stop.address}
          </p>
          ${stop.distance_from_last ? `
            <div style="margin-top: 6px; padding-top: 6px; border-t: 1px solid #e2e8f0; font-weight: bold; color: #4f46e5;">
              Leg Distance: ${stop.distance_from_last} miles
            </div>
          ` : ''}
        </div>
      `;

      marker.bindPopup(popupContent);
      if (layerGroupRef.current) {
        marker.addTo(layerGroupRef.current);
      }
    });

    // 4. Draw Polyline Route Connector
    if (latlngs.length > 1) {
      const polyline = L.polyline(latlngs, {
        color: '#6366f1', // Indigo-500
        weight: 3.5,
        opacity: 0.85,
        dashArray: '6, 6'
      });
      
      if (layerGroupRef.current) {
        polyline.addTo(layerGroupRef.current);
      }
      
      // Auto zoom to see all markers nicely
      mapRef.current.fitBounds(bounds, { padding: [50, 50] });
    } else if (latlngs.length === 1) {
      mapRef.current.setView(latlngs[0], 12);
    }
  }, [stops]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  return (
    <div className="relative w-full h-full min-h-[450px]">
      <div 
        ref={mapContainerRef} 
        className="absolute inset-0 w-full h-full rounded-2xl border border-slate-800/80 shadow-2xl z-10"
      />
    </div>
  );
}
