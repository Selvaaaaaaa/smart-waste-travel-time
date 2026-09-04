import React from 'react';
import { Menu, Clock, Server, ShieldCheck } from 'lucide-react';
import { DemoBadge } from '../common/DemoBadge';

interface HeaderProps {
  onMenuToggle?: () => void;
  title?: string;
  subtitle?: string;
}

export const Header: React.FC<HeaderProps> = ({
  onMenuToggle,
  title = 'Operations Control Center',
  subtitle = 'Context-Aware Logistics Telemetry & Travel-Time Analysis',
}) => {
  const [currentTime, setCurrentTime] = React.useState<string>(() =>
    new Date().toLocaleTimeString('en-US', { hour12: false })
  );

  React.useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString('en-US', { hour12: false }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="sticky top-0 z-30 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 lg:px-8 py-3.5 flex items-center justify-between gap-4">
      {/* Left side: Hamburger button + Page Titles */}
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 lg:hidden border border-slate-700"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-base sm:text-lg font-bold text-white tracking-tight leading-none">
            {title}
          </h2>
          <p className="text-xs text-slate-400 mt-1 hidden sm:block">{subtitle}</p>
        </div>
      </div>

      {/* Right side: Operational Badges & Live Clock */}
      <div className="flex items-center gap-3">
        <DemoBadge label="Demo Data — Phase 1" className="hidden sm:inline-flex" />

        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-slate-800/80 border border-slate-700/80 rounded-lg text-xs font-mono text-slate-300">
          <Clock className="w-3.5 h-3.5 text-emerald-400" />
          <span>{currentTime} UTC</span>
        </div>

        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-emerald-950/40 border border-emerald-800/50 rounded-lg text-xs font-medium text-emerald-300">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Constraints Active</span>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs font-mono text-slate-400">
          <Server className="w-3.5 h-3.5 text-cyan-400" />
          <span className="hidden sm:inline">API:</span>
          <span className="text-emerald-400 font-semibold">ONLINE</span>
        </div>
      </div>
    </header>
  );
};
