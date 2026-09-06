import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { RealTimeOperations } from '../pages/RealTimeOperations';
import { Sidebar } from '../components/layout/Sidebar';

// Mock Leaflet since jsdom does not implement browser Canvas / WebGL
vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: any) => <div data-testid="map-container">{children}</div>,
  TileLayer: () => <div data-testid="tile-layer" />,
  Marker: ({ children }: any) => <div data-testid="marker">{children}</div>,
  Popup: ({ children }: any) => <div data-testid="popup">{children}</div>,
  Polyline: () => <div data-testid="polyline" />,
}));

// Mock API
vi.mock('../services/api', () => {
  const mockFusedState = {
    timestamp: '2026-09-06T12:00:00Z',
    vehicles: [
      {
        vehicle_id: 'V-01',
        vehicle_code: 'V-01',
        status: 'ASSIGNED',
        latitude: 40.7128,
        longitude: -74.0060,
        speed_kmh: 35.0,
        heading: 90.0,
        current_payload_kg: 2500.0,
        capacity_kg: 12000.0,
        utilization_pct: 20.8,
        current_task_id: 'TSK-01',
        current_route: ['DEPOT_CENTRAL', 'COLLECTION_ZONE_A', 'LANDFILL_MAIN'],
        route_status: 'ON_TRACK',
        deviation_distance_m: 0.0,
        estimated_eta_min: 24.5,
        telemetry_health: 'TELEMETRY_HEALTHY',
        last_telemetry_timestamp: '2026-09-06T12:00:00Z',
        depot_id: 'DEPOT_CENTRAL',
        safety_status: 'SAFE',
      },
      {
        vehicle_id: 'V-02',
        vehicle_code: 'V-02',
        status: 'EN_ROUTE',
        latitude: 40.7300,
        longitude: -74.0100,
        speed_kmh: 28.0,
        heading: 45.0,
        current_payload_kg: 4200.0,
        capacity_kg: 12000.0,
        utilization_pct: 35.0,
        current_task_id: 'TSK-02',
        current_route: ['DEPOT_CENTRAL', 'COLLECTION_ZONE_C'],
        route_status: 'DEVIATED',
        deviation_distance_m: 145.0,
        estimated_eta_min: 32.0,
        telemetry_health: 'TELEMETRY_HEALTHY',
        last_telemetry_timestamp: '2026-09-06T12:00:00Z',
        depot_id: 'DEPOT_CENTRAL',
        safety_status: 'SAFE',
      },
    ],
    bins: [
      {
        bin_id: 'BIN-ZONE-A-01',
        location_node: 'COLLECTION_ZONE_A',
        timestamp: '2026-09-06T12:00:00Z',
        fill_level_percent: 45.0,
        estimated_waste_kg: 450.0,
        temperature_c: 21.0,
        sensor_battery_percent: 94.0,
        sensor_status: 'NORMAL',
        status_classification: 'NORMAL',
        sequence_number: 10,
        health_status: 'TELEMETRY_HEALTHY',
        source: 'SIMULATED_BIN_SENSOR',
      },
      {
        bin_id: 'BIN-ZONE-C-02',
        location_node: 'COLLECTION_ZONE_C',
        timestamp: '2026-09-06T12:00:00Z',
        fill_level_percent: 92.5,
        estimated_waste_kg: 925.0,
        temperature_c: 24.0,
        sensor_battery_percent: 89.0,
        sensor_status: 'CRITICAL',
        status_classification: 'CRITICAL',
        sequence_number: 12,
        health_status: 'TELEMETRY_HEALTHY',
        source: 'SIMULATED_BIN_SENSOR',
      },
    ],
    critical_bins_count: 1,
    active_alerts: [
      {
        alert_id: 'ALT-001',
        alert_type: 'CRITICAL_BIN',
        severity: 'CRITICAL',
        entity_id: 'BIN-ZONE-C-02',
        message: 'Smart bin BIN-ZONE-C-02 reached CRITICAL fill level (92.5%).',
        timestamp: '2026-09-06T12:00:00Z',
        recovery_action: 'TRIGGER_EMERGENCY_TASK_ALLOCATION',
        resolved: false,
      },
    ],
    traffic_condition: 'NORMAL',
    weather_condition: 'CLEAR',
    fleet_workload_balance: 0.85,
    average_eta_minutes: 24.5,
    disclaimer: 'Simulated Real-Time IoT Telemetry Layer',
  };

  const mockHealth = {
    total_messages_received: 240,
    valid_messages_count: 240,
    invalid_messages_count: 0,
    duplicate_messages_count: 0,
    stale_vehicles_count: 0,
    telemetry_health_rate_pct: 100.0,
    vehicle_health: { 'V-01': 'TELEMETRY_HEALTHY', 'V-02': 'TELEMETRY_HEALTHY' },
    bin_health: { 'BIN-ZONE-A-01': 'TELEMETRY_HEALTHY', 'BIN-ZONE-C-02': 'TELEMETRY_HEALTHY' },
    active_alerts_count: 1,
    websocket_clients_connected: 1,
    disclaimer: 'Deterministic Simulated Telemetry Health Metrics',
  };

  const mockDepots = [
    {
      depot_id: 'DEPOT_CENTRAL',
      name: 'Central Municipal Fleet Depot',
      latitude: 40.7128,
      longitude: -74.006,
      node_id: 'DEPOT_CENTRAL',
      active: true,
      assigned_vehicles_count: 4,
      capacity_vehicles: 25,
    },
    {
      depot_id: 'DEPOT_NORTH',
      name: 'North Metro Transfer Depot',
      latitude: 40.775,
      longitude: -73.955,
      node_id: 'TRANSFER_STATION_NORTH',
      active: true,
      assigned_vehicles_count: 1,
      capacity_vehicles: 15,
    },
  ];

  const mockAuditLogs = [
    {
      event_id: 'AUD-9A8B7C6D',
      timestamp: '2026-09-06T12:00:00Z',
      actor: 'dispatcher',
      role: 'DISPATCHER',
      action: 'TASK_ASSIGNED',
      entity_type: 'COLLECTION_TASK',
      entity_id: 'TSK-01',
      reason: 'Optimal allocation score',
      result: 'SUCCESS',
      details: {},
    },
  ];

  const mockBenchmark = {
    total_runs: 40,
    scenarios_evaluated: ['NORMAL_REALTIME', 'GPS_TELEMETRY_STREAM', 'CRITICAL_BIN'],
    seeds_evaluated: [42, 43, 44, 45, 46],
    overall_telemetry_health_rate_pct: 100.0,
    total_telemetry_messages_generated: 720,
    total_route_deviations_detected: 10,
    total_critical_bins_detected: 5,
    total_emergency_requests_generated: 5,
    emergency_fulfillment_rate_pct: 100.0,
    average_eta_recalculation_time_ms: 1.25,
    scenario_stats: {
      NORMAL_REALTIME: {
        scenario: 'NORMAL_REALTIME',
        runs_count: 5,
        telemetry_health_rate_pct: 100.0,
        route_deviations_detected: 0,
        critical_bins_detected: 0,
        emergency_requests_generated: 0,
        average_eta_recalculation_ms: 1.15,
        mean_eta_minutes: 24.5,
        rerouting_success_rate_pct: 100.0,
        failure_counts: {},
      },
    },
    failure_counts_by_category: {},
    disclaimer: 'Phase 9 Empirical 40-Run Benchmark Execution',
  };

  const mockScalability = {
    timestamp: '2026-09-06T12:00:00Z',
    benchmarks: [
      {
        vehicle_count: 50,
        depot_count: 3,
        telemetry_messages_processed: 2500,
        average_processing_latency_ms: 0.35,
        peak_processing_latency_ms: 1.2,
        telemetry_throughput_msg_per_sec: 1850.0,
        optimization_execution_time_ms: 4.8,
        memory_rss_mb: 85.4,
        status: 'PASS',
      },
    ],
    scalability_verdict: 'Scaled to 50 vehicles with average latency < 1.0ms',
    disclaimer: 'Measured Empirical Scalability Benchmark',
  };

  return {
    api: {
      getFusedFleetState: vi.fn().mockResolvedValue(mockFusedState),
      getTelemetryHealth: vi.fn().mockResolvedValue(mockHealth),
      getTelemetryAlerts: vi.fn().mockResolvedValue(mockFusedState.active_alerts),
      getDepots: vi.fn().mockResolvedValue(mockDepots),
      getAuditLog: vi.fn().mockResolvedValue(mockAuditLogs),
      stepTelemetrySimulation: vi.fn().mockResolvedValue(mockFusedState),
      runPhase9BenchmarkSuite: vi.fn().mockResolvedValue(mockBenchmark),
      runScalabilityBenchmark: vi.fn().mockResolvedValue(mockScalability),
    },
  };
});

describe('Phase 9 Real-Time IoT Telemetry & Operations Platform', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('1. Renders Real-Time Operations link in Sidebar Navigation', () => {
    render(
      <MemoryRouter>
        <Sidebar isOpen={true} />
      </MemoryRouter>
    );

    expect(screen.getByText('Real-Time Operations (Phase 9)')).toBeInTheDocument();
  });

  it('2. Loads Real-Time Operations Page and displays KPI Summary Cards', async () => {
    render(
      <MemoryRouter>
        <RealTimeOperations />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('REAL-TIME IoT TELEMETRY & OPERATIONS')).toBeInTheDocument();
    });

    expect(screen.getByText('Active Vehicles')).toBeInTheDocument();
    expect(screen.getByText('Smart Bins')).toBeInTheDocument();
    expect(screen.getByText('Critical Bins')).toBeInTheDocument();
    expect(screen.getByText('Telemetry Health')).toBeInTheDocument();
    expect(screen.getByText('Active Depots')).toBeInTheDocument();
  });

  it('3. Renders Vehicle Telemetry Cards and Smart Waste Bin Monitor', async () => {
    render(
      <MemoryRouter>
        <RealTimeOperations />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Streaming Vehicle GPS Telemetry/i)).toBeInTheDocument();
      expect(screen.getByText(/Smart Waste Bin Fill Telemetry/i)).toBeInTheDocument();
      expect(screen.getAllByText('BIN-ZONE-C-02').length).toBeGreaterThan(0);
    });
  });

  it('4. Switches between tabs: Benchmarks & Scalability and Audit Log', async () => {
    render(
      <MemoryRouter>
        <RealTimeOperations />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Benchmarks & Scalability')).toBeInTheDocument();
    });

    // Switch to Benchmarks tab
    fireEvent.click(screen.getByText('Benchmarks & Scalability'));
    expect(screen.getByText('PHASE 9 CONTROLLED BENCHMARK & SCALABILITY SUITE')).toBeInTheDocument();

    // Switch to Audit Log tab
    fireEvent.click(screen.getByText('Audit Log'));
    await waitFor(() => {
      expect(screen.getByText('Operational & Security Audit Log')).toBeInTheDocument();
      expect(screen.getByText('AUD-9A8B7C6D')).toBeInTheDocument();
    });
  });

  it('5. Switches user role between Dispatcher, Driver, and Supervisor', async () => {
    render(
      <MemoryRouter>
        <RealTimeOperations />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('ROLE:')).toBeInTheDocument();
    });

    const driverBtn = screen.getByText('DRIVER');
    fireEvent.click(driverBtn);
    expect(driverBtn).toHaveClass('bg-cyan-500');

    const superBtn = screen.getByText('SUPERVISOR');
    fireEvent.click(superBtn);
    expect(superBtn).toHaveClass('bg-cyan-500');
  });
});
