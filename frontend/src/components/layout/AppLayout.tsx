import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export const AppLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const getPageMeta = (pathname: string) => {
    switch (pathname) {
      case '/':
      case '/dashboard':
        return {
          title: 'Smart Waste Collection Operations',
          subtitle: 'Context-aware travel-time and route simulation',
        };
      case '/scenarios':
        return {
          title: 'Scenario Simulator',
          subtitle: 'Test how environmental and operational conditions affect travel time.',
        };
      case '/routes':
        return {
          title: 'Active Waste Collection Routes',
          subtitle: 'Fleet routing schedule, progress monitoring, and stop telemetry.',
        };
      case '/eta-analysis':
        return {
          title: 'ETA Model Analysis',
          subtitle: 'Comparative error breakdown: Baseline vs Context-Aware predictions.',
        };
      case '/experiments':
        return {
          title: 'Research Experiment Benchmark',
          subtitle: 'Cross-scenario evaluation datasets and accuracy improvement logs.',
        };
      case '/system-information':
        return {
          title: 'System Information & Architecture',
          subtitle: 'Project research documentation, mathematical formulations, and safety constraints.',
        };
      default:
        return {
          title: 'Operations Dashboard',
          subtitle: 'Smart Waste Collection Travel-Time & Route Simulator',
        };
    }
  };

  const pageMeta = getPageMeta(location.pathname);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="lg:pl-64 flex flex-col flex-1 min-w-0">
        <Header
          onMenuToggle={() => setSidebarOpen(!sidebarOpen)}
          title={pageMeta.title}
          subtitle={pageMeta.subtitle}
        />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto space-y-6">
          <Outlet />
        </main>

        <footer className="border-t border-slate-800/80 bg-slate-950/60 px-4 lg:px-8 py-4 text-center text-xs text-slate-400">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2 max-w-7xl mx-auto">
            <span>
              Smart Waste Collection Travel-Time & Route Simulator — Academic Research Prototype
            </span>
            <span className="font-mono text-slate-400">
              Phase 1: Project Foundation & Operations Dashboard
            </span>
          </div>
        </footer>
      </div>
    </div>
  );
};
