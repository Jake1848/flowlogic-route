"""
GPS Tracking API Routes
Handles GPS data ingestion, live tracking, and WebSocket connections
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import json
import asyncio

from models.gps_tracking import (
    GPSPositionCreate, GPSPositionResponse, 
    VehicleStatusResponse, LiveTrackingData
)
from services.gps_tracking import gps_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gps", tags=["GPS Tracking"])

@router.post("/positions", response_model=GPSPositionResponse)
async def ingest_gps_position(gps_data: GPSPositionCreate):
    """
    Ingest new GPS position data from vehicle tracking devices
    
    This endpoint is typically called by GPS tracking devices or mobile apps
    to report vehicle positions in real-time.
    """
    try:
        result = await gps_service.ingest_gps_data(gps_data)
        return result
    except Exception as e:
        logger.error(f"Error ingesting GPS position: {e}")
        raise HTTPException(status_code=500, detail="Failed to store GPS data")

@router.get("/live", response_model=List[LiveTrackingData])
async def get_live_positions(
    vehicle_ids: Optional[List[str]] = Query(None),
    route_id: Optional[str] = Query(None)
):
    """
    Get current live positions for all vehicles or specific vehicles
    
    Args:
        vehicle_ids: Optional list of vehicle IDs to filter by
        route_id: Optional route ID to filter vehicles assigned to specific route
    """
    try:
        live_positions = await gps_service.get_live_positions(vehicle_ids)
        
        # Filter by route if specified
        if route_id:
            live_positions = [pos for pos in live_positions if pos.route_id == route_id]
        
        return live_positions
    except Exception as e:
        logger.error(f"Error getting live positions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get live positions")

@router.get("/vehicles/{vehicle_id}/history", response_model=List[GPSPositionResponse])
async def get_vehicle_history(
    vehicle_id: str,
    hours: int = Query(24, description="Hours of history to retrieve", ge=1, le=168)
):
    """
    Get GPS position history for a specific vehicle
    
    Args:
        vehicle_id: Vehicle ID to get history for
        hours: Number of hours of history to retrieve (1-168 hours)
    """
    try:
        history = await gps_service.get_vehicle_history(vehicle_id, hours)
        return history
    except Exception as e:
        logger.error(f"Error getting vehicle history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get vehicle history")

@router.get("/vehicles/{vehicle_id}/stats")
async def get_vehicle_stats(vehicle_id: str):
    """Get performance statistics for a specific vehicle"""
    try:
        # Get 24-hour history
        history = await gps_service.get_vehicle_history(vehicle_id, 24)
        
        if not history:
            raise HTTPException(status_code=404, detail="Vehicle not found or no recent data")
        
        # Calculate statistics
        total_distance = gps_service.calculate_distance_traveled(history)
        
        # Calculate average speed (excluding stationary periods)
        moving_positions = [pos for pos in history if pos.speed and pos.speed > 5]
        avg_speed = sum(pos.speed for pos in moving_positions) / len(moving_positions) if moving_positions else 0
        
        # Get latest position
        latest = history[-1]
        
        # Calculate time spent moving vs stationary
        moving_time = sum(1 for pos in history if pos.is_moving)
        stationary_time = len(history) - moving_time
        
        return {
            "vehicle_id": vehicle_id,
            "period_hours": 24,
            "total_distance_miles": total_distance,
            "average_speed_mph": round(avg_speed, 1),
            "moving_time_percent": round((moving_time / len(history)) * 100, 1),
            "stationary_time_percent": round((stationary_time / len(history)) * 100, 1),
            "latest_position": {
                "latitude": latest.latitude,
                "longitude": latest.longitude,
                "timestamp": latest.gps_timestamp,
                "speed": latest.speed,
                "heading": latest.heading
            },
            "fuel_level": latest.fuel_level,
            "battery_level": latest.battery_level,
            "total_positions": len(history)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vehicle stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get vehicle statistics")

@router.post("/vehicles/{vehicle_id}/simulate")
async def start_gps_simulation(
    vehicle_id: str, 
    background_tasks: BackgroundTasks,
    route_points: List[dict] = None
):
    """
    Start GPS simulation for testing purposes
    
    Args:
        vehicle_id: Vehicle ID to simulate
        route_points: Optional list of {"lat": float, "lng": float} points
    """
    # Default Atlanta route if none provided
    if not route_points:
        route_points = [
            {"lat": 33.7490, "lng": -84.3880},  # Downtown Atlanta
            {"lat": 33.7683, "lng": -84.3854},  # Midtown
            {"lat": 33.7820, "lng": -84.3885},  # Tech Square
            {"lat": 33.7574, "lng": -84.3931},  # West End
            {"lat": 33.7347, "lng": -84.3614}   # East Atlanta
        ]
    
    # Convert to tuple list
    points = [(point["lat"], point["lng"]) for point in route_points]
    
    # Start simulation in background
    background_tasks.add_task(gps_service.simulate_gps_data, vehicle_id, points)
    
    return {
        "message": f"GPS simulation started for vehicle {vehicle_id}",
        "route_points": len(points),
        "estimated_duration_minutes": len(points) * 5 / 60  # 5 seconds per point
    }

@router.websocket("/ws/live-tracking")
async def websocket_live_tracking(websocket: WebSocket):
    """
    WebSocket endpoint for real-time GPS tracking updates
    
    Clients can connect to this endpoint to receive real-time position updates
    for all vehicles as they report their GPS data.
    """
    await websocket.accept()
    await gps_service.add_websocket_client(websocket)
    
    try:
        # Send initial vehicle positions
        live_positions = await gps_service.get_live_positions()
        initial_message = {
            "type": "initial_positions",
            "data": [pos.dict() for pos in live_positions]
        }
        await websocket.send_text(json.dumps(initial_message))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (like requests for specific data)
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "subscribe_vehicle":
                    vehicle_id = message.get("vehicle_id")
                    # Could implement vehicle-specific subscriptions here
                    pass
                
            except asyncio.TimeoutError:
                # Send periodic keepalive
                await websocket.send_text(json.dumps({"type": "keepalive"}))
                continue
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await gps_service.remove_websocket_client(websocket)

@router.get("/geofences/{vehicle_id}")
async def check_geofence_status(vehicle_id: str):
    """
    Check if vehicle is within defined geofences (delivery stops, depots, etc.)
    """
    try:
        # Get latest position
        history = await gps_service.get_vehicle_history(vehicle_id, 1)
        if not history:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        latest_position = history[-1]
        
        # TODO: Implement actual geofence checking logic
        # This would check against delivery stop locations, depot boundaries, etc.
        
        return {
            "vehicle_id": vehicle_id,
            "current_position": {
                "latitude": latest_position.latitude,
                "longitude": latest_position.longitude
            },
            "geofence_status": "outside",  # Would be calculated based on actual geofences
            "nearest_stop": None,  # Would find nearest delivery stop
            "distance_to_stop": None  # Distance in miles
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking geofence status: {e}")
        raise HTTPException(status_code=500, detail="Failed to check geofence status")

@router.post("/batch-positions")
async def ingest_batch_gps_positions(positions: List[GPSPositionCreate]):
    """
    Ingest multiple GPS positions at once (for bulk updates or catch-up)
    
    Useful for mobile apps that cache GPS data and upload in batches
    when connectivity is restored.
    """
    try:
        results = []
        for position_data in positions:
            result = await gps_service.ingest_gps_data(position_data)
            results.append(result)
        
        return {
            "message": f"Successfully ingested {len(results)} GPS positions",
            "processed_count": len(results),
            "positions": results
        }
        
    except Exception as e:
        logger.error(f"Error ingesting batch GPS positions: {e}")
        raise HTTPException(status_code=500, detail="Failed to process batch GPS data")

@router.get("/health")
async def gps_health_check():
    """Health check endpoint for GPS tracking service"""
    try:
        # Check database connectivity
        live_positions = await gps_service.get_live_positions()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "active_vehicles": len(live_positions),
            "websocket_clients": len(gps_service.connected_clients),
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"GPS health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )