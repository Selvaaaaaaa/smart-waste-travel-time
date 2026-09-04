import React from 'react';
import { Tag } from 'lucide-react';

interface DemoBadgeProps {
  label?: string;
  className?: string;
}

export const DemoBadge: React.FC<DemoBadgeProps> = ({
  label = 'Demo Data — Phase 1',
  className = '',
}) => {
  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 tracking-wide ${className}`}
      title="Synthetic research placeholder for Phase 1"
    >
      <Tag className="w-3 h-3 text-amber-400" />
      {label}
    </span>
  );
};
