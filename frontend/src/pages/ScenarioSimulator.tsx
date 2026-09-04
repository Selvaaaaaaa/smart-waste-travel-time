import React, { useEffect, useState } from 'react';
import {
  Sliders,
  CloudSun,
  Car,
  CalendarCheck,
  AlertOctagon,
  Scale,
  Play,
  RotateCcw,
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  TrendingUp,
  Activity,
  Layers,
} from 'lucide-react';
import { api } from '../services/api';
import {
  ScenarioRunResponse,
  PresetScenario,
} from '../types';
import { DemoBadge } from '../components/common/DemoBadge';
import { AlertBanner } from '../components/common/AlertBanner';
import { LoadingState } from '../components/common/LoadingState';

export const ScenarioSimulator: React.FC = () => {
  const [presets, setPresets] = useState<PresetScenario[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<string>('NORMAL');
  const [loadingPresets, setLoadingPresets] = useState<boolean>(true);
  const [simulating, setSimulating] = useState<boolean>(false);
  const [result, setResult] = useState<ScenarioRunResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form parameters
  const [weatherCondition, setWeatherCondition] = useState<string>('CLEAR');
  const [rainfallMm, setRainfallMm] = useState<number>(0.0);
  const [visibilityKm, setVisibilityKm] = useState<number>(10.0);
  const [trafficLevel, setTrafficLevel] = useState<string>('LOW');
  const [congestionIndex, setCongestionIndex] = useState<number>(15.0);
  const [eventLevel, setEventLevel] = useState<string>('NONE');
  const [roadRestrictionType, setRoadRestrictionType] = useState<string>('NONE');
  const [wasteVolumeTons, setWasteVolumeTons] = useState<number>(5.5);
  const [distanceKm, setDistanceKm] = useState<number>(22.5);
  const [hourOfDay, setHourOfDay] = useState<number>(9);

  useEffect(() => {
    const fetchPresets = async () => {
      try {
        const data = await api.getScenarioPresets();
        setPresets(data);
      } catch (err) {
        console.warn('Could not load scenario presets:', err);
      } finally {
        setLoadingPresets(false);
      }
    };
    fetchPresets();
  }, []);

  const applyPreset = (presetKey: string) => {
    setSelectedPreset(presetKey);
    const p = presets.find((item) => item.key === presetKey);
    if (!p) return;

    setWeatherCondition(p.weather_condition);
    setRainfallMm(p.rainfall_mm);
    setVisibilityKm(p.visibility_km);
    setTrafficLevel(p.traffic_level);
    setCongestionIndex(p.congestion_index);
    setEventLevel(p.event_level);
    setRoadRestrictionType(p.road_restriction_type);
    setWasteVolumeTons(p.waste_volume_tons);
    setHourOfDay(p.hour_of_day);
  };

  const handleRunScenario = async (e: React.FormEvent) => {
    e.preventDefault();
    setSimulating(true);
    setErrorMsg(null);
    try {
      const res = await api.runScenario({
        scenario_key: selectedPreset,
        distance_km: distanceKm,
        waste_volume_tons: wasteVolumeTons,
        weather_condition: weatherCondition,
        rainfall_mm: rainfallMm,
        visibility_km: visibilityKm,
        traffic_level: trafficLevel,
        congestion_index: congestionIndex,
        event_level: eventLevel,
        road_restriction_type: roadRestrictionType,
        hour_of_day: hourOfDay,
      });
      setResult(res);
    } catch (err: any) {
      console.error('Scenario execution failed:', err);
      setErrorMsg(err.message || 'Simulation execution failed.');
    } finally {
      setSimulating(false);
    }
  };

  const handleReset = () => {
    applyPreset('NORMAL');
    setDistanceKm(22.5);
    setResult(null);
    setErrorMsg(null);
  };

  if (loadingPresets) {
    return <LoadingState message="Loading simulation presets..." />;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
            <Sliders className="w-6 h-6 text-emerald-400" />
            Operational Scenario Simulator
          </h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Simulate environmental and logistical disruptions to compare Baseline vs Context-Aware ML ETA.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <DemoBadge label="Synthetic Dataset — Research Prototype" />
        </div>
      </div>

      {/* Preset Scenario Cards */}
      <div className="space-y-2">
        <label className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          Standard Operational Stress Scenarios
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {presets.map((sc) => {
            const isActive = selectedPreset === sc.key;
            return (
              <button
                type="button"
                key={sc.key}
                onClick={() => applyPreset(sc.key)}
                className={`p-3 text-left rounded-xl border transition-all ${
                  isActive
                    ? 'bg-emerald-500/20 border-emerald-500 text-white shadow-lg shadow-emerald-950/40 ring-1 ring-emerald-500'
                    : 'bg-slate-800/80 border-slate-700/80 text-slate-300 hover:border-slate-600 hover:bg-slate-800'
                }`}
              >
                <div className="text-xs font-bold truncate">{sc.name}</div>
                <div className="text-[10px] text-slate-400 mt-1 line-clamp-2 leading-tight">
                  {sc.description}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Simulation Result Card */}
      {errorMsg && (
        <AlertBanner type="error" title="Simulation Error" message={errorMsg} />
      )}

      {result && (
        <div className="animate-in fade-in slide-in-from-top-2 duration-300 space-y-4">
          {result.status === 'UNSAFE_ASSIGNMENT' ? (
            <div className="p-5 rounded-xl border border-rose-500/40 bg-rose-950/20 text-rose-200 flex items-start gap-3.5">
              <ShieldAlert className="w-6 h-6 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <h3 className="font-bold text-sm text-rose-300">
                  SAFETY CONSTRAINT VIOLATION — SIMULATION REJECTED
                </h3>
                <p className="text-xs text-rose-200/90 mt-1 font-mono">
                  {result.constraint_violation?.message || result.safety_message}
                </p>
                <p className="text-[11px] text-rose-400/80 mt-2">
                  Violation Type: {result.constraint_violation?.type || 'PAYLOAD_OR_FATIGUE_LIMIT'}
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-slate-800/90 border border-emerald-500/30 rounded-xl p-6 shadow-xl space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-700/80">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                      Scenario Simulation Completed
                    </span>
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      <ShieldCheck className="w-3 h-3" /> Safety Verified
                    </span>
                  </div>
                  <h2 className="text-xl font-black text-white mt-0.5">{result.scenario_name}</h2>
                </div>
                <div className="text-right">
                  <div className="text-xs text-slate-400">Simulated Ground-Truth Travel Time</div>
                  <div className="text-2xl font-black text-amber-400">
                    {result.simulated_actual_minutes} <span className="text-sm font-normal">min</span>
                  </div>
                </div>
              </div>

              {/* Baseline vs Context-Aware Metrics Comparison */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {/* Baseline Card */}
                <div className="bg-slate-900/80 border border-slate-700 rounded-xl p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                      Model 1: Baseline
                    </span>
                    <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
                      25 km/h Kinematic
                    </span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-black text-white">{result.baseline_eta_minutes}</span>
                    <span className="text-xs text-slate-400">minutes ETA</span>
                  </div>
                  <div className="pt-2 border-t border-slate-800 flex justify-between text-xs">
                    <span className="text-slate-400">Absolute Error:</span>
                    <span className="font-mono font-bold text-rose-400">
                      {result.baseline_error_minutes} min
                    </span>
                  </div>
                </div>

                {/* Context-Aware ML Card */}
                <div className="bg-gradient-to-br from-slate-900/90 to-emerald-950/30 border border-emerald-500/40 rounded-xl p-4 space-y-2 relative overflow-hidden">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-emerald-300 uppercase tracking-wider flex items-center gap-1">
                      <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                      Model 2: Context-Aware ML
                    </span>
                    <span className="text-[10px] bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded">
                      Random Forest
                    </span>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-black text-emerald-400">{result.context_aware_eta_minutes}</span>
                    <span className="text-xs text-emerald-300/80">minutes ETA</span>
                  </div>
                  <div className="pt-2 border-t border-emerald-500/20 flex justify-between text-xs">
                    <span className="text-emerald-300/80">Absolute Error:</span>
                    <span className="font-mono font-bold text-emerald-400">
                      {result.context_aware_error_minutes} min
                    </span>
                  </div>
                </div>

                {/* Improvement Card */}
                <div className="bg-slate-900/80 border border-slate-700 rounded-xl p-4 flex flex-col justify-between">
                  <div>
                    <div className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                      <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
                      Error Reduction
                    </div>
                    <div className="mt-2 flex items-baseline gap-2">
                      <span className={`text-3xl font-black ${
                        (result.improvement_pct || 0) >= 0 ? 'text-cyan-400' : 'text-amber-400'
                      }`}>
                        {result.improvement_pct !== undefined ? `${result.improvement_pct}%` : 'N/A'}
                      </span>
                      <span className="text-xs text-slate-400">error improvement</span>
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-3 pt-2 border-t border-slate-800">
                    Context-aware prediction uses environmental and operational context to compensate for real-world delays.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Scenario Configuration Controls Form */}
      <form onSubmit={handleRunScenario} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Weather Control */}
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
                <CloudSun className="w-4 h-4 text-amber-400" />
                <span>WEATHER</span>
              </div>
              <span className="text-xs font-mono text-slate-400">{weatherCondition}</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {['CLEAR', 'HEAVY_RAIN', 'STORM'].map((w) => (
                <button
                  type="button"
                  key={w}
                  onClick={() => {
                    setWeatherCondition(w);
                    if (w === 'CLEAR') { setRainfallMm(0); setVisibilityKm(10); }
                    else if (w === 'HEAVY_RAIN') { setRainfallMm(35); setVisibilityKm(3); }
                    else if (w === 'STORM') { setRainfallMm(55); setVisibilityKm(2); }
                  }}
                  className={`py-2 px-2 text-xs font-medium rounded-lg border transition-all ${
                    weatherCondition === w
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500 font-bold'
                      : 'bg-slate-900/60 text-slate-400 border-slate-700 hover:text-slate-200'
                  }`}
                >
                  {w.replace('_', ' ')}
                </button>
              ))}
            </div>
            <div className="pt-2 text-xs space-y-2">
              <div className="flex justify-between text-slate-400">
                <span>Rainfall:</span>
                <span className="font-mono text-white">{rainfallMm} mm</span>
              </div>
              <input
                type="range"
                min={0}
                max={70}
                value={rainfallMm}
                onChange={(e) => setRainfallMm(Number(e.target.value))}
                className="w-full accent-emerald-500"
              />
            </div>
          </div>

          {/* Traffic Control */}
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
                <Car className="w-4 h-4 text-cyan-400" />
                <span>TRAFFIC</span>
              </div>
              <span className="text-xs font-mono text-slate-400">{trafficLevel}</span>
            </div>
            <div className="grid grid-cols-4 gap-1.5">
              {['LOW', 'MEDIUM', 'HIGH', 'SEVERE'].map((t) => (
                <button
                  type="button"
                  key={t}
                  onClick={() => {
                    setTrafficLevel(t);
                    if (t === 'LOW') setCongestionIndex(15);
                    else if (t === 'MEDIUM') setCongestionIndex(45);
                    else if (t === 'HIGH') setCongestionIndex(70);
                    else if (t === 'SEVERE') setCongestionIndex(90);
                  }}
                  className={`py-2 px-1 text-xs font-medium rounded-lg border transition-all ${
                    trafficLevel === t
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500 font-bold'
                      : 'bg-slate-900/60 text-slate-400 border-slate-700 hover:text-slate-200'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
            <div className="pt-2 text-xs space-y-2">
              <div className="flex justify-between text-slate-400">
                <span>Congestion Index:</span>
                <span className="font-mono text-white">{congestionIndex}%</span>
              </div>
              <input
                type="range"
                min={0}
                max={100}
                value={congestionIndex}
                onChange={(e) => setCongestionIndex(Number(e.target.value))}
                className="w-full accent-emerald-500"
              />
            </div>
          </div>

          {/* Event Impact Control */}
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
                <CalendarCheck className="w-4 h-4 text-indigo-400" />
                <span>EVENT IMPACT</span>
              </div>
              <span className="text-xs font-mono text-slate-400">{eventLevel}</span>
            </div>
            <div className="grid grid-cols-4 gap-1.5">
              {['NONE', 'LOW', 'MEDIUM', 'HIGH'].map((e) => (
                <button
                  type="button"
                  key={e}
                  onClick={() => setEventLevel(e)}
                  className={`py-2 px-1 text-xs font-medium rounded-lg border transition-all ${
                    eventLevel === e
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500 font-bold'
                      : 'bg-slate-900/60 text-slate-400 border-slate-700 hover:text-slate-200'
                  }`}
                >
                  {e}
                </button>
              ))}
            </div>
            <p className="text-xs text-slate-400 pt-1">
              Public festivals, marathons, or sporting fixtures inducing arterial delays.
            </p>
          </div>

          {/* Road Restriction Control */}
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
                <AlertOctagon className="w-4 h-4 text-rose-400" />
                <span>ROAD RESTRICTION</span>
              </div>
              <span className="text-xs font-mono text-slate-400">{roadRestrictionType}</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {['NONE', 'CONSTRUCTION', 'PARTIAL_CLOSURE', 'ROAD_CLOSURE'].map((r) => (
                <button
                  type="button"
                  key={r}
                  onClick={() => setRoadRestrictionType(r)}
                  className={`py-2 px-2 text-xs font-medium rounded-lg border transition-all ${
                    roadRestrictionType === r
                      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500 font-bold'
                      : 'bg-slate-900/60 text-slate-400 border-slate-700 hover:text-slate-200'
                  }`}
                >
                  {r.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Waste Volume Control */}
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
                <Scale className="w-4 h-4 text-emerald-400" />
                <span>WASTE PAYLOAD</span>
              </div>
              <span className="text-xs font-mono text-white font-bold">{wasteVolumeTons} tons</span>
            </div>
            <input
              type="range"
              min={1.0}
              max={15.0}
              step={0.5}
              value={wasteVolumeTons}
              onChange={(e) => setWasteVolumeTons(Number(e.target.value))}
              className="w-full accent-emerald-500"
            />
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>Light (1.0t)</span>
              <span>Nominal (5.5t)</span>
              <span>Capacity Limit (12.0t)</span>
            </div>
          </div>

          {/* Route Distance Control */}
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-300 font-semibold text-sm">
                <Activity className="w-4 h-4 text-cyan-400" />
                <span>ROUTE DISTANCE</span>
              </div>
              <span className="text-xs font-mono text-white font-bold">{distanceKm} km</span>
            </div>
            <input
              type="range"
              min={5.0}
              max={60.0}
              step={1.0}
              value={distanceKm}
              onChange={(e) => setDistanceKm(Number(e.target.value))}
              className="w-full accent-emerald-500"
            />
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>Short (5 km)</span>
              <span>Urban Medium (22 km)</span>
              <span>Extended (60 km)</span>
            </div>
          </div>
        </div>

        {/* Action Panel */}
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Sparkles className="w-4 h-4" />
            </div>
            <div className="text-xs text-slate-300">
              <span className="font-semibold text-white block">Simulation Target:</span>
              <span className="font-mono text-slate-400">
                {distanceKm} km route | {wasteVolumeTons} tons | Weather: {weatherCondition} | Congestion: {congestionIndex}%
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              type="button"
              onClick={handleReset}
              className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset Defaults
            </button>
            <button
              type="submit"
              disabled={simulating}
              className="flex-1 sm:flex-none inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 text-white text-xs font-bold rounded-lg transition-all shadow-md hover:shadow-emerald-900/30"
            >
              <Play className="w-4 h-4 fill-current" />
              {simulating ? 'Simulating...' : 'Run Scenario'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
