# FlowLogic RouteAI - Autonomous Examples

## 🤖 Autonomous Routing (`/route/auto`)

The `/route/auto` endpoint accepts just a list of addresses and optional constraints, then automatically:
- Parses addresses using AI
- Estimates pallets, time windows, and special handling requirements
- Generates an optimal truck fleet
- Routes everything autonomously

### Example 1: Basic Autonomous Routing

```bash
curl -X POST "http://localhost:8000/route/auto" \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": "123 Walmart Supercenter, Atlanta GA\n456 Home Depot, Marietta GA\n789 Kroger Store, Decatur GA\n321 McDonald'\''s Restaurant, Buckhead GA\n654 Children'\''s Hospital, Atlanta GA",
    "constraints": "Deliver frozen goods first and avoid downtown during rush hour"
  }'
```

**AI Will Automatically:**
- Parse 5 addresses from the text
- Estimate Walmart: 6 pallets, business hours window
- Estimate Home Depot: 8 pallets, heavy goods, morning preferred  
- Estimate Kroger: 4 pallets, refrigerated goods, early delivery
- Estimate McDonald's: 3 pallets, frozen goods, 6AM-11AM window
- Estimate Hospital: 2 pallets, fragile medical supplies
- Generate 2-3 trucks: Dry, Refrigerated, and possibly Heavy/Flatbed
- Apply rush hour avoidance (7-9AM, 5-7PM)
- Prioritize frozen deliveries first

### Example 2: Simple Address List

```bash
curl -X POST "http://localhost:8000/route/auto" \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": "1. 100 Peachtree St, Atlanta GA\n2. 200 North Ave, Atlanta GA\n3. 300 Spring St, Atlanta GA\n4. 400 Marietta St, Atlanta GA",
    "constraints": "Keep routes under 100 miles"
  }'
```

### Example 3: Mixed Business Types

```bash
curl -X POST "http://localhost:8000/route/auto" \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": "Target Store - 500 Commerce Dr, Atlanta GA; Pharmacy Plus - 600 Medical Blvd, Roswell GA; Heavy Equipment Co - 700 Industrial Way, Marietta GA; Fresh Market - 800 Organic Ave, Decatur GA",
    "constraints": "Morning deliveries only and handle fragile items carefully"
  }'
```

**Expected AI Behavior:**
- Target: 6 pallets, standard goods, business hours
- Pharmacy: 2 pallets, fragile medical, restricted access
- Heavy Equipment: 12 pallets, heavy machinery, flatbed required
- Fresh Market: 4 pallets, refrigerated, morning delivery preferred
- Generate specialized fleet: Dry, Refrigerated, Flatbed trucks
- All deliveries scheduled before noon

---

## 🔄 Live Re-Routing (`/route/recalculate`)

Dynamic re-routing for real-time changes: stop cancellations, delays, new urgent deliveries.

### Example 1: Cancel a Stop

```bash
curl -X POST "http://localhost:8000/route/recalculate" \
  -H "Content-Type: application/json" \
  -d '{
    "original_routes": [/* previous routing response */],
    "stops": [/* original stops */],
    "trucks": [/* original trucks */],
    "changes": {
      "cancel_stop": {
        "stop_id": 3
      }
    },
    "reason": "Customer requested cancellation - store closed"
  }'
```

### Example 2: Add Urgent Delivery

```bash
curl -X POST "http://localhost:8000/route/recalculate" \
  -H "Content-Type: application/json" \
  -d '{
    "original_routes": [/* previous routing response */],
    "stops": [/* original stops */],
    "trucks": [/* original trucks */],
    "changes": {
      "add_stop": {
        "stop_id": 99,
        "address": "Emergency Medical Center, 900 Urgent Care Blvd, Atlanta GA",
        "pallets": 1,
        "special_constraint": "Fragile"
      }
    },
    "reason": "Urgent medical delivery requested"
  }'
```

### Example 3: Handle Delay

