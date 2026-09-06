import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Route as RouteIcon,
  Compass,
  BarChart3,
  FlaskConical,
  Info,
  Truck,
  Activity,
  Radio,
  Sliders,
  AlertTriangle,
  FileText,
  Users,
  HardDrive,
  Siren,
} from 'lucide-react';

import { StatusBadge } from '../common/StatusBadge';

interface NavGroup {
  title: string;
  items: {
    name: string;
    path: string;
    icon: React.ReactNode;
    badge?: string;
  }[];
}

const navGroups: NavGroup[] = [
  {
    title: 'OVERVIEW',
    items: [
      {
        name: 'Command Center',
        path: '/command-center',
        icon: <Activity className="w-4 h-4 text-emerald-400" />,
        badge: 'LIVE',
      },
      {
        name: 'Operations Dashboard',
        path: '/dashboard',
        icon: <LayoutDashboard className="w-4 h-4 text-cyan-400" />,
      },
    ],
  },
  {
    title: 'OPERATIONS',
    items: [
      {
        name: 'Live Operations',
        path: '/real-time-operations',
        icon: <Radio className="w-4 h-4 text-emerald-400" />,
      },
      {
        name: 'Fleet Management',
        path: '/fleet-coordination',
        icon: <Truck className="w-4 h-4 text-blue-400" />,
      },
      {
        name: 'Collection Tasks & Routes',
        path: '/routes',
        icon: <RouteIcon className="w-4 h-4 text-amber-400" />,
      },
      {
        name: 'Route Planning',
        path: '/dynamic-routing',
        icon: <Compass className="w-4 h-4 text-purple-400" />,
      },
      {
        name: 'Emergency Requests',
        path: '/emergency-requests',
        icon: <Siren className="w-4 h-4 text-rose-400" />,
        badge: 'AUTO',
      },
    ],
  },
  {
    title: 'ANALYTICS',
    items: [
      {
        name: 'ETA & Travel Time (ETA Analysis)',
        path: '/eta-analysis',
        icon: <BarChart3 className="w-4 h-4 text-cyan-400" />,
      },
      {
        name: 'Performance Analytics (Experiments)',
        path: '/experiments',
        icon: <FlaskConical className="w-4 h-4 text-indigo-400" />,
      },
      {
        name: 'Operating Conditions (Scenario Simulator)',
        path: '/scenarios',
        icon: <Sliders className="w-4 h-4 text-amber-400" />,
      },
    ],
  },
  {
    title: 'MONITORING',
    items: [
      {
        name: 'Smart Bins',
        path: '/smart-bins',
        icon: <HardDrive className="w-4 h-4 text-emerald-400" />,
      },
      {
        name: 'Alerts & Incidents',
        path: '/alerts-incidents',
        icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
      },
      {
        name: 'System Health',
        path: '/system-health',
        icon: <Activity className="w-4 h-4 text-cyan-400" />,
      },
    ],
  },
  {
    title: 'ADMINISTRATION',
    items: [
      {
        name: 'Users & Roles',
        path: '/users-roles',
        icon: <Users className="w-4 h-4 text-slate-400" />,
      },
      {
        name: 'Audit Logs',
        path: '/audit-logs',
        icon: <FileText className="w-4 h-4 text-slate-400" />,
      },
      {
        name: 'System Information & Diagnostics',
        path: '/system-information',
        icon: <Info className="w-4 h-4 text-slate-400" />,
      },
    ],
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
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Truck className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xs font-black tracking-wider text-white flex items-center gap-1.5 font-mono uppercase">
                SMART WASTE
              </h1>
              <p className="text-[10px] text-slate-400 font-medium tracking-tight">
                City Operations Platform
              </p>
            </div>
          </div>
        </div>

        {/* System Operational Status Badge */}
        <div className="px-4 py-2.5 border-b border-slate-800/50 bg-slate-900/40 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-[10px] font-bold text-slate-300 uppercase tracking-wider">
              Control Room
            </span>
          </div>
          <StatusBadge status="SYSTEM ONLINE" size="sm" />
        </div>

        {/* Navigation Groups */}
        <nav className="flex-1 px-3 py-3 space-y-4 overflow-y-auto custom-scrollbar">
          {navGroups.map((group) => (
            <div key={group.title} className="space-y-1">
              <div className="px-3 pb-1 text-[9px] font-bold text-slate-400 uppercase tracking-wider">
                {group.title}
              </div>
              {group.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                      isActive
                        ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-semibold shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                    }`
                  }
                >
                  <div className="flex items-center gap-2.5">
                    {item.icon}
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-slate-800 text-emerald-400 border border-emerald-500/30">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        {/* Bottom Platform Status Card */}
        <div className="p-3.5 border-t border-slate-800/80 bg-slate-900/60">
          <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1">
            <span className="font-semibold text-slate-300">Environment</span>
            <span className="font-mono text-emerald-400 font-bold">Production Simulation</span>
          </div>
          <p className="text-[9px] text-slate-400 leading-tight">
            Intelligent Waste Collection & Fleet Management Platform
          </p>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
