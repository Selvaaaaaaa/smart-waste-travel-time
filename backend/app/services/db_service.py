import math
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.route import Route
from app.models.route_stop import RouteStop
from app.models.weather import WeatherCondition
from app.models.traffic import TrafficCondition
from app.models.event import Event
from app.models.road_restriction import RoadRestriction
from app.models.observation import TravelTimeObservation
from app.models.scenario import Scenario
from app.models.experiment import Experiment


class DatabaseQueryService:
    """Service layer for querying domain models with pagination and filtering."""

    @staticmethod
    def get_vehicles(db: Session, page: int = 1, page_size: int = 20, status: Optional[str] = None) -> Tuple[List[Vehicle], int, int]:
        query = db.query(Vehicle)
        if status and status.lower() != "all":
            query = query.filter(Vehicle.status == status.upper())
        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        items = query.order_by(Vehicle.id).offset((page - 1) * page_size).limit(page_size).all()
        return items, total, total_pages

    @staticmethod
    def get_drivers(db: Session, page: int = 1, page_size: int = 20, status: Optional[str] = None) -> Tuple[List[Driver], int, int]:
        query = db.query(Driver)
        if status and status.lower() != "all":
            query = query.filter(Driver.status == status.upper())
        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        items = query.order_by(Driver.id).offset((page - 1) * page_size).limit(page_size).all()
        return items, total, total_pages

    @staticmethod
    def get_weather(db: Session, page: int = 1, page_size: int = 20) -> Tuple[List[WeatherCondition], int, int]:
        query = db.query(WeatherCondition)
        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        items = query.order_by(desc(WeatherCondition.observation_time)).offset((page - 1) * page_size).limit(page_size).all()
        return items, total, total_pages

    @staticmethod
    def get_traffic(db: Session, page: int = 1, page_size: int = 20) -> Tuple[List[TrafficCondition], int, int]:
        query = db.query(TrafficCondition)
        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        items = query.order_by(desc(TrafficCondition.observation_time)).offset((page - 1) * page_size).limit(page_size).all()
        return items, total, total_pages

    @staticmethod
    def get_events(db: Session, page: int = 1, page_size: int = 20) -> Tuple[List[Event], int, int]:
        query = db.query(Event)
        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        items = query.order_by(desc(Event.start_time)).offset((page - 1) * page_size).limit(page_size).all()
        return items, total, total_pages

    @staticmethod
    def get_road_restrictions(db: Session, page: int = 1, page_size: int = 20) -> Tuple[List[RoadRestriction], int, int]:
        query = db.query(RoadRestriction)
        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        items = query.order_by(desc(RoadRestriction.start_time)).offset((page - 1) * page_size).limit(page_size).all()
        return items, total, total_pages

    @staticmethod
    def get_observations(db: Session, page: int = 1, page_size: int = 20) -> Tuple[List[TravelTimeObservation], int, int]:
        query = db.query(TravelTimeObservation)
        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        items = query.order_by(desc(TravelTimeObservation.id)).offset((page - 1) * page_size).limit(page_size).all()
        return items, total, total_pages

    @staticmethod
    def get_scenarios(db: Session, page: int = 1, page_size: int = 20) -> Tuple[List[Scenario], int, int]:
        query = db.query(Scenario)
        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        items = query.order_by(Scenario.id).offset((page - 1) * page_size).limit(page_size).all()
        return items, total, total_pages

    @staticmethod
    def get_experiments(db: Session, page: int = 1, page_size: int = 20) -> Tuple[List[Experiment], int, int]:
        query = db.query(Experiment)
        total = query.count()
        total_pages = max(1, math.ceil(total / page_size))
        items = query.order_by(Experiment.id).offset((page - 1) * page_size).limit(page_size).all()
        return items, total, total_pages
