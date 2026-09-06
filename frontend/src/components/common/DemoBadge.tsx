import React from 'react';
import { Radio } from 'lucide-react';

interface DemoBadgeProps {
  label?: string;
  className?: string;
}

export const DemoBadge: React.FC<DemoBadgeProps> = ({
  label = 'Operations Mode: Simulation',
  className = '',
}) => {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 tracking-wide ${className}`}
      title="Environment running in simulated municipal operations mode"
    >
      <Radio className="w-3 h-3 text-emerald-400 animate-pulse" />
      {label}
    </span>
  );
};

export default DemoBadge;
