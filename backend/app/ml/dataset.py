import logging
from typing import Tuple, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from app.models.observation import TravelTimeObservation
from app.models.weather import WeatherCondition
from app.models.traffic import TrafficCondition
from app.models.event import Event
from app.models.road_restriction import RoadRestriction

logger = logging.getLogger(__name__)


class DatasetReport:
    def __init__(self, total_records: int, valid_records: int, invalid_records: int, missing_values: Dict[str, int], notes: str = ""):
        self.total_records = total_records
        self.valid_records = valid_records
        self.invalid_records = invalid_records
        self.missing_values = missing_values
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "missing_values": self.missing_values,
            "notes": self.notes,
        }


def load_dataset_from_db(db: Session) -> Tuple[pd.DataFrame, DatasetReport]:
    """
    Extract travel-time observations from PostgreSQL database, join contextual entities,
    validate records, and return clean Pandas DataFrame with data validation report.
    """
    logger.info("Extracting travel-time observations from database...")
    query = (
        db.query(
            TravelTimeObservation.id,
            TravelTimeObservation.observation_date,
            TravelTimeObservation.distance_km,
            TravelTimeObservation.waste_volume_tons,
            TravelTimeObservation.baseline_travel_minutes,
            TravelTimeObservation.actual_travel_minutes,
            TravelTimeObservation.hour_of_day,
            TravelTimeObservation.day_of_week,
            WeatherCondition.condition.label("weather_condition"),
            WeatherCondition.rainfall_mm,
            WeatherCondition.visibility_km,
            WeatherCondition.temperature_c,
            TrafficCondition.traffic_level,
            TrafficCondition.congestion_index,
            TrafficCondition.average_speed_kmh,
            Event.impact_level.label("event_level"),
            Event.impact_radius_km.label("event_radius"),
            RoadRestriction.restriction_type.label("road_restriction_type"),
            RoadRestriction.severity.label("road_restriction_severity"),
        )
        .outerjoin(WeatherCondition, TravelTimeObservation.weather_id == WeatherCondition.id)
        .outerjoin(TrafficCondition, TravelTimeObservation.traffic_id == TrafficCondition.id)
        .outerjoin(Event, TravelTimeObservation.event_id == Event.id)
        .outerjoin(RoadRestriction, TravelTimeObservation.road_restriction_id == RoadRestriction.id)
        .order_by(TravelTimeObservation.observation_date.asc(), TravelTimeObservation.id.asc())
    )

    records = [r._asdict() for r in query.all()]
    total_records = len(records)

    if total_records == 0:
        logger.warning("No observations found in database. Returning empty DataFrame.")
        return pd.DataFrame(), DatasetReport(0, 0, 0, {}, "Database contains no observation rows.")

    df = pd.DataFrame(records)

    # Impute nominal defaults for unlinked optional contextual attributes
    df["weather_condition"] = df["weather_condition"].fillna("CLEAR")
    df["rainfall_mm"] = df["rainfall_mm"].fillna(0.0)
    df["visibility_km"] = df["visibility_km"].fillna(10.0)
    df["temperature_c"] = df["temperature_c"].fillna(20.0)
    df["traffic_level"] = df["traffic_level"].fillna("LOW")
    df["congestion_index"] = df["congestion_index"].fillna(15.0)
    df["average_speed_kmh"] = df["average_speed_kmh"].fillna(45.0)
    df["event_level"] = df["event_level"].fillna("NONE")
    df["event_radius"] = df["event_radius"].fillna(0.0)
    df["road_restriction_type"] = df["road_restriction_type"].fillna("NONE")
    df["road_restriction_severity"] = df["road_restriction_severity"].fillna("NONE")

    missing_counts = df.isnull().sum().to_dict()

    # Validation filtering: reject physically invalid measurements
    valid_mask = (
        (df["distance_km"] > 0)
        & (df["waste_volume_tons"] >= 0)
        & (df["baseline_travel_minutes"] > 0)
        & (df["actual_travel_minutes"] > 0)
        & (df["congestion_index"] >= 0)
        & (df["congestion_index"] <= 100)
        & (df["hour_of_day"] >= 0)
        & (df["hour_of_day"] <= 23)
        & (df["day_of_week"] >= 0)
        & (df["day_of_week"] <= 6)
    )

    clean_df = df[valid_mask].copy()
    valid_records = len(clean_df)
    invalid_records = total_records - valid_records

    notes = (
        f"Processed {total_records} records. {valid_records} valid records retained for training. "
        f"{invalid_records} invalid records filtered out due to boundary constraints."
    )

    logger.info(notes)
    report = DatasetReport(
        total_records=total_records,
        valid_records=valid_records,
        invalid_records=invalid_records,
        missing_values=missing_counts,
        notes=notes,
    )

    return clean_df, report
