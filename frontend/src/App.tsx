import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { Dashboard } from './pages/Dashboard';
import { ScenarioSimulator } from './pages/ScenarioSimulator';
import { Routes as RoutesPage } from './pages/Routes';
import { ETAAnalysis } from './pages/ETAAnalysis';
import { Experiments } from './pages/Experiments';
import { DynamicRouting } from './pages/DynamicRouting';
import { FleetCoordination } from './pages/FleetCoordination';
import { RealTimeOperations } from './pages/RealTimeOperations';
import { CommandCenter } from './pages/CommandCenter';
import { SystemInformation } from './pages/SystemInformation';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Navigate to="/command-center" replace />} />
          <Route path="command-center" element={<CommandCenter />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="scenarios" element={<ScenarioSimulator />} />
          <Route path="routes" element={<RoutesPage />} />
          <Route path="dynamic-routing" element={<DynamicRouting />} />
          <Route path="fleet-coordination" element={<FleetCoordination />} />
          <Route path="real-time-operations" element={<RealTimeOperations />} />
          <Route path="eta-analysis" element={<ETAAnalysis />} />
          <Route path="experiments" element={<Experiments />} />
          <Route path="system-information" element={<SystemInformation />} />
          <Route path="*" element={<Navigate to="/command-center" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};


export default App;
