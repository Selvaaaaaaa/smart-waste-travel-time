import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { DemoBadge } from '../common/DemoBadge';
import { VehicleUtilizationItem } from '../../types';
import { Truck, Shield } from 'lucide-react';

interface VehicleUtilizationChartProps {
  data?: VehicleUtilizationItem[];
}

const DEFAULT_DATA: VehicleUtilizationItem[] = [
  { vehicle_id: 'V001', utilization_pct: 82.0, capacity_tons: 10.0, current_load_tons: 8.2 },
  { vehicle_id: 'V002', utilization_pct: 65.0, capacity_tons: 10.0, current_load_tons: 6.5 },
  { vehicle_id: 'V003', utilization_pct: 91.0, capacity_tons: 12.0, current_load_tons: 10.9 },
  { vehicle_id: 'V004', utilization_pct: 45.0, capacity_tons: 8.0, current_load_tons: 3.6 },
  { vehicle_id: 'V005', utilization_pct: 78.0, capacity_tons: 10.0, current_load_tons: 7.8 },
];

export const VehicleUtilizationChart: React.FC<VehicleUtilizationChartProps> = ({
  data = DEFAULT_DATA,
}) => {
  const getBarColor = (pct: number) => {
    if (pct > 90) return '#f59e0b'; // Amber approaching limit
    if (pct > 75) return '#10b981'; // Optimal
    return '#3b82f6'; // Under capacity
  };

  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-slate-700/50 text-emerald-400 border border-slate-600/40">
            <Truck className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">
              Vehicle Capacity Utilization
            </h3>
            <p className="text-xs text-slate-400">Current load relative to rated tonnage (%)</p>
          </div>
        </div>
        <DemoBadge label="Demo Metrics — Phase 1" />
      </div>

      <div className="h-64 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis
              dataKey="vehicle_id"
              stroke="#94a3b8"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#94a3b8"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              unit="%"
              domain={[0, 100]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '8px',
                color: '#f8fafc',
                fontSize: '12px',
              }}
              formatter={(val: number, _: string, item: any) => [
                `${val}% (${item.payload.current_load_tons} / ${item.payload.capacity_tons} tons)`,
                'Capacity Load',
              ]}
            />
            <Bar dataKey="utilization_pct" radius={[4, 4, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.utilization_pct)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center gap-1.5 p-2.5 rounded-lg bg-slate-900/60 border border-slate-700/50 text-[11px] text-slate-400">
        <Shield className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
        <span>Safety limits and vehicle capacity constraints will be strictly enforced in later phases.</span>
      </div>
    </div>
  );
};
