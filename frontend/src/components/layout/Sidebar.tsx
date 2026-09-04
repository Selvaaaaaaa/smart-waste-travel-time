import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Sliders,
  Route as RouteIcon,
  Compass,
  BarChart3,
  FlaskConical,
  Info,
  Truck,
  Activity,
} from 'lucide-react';

import { StatusBadge } from '../common/StatusBadge';

interface NavItem {
  name: string;
  path: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  {
    name: 'Dashboard',
    path: '/dashboard',
    icon: <LayoutDashboard className="w-4 h-4" />,
  },
  {
    name: 'Scenario Simulator',
    path: '/scenarios',
    icon: <Sliders className="w-4 h-4" />,
  },
  {
    name: 'Routes',
    path: '/routes',
    icon: <RouteIcon className="w-4 h-4" />,
  },
  {
    name: 'Dynamic Routing (Phase 6)',
    path: '/dynamic-routing',
    icon: <Compass className="w-4 h-4" />,
  },
  {
    name: 'ETA Analysis',
    path: '/eta-analysis',
    icon: <BarChart3 className="w-4 h-4" />,
  },
  {
    name: 'Experiments',
    path: '/experiments',
    icon: <FlaskConical className="w-4 h-4" />,
  },
  {
    name: 'System Information',
    path: '/system-information',
    icon: <Info className="w-4 h-4" />,
  },
];


interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  return (
    <>
      {/* Mobile overlay backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-slate-950/95 border-r border-slate-800 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Truck className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-sm font-black tracking-wider text-white flex items-center gap-1.5 font-mono">
                SMART WASTE
              </h1>
              <p className="text-[11px] text-slate-400 font-medium tracking-tight">
                Travel-Time Simulator
              </p>
            </div>
          </div>
        </div>

        {/* System Online Status Badge */}
        <div className="px-5 py-3 border-b border-slate-800/50 bg-slate-900/40 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Network Status
            </span>
          </div>
          <StatusBadge status="SYSTEM ONLINE" size="sm" />
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Navigation Menu
          </div>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-semibold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                }`
              }
            >
              {item.icon}
              <span>{item.name}</span>
            </NavLink>
          ))}
        </nav>

        {/* Bottom Phase Badge */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/60">
          <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
            <span className="font-medium">Environment</span>
            <span className="font-mono text-emerald-400">Phase 1</span>
          </div>
          <p className="text-[10px] text-slate-400 leading-tight">
            Research & Operational Baseline Dashboard
          </p>
        </div>
      </aside>
    </>
  );
};
