from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime, timedelta, time
from models.models import Stop, Truck, TruckRoute, RouteStop, SpecialConstraint, TruckType
from utils.geocoding import GeocodingService
import logging
from dataclasses import dataclass
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

logger = logging.getLogger(__name__)


@dataclass
class RouteSegment:
    from_location: str
    to_location: str
    distance_miles: float
    travel_time_minutes: float


class RoutingEngine:
    def __init__(self):
        self.geocoding_service = GeocodingService()
        self.compatibility_rules = {
            TruckType.DRY: [SpecialConstraint.NONE, SpecialConstraint.FRAGILE, SpecialConstraint.HEAVY],
            TruckType.REFRIGERATED: [SpecialConstraint.NONE, SpecialConstraint.REFRIGERATED, SpecialConstraint.FRAGILE],
            TruckType.FROZEN: [SpecialConstraint.NONE, SpecialConstraint.FROZEN, SpecialConstraint.REFRIGERATED],
            TruckType.HAZMAT: [SpecialConstraint.HAZMAT],
            TruckType.FLATBED: [SpecialConstraint.HEAVY, SpecialConstraint.NONE]
        }
    
    def route_trucks(self, stops: List[Stop], trucks: List[Truck]) -> Dict[str, TruckRoute]:
        """Main routing algorithm"""
        logger.info(f"Starting routing for {len(stops)} stops and {len(trucks)} trucks")
        
        # Step 1: Geocode all addresses
        self._geocode_locations(stops, trucks)
        
        # Step 2: Create distance matrix
        distance_matrix = self._create_full_distance_matrix(stops, trucks)
        
        # Step 3: Filter compatible stops for each truck
        truck_compatible_stops = self._get_compatible_stops(trucks, stops)
        
        # Step 4: Run optimization for each truck
        truck_routes = {}
        assigned_stops = set()
        
        for truck in sorted(trucks, key=lambda t: t.max_pallets, reverse=True):
            available_stops = [s for s in truck_compatible_stops[truck.truck_id] 
                             if s.stop_id not in assigned_stops]
            
            if not available_stops:
                truck_routes[truck.truck_id] = self._create_empty_route(truck)
                continue
            
            route = self._optimize_truck_route(truck, available_stops, distance_matrix)
            truck_routes[truck.truck_id] = route
            
            for stop in route.stops:
                assigned_stops.add(stop.stop_id)
        
        return truck_routes
    
    def _geocode_locations(self, stops: List[Stop], trucks: List[Truck]):
        """Geocode all stop and depot addresses"""
        logger.info(f"Geocoding {len(stops)} stops and {len(trucks)} trucks")
        
        for stop in stops:
            coords = self.geocoding_service.geocode_address(stop.address)
            if coords:
                stop.latitude, stop.longitude = coords
                logger.info(f"Stop {stop.stop_id} geocoded to {coords}")
            else:
                logger.warning(f"Failed to geocode stop {stop.stop_id}: {stop.address}")
        
        for truck in trucks:
            coords = self.geocoding_service.geocode_address(truck.depot_address)
            if coords:
                truck.depot_latitude, truck.depot_longitude = coords
                logger.info(f"Truck {truck.truck_id} depot geocoded to {coords}")
            else:
                logger.warning(f"Failed to geocode truck {truck.truck_id} depot: {truck.depot_address}")
    
    def _create_full_distance_matrix(self, stops: List[Stop], trucks: List[Truck]) -> Dict[Tuple[str, str], float]:
        """Create distance matrix for all locations"""
        locations = {}
        
        # Add depot locations
        for truck in trucks:
            if truck.depot_latitude and truck.depot_longitude:
                locations[f"depot_{truck.truck_id}"] = (truck.depot_latitude, truck.depot_longitude)
        
        # Add stop locations
        for stop in stops:
            if stop.latitude and stop.longitude:
                locations[f"stop_{stop.stop_id}"] = (stop.latitude, stop.longitude)
        
        return self.geocoding_service.create_distance_matrix(locations)
    
    def _get_compatible_stops(self, trucks: List[Truck], stops: List[Stop]) -> Dict[str, List[Stop]]:
        """Determine which stops are compatible with each truck"""
        compatible_stops = {}
        
        for truck in trucks:
            compatible = []
            allowed_constraints = self.compatibility_rules.get(truck.truck_type, [])
            
            for stop in stops:
                # Check special constraint compatibility
                if stop.special_constraint in allowed_constraints:
                    # Check capacity
                    if stop.pallets <= truck.max_pallets:
                        # Check time window overlap with shift
                        if self._check_time_compatibility(truck, stop):
                            compatible.append(stop)
            
            compatible_stops[truck.truck_id] = compatible
            logger.info(f"Truck {truck.truck_id} compatible with {len(compatible)} stops")
        
        return compatible_stops
    
    def _check_time_compatibility(self, truck: Truck, stop: Stop) -> bool:
        """Check if stop time window overlaps with truck shift"""
        # Convert times to minutes since midnight for easier comparison
        truck_start_mins = truck.shift_start.hour * 60 + truck.shift_start.minute
        truck_end_mins = truck.shift_end.hour * 60 + truck.shift_end.minute
        stop_start_mins = stop.time_window_start.hour * 60 + stop.time_window_start.minute
        stop_end_mins = stop.time_window_end.hour * 60 + stop.time_window_end.minute
        
        # Check for overlap
        return not (truck_end_mins < stop_start_mins or truck_start_mins > stop_end_mins)
    
    def _optimize_truck_route(self, truck: Truck, stops: List[Stop], 
                            distance_matrix: Dict[Tuple[str, str], float]) -> TruckRoute:
        """Optimize route for a single truck using OR-Tools"""
        if not stops:
            return self._create_empty_route(truck)
        
        # Create simplified distance matrix for this truck's stops
        locations = [f"depot_{truck.truck_id}"] + [f"stop_{s.stop_id}" for s in stops]
        n_locations = len(locations)
        
        # Build matrix
        matrix = []
        for i in range(n_locations):
            row = []
            for j in range(n_locations):
                if i == j:
                    row.append(0)
                else:
                    dist = distance_matrix.get((locations[i], locations[j]), 50)  # Default 50 miles
                    # Ensure dist is a valid number before conversion
                    try:
                        if isinstance(dist, (int, float)) and dist >= 0:
                            row.append(int(dist * 100))  # Convert to integers for OR-Tools
                        else:
                            row.append(5000)  # Default 50 miles * 100
                    except (ValueError, TypeError):
                        row.append(5000)  # Default 50 miles * 100
            matrix.append(row)
        
        # Create routing model
        manager = pywrapcp.RoutingIndexManager(n_locations, 1, 0)
        routing = pywrapcp.RoutingModel(manager)
        
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return matrix[from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Add capacity constraint
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            if from_node == 0:  # Depot
                return 0
            return stops[from_node - 1].pallets
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            [truck.max_pallets],  # vehicle maximum capacities
            True,  # start cumul to zero
            'Capacity')
        
        # Add time window constraints
        time_dimension_name = 'Time'
        time_per_mile = 60 / truck.avg_speed_mph  # minutes per mile
        
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            try:
                distance_value = matrix[from_node][to_node]
                travel_time = int(distance_value * time_per_mile / 100)
            except (ValueError, TypeError):
                travel_time = 60  # Default 1 hour travel time
            service_time = 0 if to_node == 0 else stops[to_node - 1].service_time_minutes
            return travel_time + service_time
        
        time_callback_index = routing.RegisterTransitCallback(time_callback)
        
        # Set time windows
        time_windows = [(0, 24 * 60)]  # Depot open all day
        for stop in stops:
            start_mins = stop.time_window_start.hour * 60 + stop.time_window_start.minute
            end_mins = stop.time_window_end.hour * 60 + stop.time_window_end.minute
            time_windows.append((start_mins, end_mins))
        
        routing.AddDimension(
            time_callback_index,
            30,  # allow waiting time
            24 * 60,  # maximum time per vehicle
            False,  # Don't force start cumul to zero
            time_dimension_name)
        
        time_dimension = routing.GetDimensionOrDie(time_dimension_name)
        for location_idx, time_window in enumerate(time_windows):
            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
        
        # Solve
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
        search_parameters.time_limit.FromSeconds(5)
        
        solution = routing.SolveWithParameters(search_parameters)
        
        if solution:
            return self._extract_route_from_solution(truck, stops, routing, manager, solution, distance_matrix)
        else:
            # Fallback to greedy algorithm
            return self._greedy_route(truck, stops, distance_matrix)
    
    def _extract_route_from_solution(self, truck: Truck, stops: List[Stop], 
                                   routing, manager, solution,
                                   distance_matrix: Dict[Tuple[str, str], float]) -> TruckRoute:
        """Extract route from OR-Tools solution"""
        route_stops = []
        total_distance = 0
        total_pallets = 0
        
        index = routing.Start(0)
        current_time = truck.shift_start.hour * 60 + truck.shift_start.minute
        base_date = datetime.now().date()
        
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            next_index = solution.Value(routing.NextVar(index))
            next_node = manager.IndexToNode(next_index)
            
            if node > 0:  # Not depot
                stop = stops[node - 1]
                arrival_mins = current_time
                
                # Ensure arrival_mins is an integer for time() constructor
                try:
                    arrival_mins_int = int(arrival_mins) if isinstance(arrival_mins, (int, float)) else 480  # Default 8 AM
                    hours = arrival_mins_int // 60
                    minutes = arrival_mins_int % 60
                    # Ensure valid time ranges
                    hours = max(0, min(23, hours))
                    minutes = max(0, min(59, minutes))
                    arrival_time = datetime.combine(base_date, time(hours, minutes))
                except (ValueError, TypeError):
                    arrival_time = datetime.combine(base_date, time(8, 0))  # Default 8 AM
                departure_time = arrival_time + timedelta(minutes=stop.service_time_minutes)
                
                prev_location = f"depot_{truck.truck_id}" if len(route_stops) == 0 else f"stop_{route_stops[-1].stop_id}"
                curr_location = f"stop_{stop.stop_id}"
                distance = distance_matrix.get((prev_location, curr_location), 50)
                
                route_stop = RouteStop(
                    stop_id=stop.stop_id,
                    eta=arrival_time.strftime("%H:%M"),
                    arrival_time=arrival_time,
                    departure_time=departure_time,
                    distance_from_previous=distance,
                    notes=self._get_stop_notes(stop, len(route_stops) + 1),
                    latitude=stop.latitude,
                    longitude=stop.longitude,
                    address=stop.address,
                    pallets=stop.pallets,
                    time_window_start=stop.time_window_start.strftime("%H:%M"),
                    time_window_end=stop.time_window_end.strftime("%H:%M"),
                    estimated_arrival=arrival_time.strftime("%H:%M")
                )
                
                route_stops.append(route_stop)
                total_distance += distance
                total_pallets += stop.pallets
            
            if not routing.IsEnd(next_index) and next_node > 0:
                # Calculate travel time to next stop
                travel_time = distance_matrix.get(
                    (f"stop_{stops[node - 1].stop_id}" if node > 0 else f"depot_{truck.truck_id}",
                     f"stop_{stops[next_node - 1].stop_id}"),
                    50) * 60 / truck.avg_speed_mph
                current_time += travel_time + (stops[node - 1].service_time_minutes if node > 0 else 0)
            
            index = next_index
        
        # Add return to depot distance
        if route_stops:
            last_stop_location = f"stop_{route_stops[-1].stop_id}"
            depot_location = f"depot_{truck.truck_id}"
            return_distance = distance_matrix.get((last_stop_location, depot_location), 50)
            total_distance += return_distance
        
        total_time_hours = total_distance / truck.avg_speed_mph + len(route_stops) * 0.25
        
        return TruckRoute(
            truck_id=truck.truck_id,
            stops=route_stops,
            total_miles=round(total_distance, 1),
            total_time_hours=round(total_time_hours, 2),
            fuel_estimate=round(total_distance * truck.cost_per_mile, 2),
            utilization_percent=round((total_pallets / truck.max_pallets) * 100, 1),
            reasoning=self._generate_route_reasoning(truck, route_stops, stops),
            depot_latitude=truck.depot_latitude,
            depot_longitude=truck.depot_longitude,
            depot_address=truck.depot_address
        )
    
    def _greedy_route(self, truck: Truck, stops: List[Stop], 
                     distance_matrix: Dict[Tuple[str, str], float]) -> TruckRoute:
        """Fallback greedy routing algorithm"""
        route_stops = []
        remaining_stops = stops.copy()
        current_location = f"depot_{truck.truck_id}"
        current_time = truck.shift_start.hour * 60 + truck.shift_start.minute
        total_distance = 0
        total_pallets = 0
        base_date = datetime.now().date()
        
        while remaining_stops and total_pallets < truck.max_pallets:
            # Find nearest feasible stop
            best_stop = None
            best_distance = float('inf')
            
            for stop in remaining_stops:
                if total_pallets + stop.pallets > truck.max_pallets:
                    continue
                
                stop_location = f"stop_{stop.stop_id}"
                distance = distance_matrix.get((current_location, stop_location), 50)
                # Ensure distance is valid before calculations
                if not isinstance(distance, (int, float)) or distance < 0:
                    distance = 50  # Default 50 miles
                travel_time = distance * 60 / truck.avg_speed_mph
                arrival_time = current_time + travel_time
                
                # Check time window
                stop_start_mins = stop.time_window_start.hour * 60 + stop.time_window_start.minute
                stop_end_mins = stop.time_window_end.hour * 60 + stop.time_window_end.minute
                
                if arrival_time <= stop_end_mins and distance < best_distance:
                    best_stop = stop
                    best_distance = distance
            
            if not best_stop:
                break
            
            # Add stop to route
            try:
                if isinstance(best_distance, (int, float)) and best_distance >= 0:
                    arrival_mins = current_time + int(best_distance * 60 / truck.avg_speed_mph)
                else:
                    arrival_mins = current_time + 60  # Default 1 hour travel time
            except (ValueError, TypeError):
                arrival_mins = current_time + 60  # Default 1 hour travel time
            arrival_time = datetime.combine(base_date, time(arrival_mins // 60, arrival_mins % 60))
            departure_time = arrival_time + timedelta(minutes=best_stop.service_time_minutes)
            
            route_stop = RouteStop(
                stop_id=best_stop.stop_id,
                eta=arrival_time.strftime("%H:%M"),
                arrival_time=arrival_time,
                departure_time=departure_time,
                distance_from_previous=best_distance,
                notes=self._get_stop_notes(best_stop, len(route_stops) + 1),
                latitude=best_stop.latitude,
                longitude=best_stop.longitude,
                address=best_stop.address,
                pallets=best_stop.pallets,
                time_window_start=best_stop.time_window_start.strftime("%H:%M"),
                time_window_end=best_stop.time_window_end.strftime("%H:%M"),
                estimated_arrival=arrival_time.strftime("%H:%M")
            )
            
            route_stops.append(route_stop)
            total_distance += best_distance
            total_pallets += best_stop.pallets
            current_location = f"stop_{best_stop.stop_id}"
            current_time = arrival_mins + best_stop.service_time_minutes
            remaining_stops.remove(best_stop)
        
        # Add return distance
        if route_stops:
            return_distance = distance_matrix.get((current_location, f"depot_{truck.truck_id}"), 50)
            total_distance += return_distance
        
        total_time_hours = total_distance / truck.avg_speed_mph + len(route_stops) * 0.25
        
        return TruckRoute(
            truck_id=truck.truck_id,
            stops=route_stops,
            total_miles=round(total_distance, 1),
            total_time_hours=round(total_time_hours, 2),
            fuel_estimate=round(total_distance * truck.cost_per_mile, 2),
            utilization_percent=round((total_pallets / truck.max_pallets) * 100, 1),
            reasoning=self._generate_route_reasoning(truck, route_stops, stops),
            depot_latitude=truck.depot_latitude,
            depot_longitude=truck.depot_longitude,
            depot_address=truck.depot_address
        )
    
    def _create_empty_route(self, truck: Truck) -> TruckRoute:
        """Create empty route for truck with no stops"""
        return TruckRoute(
            truck_id=truck.truck_id,
            stops=[],
            total_miles=0,
            total_time_hours=0,
            fuel_estimate=0,
            utilization_percent=0,
            reasoning=f"No compatible stops found for {truck.truck_id}",
            depot_latitude=truck.depot_latitude,
            depot_longitude=truck.depot_longitude,
            depot_address=truck.depot_address
        )
    
    def _get_stop_notes(self, stop: Stop, position: int) -> str:
        """Generate notes for a stop"""
        notes = []
        
        if position == 1 and stop.special_constraint == SpecialConstraint.FRAGILE:
            notes.append("Fragile - loaded last for easy access")
        elif stop.special_constraint == SpecialConstraint.REFRIGERATED:
            notes.append("Temperature-controlled delivery")
        elif stop.special_constraint == SpecialConstraint.FROZEN:
            notes.append("Frozen goods - maintain cold chain")
        elif stop.special_constraint == SpecialConstraint.HAZMAT:
            notes.append("Hazmat - follow safety protocols")
        
        if stop.time_window_end.hour < 12:
            notes.append("Morning delivery required")
        
        return "; ".join(notes) if notes else "Standard delivery"
    
    def _generate_route_reasoning(self, truck: Truck, route_stops: List[RouteStop], 
                                all_stops: List[Stop]) -> str:
        """Generate natural language explanation of routing decisions"""
        if not route_stops:
            return f"Truck {truck.truck_id} has no assigned stops due to capacity or compatibility constraints."
        
        stop_ids = [rs.stop_id for rs in route_stops]
        assigned_stops = [s for s in all_stops if s.stop_id in stop_ids]
        
        reasons = []
        
        # Explain compatibility
        special_types = set(s.special_constraint for s in assigned_stops if s.special_constraint != SpecialConstraint.NONE)
        if special_types:
            reasons.append(f"assigned {', '.join(st.value for st in special_types)} goods matching truck type {truck.truck_type.value}")
        
        # Explain capacity utilization
        total_pallets = sum(s.pallets for s in assigned_stops)
        reasons.append(f"loaded {total_pallets}/{truck.max_pallets} pallets ({round(total_pallets/truck.max_pallets*100)}% capacity)")
        
        # Explain sequencing
        if any(s.special_constraint == SpecialConstraint.FRAGILE for s in assigned_stops):
            reasons.append("sequenced fragile items for optimal handling")
        
        # Time windows
        morning_stops = sum(1 for s in assigned_stops if s.time_window_end.hour <= 12)
        if morning_stops:
            reasons.append(f"prioritized {morning_stops} morning deliveries")
        
        return f"Truck {truck.truck_id} was {'; '.join(reasons)}."