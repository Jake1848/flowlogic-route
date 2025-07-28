import httpx
import os
from typing import List, Dict, Optional, Tuple
from models.models import Stop, Truck
import logging
from dotenv import load_dotenv
import asyncio

load_dotenv()
logger = logging.getLogger(__name__)


class RouteOptimizer:
    """Service for getting optimized routes using external APIs"""
    
    def __init__(self):
        self.graphhopper_api_key = os.getenv("GRAPHHOPPER_API_KEY")
        self.use_graphhopper = bool(self.graphhopper_api_key)
        
        if self.use_graphhopper:
            logger.info("Using GraphHopper for route optimization")
        else:
            logger.info("GraphHopper API key not found, using fallback routing")
    
    async def get_optimized_route(self, depot: Tuple[float, float], 
                                 stops: List[Tuple[float, float]]) -> Optional[Dict]:
        """Get optimized route from GraphHopper or fallback"""
        if self.use_graphhopper:
            return await self._graphhopper_route(depot, stops)
        else:
            return self._fallback_route(depot, stops)
    
    async def _graphhopper_route(self, depot: Tuple[float, float], 
                               stops: List[Tuple[float, float]]) -> Optional[Dict]:
        """Use GraphHopper Route Optimization API"""
        try:
            url = "https://graphhopper.com/api/1/vrp"
            
            # Build VRP problem
            vehicles = [{
                "vehicle_id": "vehicle1",
                "start_address": {
                    "location_id": "depot",
                    "lon": depot[1],
                    "lat": depot[0]
                },
                "return_to_depot": True
            }]
            
            services = []
            for i, (lat, lon) in enumerate(stops):
                services.append({
                    "id": f"stop_{i}",
                    "address": {
                        "location_id": f"loc_{i}",
                        "lon": lon,
                        "lat": lat
                    },
                    "size": [1]  # One unit of capacity
                })
            
            problem = {
                "vehicles": vehicles,
                "services": services,
                "objectives": [{
                    "type": "min",
                    "value": "transport_time"
                }]
            }
            
            headers = {
                "Authorization": f"Bearer {self.graphhopper_api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=problem, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    return self._parse_graphhopper_response(result)
                else:
                    logger.error(f"GraphHopper API error: {response.status_code}")
                    return self._fallback_route(depot, stops)
                    
        except Exception as e:
            logger.error(f"GraphHopper routing failed: {e}")
            return self._fallback_route(depot, stops)
    
    def _parse_graphhopper_response(self, response: Dict) -> Dict:
        """Parse GraphHopper VRP response"""
        try:
            solution = response.get("solution", {})
            routes = solution.get("routes", [])
            
            if routes and routes[0].get("activities"):
                activities = routes[0]["activities"]
                stop_sequence = []
                total_distance = 0
                
                for activity in activities:
                    if activity["type"] == "service":
                        stop_id = int(activity["id"].split("_")[1])
                        distance = activity.get("distance", 0) / 1609.34  # meters to miles
                        stop_sequence.append({
                            "stop_index": stop_id,
                            "distance": distance
                        })
                        total_distance += distance
                
                return {
                    "sequence": stop_sequence,
                    "total_distance": total_distance,
                    "optimized": True
                }
        except Exception as e:
            logger.error(f"Error parsing GraphHopper response: {e}")
        
        return None
    
    def _fallback_route(self, depot: Tuple[float, float], 
                       stops: List[Tuple[float, float]]) -> Dict:
        """Simple nearest neighbor routing as fallback"""
        if not stops:
            return {
                "sequence": [],
                "total_distance": 0,
                "optimized": False
            }
        
        # Nearest neighbor algorithm
        unvisited = list(range(len(stops)))
        current_pos = depot
        sequence = []
        total_distance = 0
        
        while unvisited:
            nearest_idx = None
            nearest_dist = float('inf')
            
            for idx in unvisited:
                dist = self._haversine_distance(current_pos, stops[idx])
                if dist < nearest_dist:
                    nearest_dist = dist
                    nearest_idx = idx
            
            sequence.append({
                "stop_index": nearest_idx,
                "distance": nearest_dist
            })
            total_distance += nearest_dist
            current_pos = stops[nearest_idx]
            unvisited.remove(nearest_idx)
        
        # Add return to depot
        return_dist = self._haversine_distance(current_pos, depot)
        total_distance += return_dist
        
        return {
            "sequence": sequence,
            "total_distance": total_distance,
            "optimized": False
        }
    
    def _haversine_distance(self, coord1: Tuple[float, float], 
                           coord2: Tuple[float, float]) -> float:
        """Calculate distance in miles between two coordinates"""
        from math import radians, cos, sin, asin, sqrt
        
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of Earth in miles
        r = 3959
        return c * r