```bash
curl -X POST "http://localhost:8000/route/recalculate" \
  -H "Content-Type: application/json" \
  -d '{
    "original_routes": [/* previous routing response */],
    "stops": [/* original stops */],
    "trucks": [/* original trucks */],
    "changes": {
      "delay_stop": {
        "stop_id": 5,
        "new_time_window": "14:00-18:00"
      }
    },
    "reason": "Customer requested afternoon delivery due to staffing issues"
  }'
```

---

## 🧠 Advanced Natural Language Constraints

The AI understands complex routing instructions:

### Traffic & Geography
- "Avoid I-285 during rush hour"
- "Skip downtown Atlanta from 4-6 PM"
- "Use surface streets only"
- "Avoid toll roads"

### Time & Scheduling  
- "All deliveries before noon"
- "Morning routes only"
- "Stagger deliveries every 30 minutes"
- "Complete by 3 PM to avoid school traffic"

### Load & Capacity
- "Keep routes under 150 miles"
- "Maximum 8 stops per truck"
- "Fill trucks to 90% capacity"
- "Balance loads evenly"

### Special Handling
- "Frozen goods go first"
- "Load fragile items last for easy access"
- "Refrigerated and frozen on same truck"
- "Separate hazmat from food deliveries"

### Efficiency Goals
- "Minimize fuel costs"
- "Reduce total driving time"
- "Optimize for driver overtime"
- "Consolidate routes where possible"

---

## 💡 AI Response Examples

### Autonomous Insights
```
🤖 AUTONOMOUS ROUTING COMPLETE:

🚚 ROUTING SUMMARY: Successfully routed 8 of 8 stops across 3 trucks. 
Total distance: 127.3 miles, estimated fuel cost: $318.25

📋 TRUCK ASSIGNMENTS:
  • Truck A (Dry): 3 stops, 42.1 mi, 6.2h, 85% capacity 🔋 Efficient
  • Truck B (Refrigerated): 3 stops, 38.7 mi, 5.8h, 78% capacity 🔋 Efficient  
  • Truck C (Flatbed): 2 stops, 46.5 mi, 7.1h, 92% capacity 🔋 Efficient

🧠 AI RECOMMENDATIONS:
  • CONSOLIDATION: Consider combining Truck B and C routes to free up 1 truck
  • FUEL SAVINGS: All routes optimized within efficiency targets
  • FRAGILE HANDLING: Medical deliveries consolidated to minimize handling

🧠 AI INSIGHTS:
  • Processed 5 raw addresses into 8 delivery stops
  • AI estimated data for 6 stops (pallets, time windows, constraints)
  • Auto-generated 3 truck fleet with 3 vehicle types: Dry, Refrigerated, Flatbed
  • Applied 3 natural language constraints
  • Route efficiency: 100% of trucks operating at >75% capacity
  • Cost efficiency: $39.78 per stop delivered
```

### Re-Routing Impact Analysis
```
🔄 RE-ROUTING COMPLETE:

📊 IMPACT ANALYSIS:
  • Cancelled stop 3
  • Added new stop 99 (Emergency Medical Center)
  • Distance change: +12.4 miles
  • Cost change: +$31.00
  • 2 trucks required route adjustments

🧠 AI RECOMMENDATIONS:
  • URGENT PRIORITY: New medical delivery assigned to Truck A for fastest response
  • EFFICIENCY: Cancelled stop freed 15 minutes, absorbed by new urgent delivery
  • OVERTIME: No driver overtime impact from changes
```

---

## 🚀 Full Autonomous Workflow

1. **Input**: Just paste addresses + constraints
2. **AI Processing**: 
   - Parse & clean addresses
   - Estimate logistics requirements
   - Generate optimal fleet
   - Apply routing constraints
3. **Optimization**: Route with OR-Tools + GraphHopper
4. **Output**: Complete routes + AI explanations + recommendations
5. **Live Updates**: Handle changes dynamically

This creates a truly "hands-off" routing experience where users can go from raw addresses to optimized routes with minimal input.