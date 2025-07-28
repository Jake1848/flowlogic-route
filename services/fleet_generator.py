from typing import List, Dict, Set
from models.models import Truck, Stop, TruckType, SpecialConstraint
from datetime import time
import logging

logger = logging.getLogger(__name__)


class FleetGenerator:
    """AI-powered fleet generator for autonomous truck routing"""
    
    def __init__(self):
        self.default_depot = "1000 Distribution Center Dr, Atlanta, GA"
        
        # Fleet templates based on common logistics scenarios
        self.fleet_templates = {
            "small": {
                "count": 2,
                "capacity": [8, 10],
                "types": [TruckType.DRY, TruckType.REFRIGERATED]
            },
            "medium": {
                "count": 3,
                "capacity": [10, 8, 12],
                "types": [TruckType.DRY, TruckType.REFRIGERATED, TruckType.FLATBED]
            },
            "large": {
                "count": 4,
                "capacity": [10, 8, 12, 9],
                "types": [TruckType.DRY, TruckType.REFRIGERATED, TruckType.FLATBED, TruckType.FROZEN]
            },
            "specialized": {
                "count": 5,
                "capacity": [10, 8, 12, 9, 6],
                "types": [TruckType.DRY, TruckType.REFRIGERATED, TruckType.FLATBED, TruckType.FROZEN, TruckType.HAZMAT]
            }
        }
    
    def generate_default_fleet(self, stops: List[Stop], 
                             constraints: Dict = None,
                             depot_address: str = None) -> List[Truck]:
        """Generate optimal truck fleet based on stops analysis"""
        logger.info(f"Generating intelligent fleet for {len(stops)} stops")
        
        # Analyze stops to determine fleet requirements
        fleet_analysis = self._analyze_stop_requirements(stops)
        
        # Apply constraint-based fleet modifications
        if constraints:
            fleet_analysis = self._apply_constraints_to_fleet_analysis(fleet_analysis, constraints)
        
        # Select appropriate fleet template
        template_size = self._determine_fleet_size(stops, constraints)
        template = self.fleet_templates[template_size]
        
        # Generate truck fleet
        trucks = []
        depot = depot_address or self.default_depot
        
        # Ensure we have the right truck types for the stops
        required_types = fleet_analysis["required_types"]
        truck_types = self._optimize_truck_types(required_types, template["types"], template["count"])
        
        # Apply constraint-based truck filtering
        if constraints and "required_truck_types" in constraints:
            required_constraints = [getattr(TruckType, t.upper(), None) for t in constraints["required_truck_types"]]
            truck_types = [t for t in truck_types if t in required_constraints]
            if not truck_types:  # Fallback if no matches
                truck_types = required_constraints[:1]
        
        for i in range(len(truck_types)):
            truck_id = chr(65 + i)  # A, B, C, D...
            capacity = template["capacity"][i] if i < len(template["capacity"]) else 10
            
            # Adjust capacity based on stop requirements and constraints
            if fleet_analysis["max_pallets_per_stop"] > capacity:
                capacity = min(fleet_analysis["max_pallets_per_stop"] + 2, 20)
            
            # Apply constraint-based capacity adjustments
            if constraints and "max_pallets_per_truck" in constraints:
                capacity = min(capacity, constraints["max_pallets_per_truck"])
            
            truck = Truck(
                truck_id=truck_id,
                depot_address=depot,
                max_pallets=capacity,
                truck_type=truck_types[i],
                shift_start=self._determine_shift_start(stops, constraints),
                shift_end=self._determine_shift_end(stops, constraints),
                cost_per_mile=self._determine_cost_per_mile(truck_types[i], constraints),
                avg_speed_mph=self._determine_average_speed(constraints)
            )
            
            trucks.append(truck)
        
        # Apply cost optimization if needed
        if constraints and "cost_optimization_targets" in constraints:
            trucks = self._optimize_fleet_for_cost(trucks, constraints["cost_optimization_targets"])
        
        logger.info(f"Generated {len(trucks)} intelligent trucks: {[f'{t.truck_id}({t.truck_type.value},{t.max_pallets}p,${t.cost_per_mile}/mi)' for t in trucks]}")
        return trucks
    
    def _apply_constraints_to_fleet_analysis(self, analysis: Dict, constraints: Dict) -> Dict:
        """Apply constraints to modify fleet analysis"""
        modified_analysis = analysis.copy()
        
        # Adjust for route efficiency goals
        if "route_efficiency_goals" in constraints:
            goals = constraints["route_efficiency_goals"]
            if "minimize_cost" in goals:
                # Prefer smaller, more efficient trucks
                modified_analysis["cost_optimization"] = True
            if "minimize_time" in goals:
                # Prefer faster trucks or more trucks for parallel delivery
                modified_analysis["time_optimization"] = True
            if "minimize_distance" in goals:
                # Prefer centralized depot strategy
                modified_analysis["distance_optimization"] = True
        
        # Apply truck count constraints
        if "max_stops_per_truck" in constraints:
            max_stops = constraints["max_stops_per_truck"]
            min_trucks_needed = len(analysis.get("stops", [])) // max_stops + 1
            modified_analysis["min_truck_count"] = min_trucks_needed
        
        return modified_analysis
    
    def _determine_cost_per_mile(self, truck_type: TruckType, constraints: Dict = None) -> float:
        """Determine cost per mile based on truck type and constraints"""
        base_costs = {
            TruckType.DRY: 2.5,
            TruckType.REFRIGERATED: 3.2,
            TruckType.FROZEN: 3.8,
            TruckType.HAZMAT: 4.5,
            TruckType.FLATBED: 2.8
        }
        
        base_cost = base_costs.get(truck_type, 2.5)
        
        # Apply fuel efficiency optimization
        if constraints and constraints.get("fuel_efficiency_priority"):
            base_cost *= 0.85  # 15% reduction for fuel-efficient operations
        
        # Apply cost optimization
        if constraints and "cost_optimization_targets" in constraints:
            base_cost *= 0.9  # 10% reduction for cost-optimized fleet
        
        return round(base_cost, 2)
    
    def _determine_average_speed(self, constraints: Dict = None) -> float:
        """Determine average speed based on constraints"""
        base_speed = 45.0
        
        if constraints:
            # Faster speed for time optimization
            if "route_efficiency_goals" in constraints and "minimize_time" in constraints["route_efficiency_goals"]:
                base_speed = 50.0
            
            # Slower speed for fuel efficiency
            if constraints.get("fuel_efficiency_priority"):
                base_speed = 42.0
            
            # Account for area restrictions (slower in restricted areas)
            if "avoid_areas" in constraints:
                base_speed = 43.0  # Slightly slower due to routing around areas
        
        return base_speed
    
    def _optimize_fleet_for_cost(self, trucks: List[Truck], cost_targets: Dict) -> List[Truck]:
        """Optimize fleet composition for cost targets"""
        if "max_total_cost" in cost_targets:
            target_cost = cost_targets["max_total_cost"]
            
            # Estimate route distance (rough approximation)
            estimated_total_miles = len(trucks) * 80  # Assume 80 miles average per truck
            current_estimated_cost = sum(truck.cost_per_mile * (estimated_total_miles / len(trucks)) for truck in trucks)
            
            if current_estimated_cost > target_cost:
                # Reduce truck count or use more efficient trucks
                reduction_factor = target_cost / current_estimated_cost
                
                if reduction_factor < 0.8:
                    # Remove a truck if significant reduction needed
                    trucks = trucks[:-1] if len(trucks) > 1 else trucks
                    logger.info(f"Reduced fleet size for cost optimization: target ${target_cost}")
                else:
                    # Improve efficiency of existing trucks
                    for truck in trucks:
                        truck.cost_per_mile *= reduction_factor
                    logger.info(f"Reduced truck operating costs for cost optimization: target ${target_cost}")
        
        return trucks
    
    def _analyze_stop_requirements(self, stops: List[Stop]) -> Dict:
        """Analyze stops to understand fleet requirements"""
        total_pallets = sum(stop.pallets for stop in stops)
        max_pallets_per_stop = max(stop.pallets for stop in stops) if stops else 0
        
        # Analyze special constraints
        constraints_needed = set()
        constraint_counts = {}
        
        for stop in stops:
            if stop.special_constraint != SpecialConstraint.NONE:
                constraints_needed.add(stop.special_constraint)
                constraint_counts[stop.special_constraint] = constraint_counts.get(stop.special_constraint, 0) + 1
        
        # Determine required truck types
        required_types = [TruckType.DRY]  # Always need at least one dry truck
        
        if SpecialConstraint.REFRIGERATED in constraints_needed:
            required_types.append(TruckType.REFRIGERATED)
        
        if SpecialConstraint.FROZEN in constraints_needed:
            required_types.append(TruckType.FROZEN)
        
        if SpecialConstraint.HAZMAT in constraints_needed:
            required_types.append(TruckType.HAZMAT)
        
        if SpecialConstraint.HEAVY in constraints_needed:
            required_types.append(TruckType.FLATBED)
        
        # Time window analysis
        earliest_start = min((stop.time_window_start for stop in stops), default=time(8, 0))
        latest_end = max((stop.time_window_end for stop in stops), default=time(17, 0))
        
        return {
            "total_pallets": total_pallets,
            "max_pallets_per_stop": max_pallets_per_stop,
            "required_types": required_types,
            "constraint_counts": constraint_counts,
            "earliest_delivery": earliest_start,
            "latest_delivery": latest_end,
            "delivery_spread_hours": (latest_end.hour - earliest_start.hour)
        }
    
    def _determine_fleet_size(self, stops: List[Stop], constraints: Dict = None) -> str:
        """Determine appropriate fleet template size"""
        stop_count = len(stops)
        constraint_diversity = len(set(stop.special_constraint for stop in stops))
        
        # Consider constraints that might require more trucks
        max_stops_per_truck = None
        if constraints:
            max_stops_per_truck = constraints.get("max_stops_per_truck")
        
        # Default sizing logic
        if stop_count <= 5:
            return "small"
        elif stop_count <= 12:
            return "medium" 
        elif stop_count <= 20:
            return "large"
        else:
            return "specialized"
        
        # Adjust for constraint diversity
        if constraint_diversity >= 4:
            if stop_count <= 8:
                return "medium"
            elif stop_count <= 15:
                return "large"
            else:
                return "specialized"
    
    def _optimize_truck_types(self, required_types: List[TruckType], 
                            template_types: List[TruckType], 
                            truck_count: int) -> List[TruckType]:
        """Optimize truck type mix for the required stops"""
        optimized_types = []
        
        # Ensure all required types are included
        for req_type in required_types:
            if req_type not in optimized_types:
                optimized_types.append(req_type)
        
        # Fill remaining slots with template types or additional dry trucks
        while len(optimized_types) < truck_count:
            for template_type in template_types:
                if len(optimized_types) >= truck_count:
                    break
                if template_type not in optimized_types:
                    optimized_types.append(template_type)
            
            # If we still need more trucks, add additional dry trucks
            if len(optimized_types) < truck_count:
                optimized_types.append(TruckType.DRY)
        
        return optimized_types[:truck_count]
    
    def _determine_shift_start(self, stops: List[Stop], constraints: Dict = None) -> time:
        """Determine optimal shift start time"""
        if not stops:
            return time(7, 0)
        
        earliest_delivery = min(stop.time_window_start for stop in stops)
        
        # Give trucks 1 hour prep time before first delivery
        start_hour = max(earliest_delivery.hour - 1, 6)  # No earlier than 6 AM
        
        # Check constraints
        if constraints:
            if constraints.get("prioritize_morning"):
                start_hour = 6
            elif "preferred_delivery_window" in constraints:
                # Parse time window from constraints if available
                window = constraints["preferred_delivery_window"]
                if "07:00" in window or "7:00" in window:
                    start_hour = 6
        
        return time(start_hour, 0)
    
    def _determine_shift_end(self, stops: List[Stop], constraints: Dict = None) -> time:
        """Determine optimal shift end time"""
        if not stops:
            return time(15, 0)
        
        latest_delivery = max(stop.time_window_end for stop in stops)
        
        # Give trucks 1 hour buffer after last delivery
        end_hour = min(latest_delivery.hour + 1, 18)  # No later than 6 PM
        
        # Check constraints for maximum route hours
        if constraints and "max_route_hours" in constraints:
            max_hours = constraints["max_route_hours"]
            start_time = self._determine_shift_start(stops, constraints)
            end_hour = min(start_time.hour + int(max_hours), 18)
        
        return time(end_hour, 0)
    
    def auto_assign_truck_types(self, stops: List[Stop]) -> Dict[int, TruckType]:
        """Automatically assign the best truck type for each stop"""
        assignments = {}
        
        for stop in stops:
            if stop.special_constraint == SpecialConstraint.FROZEN:
                assignments[stop.stop_id] = TruckType.FROZEN
            elif stop.special_constraint == SpecialConstraint.REFRIGERATED:
                assignments[stop.stop_id] = TruckType.REFRIGERATED
            elif stop.special_constraint == SpecialConstraint.HAZMAT:
                assignments[stop.stop_id] = TruckType.HAZMAT
            elif stop.special_constraint == SpecialConstraint.HEAVY:
                assignments[stop.stop_id] = TruckType.FLATBED
            else:
                assignments[stop.stop_id] = TruckType.DRY
        
        return assignments
    
    def suggest_fleet_modifications(self, stops: List[Stop], 
                                  current_trucks: List[Truck],
                                  unassigned_stops: List[int]) -> Dict[str, any]:
        """Suggest modifications to existing fleet to handle unassigned stops"""
        suggestions = {
            "add_trucks": [],
            "modify_trucks": [],
            "reasoning": []
        }
        
        if not unassigned_stops:
            return suggestions
        
        unassigned_stop_objs = [s for s in stops if s.stop_id in unassigned_stops]
        
        # Analyze why stops are unassigned
        capacity_issues = []
        type_issues = []
        time_issues = []
        
        for stop in unassigned_stop_objs:
            # Check capacity
            if all(stop.pallets > truck.max_pallets for truck in current_trucks):
                capacity_issues.append(stop)
            
            # Check truck type compatibility
            required_type = self._get_required_truck_type(stop)
            available_types = [truck.truck_type for truck in current_trucks]
            if required_type not in available_types:
                type_issues.append(stop)
            
            # Check time coverage
            covered = any(
                not (truck.shift_end < stop.time_window_start or 
                     truck.shift_start > stop.time_window_end)
                for truck in current_trucks
            )
            if not covered:
                time_issues.append(stop)
        
        # Generate suggestions
        if capacity_issues:
            max_needed = max(stop.pallets for stop in capacity_issues)
            suggestions["add_trucks"].append({
                "type": TruckType.DRY,
                "capacity": max_needed + 2,
                "reason": f"Handle {len(capacity_issues)} stops requiring {max_needed}+ pallets"
            })
        
        if type_issues:
            needed_types = set(self._get_required_truck_type(stop) for stop in type_issues)
            for truck_type in needed_types:
                suggestions["add_trucks"].append({
                    "type": truck_type,
                    "capacity": 10,
                    "reason": f"Handle {truck_type.value} cargo requirements"
                })
        
        if time_issues:
            earliest = min(stop.time_window_start for stop in time_issues)
            latest = max(stop.time_window_end for stop in time_issues)
            suggestions["modify_trucks"].append({
                "action": "extend_shifts",
                "new_start": earliest,
                "new_end": latest,
                "reason": f"Cover time windows for {len(time_issues)} stops"
            })
        
        return suggestions
    
    def _get_required_truck_type(self, stop: Stop) -> TruckType:
        """Get the required truck type for a stop"""
        if stop.special_constraint == SpecialConstraint.FROZEN:
            return TruckType.FROZEN
        elif stop.special_constraint == SpecialConstraint.REFRIGERATED:
            return TruckType.REFRIGERATED
        elif stop.special_constraint == SpecialConstraint.HAZMAT:
            return TruckType.HAZMAT
        elif stop.special_constraint == SpecialConstraint.HEAVY:
            return TruckType.FLATBED
        else:
            return TruckType.DRY