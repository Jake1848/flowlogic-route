"""
GPS Tracking Service for Real-time Vehicle Monitoring
Handles GPS data ingestion, processing, and real-time updates
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, desc, and_
from sqlalchemy.orm import sessionmaker, Session
from models.gps_tracking import (
    GPSPosition, VehicleStatus, GPSPositionCreate, 
    GPSPositionResponse, VehicleStatusResponse, LiveTrackingData
)
import json
import asyncio
import websockets
from geopy.distance import geodesic
import math

logger = logging.getLogger(__name__)

class GPSTrackingService:
    """Service for handling GPS tracking and real-time updates"""
    
    def __init__(self, database_url: str = "sqlite:///./gps_tracking.db"):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.connected_clients = set()  # WebSocket clients
        
        # Create tables if they don't exist
        from models.gps_tracking import Base
        Base.metadata.create_all(bind=self.engine)
        
        logger.info("GPS Tracking Service initialized")
    
    def get_db(self) -> Session:
        """Get database session"""
        db = self.SessionLocal()
        try:
            return db
        finally:
            pass  # Don't close here, let caller handle it
    
    async def ingest_gps_data(self, gps_data: GPSPositionCreate) -> GPSPositionResponse:
        """
        Ingest new GPS position data
        
        Args:
            gps_data: GPS position data to store
            
        Returns:
            Stored GPS position with ID
        """
        db = self.get_db()
        try:
            # Create new GPS position record
            db_position = GPSPosition(**gps_data.dict())
            db.add(db_position)
            db.commit()
            db.refresh(db_position)
            
            # Update vehicle status
            await self._update_vehicle_status(db, gps_data)
            
            # Create response
            response = GPSPositionResponse.from_orm(db_position)
            
            # Broadcast to connected WebSocket clients
            await self._broadcast_position_update(response)
            
            logger.info(f"GPS data ingested for vehicle {gps_data.vehicle_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error ingesting GPS data: {e}")
            db.rollback()
            raise
        finally:
            db.close()
    
    async def _update_vehicle_status(self, db: Session, gps_data: GPSPositionCreate):
        """Update vehicle status table with latest position"""
        try:
            # Get or create vehicle status
            vehicle_status = db.query(VehicleStatus).filter(
                VehicleStatus.vehicle_id == gps_data.vehicle_id
            ).first()
            
            if not vehicle_status:
                vehicle_status = VehicleStatus(
                    vehicle_id=gps_data.vehicle_id,
                    vehicle_name=f"Vehicle {gps_data.vehicle_id}",
                    vehicle_type="truck"
                )
                db.add(vehicle_status)
            
            # Update position and status
            vehicle_status.last_latitude = gps_data.latitude
            vehicle_status.last_longitude = gps_data.longitude
            vehicle_status.last_update = gps_data.gps_timestamp
            vehicle_status.current_route_id = gps_data.route_id
            vehicle_status.current_driver = gps_data.driver_id
            vehicle_status.updated_at = datetime.utcnow()
            
            # Update status based on movement and delivery status
            if gps_data.delivery_status:
                vehicle_status.status = gps_data.delivery_status
            elif gps_data.is_at_stop:
                vehicle_status.status = "at_stop"
            elif gps_data.is_moving:
                vehicle_status.status = "in_transit"
            else:
                vehicle_status.status = "idle"
            
            # Calculate daily distance (simplified)
            if gps_data.odometer:
                vehicle_status.total_distance_today = gps_data.odometer
            
            # Update average speed
            if gps_data.speed and gps_data.speed > 0:
                # Simple moving average (could be improved)
                if vehicle_status.average_speed:
                    vehicle_status.average_speed = (vehicle_status.average_speed + gps_data.speed) / 2
                else:
                    vehicle_status.average_speed = gps_data.speed
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating vehicle status: {e}")
            db.rollback()
    
    async def get_live_positions(self, vehicle_ids: Optional[List[str]] = None) -> List[LiveTrackingData]:
        """
        Get current live positions for vehicles
        
        Args:
            vehicle_ids: Optional list of specific vehicle IDs to fetch
            
        Returns:
            List of live tracking data
        """
        db = self.get_db()
        try:
            query = db.query(VehicleStatus)
            
            if vehicle_ids:
                query = query.filter(VehicleStatus.vehicle_id.in_(vehicle_ids))
            
            # Only return vehicles with recent updates (last 30 minutes)
            cutoff_time = datetime.utcnow() - timedelta(minutes=30)
            query = query.filter(VehicleStatus.last_update > cutoff_time)
            
            vehicles = query.all()
            
            live_data = []
            for vehicle in vehicles:
                if vehicle.last_latitude and vehicle.last_longitude:
                    # Get latest GPS data for additional info
                    latest_gps = db.query(GPSPosition).filter(
                        GPSPosition.vehicle_id == vehicle.vehicle_id
                    ).order_by(desc(GPSPosition.gps_timestamp)).first()
                    
                    live_data.append(LiveTrackingData(
                        vehicle_id=vehicle.vehicle_id,
                        latitude=vehicle.last_latitude,
                        longitude=vehicle.last_longitude,
                        heading=latest_gps.heading if latest_gps else None,
                        speed=latest_gps.speed if latest_gps else None,
                        status=vehicle.status,
                        last_update=vehicle.last_update,
                        route_id=vehicle.current_route_id,
                        current_stop=latest_gps.current_stop_id if latest_gps else None,
                        is_moving=latest_gps.is_moving if latest_gps else True,
                        fuel_level=latest_gps.fuel_level if latest_gps else None,
                        battery_level=latest_gps.battery_level if latest_gps else None
                    ))
            
            return live_data
            
        except Exception as e:
            logger.error(f"Error getting live positions: {e}")
            return []
        finally:
            db.close()
    
    async def get_vehicle_history(
        self, 
        vehicle_id: str, 
        hours: int = 24
    ) -> List[GPSPositionResponse]:
        """
        Get GPS history for a specific vehicle
        
        Args:
            vehicle_id: Vehicle to get history for
            hours: Hours of history to retrieve
            
        Returns:
            List of GPS positions ordered by timestamp
        """
        db = self.get_db()
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            positions = db.query(GPSPosition).filter(
                and_(
                    GPSPosition.vehicle_id == vehicle_id,
                    GPSPosition.gps_timestamp > cutoff_time
                )
            ).order_by(GPSPosition.gps_timestamp).all()
            
            return [GPSPositionResponse.from_orm(pos) for pos in positions]
            
        except Exception as e:
            logger.error(f"Error getting vehicle history: {e}")
            return []
        finally:
            db.close()
    
    def calculate_distance_traveled(
        self, 
        positions: List[GPSPositionResponse]
    ) -> float:
        """Calculate total distance traveled from GPS positions"""
        if len(positions) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(positions)):
            prev_pos = positions[i-1]
            curr_pos = positions[i]
            
            distance = geodesic(
                (prev_pos.latitude, prev_pos.longitude),
                (curr_pos.latitude, curr_pos.longitude)
            ).miles
            
            total_distance += distance
        
        return round(total_distance, 2)
    
    def calculate_eta(
        self, 
        vehicle_position: GPSPositionResponse,
        destination_lat: float,
        destination_lng: float,
        average_speed: float = 35.0  # mph
    ) -> Optional[datetime]:
        """Calculate ETA to destination based on current position and speed"""
        try:
            distance = geodesic(
                (vehicle_position.latitude, vehicle_position.longitude),
                (destination_lat, destination_lng)
            ).miles
            
            # Use vehicle's current speed if available, otherwise use average
            speed = vehicle_position.speed if vehicle_position.speed and vehicle_position.speed > 5 else average_speed
            
            # Calculate time in hours
            time_hours = distance / speed
            
            # Add current time
            eta = datetime.utcnow() + timedelta(hours=time_hours)
            return eta
            
        except Exception as e:
            logger.error(f"Error calculating ETA: {e}")
            return None
    
    async def _broadcast_position_update(self, position: GPSPositionResponse):
        """Broadcast position update to all connected WebSocket clients"""
        if not self.connected_clients:
            return
        
        message = {
            "type": "position_update",
            "data": {
                "vehicle_id": position.vehicle_id,
                "latitude": position.latitude,
                "longitude": position.longitude,
                "heading": position.heading,
                "speed": position.speed,
                "timestamp": position.gps_timestamp.isoformat(),
                "status": position.delivery_status or "in_transit"
            }
        }
        
        # Send to all connected clients
        disconnected_clients = set()
        for client in self.connected_clients:
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.connected_clients -= disconnected_clients
    
    async def add_websocket_client(self, websocket):
        """Add a new WebSocket client"""
        self.connected_clients.add(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.connected_clients)}")
    
    async def remove_websocket_client(self, websocket):
        """Remove a WebSocket client"""
        self.connected_clients.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.connected_clients)}")
    
    async def simulate_gps_data(self, vehicle_id: str, route_points: List[tuple]):
        """
        Simulate GPS data for testing purposes
        
        Args:
            vehicle_id: Vehicle to simulate
            route_points: List of (lat, lng) tuples representing the route
        """
        logger.info(f"Starting GPS simulation for vehicle {vehicle_id}")
        
        for i, (lat, lng) in enumerate(route_points):
            # Calculate heading to next point
            heading = None
            if i < len(route_points) - 1:
                next_lat, next_lng = route_points[i + 1]
                heading = self._calculate_bearing(lat, lng, next_lat, next_lng)
            
            # Create GPS data
            gps_data = GPSPositionCreate(
                vehicle_id=vehicle_id,
                latitude=lat,
                longitude=lng,
                heading=heading,
                speed=35.0 + (i * 2),  # Simulate varying speed
                is_moving=True,
                is_online=True,
                battery_level=95.0 - (i * 0.5),  # Simulate battery drain
                gps_timestamp=datetime.utcnow(),
                engine_status="on",
                fuel_level=80.0 - (i * 0.3),  # Simulate fuel consumption
                delivery_status="in_transit"
            )
            
            # Ingest the data
            await self.ingest_gps_data(gps_data)
            
            # Wait before next update (simulate movement)
            await asyncio.sleep(5)  # 5-second intervals
    
    def _calculate_bearing(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate bearing between two GPS coordinates"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lng_rad = math.radians(lng2 - lng1)
        
        y = math.sin(delta_lng_rad) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lng_rad)
        
        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)
        
        # Normalize to 0-360 degrees
        return (bearing_deg + 360) % 360

# Global instance
gps_service = GPSTrackingService()