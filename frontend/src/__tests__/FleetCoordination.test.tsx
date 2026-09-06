import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { FleetCoordination } from '../pages/FleetCoordination';
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
  const mockFleetState = {
    summary: {
      total_vehicles: 6,
      available: 3,
      assigned: 2,
      en_route: 1,
      overloaded: 0,
      breakdown: 0,
      off_duty: 0,
      mean_utilization_pct: 28.5,
      utilization_variance: 420.0,
      load_balance_score: 0.88,
    },
    vehicles: [
      {
        vehicle_id: 'V-01',
        vehicle_code: 'V-01',
        vehicle_type: 'COMPACTOR_HEAVY',
        capacity_kg: 12000.0,
        current_payload_kg: 2500.0,
        current_location: 'DEPOT_CENTRAL',
        driver_id: 'EMP-001',
        driver_name: 'Alex Mercer',
        driver_shift_remaining_min: 270.0,
        current_route: ['DEPOT_CENTRAL', 'COLLECTION_ZONE_A', 'LANDFILL_MAIN'],
        current_task_id: 'TSK-01',
        status: 'ASSIGNED',
        overload_status: 'NORMAL',
        utilization_pct: 20.8,
        safety_status: 'SAFE',
        estimated_available_time_min: 35.0,
      },
      {
        vehicle_id: 'V-03',
        vehicle_code: 'V-03',
        vehicle_type: 'COMPACTOR_HEAVY',
        capacity_kg: 12000.0,
        current_payload_kg: 0.0,
        current_location: 'DEPOT_CENTRAL',
        driver_id: 'EMP-004',
        driver_name: 'Sarah Chen',
        driver_shift_remaining_min: 360.0,
        current_route: [],
        current_task_id: null,
        status: 'AVAILABLE',
        overload_status: 'NORMAL',
        utilization_pct: 0.0,
        safety_status: 'SAFE',
        estimated_available_time_min: 0.0,
      },
    ],
    active_tasks_count: 2,
    pending_tasks_count: 3,
    timestamp: '2026-09-06T12:00:00Z',
    disclaimer: 'Deterministic simulation',
  };

  const mockTasks = [
    {
      id: 'TSK-01',
      location_node: 'COLLECTION_ZONE_A',
      estimated_waste_kg: 1200.0,
      priority: 'NORMAL',
      request_type: 'SCHEDULED_COLLECTION',
      status: 'ASSIGNED',
      assigned_vehicle_id: 'V-01',
      created_at: '2026-09-06T10:00:00Z',
    },
    {
      id: 'TSK-02',
      location_node: 'COLLECTION_ZONE_C',
      estimated_waste_kg: 2200.0,
      priority: 'HIGH',
      request_type: 'SCHEDULED_COLLECTION',
      status: 'PENDING',
      created_at: '2026-09-06T10:30:00Z',
    },
  ];

  const mockEvents = [
    {
      id: 'EVT-01',
      event_type: 'TASK_ASSIGNED',
      task_id: 'TSK-01',
      new_vehicle_id: 'V-01',
      previous_route: [],
      new_route: ['DEPOT_CENTRAL', 'COLLECTION_ZONE_A', 'LANDFILL_MAIN'],
      predicted_eta_after: 24.5,
      distance_difference_km: 7.5,
      safety_result: 'SAFE',
      selected_eta_model: 'ADAPTIVE_HYBRID',
      reason: 'Optimal score assigned to V-01',
      timestamp: '2026-09-06T10:05:00Z',
    },
  ];

  const mockGraph = {
    nodes: [
      { id: 'DEPOT_CENTRAL', name: 'Central Fleet Depot', lat: 40.7128, lng: -74.006, node_type: 'depot' },
      { id: 'COLLECTION_ZONE_A', name: 'Commercial Zone A', lat: 40.725, lng: -74.002, node_type: 'collection' },
      { id: 'LANDFILL_MAIN', name: 'Regional Landfill', lat: 40.79, lng: -73.94, node_type: 'landfill' },
    ],
    edges: [],
    disclaimer: 'Deterministic simulation',
  };

  const mockDecision = {
    task_id: 'TSK-02',
    status: 'ASSIGNED',
    selected_vehicle_id: 'V-03',
    selected_driver_id: 'EMP-004',
    selected_route: ['DEPOT_CENTRAL', 'COLLECTION_ZONE_C', 'LANDFILL_MAIN'],
    predicted_eta_minutes: 22.4,
    allocation_score: 0.28,
    selection_reason: 'V-03 selected with sufficient capacity and lowest ETA.',
    candidate_evaluations: [
      {
        vehicle_id: 'V-03',
        vehicle_code: 'V-03',
        is_safe: true,
        allocation_score: 0.28,
        predicted_eta_min: 22.4,
        projected_payload_kg: 2200.0,
        projected_shift_minutes: 142.4,
        selected_eta_model: 'ADAPTIVE_HYBRID',
        prediction_spread_min: 1.2,
      },
    ],
    safety_result: 'SAFE',
    disclaimer: 'Deterministic simulation',
  };

  const mockBenchmark = {
    total_runs: 35,
    scenarios_evaluated: [
      'NORMAL_FLEET',
      'HIGH_WASTE_FLEET',
      'VEHICLE_BREAKDOWN',
      'EMERGENCY_REQUEST',
      'ROAD_CLOSURE_FLEET',
      'DRIVER_SHIFT_WARNING',
      'COMBINED_FLEET_STRESS',
    ],
    task_assignment_success_rate_pct: 94.29,
    safe_assignment_rate_pct: 100.0,
    avg_assignment_eta_min: 24.18,
    avg_fleet_travel_time_min: 145.1,
    avg_fleet_distance_km: 48.2,
    emergency_fulfillment_rate_pct: 100.0,
    breakdown_recovery_rate_pct: 100.0,
    avg_vehicle_utilization_pct: 38.6,
    utilization_variance: 312.4,
    fleet_load_balance_score: 0.84,
    unsafe_assignments_prevented: 14,
    reassignments_count: 5,
    avg_rebalancing_improvement_min: 5.2,
    unassigned_task_rate_pct: 5.71,
    scenario_breakdown: {
      NORMAL_FLEET: {
        success_rate_pct: 100.0,
        safe_rate_pct: 100.0,
        avg_eta_min: 22.1,
        mean_utilization_pct: 35.0,
        load_balance_score: 0.88,
        unsafe_prevented: 0,
        reassignments: 0,
      },
    },
    failure_analysis: {
      CAPACITY_EXCEEDED: 2,
    },
    detailed_runs: [],
    disclaimer: 'Deterministic simulation',
  };

  return {
    api: {
      getFleetState: vi.fn().mockResolvedValue(mockFleetState),
      getFleetVehicles: vi.fn().mockResolvedValue(mockFleetState.vehicles),
      getFleetTasks: vi.fn().mockResolvedValue(mockTasks),
      getFleetEvents: vi.fn().mockResolvedValue(mockEvents),
      getNetworkGraph: vi.fn().mockResolvedValue(mockGraph),
      assignTask: vi.fn().mockResolvedValue(mockDecision),
      createCollectionTask: vi.fn().mockResolvedValue({ ...mockTasks[0], id: 'EMG-NEW' }),
      triggerEmergencyTask: vi.fn().mockResolvedValue(mockDecision),
      simulateBreakdown: vi.fn().mockResolvedValue({
        vehicle_id: 'V-01',
        previous_status: 'ASSIGNED',
        new_status: 'BREAKDOWN',
        affected_tasks: ['TSK-01'],
        message: 'Breakdown recorded',
      }),
      recoverVehicle: vi.fn().mockResolvedValue({ vehicle_id: 'V-01', status: 'AVAILABLE', message: 'Recovered' }),
      rebalanceFleet: vi.fn().mockResolvedValue({
        rebalance_triggered: true,
        trigger_reason: 'MANUAL',
        affected_tasks_count: 1,
        reassigned_tasks_count: 1,
        deferred_tasks_count: 0,
        details: [],
        audit_events: [],
        disclaimer: '',
      }),
      simulateFleetStep: vi.fn().mockResolvedValue({
        step_duration_minutes: 10.0,
        events_detected: [],
        vehicles_updated: 2,
        tasks_completed: [],
        rebalance_performed: false,
        fleet_summary: mockFleetState.summary,
        disclaimer: '',
      }),
      runFleetBenchmark: vi.fn().mockResolvedValue(mockBenchmark),
      getOptimizationSummary: vi.fn().mockResolvedValue({
        total_vehicles: 6,
        active_vehicles: 3,
        available_vehicles: 3,
        assigned_vehicles: 2,
        fleet_workload_balance: 0.88,
        mean_utilization_pct: 28.5,
        emergency_requests_count: 0,
        unsafe_assignments_prevented: 14,
        timestamp: '2026-09-06T12:00:00Z',
      }),
      runPhase8BenchmarkSuite: vi.fn().mockResolvedValue({
        total_runs: 50,
        scenarios_evaluated: [
          'NORMAL_OPERATIONS',
          'HEAVY_TRAFFIC',
          'HEAVY_RAIN',
          'ROAD_CLOSURE',
          'MAJOR_EVENT',
          'HIGH_WASTE_VOLUME',
          'VEHICLE_BREAKDOWN',
          'EMERGENCY_REQUEST',
          'WORKLOAD_IMBALANCE',
          'COMBINED_STRESS',
        ],
        seeds_evaluated: [42, 43, 44, 45, 46],
        assignment_success_rate_pct: 100.0,
        safe_assignment_rate_pct: 100.0,
        emergency_fulfillment_rate_pct: 100.0,
        breakdown_recovery_rate_pct: 100.0,
        mean_workload_balance_score: 0.8132,
        mean_baseline_score: 0.4072,
        mean_optimized_score: 0.3039,
        mean_optimization_improvement_pct: 25.37,
        total_unsafe_candidates_rejected: 145,
        total_payload_violations_prevented: 130,
        total_shift_violations_prevented: 0,
        total_blocked_road_violations_prevented: 0,
        scenario_stats: {
          NORMAL_OPERATIONS: {
            scenario: 'NORMAL_OPERATIONS',
            runs_count: 5,
            eta_minutes: { mean: 29.4, median: 29.4, min: 29.4, max: 29.4, std_dev: 0.0 },
            distance_km: { mean: 12.3, median: 12.3, min: 12.3, max: 12.3, std_dev: 0.0 },
            optimization_score: { mean: 0.2138, median: 0.2138, min: 0.2138, max: 0.2138, std_dev: 0.0 },
            workload_balance: { mean: 0.8334, median: 0.8334, min: 0.8334, max: 0.8334, std_dev: 0.0 },
            recovery_time_minutes: { mean: 0.0, median: 0.0, min: 0.0, max: 0.0, std_dev: 0.0 },
            improvement_over_baseline_pct: 25.37,
          },
        },
        failure_counts_by_category: {
          PAYLOAD_CAPACITY_EXCEEDED: 130,
        },
        runs: [],
        disclaimer: 'Deterministic simulation',
      }),
      getPhase8BenchmarkExperiments: vi.fn().mockResolvedValue({
        total_runs: 50,
        scenarios_evaluated: [
          'NORMAL_OPERATIONS',
          'HEAVY_TRAFFIC',
          'HEAVY_RAIN',
          'ROAD_CLOSURE',
          'MAJOR_EVENT',
          'HIGH_WASTE_VOLUME',
          'VEHICLE_BREAKDOWN',
          'EMERGENCY_REQUEST',
          'WORKLOAD_IMBALANCE',
          'COMBINED_STRESS',
        ],
        seeds_evaluated: [42, 43, 44, 45, 46],
        assignment_success_rate_pct: 100.0,
        safe_assignment_rate_pct: 100.0,
        emergency_fulfillment_rate_pct: 100.0,
        breakdown_recovery_rate_pct: 100.0,
        mean_workload_balance_score: 0.8132,
        mean_baseline_score: 0.4072,
        mean_optimized_score: 0.3039,
        mean_optimization_improvement_pct: 25.37,
        total_unsafe_candidates_rejected: 145,
        total_payload_violations_prevented: 130,
        total_shift_violations_prevented: 0,
        total_blocked_road_violations_prevented: 0,
        scenario_stats: {},
        failure_counts_by_category: {},
        runs: [],
        disclaimer: 'Deterministic simulation',
      }),
      getFailureDiagnostics: vi.fn().mockResolvedValue([
        {
          scenario: 'HIGH_WASTE_VOLUME',
          seed: 42,
          task_id: 'TSK-02',
          vehicle_id: 'V-02',
          failure_category: 'PAYLOAD_CAPACITY_EXCEEDED',
          failure_reason: 'Projected load 12500kg exceeds capacity 12000kg',
          recovery_action: 'REJECT_CANDIDATE',
          final_status: 'PREVENTED',
          timestamp: '2026-09-06T12:00:00Z',
        },
      ]),
      getOptimizationComparison: vi.fn().mockResolvedValue({
        scenario: 'NORMAL_OPERATIONS',
        tasks_count: 5,
        eta_comparison: {
          baseline_value: 36.0,
          optimized_value: 29.4,
          percentage_improvement: 18.3,
          is_statistically_significant: false,
        },
        distance_comparison: {
          baseline_value: 14.1,
          optimized_value: 12.3,
          percentage_improvement: 12.7,
          is_statistically_significant: false,
        },
        workload_balance_comparison: {
          baseline_value: 0.65,
          optimized_value: 0.85,
          percentage_improvement: 30.7,
          is_statistically_significant: false,
        },
        utilization_comparison: {
          baseline_value: 45.0,
          optimized_value: 42.0,
          percentage_improvement: 0.0,
          is_statistically_significant: false,
        },
        summary_verdict: 'Advanced optimizer achieves superior workload balance and reduces trip travel time.',
        disclaimer: 'Deterministic simulation',
      }),
      rebalanceWithBenefit: vi.fn().mockResolvedValue({
        rebalance_required: false,
        rebalance_beneficial: false,
        trigger_reason: 'NO_CRITICAL_DISRUPTION',
        affected_vehicles: [],
        affected_tasks: [],
        previous_allocation: {},
        new_allocation: {},
        expected_eta_change_min: 0.0,
        expected_distance_change_km: 0.0,
        disclaimer: 'Deterministic simulation',
      }),
    },
  };
});

