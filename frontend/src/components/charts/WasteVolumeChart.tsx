import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { DemoBadge } from '../common/DemoBadge';
import { WasteVolumeTrend } from '../../types';
import { Trash2 } from 'lucide-react';

interface WasteVolumeChartProps {
  data?: WasteVolumeTrend[];
}

const DEFAULT_DATA: WasteVolumeTrend[] = [
  { day: 'Mon', volume_tons: 7.8 },
  { day: 'Tue', volume_tons: 8.2 },
  { day: 'Wed', volume_tons: 8.9 },
  { day: 'Thu', volume_tons: 8.4 },
  { day: 'Fri', volume_tons: 9.6 },
  { day: 'Sat', volume_tons: 6.5 },
  { day: 'Sun', volume_tons: 5.1 },
];

export const WasteVolumeChart: React.FC<WasteVolumeChartProps> = ({
  data = DEFAULT_DATA,
}) => {
  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-slate-700/50 text-emerald-400 border border-slate-600/40">
            <Trash2 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">
              Waste Volume by Day
            </h3>
            <p className="text-xs text-slate-400">Weekly accumulation trend (metric tons)</p>
          </div>
        </div>
        <DemoBadge label="Demo Data — Phase 1" />
      </div>

      <div className="h-64 w-full pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis
              dataKey="day"
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
              unit=" t"
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '8px',
                color: '#f8fafc',
                fontSize: '12px',
              }}
              formatter={(val: number) => [`${val} tons`, 'Waste Volume']}
            />
            <Bar
              dataKey="volume_tons"
              name="Waste Volume"
              fill="#10b981"
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="text-[11px] text-slate-400 flex items-center justify-between pt-1 border-t border-slate-700/50">
        <span>Average Daily: 7.79 tons</span>
        <span>Peak Collection: Friday</span>
      </div>
    </div>
  );
};
