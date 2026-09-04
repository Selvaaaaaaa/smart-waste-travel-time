"""Initial domain models migration for Phase 2

Revision ID: 001_initial
Revises: 
Create Date: 2026-09-04 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Vehicles
    op.create_table(
        'vehicles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_code', sa.String(length=50), nullable=False),
        sa.Column('vehicle_type', sa.String(length=50), nullable=False),
        sa.Column('capacity_tons', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('capacity_tons > 0', name='check_positive_vehicle_capacity'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicles_id'), 'vehicles', ['id'], unique=False)
    op.create_index(op.f('ix_vehicles_vehicle_code'), 'vehicles', ['vehicle_code'], unique=True)

    # 2. Drivers
    op.create_table(
        'drivers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('max_work_minutes_per_shift', sa.Integer(), nullable=False),
        sa.Column('current_work_minutes', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('max_work_minutes_per_shift > 0', name='check_positive_max_work_shift'),
        sa.CheckConstraint('current_work_minutes >= 0', name='check_non_negative_current_work'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_drivers_id'), 'drivers', ['id'], unique=False)
    op.create_index(op.f('ix_drivers_employee_code'), 'drivers', ['employee_code'], unique=True)

    # 3. Routes
    op.create_table(
        'routes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route_code', sa.String(length=50), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=True),
        sa.Column('driver_id', sa.Integer(), nullable=True),
        sa.Column('route_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('total_distance_km', sa.Float(), nullable=False),
        sa.Column('total_waste_tons', sa.Float(), nullable=False),
        sa.Column('baseline_eta_minutes', sa.Float(), nullable=False),
        sa.Column('actual_duration_minutes', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('total_distance_km >= 0', name='check_non_negative_route_distance'),
        sa.CheckConstraint('total_waste_tons >= 0', name='check_non_negative_route_waste'),
        sa.CheckConstraint('baseline_eta_minutes >= 0', name='check_non_negative_baseline_eta'),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_routes_id'), 'routes', ['id'], unique=False)
    op.create_index(op.f('ix_routes_route_code'), 'routes', ['route_code'], unique=True)
    op.create_index(op.f('ix_routes_route_date'), 'routes', ['route_date'], unique=False)
    op.create_index(op.f('ix_routes_vehicle_id'), 'routes', ['vehicle_id'], unique=False)
    op.create_index(op.f('ix_routes_driver_id'), 'routes', ['driver_id'], unique=False)

    # 4. Route Stops
    op.create_table(
        'route_stops',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=False),
        sa.Column('stop_sequence', sa.Integer(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('waste_tons', sa.Float(), nullable=False),
        sa.Column('service_minutes', sa.Float(), nullable=False),
        sa.Column('completed', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('stop_sequence >= 1', name='check_positive_stop_sequence'),
        sa.CheckConstraint('waste_tons >= 0', name='check_non_negative_stop_waste'),
        sa.CheckConstraint('service_minutes >= 0', name='check_non_negative_service_minutes'),
        sa.CheckConstraint('latitude >= -90 AND latitude <= 90', name='check_valid_latitude'),
        sa.CheckConstraint('longitude >= -180 AND longitude <= 180', name='check_valid_longitude'),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_route_stops_id'), 'route_stops', ['id'], unique=False)
    op.create_index(op.f('ix_route_stops_route_id'), 'route_stops', ['route_id'], unique=False)

    # 5. Waste Collections
    op.create_table(
        'waste_collections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=False),
        sa.Column('stop_id', sa.Integer(), nullable=True),
        sa.Column('collection_date', sa.Date(), nullable=False),
        sa.Column('waste_tons', sa.Float(), nullable=False),
        sa.Column('waste_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('waste_tons >= 0', name='check_non_negative_waste_collection'),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stop_id'], ['route_stops.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_waste_collections_id'), 'waste_collections', ['id'], unique=False)
    op.create_index(op.f('ix_waste_collections_route_id'), 'waste_collections', ['route_id'], unique=False)
    op.create_index(op.f('ix_waste_collections_stop_id'), 'waste_collections', ['stop_id'], unique=False)
    op.create_index(op.f('ix_waste_collections_collection_date'), 'waste_collections', ['collection_date'], unique=False)

    # 6. Weather Conditions
    op.create_table(
        'weather_conditions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('observation_time', sa.DateTime(), nullable=False),
        sa.Column('condition', sa.String(length=50), nullable=False),
        sa.Column('temperature_c', sa.Float(), nullable=False),
        sa.Column('rainfall_mm', sa.Float(), nullable=False),
        sa.Column('visibility_km', sa.Float(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_weather_conditions_id'), 'weather_conditions', ['id'], unique=False)
    op.create_index(op.f('ix_weather_conditions_observation_time'), 'weather_conditions', ['observation_time'], unique=False)

    # 7. Traffic Conditions
    op.create_table(
        'traffic_conditions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('observation_time', sa.DateTime(), nullable=False),
        sa.Column('traffic_level', sa.String(length=50), nullable=False),
        sa.Column('congestion_index', sa.Float(), nullable=False),
        sa.Column('average_speed_kmh', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('congestion_index >= 0 AND congestion_index <= 100', name='check_congestion_index_range'),
        sa.CheckConstraint('average_speed_kmh >= 0', name='check_non_negative_speed'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_traffic_conditions_id'), 'traffic_conditions', ['id'], unique=False)
    op.create_index(op.f('ix_traffic_conditions_observation_time'), 'traffic_conditions', ['observation_time'], unique=False)

    # 8. Events
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_name', sa.String(length=150), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('impact_radius_km', sa.Float(), nullable=False),
        sa.Column('impact_level', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('impact_radius_km >= 0', name='check_non_negative_event_radius'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_id'), 'events', ['id'], unique=False)

    # 9. Road Restrictions
    op.create_table(
        'road_restrictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('restriction_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('affected_radius_km', sa.Float(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('affected_radius_km >= 0', name='check_non_negative_restriction_radius'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_road_restrictions_id'), 'road_restrictions', ['id'], unique=False)

    # 10. Travel Time Observations
    op.create_table(
        'travel_time_observations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=False),
        sa.Column('observation_date', sa.Date(), nullable=False),
        sa.Column('distance_km', sa.Float(), nullable=False),
        sa.Column('baseline_travel_minutes', sa.Float(), nullable=False),
        sa.Column('actual_travel_minutes', sa.Float(), nullable=False),
        sa.Column('weather_id', sa.Integer(), nullable=True),
        sa.Column('traffic_id', sa.Integer(), nullable=True),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('road_restriction_id', sa.Integer(), nullable=True),
        sa.Column('waste_volume_tons', sa.Float(), nullable=False),
        sa.Column('hour_of_day', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('distance_km >= 0', name='check_obs_distance_non_negative'),
        sa.CheckConstraint('baseline_travel_minutes >= 0', name='check_obs_baseline_non_negative'),
        sa.CheckConstraint('actual_travel_minutes >= 0', name='check_obs_actual_non_negative'),
        sa.CheckConstraint('hour_of_day >= 0 AND hour_of_day <= 23', name='check_valid_hour'),
        sa.CheckConstraint('day_of_week >= 0 AND day_of_week <= 6', name='check_valid_day_of_week'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['road_restriction_id'], ['road_restrictions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['traffic_id'], ['traffic_conditions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['weather_id'], ['weather_conditions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_travel_time_observations_id'), 'travel_time_observations', ['id'], unique=False)
    op.create_index(op.f('ix_travel_time_observations_observation_date'), 'travel_time_observations', ['observation_date'], unique=False)
    op.create_index(op.f('ix_travel_time_observations_route_id'), 'travel_time_observations', ['route_id'], unique=False)

    # 11. ETA Predictions
    op.create_table(
        'eta_predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=False),
        sa.Column('prediction_time', sa.DateTime(), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('predicted_eta_minutes', sa.Float(), nullable=False),
        sa.Column('actual_eta_minutes', sa.Float(), nullable=True),
        sa.Column('absolute_error_minutes', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('predicted_eta_minutes >= 0', name='check_predicted_eta_non_negative'),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_eta_predictions_id'), 'eta_predictions', ['id'], unique=False)
    op.create_index(op.f('ix_eta_predictions_model_type'), 'eta_predictions', ['model_type'], unique=False)
    op.create_index(op.f('ix_eta_predictions_prediction_time'), 'eta_predictions', ['prediction_time'], unique=False)
    op.create_index(op.f('ix_eta_predictions_route_id'), 'eta_predictions', ['route_id'], unique=False)

    # 12. Scenarios
    op.create_table(
        'scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_name', sa.String(length=100), nullable=False),
        sa.Column('weather_condition', sa.String(length=50), nullable=False),
        sa.Column('traffic_level', sa.String(length=50), nullable=False),
        sa.Column('event_level', sa.String(length=50), nullable=False),
        sa.Column('road_restriction_level', sa.String(length=50), nullable=False),
        sa.Column('waste_volume_level', sa.String(length=50), nullable=False),
        sa.Column('time_of_day', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scenarios_id'), 'scenarios', ['id'], unique=False)
    op.create_index(op.f('ix_scenarios_scenario_name'), 'scenarios', ['scenario_name'], unique=True)

    # 13. Experiments
    op.create_table(
        'experiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('scenario_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_experiments_id'), 'experiments', ['id'], unique=False)
    op.create_index(op.f('ix_experiments_scenario_id'), 'experiments', ['scenario_id'], unique=False)

    # 14. Experiment Results
    op.create_table(
        'experiment_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('mae', sa.Float(), nullable=False),
        sa.Column('rmse', sa.Float(), nullable=False),
        sa.Column('mean_error', sa.Float(), nullable=False),
        sa.Column('median_error', sa.Float(), nullable=False),
        sa.Column('within_tolerance_percent', sa.Float(), nullable=False),
        sa.Column('route_completion_minutes', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('mae >= 0', name='check_mae_non_negative'),
        sa.CheckConstraint('rmse >= 0', name='check_rmse_non_negative'),
        sa.CheckConstraint('within_tolerance_percent >= 0 AND within_tolerance_percent <= 100', name='check_tolerance_range'),
        sa.ForeignKeyConstraint(['experiment_id'], ['experiments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_experiment_results_id'), 'experiment_results', ['id'], unique=False)
    op.create_index(op.f('ix_experiment_results_experiment_id'), 'experiment_results', ['experiment_id'], unique=False)


def downgrade() -> None:
    op.drop_table('experiment_results')
    op.drop_table('experiments')
    op.drop_table('scenarios')
    op.drop_table('eta_predictions')
    op.drop_table('travel_time_observations')
    op.drop_table('road_restrictions')
    op.drop_table('events')
    op.drop_table('traffic_conditions')
    op.drop_table('weather_conditions')
    op.drop_table('waste_collections')
    op.drop_table('route_stops')
    op.drop_table('routes')
    op.drop_table('drivers')
    op.drop_table('vehicles')
