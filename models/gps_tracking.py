from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, DateTime, Integer, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel

Base = declarative_base()

class GPSPosition(Base):
    """GPS tracking data for vehicles"""
    __tablename__ = "gps_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(String(50), index=True, nullable=False)  # Truck A, B, etc.
    route_id = Column(String(100), index=True)  # Link to specific route
    
    # Location data
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)  # GPS accuracy in meters
    
    # Movement data
    speed = Column(Float, nullable=True)  # Speed in mph/kmh
    heading = Column(Float, nullable=True)  # Compass direction (0-360)
    
    # Status information
    is_moving = Column(Boolean, default=True)
    is_online = Column(Boolean, default=True)
    battery_level = Column(Float, nullable=True)  # Battery percentage
    
    # Timestamps
    gps_timestamp = Column(DateTime, nullable=False)  # When GPS reading was taken
    received_timestamp = Column(DateTime, default=datetime.utcnow)  # When server received it
    
    # Additional data
    driver_id = Column(String(100), nullable=True)
    odometer = Column(Float, nullable=True)  # Total distance traveled
    engine_status = Column(String(20), nullable=True)  # on, off, idle
    fuel_level = Column(Float, nullable=True)  # Fuel percentage
    
    # Geofence and delivery status
    current_stop_id = Column(String(100), nullable=True)
    is_at_stop = Column(Boolean, default=False)
    delivery_status = Column(String(50), nullable=True)  # en_route, arrived, delivering, completed
    
    # Metadata
    device_id = Column(String(100), nullable=True)  # GPS device identifier
    raw_data = Column(Text, nullable=True)  # Store original GPS message


class VehicleStatus(Base):
    """Current status and metadata for each vehicle"""
    __tablename__ = "vehicle_status"
    
    vehicle_id = Column(String(50), primary_key=True, index=True)
    
    # Vehicle info
    vehicle_name = Column(String(100))
    vehicle_type = Column(String(50))  # truck, van, etc.
    license_plate = Column(String(20))
    
    # Current status
    current_route_id = Column(String(100), nullable=True)
    current_driver = Column(String(100), nullable=True)
    status = Column(String(50), default='available')  # available, dispatched, in_transit, at_stop, maintenance
    
    # Last known position (for quick lookups)
    last_latitude = Column(Float, nullable=True)
    last_longitude = Column(Float, nullable=True)
    last_update = Column(DateTime, nullable=True)
    
    # Performance metrics
    total_distance_today = Column(Float, default=0.0)
    stops_completed_today = Column(Integer, default=0)
    average_speed = Column(Float, nullable=True)
    
    # Vehicle specs
    max_capacity = Column(Float, nullable=True)  # Max weight/pallets
    fuel_capacity = Column(Float, nullable=True)
    
    # Maintenance
    last_maintenance = Column(DateTime, nullable=True)
    next_maintenance = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic models for API
class GPSPositionCreate(BaseModel):
    vehicle_id: str
    route_id: Optional[str] = None
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None
    is_moving: bool = True
    is_online: bool = True
    battery_level: Optional[float] = None
    gps_timestamp: datetime
    driver_id: Optional[str] = None
    odometer: Optional[float] = None
    engine_status: Optional[str] = None
    fuel_level: Optional[float] = None
    current_stop_id: Optional[str] = None
    is_at_stop: bool = False
    delivery_status: Optional[str] = None
    device_id: Optional[str] = None
    raw_data: Optional[str] = None

class GPSPositionResponse(BaseModel):
    id: int
    vehicle_id: str
    route_id: Optional[str]
    latitude: float
    longitude: float
    altitude: Optional[float]
    accuracy: Optional[float]
    speed: Optional[float]
    heading: Optional[float]
    is_moving: bool
    is_online: bool
    battery_level: Optional[float]
    gps_timestamp: datetime
    received_timestamp: datetime
    driver_id: Optional[str]
    odometer: Optional[float]
    engine_status: Optional[str]
    fuel_level: Optional[float]
    current_stop_id: Optional[str]
    is_at_stop: bool
    delivery_status: Optional[str]
    device_id: Optional[str]
    
    class Config:
        from_attributes = True

class VehicleStatusResponse(BaseModel):
    vehicle_id: str
    vehicle_name: Optional[str]
    vehicle_type: Optional[str]
    license_plate: Optional[str]
    current_route_id: Optional[str]
    current_driver: Optional[str]
    status: str
    last_latitude: Optional[float]
    last_longitude: Optional[float]
    last_update: Optional[datetime]
    total_distance_today: float
    stops_completed_today: int
    average_speed: Optional[float]
    max_capacity: Optional[float]
    fuel_capacity: Optional[float]
    last_maintenance: Optional[datetime]
    next_maintenance: Optional[datetime]
    
    class Config:
        from_attributes = True

class LiveTrackingData(BaseModel):
    """Real-time tracking data for frontend"""
    vehicle_id: str
    latitude: float
    longitude: float
    heading: Optional[float] = None
    speed: Optional[float] = None
    status: str
    last_update: datetime
    route_id: Optional[str] = None
    current_stop: Optional[str] = None
    is_moving: bool = True
    fuel_level: Optional[float] = None
    battery_level: Optional[float] = None