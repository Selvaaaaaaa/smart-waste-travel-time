import React from 'react';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = status.toLowerCase();

  let styles = 'bg-slate-800 text-slate-300 border-slate-700';

  if (
    normalized === 'on schedule' ||
    normalized === 'within limits' ||
    normalized === 'normal' ||
    normalized === 'clear' ||
    normalized === 'low' ||
    normalized === 'none' ||
    normalized === 'system online' ||
    normalized === 'completed (demo)'
  ) {
    styles = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
  } else if (
    normalized === 'moderate' ||
    normalized === 'medium' ||
    normalized === 'at risk' ||
    normalized === 'light rain' ||
    normalized === 'small event' ||
    normalized === 'partial closure' ||
    normalized === 'pending ml phase'
  ) {
    styles = 'bg-amber-500/10 text-amber-400 border-amber-500/30';
  } else if (
    normalized === 'delayed' ||
    normalized === 'high' ||
    normalized === 'extreme' ||
    normalized === 'heavy rain' ||
    normalized === 'major event' ||
    normalized === 'full closure' ||
    normalized === 'exceeded'
  ) {
    styles = 'bg-rose-500/10 text-rose-400 border-rose-500/30';
  }

  const sizeStyles = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-semibold';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border font-medium uppercase tracking-wider ${styles} ${sizeStyles}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80 animate-pulse" />
      {status}
    </span>
  );
};
