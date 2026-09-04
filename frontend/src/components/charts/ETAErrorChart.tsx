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
import { ETAErrorItem } from '../../types';
import { AlertCircle } from 'lucide-react';

interface ETAErrorChartProps {
  data?: ETAErrorItem[];
}

const DEFAULT_DATA: ETAErrorItem[] = [
  { route_id: 'R001', baseline_error_min: 9.0, context_error_min: 2.0 },
  { route_id: 'R002', baseline_error_min: 2.0, context_error_min: 1.0 },
  { route_id: 'R003', baseline_error_min: 16.0, context_error_min: 3.0 },
  { route_id: 'R004', baseline_error_min: 1.0, context_error_min: 1.0 },
  { route_id: 'R005', baseline_error_min: 13.0, context_error_min: 2.0 },
];

export const ETAErrorChart: React.FC<ETAErrorChartProps> = ({
  data = DEFAULT_DATA,
}) => {
  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-slate-700/50 text-rose-400 border border-slate-600/40">
            <AlertCircle className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">
              ETA Error by Route
            </h3>
            <p className="text-xs text-slate-400">Absolute prediction deviation |Predicted - Actual| (min)</p>
          </div>
        </div>
        <DemoBadge label="Demo Metrics — Phase 1" />
      </div>

      <div className="h-64 w-full pt-2">
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
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
            <Bar
              dataKey="baseline_error_min"
              name="Baseline Error"
              fill="#f43f5e"
              radius={[3, 3, 0, 0]}
            />
            <Bar
              dataKey="context_error_min"
              name="Context-aware Error"
              fill="#10b981"
              radius={[3, 3, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="text-[11px] text-slate-400 flex items-center justify-between pt-1 border-t border-slate-700/50">
        <span>Baseline Mean Error: 8.2 min</span>
        <span className="text-emerald-400 font-medium">Context Mean Error: 1.8 min (Demo)</span>
      </div>
    </div>
  );
};
