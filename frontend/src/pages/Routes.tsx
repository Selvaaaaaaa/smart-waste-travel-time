import React, { useEffect, useState } from 'react';
import {
  Route as RouteIcon,
  Search,
  Filter,
  RefreshCw,
  Truck,
  User,
  Navigation,
  Scale,
  Clock,
} from 'lucide-react';
import { api } from '../services/api';
import { RouteItem } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { DemoBadge } from '../components/common/DemoBadge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';

export const Routes: React.FC = () => {
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [vehicleFilter, setVehicleFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchRoutes = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getRoutes({
        status: statusFilter !== 'all' ? statusFilter : undefined,
        vehicle_id: vehicleFilter !== 'all' ? vehicleFilter : undefined,
        search: searchQuery || undefined,
      });
      setRoutes(res.routes);
    } catch (err) {
      console.error('Failed to load routes:', err);
      setError(err instanceof Error ? err.message : 'Error loading routes.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoutes();
  }, [statusFilter, vehicleFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchRoutes();
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
            <RouteIcon className="w-6 h-6 text-emerald-400" />
            Active Collection Routes
          </h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Monitor real-time progress, stop assignments, and travel-time baselines across the fleet.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchRoutes}
            className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Table
          </button>
          <DemoBadge label="Demo Data — Phase 1" />
        </div>
      </div>

      {/* Filter and Search Controls Bar */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search Route ID, Driver, or Vehicle..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900/90 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-emerald-500 transition-colors"
          />
        </form>

        <div className="flex items-center gap-3 w-full md:w-auto flex-wrap">
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs text-slate-400 font-medium">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="all">All Statuses</option>
              <option value="On Schedule">On Schedule</option>
              <option value="Delayed">Delayed</option>
              <option value="At Risk">At Risk</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Truck className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-xs text-slate-400 font-medium">Vehicle:</span>
            <select
              value={vehicleFilter}
              onChange={(e) => setVehicleFilter(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
            >
              <option value="all">All Vehicles</option>
              <option value="V-01">V-01</option>
              <option value="V-02">V-02</option>
              <option value="V-03">V-03</option>
              <option value="V-04">V-04</option>
              <option value="V-05">V-05</option>
              <option value="V-06">V-06</option>
              <option value="V-07">V-07</option>
              <option value="V-08">V-08</option>
            </select>
          </div>
        </div>
      </div>

      {/* Routes Table */}
      {loading ? (
        <LoadingState message="Fetching active routes telemetry..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchRoutes} />
      ) : routes.length === 0 ? (
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-12 text-center text-slate-400 text-xs">
          No routes matched the specified filter criteria.
        </div>
      ) : (
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-900/80 border-b border-slate-700 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Route ID</th>
                  <th className="py-3.5 px-4">Vehicle</th>
                  <th className="py-3.5 px-4">Driver</th>
                  <th className="py-3.5 px-4">Waste Volume</th>
                  <th className="py-3.5 px-4">Distance</th>
                  <th className="py-3.5 px-4">Baseline ETA</th>
                  <th className="py-3.5 px-4">Context ETA</th>
                  <th className="py-3.5 px-4">Stops</th>
                  <th className="py-3.5 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50 text-xs">
                {routes.map((route) => (
                  <tr
                    key={route.route_id}
                    className="hover:bg-slate-700/30 transition-colors"
                  >
                    <td className="py-3.5 px-4 font-mono font-bold text-emerald-400">
                      {route.route_id}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1.5 text-slate-300 font-mono">
                        <Truck className="w-3.5 h-3.5 text-slate-400" />
                        {route.vehicle_id}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1.5 text-slate-200">
                        <User className="w-3.5 h-3.5 text-slate-400" />
                        {route.driver_name}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1.5 font-mono text-slate-300">
                        <Scale className="w-3.5 h-3.5 text-slate-400" />
                        {route.waste_volume_tons} tons
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-1.5 font-mono text-slate-300">
                        <Navigation className="w-3.5 h-3.5 text-slate-400" />
                        {route.distance_km} km
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        {route.baseline_eta_min} min
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-cyan-400 font-semibold">
                      {route.context_eta_min} min
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-300">
                      {route.collection_stops_count} stops
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={route.status} size="sm" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="p-3 bg-slate-900/60 border-t border-slate-700/60 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-slate-400">
            <span>Showing {routes.length} active collection routes</span>
            <DemoBadge label="Demo Data — Phase 1" className="text-[10px]" />
          </div>
        </div>
      )}
    </div>
  );
};