describe('Phase 8 Fleet Coordination & Advanced Optimization Platform', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('1. Renders Fleet Coordination in Sidebar Navigation', () => {
    render(
      <MemoryRouter>
        <Sidebar isOpen={true} />
      </MemoryRouter>
    );

    expect(screen.getByRole('link', { name: /Fleet Management/i })).toBeInTheDocument();
  });

  it('2. Loads Fleet Coordination Page and displays KPI Summary Cards', async () => {
    render(
      <MemoryRouter>
        <FleetCoordination />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('FLEET COORDINATION & TASK ALLOCATION')).toBeInTheDocument();
    });

    expect(screen.getByText('Total Fleet')).toBeInTheDocument();
    expect(screen.getByText('Available')).toBeInTheDocument();
    expect(screen.getByText('Assigned / En Route')).toBeInTheDocument();
    expect(screen.getByText('Load Balance')).toBeInTheDocument();
    expect(screen.getByText('Mean Utilization')).toBeInTheDocument();
  });

  it('3. Renders Vehicles Table with unit status, driver, and payload', async () => {
    render(
      <MemoryRouter>
        <FleetCoordination />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Alex Mercer')).toBeInTheDocument();
      expect(screen.getByText('Sarah Chen')).toBeInTheDocument();
    });

    expect(screen.getByText('Fleet Vehicles & Crew Workload')).toBeInTheDocument();
  });

  it('4. Assigns pending task and displays allocation decision panel', async () => {
    render(
      <MemoryRouter>
        <FleetCoordination />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('TSK-02')).toBeInTheDocument();
    });

    const assignBtn = screen.getByText('Assign');
    fireEvent.click(assignBtn);

    await waitFor(() => {
      expect(screen.getByText('Allocation Decision Engine Output')).toBeInTheDocument();
      expect(screen.getByText(/V-03 selected with sufficient capacity/i)).toBeInTheDocument();
    });
  });

  it('5. Switches to Benchmark tab and runs 50-run benchmark suite', async () => {
    render(
      <MemoryRouter>
        <FleetCoordination />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Optimization Benchmark (50 Runs)')).toBeInTheDocument();
    });

    const benchmarkTabBtn = screen.getByText('Optimization Benchmark (50 Runs)');
    fireEvent.click(benchmarkTabBtn);

    expect(screen.getByText('FLEET OPTIMIZATION BENCHMARK EVALUATION')).toBeInTheDocument();
    const runBenchmarkBtn = screen.getByText('Re-Run Benchmark Suite (50 Runs)');
    fireEvent.click(runBenchmarkBtn);

    await waitFor(() => {
      expect(screen.getByText('F. Scenario Statistical Performance Breakdown (10 Scenarios)')).toBeInTheDocument();
      expect(screen.getByText('NORMAL_OPERATIONS')).toBeInTheDocument();
    });
  });
});
