import React, { useEffect, useState } from 'react';
import {
  Scale,
  Route as RouteIcon,
  Clock,
  Target,
  Truck,
  ShieldCheck,
  CloudSun,
  Car,
  CalendarCheck,
  AlertOctagon,
  RefreshCw,
} from 'lucide-react';
import { api } from '../services/api';
import { DashboardSummary } from '../types';
import { MetricCard } from '../components/common/MetricCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { DemoBadge } from '../components/common/DemoBadge';
import { LoadingState } from '../components/common/LoadingState';
import { ErrorState } from '../components/common/ErrorState';
import { DemoRouteMap } from '../components/maps/DemoRouteMap';
import { WasteVolumeChart } from '../components/charts/WasteVolumeChart';
import { ETAComparisonChart } from '../components/charts/ETAComparisonChart';
import { ETAErrorChart } from '../components/charts/ETAErrorChart';
import { VehicleUtilizationChart } from '../components/charts/VehicleUtilizationChart';

export const Dashboard: React.FC = () => {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const summary = await api.getDashboardSummary();
      setData(summary);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError(err instanceof Error ? err.message : 'An unknown error occurred.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return <LoadingState message="Loading operations telemetry..." subMessage="Fetching live KPI aggregates from FastAPI backend" />;
  }

  if (error || !data) {
    return (
      <ErrorState
        title="Failed to Load Dashboard Data"
        message={error || 'No data received from backend service.'}
        onRetry={fetchDashboardData}
      />
    );
  }

  const { operating_conditions } = data;

  return (
    <div className="space-y-6">
      {/* Page Title Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight">
            Smart Waste Collection Operations
          </h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Context-aware travel-time and route simulation
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchDashboardData}
            className="inline-flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Telemetry
          </button>
          <DemoBadge label="Demo Data — Phase 1" />
        </div>
      </div>

      {/* 6 KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard
          title="Today's Waste Volume"
          value={data.waste_volume}
          unit={data.waste_volume_unit}
          icon={<Scale className="w-4 h-4" />}
          badgeLabel="Demo Data — Phase 1"
          trend={{ value: '+4.2% vs yesterday', isPositive: false }}
        />
        <MetricCard
          title="Active Routes"
          value={data.active_routes}
          icon={<RouteIcon className="w-4 h-4" />}
          badgeLabel="Demo Data — Phase 1"
          trend={{ value: '100% assigned', isPositive: true }}
        />
        <MetricCard
          title="Average ETA"
          value={data.average_eta_min}
          unit="min"
          icon={<Clock className="w-4 h-4" />}
          badgeLabel="Demo Data — Phase 1"
          trend={{ value: '-3 min under baseline', isPositive: true }}
        />
        <MetricCard
          title="ETA Accuracy"
          value={`${data.eta_accuracy_pct}%`}
          icon={<Target className="w-4 h-4" />}
          badgeLabel="Demo Data — Phase 1"
          trend={{ value: 'Within ±5 min tolerance', isPositive: true }}
        />
        <MetricCard
          title="Available Vehicles"
          value={data.available_vehicles}
          icon={<Truck className="w-4 h-4" />}
          badgeLabel="Demo Data — Phase 1"
          trend={{ value: '2 in reserve maintenance', isPositive: true }}
        />
        <MetricCard
          title="Workload Status"
          value={data.workload_status}
          icon={<ShieldCheck className="w-4 h-4" />}
          badgeLabel="Demo Data — Phase 1"
          trend={{ value: 'No safety violations', isPositive: true }}
        />
      </div>

      {/* Current Operating Conditions Section */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide uppercase">
              Current Operating Conditions
            </h2>
            <p className="text-xs text-slate-400">
              Environmental, logistical, and municipal restrictions affecting collection travel-times
            </p>
          </div>
          <DemoBadge label="Demo Data — Phase 1" />
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 pt-2">
          {/* Weather */}
          <div className="p-3 bg-slate-900/70 border border-slate-700/60 rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CloudSun className="w-4 h-4 text-amber-400 shrink-0" />
              <div className="text-xs">
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Weather</span>
                <span className="font-semibold text-slate-200">{operating_conditions.weather}</span>
              </div>
            </div>
            <StatusBadge status={operating_conditions.weather} size="sm" />
          </div>

          {/* Traffic */}
          <div className="p-3 bg-slate-900/70 border border-slate-700/60 rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Car className="w-4 h-4 text-cyan-400 shrink-0" />
              <div className="text-xs">
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Traffic</span>
                <span className="font-semibold text-slate-200">{operating_conditions.traffic}</span>
              </div>
            </div>
            <StatusBadge status={operating_conditions.traffic} size="sm" />
          </div>

          {/* Event Impact */}
          <div className="p-3 bg-slate-900/70 border border-slate-700/60 rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CalendarCheck className="w-4 h-4 text-indigo-400 shrink-0" />
              <div className="text-xs">
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Event Impact</span>
                <span className="font-semibold text-slate-200">{operating_conditions.event_impact}</span>
              </div>
            </div>
            <StatusBadge status={operating_conditions.event_impact} size="sm" />
          </div>

          {/* Road Restrictions */}
          <div className="p-3 bg-slate-900/70 border border-slate-700/60 rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 text-rose-400 shrink-0" />
              <div className="text-xs">
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Road Restrictions</span>
                <span className="font-semibold text-slate-200">{operating_conditions.road_restrictions}</span>
              </div>
            </div>
            <StatusBadge status={operating_conditions.road_restrictions} size="sm" />
          </div>

          {/* Waste Volume */}
          <div className="p-3 bg-slate-900/70 border border-slate-700/60 rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Scale className="w-4 h-4 text-emerald-400 shrink-0" />
              <div className="text-xs">
                <span className="text-slate-400 block text-[10px] uppercase font-semibold">Waste Volume</span>
                <span className="font-semibold text-slate-200">{operating_conditions.waste_volume}</span>
              </div>
            </div>
            <StatusBadge status={operating_conditions.waste_volume} size="sm" />
          </div>
        </div>
      </div>

      {/* Map Section */}
      <DemoRouteMap />

      {/* 4 Analytics & Comparison Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WasteVolumeChart data={data.waste_volume_trends} />
        <ETAComparisonChart data={data.eta_comparisons} />
        <ETAErrorChart data={data.eta_errors} />
        <VehicleUtilizationChart data={data.vehicle_utilization} />
      </div>
    </div>
  );
};
