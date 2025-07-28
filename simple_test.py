#!/usr/bin/env python3
"""
Simple test script for FlowLogic RouteAI Core Functionality
Tests the basic routing algorithm without external dependencies
"""

import json
import math
from typing import List, Dict, Tuple, Optional

class Location:
    def __init__(self, lat: float, lng: float, address: str = ""):
        self.lat = lat
        self.lng = lng
        self.address = address
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance using Haversine formula (km)"""
        R = 6371  # Earth's radius in kilometers
        
        lat1, lng1 = math.radians(self.lat), math.radians(self.lng)
        lat2, lng2 = math.radians(other.lat), math.radians(other.lng)
        
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c

class Stop:
    def __init__(self, id: str, location: Location, service_time: int = 15):
        self.id = id
        self.location = location
        self.service_time = service_time  # minutes
    
    def __repr__(self):
        return f"Stop({self.id}, {self.location.address})"

class Truck:
    def __init__(self, id: str, capacity: int, start_location: Location):
        self.id = id
        self.capacity = capacity
        self.start_location = start_location
        self.route: List[Stop] = []
        self.total_distance = 0.0
        self.total_time = 0
    
    def add_stop(self, stop: Stop):
        if len(self.route) < self.capacity:
            self.route.append(stop)
            return True
        return False
    
    def calculate_route_stats(self):
        """Calculate total distance and time for the route"""
        if not self.route:
            return
        
        total_distance = 0.0
        total_time = 0
        current_location = self.start_location
        
        for stop in self.route:
            # Travel distance and time
            distance = current_location.distance_to(stop.location)
            total_distance += distance
            total_time += int(distance * 2)  # Assume 30 km/h average speed
            
            # Service time
            total_time += stop.service_time
            current_location = stop.location
        
        # Return to start
        total_distance += current_location.distance_to(self.start_location)
        total_time += int(current_location.distance_to(self.start_location) * 2)
        
        self.total_distance = total_distance
        self.total_time = total_time

class SimpleRouteOptimizer:
    """Basic nearest neighbor routing algorithm"""
    
    def __init__(self):
        self.name = "Simple Nearest Neighbor"
    
    def optimize_routes(self, trucks: List[Truck], stops: List[Stop]) -> Dict:
        """
        Simple nearest neighbor algorithm for vehicle routing
        """
        unassigned_stops = stops.copy()
        results = []
        
        for truck in trucks:
            truck.route = []
            current_location = truck.start_location
            
            # Assign stops using nearest neighbor
            while unassigned_stops and len(truck.route) < truck.capacity:
                # Find nearest unassigned stop
                nearest_stop = None
                min_distance = float('inf')
                
                for stop in unassigned_stops:
                    distance = current_location.distance_to(stop.location)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_stop = stop
                
                if nearest_stop:
                    truck.route.append(nearest_stop)
                    unassigned_stops.remove(nearest_stop)
                    current_location = nearest_stop.location
            
            # Calculate route statistics
            truck.calculate_route_stats()
            
            # Add to results
            results.append({
                "truck_id": truck.id,
                "stops": [{"id": s.id, "address": s.location.address} for s in truck.route],
                "total_distance_km": round(truck.total_distance, 2),
                "total_time_minutes": truck.total_time,
                "efficiency_score": round(len(truck.route) / max(truck.total_distance, 1), 2)
            })
        
        return {
            "success": True,
            "algorithm": self.name,
            "routes": results,
            "total_stops_assigned": sum(len(r["stops"]) for r in results),
            "total_distance_km": sum(r["total_distance_km"] for r in results),
            "unassigned_stops": len(unassigned_stops)
        }

def create_test_data():
    """Create sample test data"""
    
    # Depot location (downtown area)
    depot = Location(40.7580, -73.9855, "New York City Depot")
    
    # Sample delivery stops around NYC
    stops = [
        Stop("S001", Location(40.7505, -73.9934, "Times Square")),
        Stop("S002", Location(40.7614, -73.9776, "Central Park South")),
        Stop("S003", Location(40.7527, -73.9772, "5th Avenue")),
        Stop("S004", Location(40.7282, -74.0776, "Brooklyn Bridge")),
        Stop("S005", Location(40.7488, -73.9857, "Empire State Building")),
        Stop("S006", Location(40.7519, -73.9777, "Rockefeller Center")),
        Stop("S007", Location(40.7408, -74.0060, "Greenwich Village")),
        Stop("S008", Location(40.7282, -73.9942, "SoHo")),
        Stop("S009", Location(40.7686, -73.9918, "Upper West Side")),
        Stop("S010", Location(40.7736, -73.9566, "Upper East Side"))
    ]
    
    # Sample trucks
    trucks = [
        Truck("T001", capacity=5, start_location=depot),
        Truck("T002", capacity=5, start_location=depot),
        Truck("T003", capacity=4, start_location=depot)
    ]
    
    return trucks, stops

def run_routing_test():
    """Run a complete routing test"""
    print("🚛 FlowLogic RouteAI - Simple Test")
    print("=" * 50)
    
    # Create test data
    print("📍 Creating test data...")
    trucks, stops = create_test_data()
    print(f"   - Trucks: {len(trucks)}")
    print(f"   - Stops: {len(stops)}")
    
    # Initialize optimizer
    print("\n🧠 Initializing route optimizer...")
    optimizer = SimpleRouteOptimizer()
    
    # Optimize routes
    print("\n⚡ Optimizing routes...")
    results = optimizer.optimize_routes(trucks, stops)
    
    # Display results
    print(f"\n✅ Routing Results ({results['algorithm']}):")
    print("-" * 40)
    
    for i, route in enumerate(results['routes']):
        print(f"\n🚛 Truck {route['truck_id']}:")
        print(f"   Stops: {len(route['stops'])}")
        print(f"   Distance: {route['total_distance_km']} km")
        print(f"   Time: {route['total_time_minutes']} minutes")
        print(f"   Efficiency: {route['efficiency_score']} stops/km")
        
        if route['stops']:
            print("   Route:")
            for j, stop in enumerate(route['stops'], 1):
                print(f"     {j}. {stop['address']}")
    
    print(f"\n📊 Summary:")
    print(f"   Total stops assigned: {results['total_stops_assigned']} / {len(stops)}")
    print(f"   Total distance: {results['total_distance_km']} km")
    print(f"   Unassigned stops: {results['unassigned_stops']}")
    
    return results

def test_api_format():
    """Test API-compatible request/response format"""
    print("\n🌐 Testing API Format...")
    print("-" * 30)
    
    # Sample API request
    api_request = {
        "trucks": [
            {"id": "T001", "capacity": 5, "start_lat": 40.7580, "start_lng": -73.9855},
            {"id": "T002", "capacity": 3, "start_lat": 40.7580, "start_lng": -73.9855}
        ],
        "stops": [
            {"id": "S001", "lat": 40.7505, "lng": -73.9934, "address": "Times Square"},
            {"id": "S002", "lat": 40.7614, "lng": -73.9776, "address": "Central Park"},
            {"id": "S003", "lat": 40.7527, "lng": -73.9772, "address": "5th Avenue"},
            {"id": "S004", "lat": 40.7282, "lng": -74.0776, "address": "Brooklyn Bridge"}
        ]
    }
    
    print("Sample API Request:")
    print(json.dumps(api_request, indent=2))
    
    # Convert to internal format
    trucks = []
    for truck_data in api_request["trucks"]:
        depot = Location(truck_data["start_lat"], truck_data["start_lng"], "Depot")
        truck = Truck(truck_data["id"], truck_data["capacity"], depot)
        trucks.append(truck)
    
    stops = []
    for stop_data in api_request["stops"]:
        location = Location(stop_data["lat"], stop_data["lng"], stop_data["address"])
        stop = Stop(stop_data["id"], location)
        stops.append(stop)
    
    # Process
    optimizer = SimpleRouteOptimizer()
    results = optimizer.optimize_routes(trucks, stops)
    
    print("\nAPI Response:")
    print(json.dumps(results, indent=2))
    
    return results

if __name__ == "__main__":
    try:
        # Run basic routing test
        results = run_routing_test()
        
        # Test API format
        api_results = test_api_format()
        
        print("\n🎉 All tests completed successfully!")
        print("\n💡 Next Steps:")
        print("   1. Install Docker and run: docker-compose up -d")
        print("   2. Access API at: http://localhost:8001/docs")
        print("   3. Try the /route endpoint with the sample data above")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()