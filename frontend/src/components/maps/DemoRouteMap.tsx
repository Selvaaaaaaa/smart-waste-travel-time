import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import { DemoBadge } from '../common/DemoBadge';
import { Navigation, Info } from 'lucide-react';

// Fix standard Leaflet default marker icons in Vite/bundler setups
const depotIcon = new L.DivIcon({
  className: 'custom-leaflet-icon',
  html: `<div style="background-color: #10b981; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 11px; border: 2px solid white; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5);">DEP</div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

const stopIcon = new L.DivIcon({
  className: 'custom-leaflet-icon',
  html: `<div style="background-color: #3b82f6; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 10px; border: 2px solid white; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5);">ST</div>`,
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

const destIcon = new L.DivIcon({
  className: 'custom-leaflet-icon',
  html: `<div style="background-color: #ef4444; color: white; border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 11px; border: 2px solid white; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.5);">FAC</div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

// Safe synthetic coordinates (depot -> collection points -> processing plant)
const DEMO_WAYPOINTS: [number, number][] = [
  [40.7128, -74.0060], // Depot / Start
  [40.7180, -73.9980], // Stop 1
  [40.7250, -73.9920], // Stop 2
  [40.7310, -73.9850], // Stop 3
  [40.7380, -73.9800], // Stop 4
  [40.7450, -73.9720], // Processing Hub / Destination
];

export const DemoRouteMap: React.FC = () => {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-slate-700/50 text-emerald-400 border border-slate-600/40">
            <Navigation className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide flex items-center gap-2">
              Route Simulation Map (Route R-101)
            </h3>
            <p className="text-xs text-slate-400">
              Interactive geographic tracking & stop progression preview
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <DemoBadge label="Operations Mode: Simulation" />
        </div>
      </div>

      {/* Map viewport container */}
      <div className="h-[360px] w-full rounded-lg overflow-hidden border border-slate-700/80 relative bg-slate-900">
        {isMounted ? (
          <MapContainer
            center={[40.728, -73.99]}
            zoom={13}
            scrollWheelZoom={false}
            className="w-full h-full"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {/* Polyline connecting route stops */}
            <Polyline
              positions={DEMO_WAYPOINTS}
              pathOptions={{
                color: '#10b981',
                weight: 4,
                dashArray: '8, 8',
                opacity: 0.85,
              }}
            />

            {/* Start Depot */}
            <Marker position={DEMO_WAYPOINTS[0]} icon={depotIcon}>
              <Popup>
                <div className="text-xs space-y-1">
                  <p className="font-bold text-emerald-400">Start: Central Depot (Synthetic)</p>
                  <p className="text-slate-300">Vehicle: V-01 (Capacity: 10.0 tons)</p>
                  <p className="text-slate-400 font-mono">Departure: 07:00 AM</p>
                </div>
              </Popup>
            </Marker>

            {/* Stop 1 */}
            <Marker position={DEMO_WAYPOINTS[1]} icon={stopIcon}>
              <Popup>
                <div className="text-xs space-y-1">
                  <p className="font-bold text-blue-400">Stop 1: Sector A (Commercial)</p>
                  <p className="text-slate-300">Est. Volume: 850 kg</p>
                </div>
              </Popup>
            </Marker>

            {/* Stop 2 */}
            <Marker position={DEMO_WAYPOINTS[2]} icon={stopIcon}>
              <Popup>
                <div className="text-xs space-y-1">
                  <p className="font-bold text-blue-400">Stop 2: Sector B (Residential)</p>
                  <p className="text-slate-300">Est. Volume: 1,200 kg</p>
                </div>
              </Popup>
            </Marker>

            {/* Stop 3 */}
            <Marker position={DEMO_WAYPOINTS[3]} icon={stopIcon}>
              <Popup>
                <div className="text-xs space-y-1">
                  <p className="font-bold text-blue-400">Stop 3: Sector C (Civic Block)</p>
                  <p className="text-slate-300">Est. Volume: 950 kg</p>
                </div>
              </Popup>
            </Marker>

            {/* Stop 4 */}
            <Marker position={DEMO_WAYPOINTS[4]} icon={stopIcon}>
              <Popup>
                <div className="text-xs space-y-1">
                  <p className="font-bold text-blue-400">Stop 4: Sector D (Market District)</p>
                  <p className="text-slate-300">Est. Volume: 1,200 kg</p>
                </div>
              </Popup>
            </Marker>

            {/* Destination Facility */}
            <Marker position={DEMO_WAYPOINTS[5]} icon={destIcon}>
              <Popup>
                <div className="text-xs space-y-1">
                  <p className="font-bold text-rose-400">Destination: Municipal Transfer Facility</p>
                  <p className="text-slate-300">Unloading bay & weighbridge station</p>
                </div>
              </Popup>
            </Marker>
          </MapContainer>
        ) : (
          <div className="flex items-center justify-center h-full text-xs text-slate-400">
            Initializing Leaflet map engine...
          </div>
        )}
      </div>

      {/* Map Legend & Disclaimer */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 pt-1 text-xs text-slate-400">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" />
            <span className="text-slate-300">Start (Depot)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-blue-500 inline-block" />
            <span className="text-slate-300">Collection Stops (1-4)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-rose-500 inline-block" />
            <span className="text-slate-300">Destination (Hub)</span>
          </div>
        </div>

        <div className="flex items-center gap-1 text-[11px] text-slate-400">
          <Info className="w-3.5 h-3.5 text-slate-400" />
          <span>Operational coordinates for simulated municipal route demonstration.</span>
        </div>
      </div>
    </div>
  );
};
