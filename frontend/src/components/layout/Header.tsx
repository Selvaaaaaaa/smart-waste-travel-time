import React, { useState, useEffect } from 'react';
import { Menu, Clock, Bell, Settings, User, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { DemoBadge } from '../common/DemoBadge';

interface HeaderProps {
  onMenuToggle?: () => void;
  title?: string;
  subtitle?: string;
}

export const Header: React.FC<HeaderProps> = ({
  onMenuToggle,
  title = 'SMART CITY WASTE OPERATIONS',
  subtitle = 'Intelligent Waste Collection & Fleet Management Platform',
}) => {
  const [currentDateTime, setCurrentDateTime] = useState<string>('');
  const [userRole, setUserRole] = useState<'Dispatcher' | 'Driver' | 'Municipal Supervisor'>('Dispatcher');
  const [isRoleDropdownOpen, setIsRoleDropdownOpen] = useState<boolean>(false);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setCurrentDateTime(
        now.toLocaleString('en-US', {
          weekday: 'short',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false,
        })
      );
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="sticky top-0 z-30 bg-slate-900/95 backdrop-blur-md border-b border-slate-800/90 px-4 lg:px-8 py-3 flex items-center justify-between gap-4">
      {/* Left side: Hamburger button + Platform Branding */}
      <div className="flex items-center gap-3.5">
        <button
          onClick={onMenuToggle}
          className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 lg:hidden border border-slate-700"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base sm:text-lg font-black text-white tracking-tight leading-none uppercase">
              {title}
            </h2>
            <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              SYSTEM OPERATIONAL
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 hidden sm:block font-medium">
            {subtitle}
          </p>
        </div>
      </div>

      {/* Right side: Operations Mode, Live Clock, Notifications, Role Switcher */}
      <div className="flex items-center gap-3">
        {/* Simulation Environment Disclaimer Badge */}
        <DemoBadge label="Operations Mode: Simulation" className="hidden sm:inline-flex text-[11px]" />

        {/* Live Date / Time Clock */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-slate-800/80 border border-slate-700/80 rounded-lg text-xs font-mono text-slate-300">
          <Clock className="w-3.5 h-3.5 text-emerald-400" />
          <span>{currentDateTime}</span>
        </div>

        {/* Safety Constraints Active Badge */}
        <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1.5 bg-emerald-950/40 border border-emerald-800/50 rounded-lg text-xs font-medium text-emerald-300">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Safety Active</span>
        </div>

        {/* Notifications Icon with Badge */}
        <button
          className="relative p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/80 transition-colors"
          title="Live Operational Alerts"
          aria-label="Alerts"
        >
          <Bell className="w-4 h-4 text-slate-300" />
          <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-amber-500 text-slate-950 text-[10px] font-bold flex items-center justify-center">
            2
          </span>
        </button>

        {/* User Profile & Role Selector */}
        <div className="relative">
          <button
            onClick={() => setIsRoleDropdownOpen(!isRoleDropdownOpen)}
            className="flex items-center gap-2 px-2.5 py-1.5 bg-slate-800/90 hover:bg-slate-700 border border-slate-700 rounded-lg text-xs transition-colors"
            title="Switch Operational Role"
          >
            <div className="w-6 h-6 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold text-[11px]">
              <User className="w-3.5 h-3.5" />
            </div>
            <div className="hidden sm:block text-left">
              <span className="block text-[11px] font-semibold text-white leading-tight">
                {userRole}
              </span>
              <span className="block text-[9px] text-slate-400 uppercase tracking-wider">
                Municipal Control
              </span>
            </div>
          </button>

          {isRoleDropdownOpen && (
            <div className="absolute right-0 mt-2 w-48 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl py-1.5 z-50">
              <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                Switch Role Profile
              </div>
              {(['Dispatcher', 'Driver', 'Municipal Supervisor'] as const).map((role) => (
                <button
                  key={role}
                  onClick={() => {
                    setUserRole(role);
                    setIsRoleDropdownOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-800 transition-colors ${
                    userRole === role ? 'text-emerald-400 font-bold bg-slate-800/50' : 'text-slate-300'
                  }`}
                >
                  <span>{role}</span>
                  {userRole === role && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Settings Button */}
        <button
          className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
          title="Platform Settings"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};

export default Header;
