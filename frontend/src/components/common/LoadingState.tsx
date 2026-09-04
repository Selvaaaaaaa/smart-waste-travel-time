import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  subMessage?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading operational telemetry...',
  subMessage = 'Connecting to Smart Waste API service',
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 min-h-[300px] text-center">
      <div className="relative mb-4">
        <div className="w-12 h-12 rounded-full border-2 border-emerald-500/20 border-t-emerald-500 animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center">
          <Loader2 className="w-5 h-5 text-emerald-400 animate-pulse" />
        </div>
      </div>
      <h3 className="text-base font-medium text-slate-200">{message}</h3>
      <p className="text-xs text-slate-400 mt-1 max-w-sm">{subMessage}</p>
    </div>
  );
};
