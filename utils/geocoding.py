from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from typing import Tuple, Optional, Dict
import logging
import time
from functools import lru_cache

logger = logging.getLogger(__name__)


class GeocodingService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="flowlogic_routeai_v1")
        self._cache = {}
    
    @lru_cache(maxsize=1000)
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to lat/lon coordinates"""
        try:
            if address in self._cache:
                return self._cache[address]
            
            time.sleep(1)  # Rate limiting for Nominatim
            location = self.geolocator.geocode(address)
            
            if location:
                coords = (location.latitude, location.longitude)
                self._cache[address] = coords
                logger.info(f"Geocoded '{address}' to {coords}")
                return coords
            else:
                logger.warning(f"Could not geocode address: {address}")
                return None
                
        except Exception as e:
            logger.error(f"Geocoding error for '{address}': {e}")
            return None
    
    def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance in miles between two coordinates"""
        try:
            return geodesic(coord1, coord2).miles
        except Exception as e:
            logger.error(f"Distance calculation error: {e}")
            return 0.0
    
    def create_distance_matrix(self, locations: Dict[str, Tuple[float, float]]) -> Dict[Tuple[str, str], float]:
        """Create a distance matrix for all location pairs"""
        matrix = {}
        location_ids = list(locations.keys())
        
        for i, loc1_id in enumerate(location_ids):
            for j, loc2_id in enumerate(location_ids):
                if i != j:
                    coord1 = locations[loc1_id]
                    coord2 = locations[loc2_id]
                    distance = self.calculate_distance(coord1, coord2)
                    matrix[(loc1_id, loc2_id)] = distance
                else:
                    matrix[(loc1_id, loc2_id)] = 0.0
        
        return matrix