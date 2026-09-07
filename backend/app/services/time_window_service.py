"""Time-window and regulatory driving-hour constraint service.

Enforces two categories of operational constraints that go beyond physical
payload capacity:

1. **Customer Service Time-Windows** — a collection zone may only be
   serviced within a contracted time band (e.g. 07:00 – 11:00).  Arriving
   outside this window violates the municipal service level agreement.

2. **Regulatory Driving-Hour Caps** — based on EU/UK HGV driving-hour
   regulations (Regulation EC 561/2006):
   - Maximum continuous driving before a break: 4.5 h (270 min).
   - Minimum break required after 4.5 h continuous driving: 45 min
     (or two splits of 15 + 30 min in that order).
   - Maximum daily driving time: 9 h (540 min), extendable to 10 h twice
     a week.
   - Maximum weekly driving time: 56 h.

This module is integrated by SafetyService and exercised in the final
benchmark validation suite.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.services.safety_service import SafetyValidationResult


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class TimeWindow:
    """Defines a contracted collection service window for a location node.

    Attributes:
        location_node: Identifier matching the routing graph node (e.g. 'COLLECTION_ZONE_A').
        earliest_minute: Minutes from shift start when service may begin (inclusive).
        latest_minute: Minutes from shift start by which service must be complete (inclusive).
        label: Human-readable description shown in violation messages.
    """
    location_node: str
    earliest_minute: float  # e.g. 0.0 = shift start, 120.0 = 2 h into shift
    latest_minute: float
    label: str = ""

    def __post_init__(self) -> None:
        if self.earliest_minute < 0:
            raise ValueError("earliest_minute must be >= 0")
        if self.latest_minute <= self.earliest_minute:
            raise ValueError("latest_minute must be > earliest_minute")


@dataclass
class DrivingHoursRecord:
    """Tracks a driver's driving time within a single shift.

    Attributes:
        total_driving_minutes: Cumulative driving minutes so far this shift.
        break_minutes_taken: Total minutes of qualifying rest breaks taken.
        continuous_driving_minutes: Minutes driven since the last qualifying break.
        weekly_driving_minutes: Cumulative driving minutes this week (Mon–Sun).
        daily_limit_extended: Whether the 10-h extended daily limit applies today.
    """
    total_driving_minutes: float = 0.0
    break_minutes_taken: float = 0.0
    continuous_driving_minutes: float = 0.0
    weekly_driving_minutes: float = 0.0
    daily_limit_extended: bool = False  # True = 10 h limit; False = 9 h default


# ---------------------------------------------------------------------------
# Regulation Constants (EC 561/2006)
# ---------------------------------------------------------------------------

MAX_CONTINUOUS_DRIVING_MIN: float = 270.0   # 4.5 hours
REQUIRED_BREAK_MIN: float = 45.0           # after 4.5 h continuous
MAX_DAILY_DRIVING_MIN_STANDARD: float = 540.0   # 9 hours
MAX_DAILY_DRIVING_MIN_EXTENDED: float = 600.0   # 10 hours (max twice per week)
MAX_WEEKLY_DRIVING_MIN: float = 3360.0     # 56 hours


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class TimeWindowService:
    """Validates time-window and regulatory driving-hour constraints."""

    # ------------------------------------------------------------------
    # 1. Service Time-Window Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_time_window(
        arrival_minutes_from_shift_start: float,
        time_window: TimeWindow,
    ) -> SafetyValidationResult:
        """Check that a vehicle arrives at a collection zone within the contracted window.

        Args:
            arrival_minutes_from_shift_start: Projected arrival time relative to shift
                start (in minutes).
            time_window: The contracted service window for the target location.

        Returns:
            SafetyValidationResult — is_valid=True if arrival is within [earliest, latest].
        """
        node = time_window.location_node
        label = time_window.label or node
        earliest = time_window.earliest_minute
        latest = time_window.latest_minute

        if arrival_minutes_from_shift_start < earliest:
            return SafetyValidationResult(
                is_valid=False,
                message=(
                    f"SERVICE WINDOW VIOLATION: Projected arrival at {label} is "
                    f"{arrival_minutes_from_shift_start:.1f} min into shift — "
                    f"before contracted window opens at {earliest:.0f} min "
                    f"({_fmt_shift_time(earliest)})."
                ),
                violation_type="SERVICE_WINDOW_TOO_EARLY",
            )

        if arrival_minutes_from_shift_start > latest:
            return SafetyValidationResult(
                is_valid=False,
                message=(
                    f"SERVICE WINDOW VIOLATION: Projected arrival at {label} is "
                    f"{arrival_minutes_from_shift_start:.1f} min into shift — "
                    f"after contracted window closes at {latest:.0f} min "
                    f"({_fmt_shift_time(latest)}). Collection will miss the SLA."
                ),
                violation_type="SERVICE_WINDOW_EXCEEDED",
            )

        return SafetyValidationResult(
            is_valid=True,
            message=(
                f"Service window OK: Arrival at {label} at "
                f"{_fmt_shift_time(arrival_minutes_from_shift_start)} is within "
                f"contracted window [{_fmt_shift_time(earliest)} – {_fmt_shift_time(latest)}]."
            ),
        )

    # ------------------------------------------------------------------
    # 2. Regulatory Driving-Hour Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_regulatory_driving_hours(
        record: DrivingHoursRecord,
        additional_driving_minutes: float,
    ) -> SafetyValidationResult:
        """Validate that assigning additional driving time keeps the driver within
        EU/UK HGV regulatory limits.

        Checks performed (in order):
        1. Continuous driving limit (4.5 h) without a qualifying 45-min break.
        2. Daily driving limit (9 h standard / 10 h extended).
        3. Weekly driving limit (56 h).

        Args:
            record: Current driving-hours state for the driver.
            additional_driving_minutes: Minutes of driving to be added.

        Returns:
            SafetyValidationResult for the *first* violated rule, or valid if all pass.
        """
        projected_continuous = record.continuous_driving_minutes + additional_driving_minutes
        projected_daily = record.total_driving_minutes + additional_driving_minutes
        projected_weekly = record.weekly_driving_minutes + additional_driving_minutes
        daily_cap = (
            MAX_DAILY_DRIVING_MIN_EXTENDED
            if record.daily_limit_extended
            else MAX_DAILY_DRIVING_MIN_STANDARD
        )

        # Rule 1: Continuous driving cap
        if projected_continuous > MAX_CONTINUOUS_DRIVING_MIN and record.break_minutes_taken < REQUIRED_BREAK_MIN:
            return SafetyValidationResult(
                is_valid=False,
                message=(
                    f"REGULATORY VIOLATION (EC 561/2006 Art.7): Projected continuous driving "
                    f"({projected_continuous:.0f} min) exceeds the 4.5-hour limit "
                    f"({MAX_CONTINUOUS_DRIVING_MIN:.0f} min) without a qualifying "
                    f"{REQUIRED_BREAK_MIN:.0f}-min break (taken: {record.break_minutes_taken:.0f} min)."
                ),
                violation_type="CONTINUOUS_DRIVING_LIMIT_EXCEEDED",
            )

        # Rule 2: Daily cap
        if projected_daily > daily_cap:
            cap_label = "extended 10-hour" if record.daily_limit_extended else "standard 9-hour"
            return SafetyValidationResult(
                is_valid=False,
                message=(
                    f"REGULATORY VIOLATION (EC 561/2006 Art.6): Projected daily driving "
                    f"({projected_daily:.0f} min) exceeds the {cap_label} daily limit "
                    f"({daily_cap:.0f} min)."
                ),
                violation_type="DAILY_DRIVING_LIMIT_EXCEEDED",
            )

        # Rule 3: Weekly cap
        if projected_weekly > MAX_WEEKLY_DRIVING_MIN:
            return SafetyValidationResult(
                is_valid=False,
                message=(
                    f"REGULATORY VIOLATION (EC 561/2006 Art.6): Projected weekly driving "
                    f"({projected_weekly:.0f} min) exceeds the 56-hour weekly limit "
                    f"({MAX_WEEKLY_DRIVING_MIN:.0f} min)."
                ),
                violation_type="WEEKLY_DRIVING_LIMIT_EXCEEDED",
            )

        return SafetyValidationResult(
            is_valid=True,
            message=(
                f"Regulatory driving hours OK: +{additional_driving_minutes:.0f} min proposed; "
                f"daily total would be {projected_daily:.0f}/{daily_cap:.0f} min, "
                f"continuous {projected_continuous:.0f}/{MAX_CONTINUOUS_DRIVING_MIN:.0f} min."
            ),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_shift_time(minutes_from_start: float, shift_start_hour: int = 6) -> str:
    """Convert minutes-from-shift-start to a readable clock time (e.g. '09:30').

    Default shift start assumed at 06:00 (early morning municipal collection).
    """
    total_minutes = int(shift_start_hour * 60 + minutes_from_start)
    hh = (total_minutes // 60) % 24
    mm = total_minutes % 60
    return f"{hh:02d}:{mm:02d}"
