from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, time
from enum import Enum


class SpecialConstraint(str, Enum):
    NONE = "None"
    FRAGILE = "Fragile"
    REFRIGERATED = "Refrigerated"
    FROZEN = "Frozen"
    HAZMAT = "Hazmat"
    HEAVY = "Heavy"


class TruckType(str, Enum):
    DRY = "Dry"
    REFRIGERATED = "Refrigerated"
    FROZEN = "Frozen"
    HAZMAT = "Hazmat"
    FLATBED = "Flatbed"


class Stop(BaseModel):
    stop_id: int
    address: str
    time_window_start: time
    time_window_end: time
    pallets: int
    special_constraint: SpecialConstraint
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    service_time_minutes: int = 15  # Default 15 min per stop


class Truck(BaseModel):
    truck_id: str
    depot_address: str
    max_pallets: int
    truck_type: TruckType
    shift_start: time
    shift_end: time
    depot_latitude: Optional[float] = None
    depot_longitude: Optional[float] = None
    cost_per_mile: float = 2.5
    avg_speed_mph: float = 45


class RouteStop(BaseModel):
    stop_id: int
    eta: str
    arrival_time: datetime
    departure_time: datetime
    distance_from_previous: float
    notes: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    pallets: Optional[int] = None
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None
    estimated_arrival: Optional[str] = None


class TruckRoute(BaseModel):
    truck_id: str
    stops: List[RouteStop]
    total_miles: float
    total_time_hours: float
    fuel_estimate: float
    utilization_percent: float
    reasoning: str
    depot_latitude: Optional[float] = None
    depot_longitude: Optional[float] = None
    depot_address: Optional[str] = None


class RoutingRequest(BaseModel):
    stops: List[Stop]
    trucks: List[Truck]
    constraints: Optional[Dict[str, Any]] = {}
    optimization_preference: str = "minimize_distance"


class RoutingResponse(BaseModel):
    routes: List[TruckRoute]
    unassigned_stops: List[int]
    total_miles: float
    total_fuel_cost: float
    average_utilization: float
    routing_time_seconds: float
    natural_language_summary: str