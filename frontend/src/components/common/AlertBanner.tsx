import React from 'react';
import { Info, AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';

interface AlertBannerProps {
  type?: 'info' | 'warning' | 'success' | 'error';
  title?: string;
  message: string;
  className?: string;
}

export const AlertBanner: React.FC<AlertBannerProps> = ({
  type = 'info',
  title,
  message,
  className = '',
}) => {
  const configs = {
    info: {
      bg: 'bg-cyan-950/40 border-cyan-800/60 text-cyan-200',
      icon: <Info className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />,
      titleColor: 'text-cyan-300',
    },
    warning: {
      bg: 'bg-amber-950/40 border-amber-800/60 text-amber-200',
      icon: <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />,
      titleColor: 'text-amber-300',
    },
    success: {
      bg: 'bg-emerald-950/40 border-emerald-800/60 text-emerald-200',
      icon: <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />,
      titleColor: 'text-emerald-300',
    },
    error: {
      bg: 'bg-rose-950/40 border-rose-800/60 text-rose-200',
      icon: <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />,
      titleColor: 'text-rose-300',
    },
  };

  const config = configs[type];

  return (
    <div className={`flex gap-3 p-4 rounded-xl border ${config.bg} ${className}`}>
      {config.icon}
      <div className="text-sm">
        {title && <h4 className={`font-semibold mb-0.5 ${config.titleColor}`}>{title}</h4>}
        <p className="leading-relaxed opacity-90">{message}</p>
      </div>
    </div>
  );
};
