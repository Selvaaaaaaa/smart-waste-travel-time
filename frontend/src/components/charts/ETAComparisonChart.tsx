import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { DemoBadge } from '../common/DemoBadge';
import { ETAComparisonItem } from '../../types';
import { Timer, Info } from 'lucide-react';

interface ETAComparisonChartProps {
  data?: ETAComparisonItem[];
}

const DEFAULT_DATA: ETAComparisonItem[] = [
  { route_id: 'Route R001', baseline_eta_min: 45, context_eta_min: 52, actual_eta_min: 54 },
  { route_id: 'Route R002', baseline_eta_min: 38, context_eta_min: 41, actual_eta_min: 40 },
  { route_id: 'Route R003', baseline_eta_min: 55, context_eta_min: 68, actual_eta_min: 71 },
  { route_id: 'Route R004', baseline_eta_min: 30, context_eta_min: 32, actual_eta_min: 31 },
  { route_id: 'Route R005', baseline_eta_min: 50, context_eta_min: 61, actual_eta_min: 63 },
];

export const ETAComparisonChart: React.FC<ETAComparisonChartProps> = ({
  data = DEFAULT_DATA,
}) => {
  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-slate-700/50 text-cyan-400 border border-slate-600/40">
            <Timer className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">
              ETA Comparison by Route
            </h3>
            <p className="text-xs text-slate-400">Baseline vs. Context-Aware vs. Actual (minutes)</p>
          </div>
        </div>
        <DemoBadge label="Operations Mode: Simulation" />
      </div>

      <div className="h-72 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis
              dataKey="route_id"
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              axisLine={false}
              unit=" m"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '8px',
                color: '#f8fafc',
                fontSize: '12px',
              }}
              formatter={(val: number, name: string) => [`${val} min`, name]}
            />
            <Legend
              wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }}
            />
            <Bar
              dataKey="baseline_eta_min"
              name="Baseline ETA"
              fill="#64748b"
              radius={[3, 3, 0, 0]}
            />
            <Bar
              dataKey="context_eta_min"
              name="Context-aware ETA"
              fill="#06b6d4"
              radius={[3, 3, 0, 0]}
            />
            <Bar
              dataKey="actual_eta_min"
              name="Actual ETA"
              fill="#10b981"
              radius={[3, 3, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center gap-1.5 p-2.5 rounded-lg bg-slate-900/60 border border-slate-700/50 text-[11px] text-slate-400">
        <Info className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
        <span>
          Comparative evaluation between static baseline estimates, context-aware regression, and ground truth telemetry.
        </span>
      </div>
    </div>
  );
};
