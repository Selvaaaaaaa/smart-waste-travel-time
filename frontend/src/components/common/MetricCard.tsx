import React from 'react';
import { DemoBadge } from './DemoBadge';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  icon: React.ReactNode;
  subtitle?: string;
  badgeLabel?: string;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  icon,
  subtitle,
  badgeLabel = 'Operations Mode: Simulation',
  trend,
}) => {
  return (
    <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 shadow-sm hover:border-slate-600/80 transition-all duration-200">
      <div className="flex items-center justify-between gap-3 mb-3">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          {title}
        </span>
        <div className="p-2 rounded-lg bg-slate-700/50 text-emerald-400 border border-slate-600/40">
          {icon}
        </div>
      </div>

      <div className="flex items-baseline gap-2 mb-2">
        <span className="text-2xl sm:text-3xl font-bold tracking-tight text-white font-mono">
          {value}
        </span>
        {unit && <span className="text-sm font-medium text-slate-400">{unit}</span>}
      </div>

      {subtitle && <p className="text-xs text-slate-400 mb-3">{subtitle}</p>}

      <div className="flex items-center justify-between pt-2 border-t border-slate-700/50 mt-3">
        <DemoBadge label={badgeLabel} className="text-[10px] px-2 py-0.5" />
        {trend && (
          <span
            className={`text-xs font-medium ${
              trend.isPositive ? 'text-emerald-400' : 'text-rose-400'
            }`}
          >
            {trend.value}
          </span>
        )}
      </div>
    </div>
  );
};
