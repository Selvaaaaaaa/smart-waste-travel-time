import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import {
  Compass,
  AlertTriangle,
  Play,
  RefreshCw,
  Zap,
  ShieldCheck,
  ShieldAlert,
  Clock,
  Weight,
  Activity,
  ChevronRight,
  TrendingDown,
  Info,
  CheckCircle2,
  Sliders,
  Sparkles,
} from 'lucide-react';
import { api } from '../services/api';
import {
  NetworkGraphResponse,
  ActiveTrip,
  RouteCandidate,
  ReroutingEvent,
  RoutingExperimentSummary,
} from '../types';

// Custom Marker Icons for Leaflet
const createNodeIcon = (type: string, isCurrent: boolean = false) => {
  let bg = '#3b82f6';
  let label = 'LOC';
  let size = 26;

  if (type === 'depot') {
    bg = '#10b981';
    label = 'DEP';
    size = 28;
  } else if (type === 'landfill') {
    bg = '#ef4444';
    label = 'LAND';
    size = 28;
  } else if (type === 'transfer_station') {
    bg = '#8b5cf6';
    label = 'HUB';
    size = 26;
  } else if (type === 'collection') {
    bg = '#f59e0b';
    label = 'ZONE';
    size = 24;
  } else {
    bg = '#64748b';
    label = 'INT';
    size = 20;
  }

  const border = isCurrent ? '3px solid #38bdf8' : '2px solid white';
  const shadow = isCurrent ? '0 0 12px #38bdf8' : '0 2px 5px rgba(0,0,0,0.5)';

  return new L.DivIcon({
    className: 'custom-leaflet-icon',
    html: `<div style="background-color: ${bg}; color: white; border-radius: 50%; width: ${size}px; height: ${size}px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 9px; border: ${border}; box-shadow: ${shadow};">${label}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};

export const DynamicRouting: React.FC = () => {
  const [graphData, setGraphData] = useState<NetworkGraphResponse | null>(null);
  const [activeTrip, setActiveTrip] = useState<ActiveTrip | null>(null);
  const [candidates, setCandidates] = useState<RouteCandidate[]>([]);
  const [latestEvent, setLatestEvent] = useState<ReroutingEvent | null>(null);
  const [benchmarkSummary, setBenchmarkSummary] = useState<RoutingExperimentSummary | null>(null);

  const [loading, setLoading] = useState(false);
  const [stepping, setStepping] = useState(false);
  const [rerouting, setRerouting] = useState(false);
  const [runningBenchmark, setRunningBenchmark] = useState(false);
  const [autoReroute, setAutoReroute] = useState(true);

  // Disruption Injection Form State
  const [disruptionType, setDisruptionType] = useState('ROAD_CLOSURE');
  const [targetEdgeSource, setTargetEdgeSource] = useState('COLLECTION_ZONE_B');
  const [targetEdgeTarget, setTargetEdgeTarget] = useState('COLLECTION_ZONE_C');
  const [severity, setSeverity] = useState(1.5);
  const [extraWasteKg, setExtraWasteKg] = useState(0);
  const [disruptionStatus, setDisruptionStatus] = useState<string | null>(null);

  // Initial Load: Fetch graph and active trip
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const graph = await api.getNetworkGraph();
      setGraphData(graph);

      // Check for existing trips or create a demo trip
      const trips = await api.listActiveTrips(1);
      if (trips && trips.length > 0) {
        setActiveTrip(trips[0]);
      } else {
        const newTrip = await api.createActiveTrip({
          vehicle_id: 'V-03',
          driver_id: 'EMP-001',
          origin_node: 'DEPOT_CENTRAL',
          destination_node: 'LANDFILL_MAIN',
          initial_stops: ['COLLECTION_ZONE_A', 'COLLECTION_ZONE_B', 'COLLECTION_ZONE_C'],
          vehicle_capacity_kg: 8000.0,
          initial_payload_kg: 1000.0,
          max_shift_hours: 4.0,
          notes: 'Live Municipal Route Session',
        });
        setActiveTrip(newTrip);
      }
    } catch (err) {
      console.error('Failed to load dynamic routing data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNewTrip = async () => {
    try {
      setLoading(true);
      const newTrip = await api.createActiveTrip({
        vehicle_id: 'V-08',
        driver_id: 'EMP-002',
        origin_node: 'DEPOT_CENTRAL',
        destination_node: 'LANDFILL_MAIN',
        initial_stops: ['COLLECTION_ZONE_A', 'COLLECTION_ZONE_B', 'COLLECTION_ZONE_C', 'COLLECTION_ZONE_D'],
        vehicle_capacity_kg: 8000.0,
        initial_payload_kg: 1200.0,
        max_shift_hours: 4.5,
        notes: 'Interactive Dynamic Rerouting Simulation',
      });
      setActiveTrip(newTrip);
      setCandidates([]);
      setLatestEvent(null);
      setDisruptionStatus(null);
    } catch (err) {
      console.error('Failed to create trip', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStepSimulation = async () => {
    if (!activeTrip) return;
    try {
      setStepping(true);
      const stepRes = await api.simulateStep(activeTrip.id, {
        step_duration_minutes: 10.0,
        auto_reroute_on_disruption: autoReroute,
      });
      setActiveTrip(stepRes.trip);
      if (stepRes.reroute_occurred && stepRes.reroute_event) {
        setLatestEvent(stepRes.reroute_event);
      }
    } catch (err) {
      console.error('Failed to step simulation', err);
    } finally {
      setStepping(false);
    }
  };

  const handleTriggerReroute = async (force: boolean = false) => {
    if (!activeTrip) return;
    try {
      setRerouting(true);
      const res = await api.executeReroute(activeTrip.id, {
        force_reroute: force,
      });
      setActiveTrip(res.trip);
      setCandidates(res.all_candidates);
      if (res.event) {
        setLatestEvent(res.event);
      }
    } catch (err) {
      console.error('Failed to execute reroute', err);
    } finally {
      setRerouting(false);
    }
  };

  const handleInjectDisruption = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeTrip) return;
    try {
      setLoading(true);
      await api.injectDisruption(activeTrip.id, {
        disruption_type: disruptionType,
        target_edge: [targetEdgeSource, targetEdgeTarget],
        severity: Number(severity),
        additional_waste_kg: Number(extraWasteKg),
        description: `Simulated ${disruptionType} on segment ${targetEdgeSource} -> ${targetEdgeTarget}`,
      });
      setDisruptionStatus(`Injected ${disruptionType} successfully.`);

      // Refresh trip & road graph
      const updatedGraph = await api.getNetworkGraph();
      setGraphData(updatedGraph);
      const updatedTrip = await api.getActiveTrip(activeTrip.id);
      setActiveTrip(updatedTrip);

      // Trigger automatic rerouting check
      if (autoReroute) {
        await handleTriggerReroute(false);
      }
    } catch (err) {
      console.error('Failed to inject disruption', err);
      setDisruptionStatus('Error injecting disruption.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunBenchmark = async () => {
    try {
      setRunningBenchmark(true);
      const summary = await api.runRoutingBenchmark();
      setBenchmarkSummary(summary);
    } catch (err) {
      console.error('Failed to run Phase 6 benchmark', err);
    } finally {
      setRunningBenchmark(false);
    }
  };

  // Coordinates of the current active trip path
  const currentPathCoords: [number, number][] = React.useMemo(() => {
    if (!activeTrip || !graphData) return [];
    const nodeMap = new Map(graphData.nodes.map((n) => [n.id, n]));
    return activeTrip.current_path
      .filter((nodeId) => nodeMap.has(nodeId))
      .map((nodeId) => {
        const node = nodeMap.get(nodeId)!;
        return [node.lat, node.lng];
      });
  }, [activeTrip, graphData]);

  // Payload utilization calculation
  const payloadPct = activeTrip
    ? Math.min(100, (activeTrip.current_payload_kg / activeTrip.vehicle_capacity_kg) * 100)
    : 0;

  // Fatigue shift calculation
  const shiftLimitMin = activeTrip ? activeTrip.max_shift_hours * 60 : 240;
  const shiftPct = activeTrip
    ? Math.min(100, (activeTrip.elapsed_time_minutes / shiftLimitMin) * 100)
    : 0;

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 p-6 rounded-2xl border border-indigo-500/20 shadow-xl">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2.5">
            <span className="px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-400/30">
              Dynamic Routing Active
            </span>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> Adaptive Hybrid ETA Enabled
            </span>
          </div>
          <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            <Compass className="w-8 h-8 text-indigo-400 animate-spin-slow" />
            Dynamic Real-Time Route Rerouting & Optimization
          </h1>
          <p className="text-sm text-slate-300 max-w-3xl">
            Simulates dynamic municipal collection trips under unexpected road closures, traffic spikes, and extreme weather.
            Candidate paths are evaluated against hard safety constraints and scored using Adaptive Hybrid ETA predictions.
          </p>
        </div>

        {/* Disclaimer Notice */}
        <div className="bg-slate-950/80 border border-amber-500/30 rounded-xl p-3.5 max-w-sm">
          <div className="flex items-start gap-2 text-amber-300 text-xs font-semibold mb-1">
            <Info className="w-4 h-4 shrink-0 text-amber-400 mt-0.5" />
            SIMULATION DISCLAIMER
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            This is a deterministic simulation and research prototype. It does not represent live municipal routing or live GPS data.
          </p>
        </div>
      </div>

      {/* Main Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/90 border border-slate-800 p-4 rounded-xl">
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={handleStepSimulation}
            disabled={stepping || !activeTrip || activeTrip.status === 'COMPLETED'}
            className="flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition shadow-md hover:shadow-emerald-600/30 disabled:opacity-50"
          >
            <Play className={`w-4 h-4 ${stepping ? 'animate-spin' : ''}`} />
            Step Simulation (Next Stop)
          </button>

          <button
            onClick={() => handleTriggerReroute(true)}
            disabled={rerouting || !activeTrip}
            className="flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition shadow-md hover:shadow-indigo-600/30 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${rerouting ? 'animate-spin' : ''}`} />
            Evaluate Candidates & Reroute
          </button>

          <button
            onClick={handleCreateNewTrip}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
          >
            <Sliders className="w-4 h-4 text-slate-400" />
            Reset / New Trip
          </button>
        </div>

        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-xs font-medium text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={autoReroute}
              onChange={(e) => setAutoReroute(e.target.checked)}
              className="w-4 h-4 rounded bg-slate-800 border-slate-700 text-indigo-600 focus:ring-indigo-500"
            />
            Auto-Reroute on Disruption
          </label>

          <button
            onClick={handleRunBenchmark}
            disabled={runningBenchmark}
            className="flex items-center gap-2 px-4 py-2 text-xs font-bold uppercase tracking-wider rounded-lg bg-amber-600 hover:bg-amber-500 text-white transition shadow-md hover:shadow-amber-600/30 disabled:opacity-50"
          >
            <Zap className={`w-3.5 h-3.5 ${runningBenchmark ? 'animate-bounce' : ''}`} />
            {runningBenchmark ? 'Running 35 Runs...' : 'Run Routing Benchmark Suite'}
          </button>
        </div>
      </div>

      {/* Grid: Map View (Left/Center) + Active Trip / Controls (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Road Network Map (Span 2) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Compass className="w-5 h-5 text-indigo-400" />
                <h2 className="text-base font-bold text-white">
                  Municipal Road Network Simulation Map
                </h2>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-400">
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block"></span> Depot
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-amber-500 inline-block"></span> Collection Zone
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-purple-500 inline-block"></span> Transfer Hub
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-rose-500 inline-block"></span> Landfill
                </span>
              </div>
            </div>

            {/* Map Container */}
            <div className="h-[460px] rounded-xl overflow-hidden border border-slate-800 bg-slate-950 relative">
              {graphData && (
                <MapContainer
                  center={[40.745, -73.985]}
                  zoom={12}
                  scrollWheelZoom={false}
                  style={{ height: '100%', width: '100%', backgroundColor: '#0f172a' }}
                >
                  <TileLayer
                    attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                  />

                  {/* Draw Road Network Edges */}
                  {graphData.edges.map((edge, idx) => {
                    const src = graphData.nodes.find((n) => n.id === edge.source);
                    const tgt = graphData.nodes.find((n) => n.id === edge.target);
                    if (!src || !tgt) return null;

                    const isBlocked = edge.is_blocked;
                    const isCongested = edge.congestion_factor > 1.5;
                    const color = isBlocked ? '#ef4444' : isCongested ? '#f97316' : '#334155';
                    const weight = isBlocked ? 4 : isCongested ? 3 : 2;
                    const dashArray = isBlocked ? '6, 6' : undefined;

                    return (
                      <Polyline
                        key={`edge-${idx}`}
                        positions={[
                          [src.lat, src.lng],
                          [tgt.lat, tgt.lng],
                        ]}
                        pathOptions={{
                          color,
                          weight,
                          dashArray,
                          opacity: 0.7,
                        }}
                      />
                    );
                  })}

                  {/* Draw Current Active Trip Path Polyline */}
                  {currentPathCoords.length > 1 && (
                    <Polyline
                      positions={currentPathCoords}
                      pathOptions={{
                        color: '#38bdf8',
                        weight: 5,
                        opacity: 0.9,
                        lineCap: 'round',
                      }}
                    />
                  )}

                  {/* Graph Node Markers */}
                  {graphData.nodes.map((node) => {
                    const isCurrent = activeTrip?.current_node === node.id;
                    return (
                      <Marker
                        key={node.id}
                        position={[node.lat, node.lng]}
                        icon={createNodeIcon(node.node_type, isCurrent)}
                      >
                        <Popup className="text-slate-900">
                          <div className="font-sans text-xs">
                            <p className="font-bold text-slate-800">{node.name}</p>
                            <p className="text-slate-600">ID: {node.id}</p>
                            <p className="text-slate-600">Type: {node.node_type}</p>
                            {isCurrent && (
                              <p className="mt-1 font-bold text-emerald-600 flex items-center gap-1">
                                <Activity className="w-3 h-3" /> Current Vehicle Location
                              </p>
                            )}
                          </div>
                        </Popup>
                      </Marker>
                    );
                  })}
                </MapContainer>
              )}
            </div>

            {/* Current Path Breadcrumbs */}
            {activeTrip && (
              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80 flex items-center gap-2 overflow-x-auto text-xs">
                <span className="font-bold text-slate-400 shrink-0">Current Route Path:</span>
                {activeTrip.current_path.map((node, idx) => {
                  const isPast = activeTrip.visited_nodes.includes(node);
                  const isCurrent = activeTrip.current_node === node;
                  return (
                    <React.Fragment key={`path-${idx}`}>
                      {idx > 0 && <ChevronRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />}
                      <span
                        className={`px-2 py-0.5 rounded-md font-medium shrink-0 ${
                          isCurrent
                            ? 'bg-sky-500/20 text-sky-300 border border-sky-400/40 ring-1 ring-sky-400'
                            : isPast
                            ? 'bg-slate-800 text-slate-400 line-through'
                            : 'bg-slate-800/60 text-slate-300'
                        }`}
                      >
                        {node}
                      </span>
                    </React.Fragment>
                  );
                })}
              </div>
            )}
          </div>

          {/* Candidate Routes Multi-Objective Scoring Table */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-lg">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sliders className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white">
                  Candidate Routes Evaluation & Safety Scoring
                </h3>
              </div>
              <span className="text-xs text-slate-400">
                Evaluated with Adaptive Hybrid ETA
              </span>
            </div>

            {candidates.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-sm">
                Click &quot;Evaluate Candidates &amp; Reroute&quot; to generate and score 5 candidate paths.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                      <th className="py-2.5 px-3">Strategy</th>
                      <th className="py-2.5 px-3">Distance</th>
                      <th className="py-2.5 px-3">Hybrid ETA</th>
                      <th className="py-2.5 px-3">Uncertainty</th>
                      <th className="py-2.5 px-3">Safety Status</th>
                      <th className="py-2.5 px-3">Score</th>
                      <th className="py-2.5 px-3">Decision</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {candidates.map((cand, idx) => (
                      <tr
                        key={`cand-${idx}`}
                        className={`transition ${
                          cand.is_selected ? 'bg-indigo-950/40 font-semibold' : 'hover:bg-slate-800/30'
                        }`}
                      >
                        <td className="py-2.5 px-3 font-mono text-slate-200">
                          {cand.strategy}
                        </td>
                        <td className="py-2.5 px-3 text-slate-300">
                          {cand.total_distance_km} km
                        </td>
                        <td className="py-2.5 px-3 text-emerald-400 font-medium">
                          {cand.hybrid_eta_minutes} min
                        </td>
                        <td className="py-2.5 px-3 text-slate-400">
                          &plusmn;{cand.eta_uncertainty_minutes} min
                        </td>
                        <td className="py-2.5 px-3">
                          {cand.safety_valid ? (
                            <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
                              <ShieldCheck className="w-3.5 h-3.5" /> Valid
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-rose-400 font-medium" title={cand.safety_violations?.join(', ')}>
                              <ShieldAlert className="w-3.5 h-3.5" /> Violations
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-300">
                          {cand.optimization_score > 9000 ? 'REJECTED' : cand.optimization_score.toFixed(4)}
                        </td>
                        <td className="py-2.5 px-3">
                          {cand.is_selected ? (
                            <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold text-[10px]">
                              SELECTED
                            </span>
                          ) : cand.rejection_reason ? (
                            <span className="text-slate-500 text-[10px] italic truncate max-w-[150px] inline-block">
                              {cand.rejection_reason}
                            </span>
                          ) : (
                            <span className="text-slate-500 text-[10px]">Alternate</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Active Trip State + Disruption Injection (Span 1) */}
        <div className="space-y-6">
          {/* Active Trip Telemetry Card */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-lg">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-emerald-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Active Trip Status
                </h3>
              </div>
              <span
                className={`px-2 py-0.5 text-xs font-bold rounded-full ${
                  activeTrip?.status === 'COMPLETED'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                }`}
              >
                {activeTrip?.status || 'INITIALIZING'}
              </span>
            </div>

            {activeTrip && (
              <div className="space-y-4 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                    <p className="text-slate-400">Vehicle / Driver</p>
                    <p className="font-bold text-white text-sm mt-0.5">
                      {activeTrip.vehicle_id} <span className="text-slate-400 font-normal">({activeTrip.driver_id})</span>
                    </p>
                  </div>
                  <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                    <p className="text-slate-400">Current Node</p>
                    <p className="font-bold text-sky-400 text-sm mt-0.5">
                      {activeTrip.current_node}
                    </p>
                  </div>
                </div>

                {/* Payload Capacity Progress */}
                <div className="space-y-1.5 bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <div className="flex justify-between">
                    <span className="text-slate-400 flex items-center gap-1">
                      <Weight className="w-3.5 h-3.5" /> Payload Capacity
                    </span>
                    <span className="font-bold text-white">
                      {activeTrip.current_payload_kg.toFixed(0)} / {activeTrip.vehicle_capacity_kg.toFixed(0)} kg ({payloadPct.toFixed(0)}%)
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        payloadPct > 90 ? 'bg-rose-500' : payloadPct > 75 ? 'bg-amber-500' : 'bg-emerald-500'
                      }`}
                      style={{ width: `${payloadPct}%` }}
                    ></div>
                  </div>
                </div>

                {/* Driver Shift Fatigue Progress */}
                <div className="space-y-1.5 bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <div className="flex justify-between">
                    <span className="text-slate-400 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" /> Driver Shift Time
                    </span>
                    <span className="font-bold text-white">
                      {activeTrip.elapsed_time_minutes.toFixed(1)} / {shiftLimitMin} min ({shiftPct.toFixed(0)}%)
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        shiftPct > 90 ? 'bg-rose-500' : shiftPct > 75 ? 'bg-amber-500' : 'bg-sky-500'
                      }`}
                      style={{ width: `${shiftPct}%` }}
                    ></div>
                  </div>
                </div>

                {/* ETA Metric Breakdown */}
                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                    <p className="text-slate-400">Hybrid ETA</p>
                    <p className="font-extrabold text-emerald-400 text-base mt-0.5">
                      {activeTrip.hybrid_eta_minutes.toFixed(1)} min
                    </p>
                    <p className="text-[10px] text-slate-500">&plusmn;{activeTrip.eta_uncertainty_minutes} min spread</p>
                  </div>
                  <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                    <p className="text-slate-400">Reroute Count</p>
                    <p className="font-extrabold text-indigo-300 text-base mt-0.5">
                      {activeTrip.reroute_count} events
                    </p>
                    <p className="text-[10px] text-slate-500">Autonomous triggers</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Disruption Injection Form */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-lg">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Inject Real-Time Disruption
              </h3>
            </div>

            <form onSubmit={handleInjectDisruption} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Disruption Vector</label>
                <select
                  value={disruptionType}
                  onChange={(e) => setDisruptionType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200"
                >
                  <option value="ROAD_CLOSURE">Emergency Road Closure</option>
                  <option value="TRAFFIC_SPIKE">Severe Traffic Congestion Spike</option>
                  <option value="HEAVY_RAIN">Extreme Rain & Flooding</option>
                  <option value="HIGH_WASTE">Unexpected High Waste Overflow</option>
                  <option value="EVENT_BLOCK">Civic Event Corridor Obstruction</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-400 mb-1">From Node</label>
                  <select
                    value={targetEdgeSource}
                    onChange={(e) => setTargetEdgeSource(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200"
                  >
                    {graphData?.nodes.map((n) => (
                      <option key={n.id} value={n.id}>
                        {n.id}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 mb-1">To Node</label>
                  <select
                    value={targetEdgeTarget}
                    onChange={(e) => setTargetEdgeTarget(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200"
                  >
                    {graphData?.nodes.map((n) => (
                      <option key={n.id} value={n.id}>
                        {n.id}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {disruptionType === 'HIGH_WASTE' ? (
                <div>
                  <label className="block text-slate-400 mb-1">Additional Waste (kg)</label>
                  <input
                    type="number"
                    value={extraWasteKg}
                    onChange={(e) => setExtraWasteKg(Number(e.target.value))}
                    min="500"
                    max="4000"
                    step="250"
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-slate-200"
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-slate-400 mb-1">Severity Factor: {severity}x</label>
                  <input
                    type="range"
                    value={severity}
                    onChange={(e) => setSeverity(Number(e.target.value))}
                    min="1.0"
                    max="4.0"
                    step="0.5"
                    className="w-full accent-amber-500 cursor-pointer"
                  />
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 font-bold uppercase tracking-wider rounded-lg bg-amber-600 hover:bg-amber-500 text-white transition shadow-md hover:shadow-amber-600/30 disabled:opacity-50 mt-2"
              >
                {loading ? 'Injecting...' : 'Inject Disruption Vector'}
              </button>

              {disruptionStatus && (
                <p className="text-[11px] text-amber-300 bg-amber-950/40 p-2 rounded-lg border border-amber-500/30">
                  {disruptionStatus}
                </p>
              )}
            </form>
          </div>

          {/* Latest Decision & Rationale Card */}
          {latestEvent && (
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-3 shadow-lg">
              <div className="flex items-center gap-2 text-emerald-400">
                <CheckCircle2 className="w-5 h-5" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Latest Rerouting Decision
                </h3>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/70 p-3 rounded-xl border border-slate-800">
                {latestEvent.decision_rationale}
              </p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-slate-950/60 p-2 rounded-lg">
                  <span className="text-slate-400">Time Saved:</span>{' '}
                  <span className="font-bold text-emerald-400">
                    {latestEvent.time_saved_minutes > 0 ? `+${latestEvent.time_saved_minutes} min` : '0 min'}
                  </span>
                </div>
                <div className="bg-slate-950/60 p-2 rounded-lg">
                  <span className="text-slate-400">Trigger:</span>{' '}
                  <span className="font-bold text-slate-200">{latestEvent.trigger_type}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Benchmark Summary Section (When benchmark has been run) */}
      {benchmarkSummary && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <TrendingDown className="w-5 h-5 text-emerald-400" />
                Empirical Routing Benchmark Results (35 Simulation Runs)
              </h2>
              <p className="text-xs text-slate-400">
                Evaluates 7 scenarios across 5 random seeds (42, 43, 44, 45, 46) comparing Static Baseline vs. Dynamic Rerouting Engine.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 font-bold text-xs rounded-full border border-emerald-500/30">
                Mean Time Saved: {benchmarkSummary.mean_time_saved_min} min ({benchmarkSummary.mean_pct_time_saved}%)
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <p className="text-xs text-slate-400">Total Runs</p>
              <p className="text-2xl font-extrabold text-white mt-1">{benchmarkSummary.total_runs}</p>
            </div>
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <p className="text-xs text-slate-400">Mean Time Saved</p>
              <p className="text-2xl font-extrabold text-emerald-400 mt-1">{benchmarkSummary.mean_time_saved_min} min</p>
            </div>
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <p className="text-xs text-slate-400">Static Safety Rate</p>
              <p className="text-2xl font-extrabold text-slate-300 mt-1">{benchmarkSummary.overall_safety_rate_static_pct}%</p>
            </div>
            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800">
              <p className="text-xs text-slate-400">Dynamic Safety Rate</p>
              <p className="text-2xl font-extrabold text-emerald-400 mt-1">{benchmarkSummary.overall_safety_rate_dynamic_pct}%</p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                  <th className="py-2.5 px-3">Scenario</th>
                  <th className="py-2.5 px-3">Static Time</th>
                  <th className="py-2.5 px-3">Dynamic Time</th>
                  <th className="py-2.5 px-3">Time Saved</th>
                  <th className="py-2.5 px-3">% Saved</th>
                  <th className="py-2.5 px-3">Dist Penalty</th>
                  <th className="py-2.5 px-3">Static Safety</th>
                  <th className="py-2.5 px-3">Dynamic Safety</th>
                  <th className="py-2.5 px-3">Violations Prevented</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {Object.entries(benchmarkSummary.scenario_breakdown).map(([scName, scData]) => (
                  <tr key={scName} className="hover:bg-slate-800/30">
                    <td className="py-2.5 px-3 font-mono text-slate-200">{scName}</td>
                    <td className="py-2.5 px-3 text-slate-400">{scData.mean_static_time_min} min</td>
                    <td className="py-2.5 px-3 text-emerald-400 font-medium">{scData.mean_dynamic_time_min} min</td>
                    <td className="py-2.5 px-3 font-bold text-emerald-300">{scData.mean_time_saved_min} min</td>
                    <td className="py-2.5 px-3 font-bold text-emerald-400">{scData.mean_pct_time_saved}%</td>
                    <td className="py-2.5 px-3 text-slate-400">{scData.mean_distance_penalty_km > 0 ? `+${scData.mean_distance_penalty_km} km` : `${scData.mean_distance_penalty_km} km`}</td>
                    <td className="py-2.5 px-3 text-slate-400">{scData.static_safety_rate_pct}%</td>
                    <td className="py-2.5 px-3 font-bold text-emerald-400">{scData.dynamic_safety_rate_pct}%</td>
                    <td className="py-2.5 px-3 text-sky-400 font-bold">{scData.total_violations_prevented}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
