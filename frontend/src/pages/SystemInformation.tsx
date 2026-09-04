import React from 'react';
import {
  Info,
  ShieldAlert,
  Layers,
  Cpu,
  CheckCircle2,
  Database,
  Code2,
  GitBranch,
} from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';

export const SystemInformation: React.FC = () => {
  return (
    <div className="space-y-8 max-w-5xl">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-black text-white tracking-tight flex items-center gap-2.5">
            <Info className="w-6 h-6 text-emerald-400" />
            System Information & Research Architecture
          </h1>
          <p className="text-sm text-slate-400 mt-0.5">
            Academic specifications, mathematical definitions, and physical safety constraints.
          </p>
        </div>
        <StatusBadge status="SYSTEM ONLINE" />
      </div>

      {/* Project Status Banner */}
      <div className="bg-emerald-950/40 border border-emerald-800/60 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <span className="font-bold text-emerald-300 text-sm">
              PROJECT STATUS: Phase 2 — Database & Operational Data Complete
            </span>
          </div>
          <p className="text-xs text-emerald-200/80">
            PostgreSQL 16 relational database with 14 domain entities, Alembic migrations, realistic seeded datasets, safety validation routines, and database-backed telemetry completed.
          </p>
        </div>
        <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-lg text-xs font-mono font-bold shrink-0 text-center">
          Phase 2 Active
        </span>
      </div>

      {/* Problem & Objective Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2 text-white font-bold text-sm">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <span>PROJECT PROBLEM</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Municipal waste collection operates across highly dynamic urban environments subject to stochastic waste generation volumes. Static or distance-only travel-time estimations systematically fail during adverse meteorological conditions, unexpected peak traffic, public street events, and seasonal waste volume surges, causing fleet delays, overtime fatigue, and missed collection windows.
          </p>
        </div>

        <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2 text-white font-bold text-sm">
            <Layers className="w-4 h-4 text-cyan-400" />
            <span>PROJECT OBJECTIVE</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Develop, calibrate, and validate a <strong>context-aware travel-time prediction platform</strong>. The system models complex interactions among weather, live traffic indices, urban road closures, and bin load volumes to deliver robust Estimated Times of Arrival (ETAs) and prevent compounding logistical disruptions.
          </p>
        </div>
      </div>

      {/* Context Variables & Model Strategy */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">
          Context Feature Variables & Modeling Strategy
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5">
          {[
            { label: 'Weather', desc: 'Precipitation, visibility, road traction' },
            { label: 'Traffic', desc: 'Arterial speed & congestion index' },
            { label: 'Events', desc: 'Festivals, sports & public gatherings' },
            { label: 'Road Restrictions', desc: 'Lane closures & construction' },
            { label: 'Waste Volume', desc: 'Bin density & loading dwell-time' },
            { label: 'Time of Day', desc: 'Peak commuter hours vs off-peak' },
            { label: 'Day of Week', desc: 'Commercial vs residential cycles' },
          ].map((v) => (
            <div
              key={v.label}
              className="p-3 bg-slate-900/70 border border-slate-700/60 rounded-lg text-center space-y-1"
            >
              <div className="text-xs font-bold text-emerald-400">{v.label}</div>
              <div className="text-[10px] text-slate-400 leading-tight">{v.desc}</div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <div className="p-4 bg-slate-900/60 border border-slate-700/50 rounded-lg space-y-1.5">
            <span className="text-xs font-bold text-slate-300 block">Baseline Model (Phase 2/3)</span>
            <p className="text-xs text-slate-400 leading-relaxed">
              Simple historical route average and static speed-distance formula (e.g. constant 25 km/h + fixed stop dwell). Serves as the benchmark comparator to quantify predictive gains.
            </p>
          </div>
          <div className="p-4 bg-slate-900/60 border border-slate-700/50 rounded-lg space-y-1.5">
            <span className="text-xs font-bold text-cyan-300 block">Context-Aware ML Model (Phase 3)</span>
            <p className="text-xs text-slate-400 leading-relaxed">
              Supervised gradient-boosted / ensemble regression model trained on feature vectors incorporating dynamic environmental shocks and volume multipliers to compute precise leg ETAs.
            </p>
          </div>
        </div>
      </div>

      {/* Safety & Physical Constraints */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2 text-white font-bold text-sm">
          <ShieldAlert className="w-4 h-4 text-rose-400" />
          <span>SAFETY CONSTRAINTS & OPERATIONAL BOUNDS</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div className="p-3.5 bg-slate-900/60 border border-slate-700/60 rounded-lg space-y-1">
            <div className="text-xs font-bold text-slate-200">Vehicle Gross Capacity</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Hard physical payload upper-bounds (e.g. 10.0 tons max). Overloading is strictly prohibited regardless of route efficiency incentive.
            </p>
          </div>
          <div className="p-3.5 bg-slate-900/60 border border-slate-700/60 rounded-lg space-y-1">
            <div className="text-xs font-bold text-slate-200">Driver & Worker Workload</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Mandatory maximum consecutive shift hours and required rest periods to eliminate fatigue and hazardous operating conditions.
            </p>
          </div>
          <div className="p-3.5 bg-slate-900/60 border border-slate-700/60 rounded-lg space-y-1">
            <div className="text-xs font-bold text-slate-200">Time-Window Constraints</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Municipal noise ordinances and commercial access windows strictly constrain earliest and latest allowable collection intervals.
            </p>
          </div>
          <div className="p-3.5 bg-slate-900/60 border border-slate-700/60 rounded-lg space-y-1">
            <div className="text-xs font-bold text-slate-200">Safe Route Assignment</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Strict prohibition of sharp turning or narrow residential access for heavy tonnage class vehicles.
            </p>
          </div>
          <div className="p-3.5 bg-slate-900/60 border border-slate-700/60 rounded-lg space-y-1 sm:col-span-2">
            <div className="text-xs font-bold text-amber-300">No Efficiency via Safety Violation</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Under no circumstance will an algorithm propose travel-time optimizations that compromise worker safety, speed limits, or vehicle payload boundaries.
            </p>
          </div>
        </div>
      </div>

      {/* Evaluation Metrics */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 space-y-3">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">
          Evaluation Metrics Framework
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="p-3 bg-slate-900/60 border border-slate-700/60 rounded-lg">
            <span className="text-xs font-bold text-emerald-400 block font-mono">MAE</span>
            <span className="text-[11px] text-slate-400">Mean Absolute Error in travel minutes across all active legs.</span>
          </div>
          <div className="p-3 bg-slate-900/60 border border-slate-700/60 rounded-lg">
            <span className="text-xs font-bold text-cyan-400 block font-mono">RMSE</span>
            <span className="text-[11px] text-slate-400">Root Mean Squared Error penalizing large unforeseen delay spikes.</span>
          </div>
          <div className="p-3 bg-slate-900/60 border border-slate-700/60 rounded-lg">
            <span className="text-xs font-bold text-indigo-400 block font-mono">ETA Error Distribution</span>
            <span className="text-[11px] text-slate-400">Quantiles (p50, p90, p99) of estimation residual variances.</span>
          </div>
          <div className="p-3 bg-slate-900/60 border border-slate-700/60 rounded-lg">
            <span className="text-xs font-bold text-amber-400 block font-mono">Improvement (%)</span>
            <span className="text-[11px] text-slate-400">Relative accuracy improvement: (MAE_base - MAE_context) / MAE_base.</span>
          </div>
        </div>
      </div>

      {/* Technology Stack Grid */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">
          Complete Technology Stack
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-3.5 bg-slate-900/70 border border-slate-700/60 rounded-lg space-y-2">
            <div className="flex items-center gap-1.5 font-bold text-emerald-400">
              <Code2 className="w-4 h-4" />
              <span>Frontend Layer</span>
            </div>
            <ul className="text-slate-300 space-y-1 text-[11px]">
              <li>• React 18 + Vite</li>
              <li>• TypeScript Strict Mode</li>
              <li>• Tailwind CSS & Custom Theme</li>
              <li>• React Router v6</li>
              <li>• Recharts Data Visualizations</li>
              <li>• Leaflet & OpenStreetMap</li>
            </ul>
          </div>

          <div className="p-3.5 bg-slate-900/70 border border-slate-700/60 rounded-lg space-y-2">
            <div className="flex items-center gap-1.5 font-bold text-cyan-400">
              <Cpu className="w-4 h-4" />
              <span>Backend Layer</span>
            </div>
            <ul className="text-slate-300 space-y-1 text-[11px]">
              <li>• Python 3.13 / 3.11</li>
              <li>• FastAPI Framework</li>
              <li>• Pydantic v2 Type Schemas</li>
              <li>• Pandas & NumPy</li>
              <li>• scikit-learn (Prepared)</li>
              <li>• Uvicorn ASGI Server</li>
            </ul>
          </div>

          <div className="p-3.5 bg-slate-900/70 border border-slate-700/60 rounded-lg space-y-2">
            <div className="flex items-center gap-1.5 font-bold text-indigo-400">
              <Database className="w-4 h-4" />
              <span>Database Layer</span>
            </div>
            <ul className="text-slate-300 space-y-1 text-[11px]">
              <li>• PostgreSQL 16 Alpine</li>
              <li>• SQLAlchemy 2.0 ORM</li>
              <li>• Async & Synced Sessions</li>
              <li>• Docker Containerization</li>
              <li>• Relational Schema (Phase 2)</li>
            </ul>
          </div>

          <div className="p-3.5 bg-slate-900/70 border border-slate-700/60 rounded-lg space-y-2">
            <div className="flex items-center gap-1.5 font-bold text-amber-400">
              <GitBranch className="w-4 h-4" />
              <span>Testing & DevOps</span>
            </div>
            <ul className="text-slate-300 space-y-1 text-[11px]">
              <li>• pytest & pytest-asyncio</li>
              <li>• httpx TestClient</li>
              <li>• Vitest & React Testing Library</li>
              <li>• Docker & Docker Compose</li>
              <li>• Git Version Control</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
