from typing import List, Dict, Optional, Tuple, Any
from models.models import TruckRoute, Stop, Truck, RoutingResponse, SpecialConstraint, TruckType
from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
import re
import json
from datetime import time, datetime

load_dotenv()
logger = logging.getLogger(__name__)


class NaturalLanguageProcessor:
    """Enhanced AI-powered natural language processor for routing decisions"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.client = OpenAI(api_key=self.openai_api_key)
            self.use_llm = True
            logger.info("OpenAI API configured for enhanced explanations")
        else:
            self.client = None
            self.use_llm = False
            logger.info("Using rule-based natural language generation")
        
        # Enhanced routing patterns for complex constraint parsing
        self.route_patterns = {
            'highways': r'I-\d+|US-\d+|SR-\d+|highway \d+',
            'times': r'(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?',
            'distances': r'(\d+)\s*(miles?|mi|kilometers?|km)',
            'weights': r'(\d+)\s*(lbs?|pounds?|tons?|kg|kilograms?)',
            'pallets': r'(\d+)\s*(pallets?|boxes?|units?)',
            'percentages': r'(\d+)%',
            'priorities': r'(first|last|priority|urgent|rush|asap|immediately)',
            'avoidance': r'avoid|skip|bypass|exclude|not|don\'t',
            'time_windows': r'(\d{1,2}):?(\d{2})?\s*(am|pm)?\s*[-to]+\s*(\d{1,2}):?(\d{2})?\s*(am|pm)?'
        }
    
    def generate_routing_summary(self, routes: List[TruckRoute], 
                               unassigned_stops: List[int],
                               stops: List[Stop], 
                               trucks: List[Truck]) -> str:
        """Generate comprehensive routing summary"""
        if self.use_llm:
            return self._llm_summary(routes, unassigned_stops, stops, trucks)
        else:
            return self._rule_based_summary(routes, unassigned_stops, stops, trucks)
    
    def _rule_based_summary(self, routes: List[TruckRoute], 
                          unassigned_stops: List[int],
                          stops: List[Stop], 
                          trucks: List[Truck]) -> str:
        """Generate enhanced summary with actionable recommendations"""
        summary_parts = []
        
        # Overall statistics
        total_stops_assigned = sum(len(route.stops) for route in routes)
        total_stops = len(stops)
        total_miles = sum(route.total_miles for route in routes)
        total_fuel_cost = sum(route.fuel_estimate for route in routes)
        
        summary_parts.append(
            f"🚚 ROUTING SUMMARY: Successfully routed {total_stops_assigned} of {total_stops} stops "
            f"across {len(trucks)} trucks. Total distance: {total_miles:.1f} miles, "
            f"estimated fuel cost: ${total_fuel_cost:.2f}"
        )
        
        # Per-truck summaries with detailed analysis
        summary_parts.append("\n📋 TRUCK ASSIGNMENTS:")
        for route in routes:
            if route.stops:
                truck = next(t for t in trucks if t.truck_id == route.truck_id)
                overtime_risk = "⚠️ OVERTIME RISK" if route.total_time_hours > 8 else ""
                efficiency = "🔋 Efficient" if route.utilization_percent > 80 else "📦 Underutilized"
                
                summary_parts.append(
                    f"  • Truck {route.truck_id} ({truck.truck_type.value}): "
                    f"{len(route.stops)} stops, {route.total_miles:.1f} mi, "
                    f"{route.total_time_hours:.1f}h, {route.utilization_percent}% capacity {efficiency} {overtime_risk}"
                )
        
        # AI-powered optimization recommendations
        recommendations = self._generate_ai_recommendations(routes, unassigned_stops, stops, trucks)
        if recommendations:
            summary_parts.append(f"\n🧠 AI RECOMMENDATIONS:\n{recommendations}")
        
        # Unassigned stops with solutions
        if unassigned_stops:
            summary_parts.append(f"\n❌ UNASSIGNED STOPS ({len(unassigned_stops)}):")
            for stop_id in unassigned_stops:
                stop = next(s for s in stops if s.stop_id == stop_id)
                reason = self._get_unassigned_reason(stop, trucks)
                solution = self._suggest_solution(stop, trucks, routes)
                summary_parts.append(f"  - Stop {stop_id}: {reason}\n    💡 Solution: {solution}")
        
        return "\n".join(summary_parts)
    
    def _generate_ai_recommendations(self, routes: List[TruckRoute], 
                                   unassigned_stops: List[int],
                                   stops: List[Stop], 
                                   trucks: List[Truck]) -> str:
        """Generate actionable AI recommendations"""
        recommendations = []
        
        # Analyze utilization patterns
        avg_utilization = sum(r.utilization_percent for r in routes) / len(routes) if routes else 0
        high_util_trucks = [r for r in routes if r.utilization_percent > 90]
        low_util_trucks = [r for r in routes if r.utilization_percent < 50 and r.stops]
        
        # Route consolidation opportunities
        if len(low_util_trucks) >= 2:
            total_low_pallets = sum(len(r.stops) for r in low_util_trucks)
            recommendations.append(
                f"  • CONSOLIDATION: Combine {len(low_util_trucks)} underutilized trucks "
                f"({total_low_pallets} total stops) to free up {len(low_util_trucks)-1} trucks"
            )
        
        # Overtime prevention
        overtime_trucks = [r for r in routes if r.total_time_hours > 8]
        if overtime_trucks:
            for truck in overtime_trucks:
                excess_time = truck.total_time_hours - 8
                recommendations.append(
                    f"  • OVERTIME: Truck {truck.truck_id} exceeds 8h by {excess_time:.1f}h. "
                    f"Consider moving {len(truck.stops)//3} stops to another truck"
                )
        
        # Fuel efficiency improvements
        high_mile_trucks = [r for r in routes if r.total_miles > 150]
        if high_mile_trucks:
            for truck in high_mile_trucks:
                savings = (truck.total_miles - 150) * 2.5
                recommendations.append(
                    f"  • FUEL SAVINGS: Truck {truck.truck_id} route ({truck.total_miles:.1f} mi) "
                    f"could save ${savings:.2f} if reduced by route optimization"
                )
        
        # Capacity optimization
        if avg_utilization < 70:
            recommendations.append(
                f"  • CAPACITY: Average utilization is {avg_utilization:.1f}%. "
                f"Consider using {len([r for r in routes if r.stops])//2} fewer trucks or smaller vehicles"
            )
        
        # Load balancing
        max_stops = max((len(r.stops) for r in routes if r.stops), default=0)
        min_stops = min((len(r.stops) for r in routes if r.stops), default=0)
        if max_stops - min_stops > 3:
            recommendations.append(
                f"  • LOAD BALANCE: Stop distribution varies widely ({min_stops}-{max_stops} stops). "
                f"Rebalancing could improve overall efficiency"
            )
        
        # Special handling insights
        fragile_stops = [s for s in stops if s.special_constraint == SpecialConstraint.FRAGILE]
        if fragile_stops:
            fragile_routes = [r for r in routes if any(rs.stop_id in [fs.stop_id for fs in fragile_stops] for rs in r.stops)]
            if len(fragile_routes) > 1:
                recommendations.append(
                    f"  • FRAGILE HANDLING: {len(fragile_stops)} fragile stops spread across "
                    f"{len(fragile_routes)} trucks. Consider consolidating to minimize handling"
                )
        
        return "\n".join(recommendations) if recommendations else ""
    
    def _suggest_solution(self, stop: Stop, trucks: List[Truck], routes: List[TruckRoute]) -> str:
        """Suggest specific solutions for unassigned stops"""
        solutions = []
        
        # Check if capacity is the issue
        if all(stop.pallets > truck.max_pallets for truck in trucks):
            solutions.append("Add larger capacity truck or split delivery")
        
        # Check truck type compatibility
        compatible_types = []
        if stop.special_constraint == SpecialConstraint.REFRIGERATED:
            compatible_types = ["Refrigerated", "Frozen"]
        elif stop.special_constraint == SpecialConstraint.FROZEN:
            compatible_types = ["Frozen"]
        elif stop.special_constraint == SpecialConstraint.HAZMAT:
            compatible_types = ["Hazmat"]
        elif stop.special_constraint == SpecialConstraint.HEAVY:
            compatible_types = ["Flatbed", "Heavy-duty"]
        
        available_types = [truck.truck_type.value for truck in trucks]
        missing_types = [t for t in compatible_types if t not in available_types]
        if missing_types:
            solutions.append(f"Add {missing_types[0]} truck to fleet")
        
        # Check time window conflicts
        shift_coverage = any(
            not (truck.shift_end.hour * 60 + truck.shift_end.minute < 
                 stop.time_window_start.hour * 60 + stop.time_window_start.minute)
            for truck in trucks
        )
        if not shift_coverage:
            solutions.append(f"Extend truck shifts to cover {stop.time_window_start}-{stop.time_window_end} window")
        
        # Load balancing suggestion
        underutilized = [r for r in routes if r.utilization_percent < 70 and r.stops]
        if underutilized:
            best_truck = min(underutilized, key=lambda r: r.utilization_percent)
            if best_truck.utilization_percent + (stop.pallets/10)*100 <= 100:  # Rough calculation
                solutions.append(f"Assign to Truck {best_truck.truck_id} (currently {best_truck.utilization_percent}% utilized)")
        
        return solutions[0] if solutions else "Reschedule delivery or use external carrier"
    
    def _llm_summary(self, routes: List[TruckRoute], 
                    unassigned_stops: List[int],
                    stops: List[Stop], 
                    trucks: List[Truck]) -> str:
        """Generate summary using LLM"""
        try:
            # Prepare context
            route_data = []
            for route in routes:
                truck = next(t for t in trucks if t.truck_id == route.truck_id)
                route_data.append({
                    "truck": route.truck_id,
                    "type": truck.truck_type.value,
                    "stops": len(route.stops),
                    "miles": route.total_miles,
                    "utilization": route.utilization_percent,
                    "reasoning": route.reasoning
                })
            
            unassigned_data = []
            for stop_id in unassigned_stops:
                stop = next(s for s in stops if s.stop_id == stop_id)
                unassigned_data.append({
                    "stop_id": stop_id,
                    "constraint": stop.special_constraint.value,
                    "pallets": stop.pallets,
                    "time_window": f"{stop.time_window_start}-{stop.time_window_end}"
                })
            
            prompt = f"""
            Generate a natural language summary of this truck routing solution:
            
            Routes: {route_data}
            Unassigned stops: {unassigned_data}
            Total trucks: {len(trucks)}
            Total stops: {len(stops)}
            
            Include:
            1. Overall routing success metrics
            2. Key decisions made per truck
            3. Reasons for unassigned stops
            4. Optimization recommendations
            
            Keep it concise but informative, suitable for a logistics manager.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a logistics optimization expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}")
            return self._rule_based_summary(routes, unassigned_stops, stops, trucks)
    
    def _get_unassigned_reason(self, stop: Stop, trucks: List[Truck]) -> str:
        """Determine why a stop wasn't assigned"""
        reasons = []
        
        # Check capacity
        if all(stop.pallets > truck.max_pallets for truck in trucks):
            reasons.append(f"exceeds all truck capacities ({stop.pallets} pallets)")
        
        # Check compatibility
        compatible_trucks = [
            t for t in trucks 
            if self._is_compatible(stop.special_constraint.value, t.truck_type.value)
        ]
        if not compatible_trucks:
            reasons.append(f"{stop.special_constraint.value} requires special truck type")
        
        # Check time windows
        time_compatible = any(
            self._check_time_overlap(stop, truck) for truck in trucks
        )
        if not time_compatible:
            reasons.append(f"time window {stop.time_window_start}-{stop.time_window_end} conflicts with all truck shifts")
        
        return "; ".join(reasons) if reasons else "capacity or route optimization constraints"
    
    def _is_compatible(self, constraint: str, truck_type: str) -> bool:
        """Check if stop constraint is compatible with truck type"""
        compatibility = {
            "Dry": ["None", "Fragile", "Heavy"],
            "Refrigerated": ["None", "Refrigerated", "Fragile"],
            "Frozen": ["None", "Frozen", "Refrigerated"],
            "Hazmat": ["Hazmat"],
            "Flatbed": ["Heavy", "None"]
        }
        return constraint in compatibility.get(truck_type, [])
    
    def _check_time_overlap(self, stop: Stop, truck: Truck) -> bool:
        """Check if stop time window overlaps with truck shift"""
        truck_start_mins = truck.shift_start.hour * 60 + truck.shift_start.minute
        truck_end_mins = truck.shift_end.hour * 60 + truck.shift_end.minute
        stop_start_mins = stop.time_window_start.hour * 60 + stop.time_window_start.minute
        stop_end_mins = stop.time_window_end.hour * 60 + stop.time_window_end.minute
        
        return not (truck_end_mins < stop_start_mins or truck_start_mins > stop_end_mins)
    
    def parse_natural_constraints(self, instruction: str) -> Dict[str, Any]:
        """Enhanced natural language constraint parsing with AI fallback"""
        if self.use_llm:
            return self._ai_parse_constraints(instruction)
        else:
            return self._regex_parse_constraints(instruction)
    
    def _ai_parse_constraints(self, instruction: str) -> Dict[str, Any]:
        """Use AI to parse complex natural language routing constraints"""
        try:
            prompt = f"""
            Parse the following routing instruction into structured constraints. Extract specific details:
            
            Instruction: "{instruction}"
            
            Parse into JSON format with these possible fields:
            - max_route_miles: integer (distance limits)
            - max_route_hours: float (time limits) 
            - max_route_cost: float (cost limits in dollars)
            - avoid_highways: list of highway names/numbers
            - avoid_areas: list of area names
            - avoid_times: list of time ranges to avoid
            - conditional_rules: list of conditional routing rules
            - truck_restrictions: dict of truck-specific restrictions
            - prioritize_morning: boolean
            - prioritize_frozen: boolean
            - prioritize_fragile: boolean
            - fragile_last: boolean
            - max_stops_per_truck: integer
            - preferred_truck_types: list of truck types
            - required_truck_types: list of required truck types
            - rush_hour_avoidance: boolean
            - fuel_efficiency_priority: boolean
            - delivery_sequence_requirements: list of specific ordering rules
            - special_handling: list of special instructions
            - time_window_preferences: dict of time preferences
            - cost_optimization_targets: dict of cost targets
            - route_efficiency_goals: list of efficiency objectives
            
            Advanced Examples:
            Input: "Avoid sending Truck A into Atlanta and keep routes under $200"
            Output: {{"truck_restrictions": {{"Truck A": ["avoid Atlanta"]}}, "max_route_cost": 200}}
            
            Input: "Use refrigerated trucks only and complete by 2 PM"
            Output: {{"required_truck_types": ["Refrigerated"], "time_window_preferences": {{"completion_time": "14:00"}}}}
            
            Input: "Reduce route costs under $200 and avoid downtown during lunch"
            Output: {{"cost_optimization_targets": {{"max_total_cost": 200}}, "avoid_times": ["11:30-13:30"], "avoid_areas": ["downtown"]}}
            
            Only return valid JSON, no explanations:
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a logistics AI that parses routing constraints into JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"AI parsed constraints: {result}")
            return result
            
        except Exception as e:
            logger.error(f"AI constraint parsing failed: {e}")
            return self._regex_parse_constraints(instruction)
    
    def _regex_parse_constraints(self, instruction: str) -> Dict[str, Any]:
        """Enhanced regex-based constraint parsing with advanced rules"""
        constraints = {}
        instruction_lower = instruction.lower()
        
        # Distance constraints
        distance_match = re.search(self.route_patterns['distances'], instruction_lower)
        if distance_match:
            distance = int(distance_match.group(1))
            if 'under' in instruction_lower or 'limit' in instruction_lower or 'max' in instruction_lower:
                constraints["max_route_miles"] = distance
        
        # Cost constraints
        cost_match = re.search(r'\$(\d+)', instruction)
        if cost_match:
            cost = float(cost_match.group(1))
            if 'under' in instruction_lower or 'limit' in instruction_lower or 'max' in instruction_lower:
                constraints["max_route_cost"] = cost
            elif 'reduce' in instruction_lower or 'save' in instruction_lower:
                constraints["cost_optimization_targets"] = {"max_total_cost": cost}
        
        # Time constraints with hours
        hour_match = re.search(r'(\d+)\s*hours?', instruction_lower)
        if hour_match:
            hours = float(hour_match.group(1))
            if 'under' in instruction_lower or 'limit' in instruction_lower or 'max' in instruction_lower:
                constraints["max_route_hours"] = hours
        
        # Conditional truck restrictions
        truck_avoid_match = re.search(r'avoid sending (truck [a-z]|[a-z]) (into|to) ([a-z\s]+)', instruction_lower)
        if truck_avoid_match:
            truck_id = truck_avoid_match.group(1).replace('truck ', '').upper()
            location = truck_avoid_match.group(3)
            constraints["truck_restrictions"] = {truck_id: [f"avoid {location}"]}
        
        # Required truck types
        if re.search(r'use (refrigerated|frozen|hazmat|flatbed|dry) trucks? only', instruction_lower):
            truck_type_match = re.search(r'use (\w+) trucks? only', instruction_lower)
            if truck_type_match:
                truck_type = truck_type_match.group(1).capitalize()
                constraints["required_truck_types"] = [truck_type]
        
        # Completion time constraints
        completion_time_match = re.search(r'complete by (\d{1,2})\s*(pm|am)', instruction_lower)
        if completion_time_match:
            hour = int(completion_time_match.group(1))
            period = completion_time_match.group(2)
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            constraints["time_window_preferences"] = {"completion_time": f"{hour:02d}:00"}
        
        # Highway avoidance  
        highway_matches = re.findall(self.route_patterns['highways'], instruction, re.IGNORECASE)
        if highway_matches and re.search(self.route_patterns['avoidance'], instruction_lower):
            constraints["avoid_highways"] = highway_matches
        
        # Rush hour detection with lunch hour
        if 'rush hour' in instruction_lower:
            constraints["rush_hour_avoidance"] = True
            constraints["avoid_times"] = ["07:00-09:00", "17:00-19:00"]
        elif 'lunch' in instruction_lower and 'avoid' in instruction_lower:
            constraints["avoid_times"] = ["11:30-13:30"]
        
        # Time window constraints
        time_window_match = re.search(self.route_patterns['time_windows'], instruction_lower)
        if time_window_match:
            constraints["preferred_delivery_window"] = time_window_match.group(0)
        
        # Priority handling
        if re.search(r'frozen.*first|first.*frozen', instruction_lower):
            constraints["prioritize_frozen"] = True
        
        if re.search(r'fragile.*(last|careful)|load.*fragile.*last', instruction_lower):
            constraints["fragile_last"] = True
        
        # Morning delivery priority
        if 'morning' in instruction_lower or 'before noon' in instruction_lower or 'am only' in instruction_lower:
            constraints["prioritize_morning"] = True
        
        # Truck count/capacity limits
        pallet_match = re.search(self.route_patterns['pallets'], instruction_lower)
        if pallet_match and ('max' in instruction_lower or 'limit' in instruction_lower):
            constraints["max_pallets_per_truck"] = int(pallet_match.group(1))
        
        # Fuel efficiency
        if 'fuel' in instruction_lower and ('efficient' in instruction_lower or 'save' in instruction_lower):
            constraints["fuel_efficiency_priority"] = True
        
        # Area avoidance
        if 'avoid downtown' in instruction_lower or 'skip downtown' in instruction_lower:
            constraints["avoid_areas"] = ["downtown"]
        elif 'avoid' in instruction_lower:
            # Try to extract any area mentioned after "avoid"
            avoid_match = re.search(r'avoid ([a-z\s]+?)(?:\s|$|,)', instruction_lower)
            if avoid_match:
                area = avoid_match.group(1).strip()
                if area not in ['rush', 'sending', 'downtown']:  # Filter out non-location words
                    constraints["avoid_areas"] = [area]
        
        # Same-day delivery
        if 'same day' in instruction_lower or 'today' in instruction_lower:
            constraints["same_day_delivery"] = True
        
        # Route efficiency goals
        efficiency_goals = []
        if 'minimize' in instruction_lower:
            if 'cost' in instruction_lower:
                efficiency_goals.append("minimize_cost")
            if 'time' in instruction_lower:
                efficiency_goals.append("minimize_time")
            if 'distance' in instruction_lower or 'miles' in instruction_lower:
                efficiency_goals.append("minimize_distance")
        
        if efficiency_goals:
            constraints["route_efficiency_goals"] = efficiency_goals
        
        return constraints
    
    def enrich_stop_data(self, address: str, existing_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """AI-powered data enrichment for incomplete stop information"""
        enriched_data = existing_data or {}
        
        if self.use_llm:
            try:
                prompt = f"""
                Analyze this delivery address and provide logistics details:
                Address: "{address}"
                
                Based on the address type, estimate:
                1. Likely pallet count (1-20)
                2. Special handling requirements (Fragile, Refrigerated, Frozen, Hazmat, Heavy, None)
                3. Suggested delivery time window (business hours, morning preferred, etc.)
                4. Expected service time in minutes (10-30)
                
                Address types to consider:
                - Residential: 1-3 pallets, fragile items, flexible windows
                - Retail stores: 3-8 pallets, mixed goods, business hours
                - Restaurants: 2-6 pallets, refrigerated/frozen, morning preferred
                - Warehouses: 5-20 pallets, heavy items, all day
                - Hospitals: 1-5 pallets, fragile/medical, specific windows
                
                Return JSON format:
                {{
                    "estimated_pallets": integer,
                    "special_constraint": "None|Fragile|Refrigerated|Frozen|Hazmat|Heavy",
                    "suggested_time_window": "HH:MM-HH:MM",
                    "service_time_minutes": integer,
                    "confidence": float (0.0-1.0),
                    "reasoning": "brief explanation"
                }}
                """
                
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a logistics AI that analyzes delivery addresses."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.3
                )
                
                ai_data = json.loads(response.choices[0].message.content)
                
                # Only use AI suggestions if confidence is high or data is missing
                if ai_data.get("confidence", 0) > 0.7 or not existing_data:
                    enriched_data.update({
                        "estimated_pallets": ai_data.get("estimated_pallets", 3),
                        "special_constraint": ai_data.get("special_constraint", "None"),
                        "suggested_time_window": ai_data.get("suggested_time_window", "08:00-17:00"),
                        "service_time_minutes": ai_data.get("service_time_minutes", 15),
                        "ai_reasoning": ai_data.get("reasoning", "AI analysis")
                    })
                
                logger.info(f"AI enriched address '{address}': {ai_data}")
                
            except Exception as e:
                logger.error(f"AI enrichment failed for {address}: {e}")
                
        # Fallback rule-based enrichment
        return self._rule_based_enrichment(address, enriched_data)
    
    def _rule_based_enrichment(self, address: str, existing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based fallback for data enrichment"""
        address_lower = address.lower()
        
        # Default values if not already set
        if "estimated_pallets" not in existing_data:
            if any(word in address_lower for word in ['walmart', 'target', 'costco', 'store', 'retail']):
                existing_data["estimated_pallets"] = 6
            elif any(word in address_lower for word in ['restaurant', 'cafe', 'diner', 'kitchen']):
                existing_data["estimated_pallets"] = 4
            elif any(word in address_lower for word in ['hospital', 'clinic', 'medical']):
                existing_data["estimated_pallets"] = 2
            elif any(word in address_lower for word in ['warehouse', 'distribution', 'depot']):
                existing_data["estimated_pallets"] = 12
            else:
                existing_data["estimated_pallets"] = 3  # Residential default
        
        if "special_constraint" not in existing_data:
            if any(word in address_lower for word in ['restaurant', 'food', 'grocery', 'fresh']):
                existing_data["special_constraint"] = "Refrigerated"
            elif any(word in address_lower for word in ['pharmacy', 'medical', 'hospital']):
                existing_data["special_constraint"] = "Fragile"
            elif any(word in address_lower for word in ['warehouse', 'industrial', 'manufacturing']):
                existing_data["special_constraint"] = "Heavy"
            else:
                existing_data["special_constraint"] = "None"
        
        if "suggested_time_window" not in existing_data:
            if any(word in address_lower for word in ['restaurant', 'cafe']):
                existing_data["suggested_time_window"] = "06:00-11:00"  # Morning delivery
            elif any(word in address_lower for word in ['office', 'business']):
                existing_data["suggested_time_window"] = "09:00-17:00"  # Business hours
            else:
                existing_data["suggested_time_window"] = "08:00-18:00"  # Standard window
        
        if "service_time_minutes" not in existing_data:
            existing_data["service_time_minutes"] = 15
        
        return existing_data
    
    def parse_address_list(self, address_text: str) -> List[str]:
        """Parse free-form address text into individual addresses"""
        if self.use_llm:
            return self._ai_parse_addresses(address_text)
        else:
            return self._regex_parse_addresses(address_text)
    
    def _ai_parse_addresses(self, address_text: str) -> List[str]:
        """Use AI to parse complex address lists"""
        try:
            prompt = f"""
            Extract individual delivery addresses from this text. Clean up formatting and return as a JSON list:
            
            Text: "{address_text}"
            
            Guidelines:
            - Extract complete addresses (street, city, state if present)
            - Clean up extra whitespace and formatting
            - Remove bullet points, numbers, or list formatting
            - Ensure each address is valid and complete
            - If city/state missing, don't assume location
            
            Return only JSON array of strings:
            ["address1", "address2", ...]
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an address parsing AI. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            addresses = json.loads(response.choices[0].message.content)
            logger.info(f"AI parsed {len(addresses)} addresses from text")
            return addresses
            
        except Exception as e:
            logger.error(f"AI address parsing failed: {e}")
            return self._regex_parse_addresses(address_text)
    
    def _regex_parse_addresses(self, address_text: str) -> List[str]:
        """Regex-based address parsing fallback"""
        # Split by common delimiters
        lines = re.split(r'\n|;|\d+\.|•|-\s+', address_text)
        
        addresses = []
        for line in lines:
            line = line.strip()
            if len(line) > 10 and any(word in line.lower() for word in ['st', 'ave', 'rd', 'blvd', 'way', 'dr', 'lane', 'court']):
                addresses.append(line)
        
        return addresses if addresses else [address_text.strip()]
    
    def estimate_time_windows_from_vague_phrases(self, instruction: str) -> Dict[str, str]:
        """Estimate time windows from vague phrases"""
        if self.use_llm:
            return self._ai_estimate_time_windows(instruction)
        else:
            return self._rule_based_time_estimation(instruction)
    
    def _ai_estimate_time_windows(self, instruction: str) -> Dict[str, str]:
        """Use AI to estimate time windows from vague descriptions"""
        try:
            prompt = f"""
            Convert vague time descriptions into specific time windows:
            
            Instruction: "{instruction}"
            
            Convert phrases like:
            - "early morning" → "06:00-09:00"
            - "lunch time" → "11:30-13:30"
            - "afternoon" → "13:00-17:00"
            - "before rush hour" → "08:00-16:00"
            - "evening delivery" → "17:00-20:00"
            - "business hours" → "09:00-17:00"
            - "late delivery" → "15:00-19:00"
            
            Return JSON format:
            {{
                "estimated_window": "HH:MM-HH:MM",
                "confidence": float (0.0-1.0),
                "reasoning": "brief explanation"
            }}
            
            Only return valid JSON:
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a time window estimation AI."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"AI estimated time window: {result}")
            return result
            
        except Exception as e:
            logger.error(f"AI time window estimation failed: {e}")
            return self._rule_based_time_estimation(instruction)
    
    def _rule_based_time_estimation(self, instruction: str) -> Dict[str, str]:
        """Rule-based time window estimation"""
        instruction_lower = instruction.lower()
        
        # Time phrase mappings
        time_mappings = {
            'early morning': "06:00-09:00",
            'morning': "08:00-12:00", 
            'lunch time': "11:30-13:30",
            'afternoon': "13:00-17:00",
            'evening': "17:00-20:00",
            'business hours': "09:00-17:00",
            'before rush hour': "08:00-16:00",
            'after rush hour': "19:00-21:00",
            'late delivery': "15:00-19:00",
            'night delivery': "20:00-23:00"
        }
        
        for phrase, window in time_mappings.items():
            if phrase in instruction_lower:
                return {
                    "estimated_window": window,
                    "confidence": 0.8,
                    "reasoning": f"Matched phrase: {phrase}"
                }
        
        # Default business hours
        return {
            "estimated_window": "09:00-17:00",
            "confidence": 0.5,
            "reasoning": "Default business hours"
        }
    
    def analyze_cost_targets(self, instruction: str, current_routes: List[TruckRoute] = None) -> Dict[str, Any]:
        """Analyze cost optimization targets from natural language"""
        instruction_lower = instruction.lower()
        analysis = {}
        
        # Extract cost targets
        cost_match = re.search(r'\$(\d+(?:\.\d{2})?)', instruction)
        if cost_match:
            target_cost = float(cost_match.group(1))
            analysis["target_cost"] = target_cost
            
            if current_routes:
                current_cost = sum(route.fuel_estimate for route in current_routes)
                savings_needed = current_cost - target_cost
                analysis["current_cost"] = current_cost
                analysis["savings_needed"] = savings_needed
                analysis["reduction_percentage"] = (savings_needed / current_cost) * 100 if current_cost > 0 else 0
        
        # Identify cost reduction strategies
        strategies = []
        if 'reduce' in instruction_lower or 'minimize' in instruction_lower:
            if 'fuel' in instruction_lower:
                strategies.append("fuel_optimization")
            if 'distance' in instruction_lower or 'miles' in instruction_lower:
                strategies.append("distance_optimization")
            if 'time' in instruction_lower:
                strategies.append("time_optimization")
            if 'overtime' in instruction_lower:
                strategies.append("overtime_prevention")
        
        if strategies:
            analysis["strategies"] = strategies
        
        return analysis