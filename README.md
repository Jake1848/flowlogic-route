# FlowLogic RouteAI 🚚🤖

A fully autonomous AI-powered truck routing system that transforms raw addresses into optimized delivery routes with minimal user input.

## 🌟 Autonomous Features

- **🤖 Zero-Config Routing**: Just provide addresses - AI handles everything else
- **🧠 Smart Data Enrichment**: AI estimates pallets, time windows, and special handling
- **🚛 Auto Fleet Generation**: Dynamically creates optimal truck fleet based on stops
- **💬 Advanced Natural Language**: Complex routing constraints in plain English
- **🔄 Live Re-routing**: Dynamic updates for cancellations, delays, and new stops
- **📊 Actionable AI Recommendations**: Specific suggestions for route optimization
- **🎯 Hands-off Operation**: From raw text to optimized routes in one API call

## Quick Start

### Using Docker (Recommended)

1. Clone and navigate to the project:
```bash
git clone <repo-url>
cd flowlogic_routeai
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys (optional but recommended)
```

3. Start the service:
```bash
docker-compose up -d
```

4. Access the API at `http://localhost:8000`

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python -m uvicorn app.main:app --reload
```

## 🚀 API Usage

### 🤖 Autonomous Routing (Recommended)

Just provide addresses and constraints - AI handles everything else:

```bash
curl -X POST "http://localhost:8000/route/auto" \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": "Walmart Supercenter, Atlanta GA\nHome Depot, Marietta GA\nKroger Store, Decatur GA\nMcDonald'\''s, Buckhead GA",
    "constraints": "Deliver frozen goods first and avoid I-285 during rush hour"
  }'
```

**What AI Does Automatically:**
- 🏠 Parses and cleans addresses
- 📦 Estimates pallets based on business type
- ⏰ Suggests optimal delivery windows  
- 🚛 Generates appropriate truck fleet
- 🧭 Applies complex routing constraints
- 📊 Provides optimization recommendations

### 🔄 Live Re-routing

Handle changes dynamically:

```bash
curl -X POST "http://localhost:8000/route/recalculate" \
  -H "Content-Type: application/json" \
  -d '{
    "original_routes": [/* previous routes */],
    "changes": {
      "cancel_stop": {"stop_id": 3},
      "add_stop": {
        "stop_id": 99,
        "address": "Emergency Medical Center, Atlanta GA",
        "pallets": 1
      }
    },
    "reason": "Urgent medical delivery + customer cancellation"
  }'
```

### 📁 Traditional CSV Upload

```bash
curl -X POST "http://localhost:8000/route/upload" \
  -F "stops_file=@stops.csv" \
  -F "trucks_file=@trucks.csv" \
  -F "constraints=Make sure frozen goods go first"
```

### CSV Format

**stops.csv**:
```csv
StopID,Address,TimeWindow,Pallets,Special
1,"123 Peach St, Atlanta, GA","08:00-12:00",6,"Fragile"
2,"789 Oak Ave, Augusta, GA","09:00-15:00",8,"Refrigerated"
```

**trucks.csv**:
```csv
TruckID,Depot,MaxPallets,Type,ShiftStart,ShiftEnd
A,"999 Warehouse Way, Atlanta, GA",10,"Dry",07:00,15:00
B,"999 Warehouse Way, Atlanta, GA",8,"Refrigerated",08:00,16:00
```

### 🎯 Enhanced AI Response

```json
{
  "routes": [
    {
      "truck_id": "A",
      "stops": [
        {
          "stop_id": 1,
          "eta": "09:10",
          "notes": "Fragile - loaded first"
        }
      ],
      "total_miles": 84.2,
      "fuel_estimate": 43.20,
      "utilization_percent": 80.0,
      "reasoning": "Truck A was assigned stops 1 and 3 due to overlapping time windows..."
    }
  ],
  "unassigned_stops": [],
  "natural_language_summary": "🤖 AUTONOMOUS ROUTING COMPLETE:\n\n🚚 Successfully routed 8 of 8 stops across 3 trucks...\n\n🧠 AI RECOMMENDATIONS:\n  • CONSOLIDATION: Combine 2 underutilized trucks to free up 1 truck\n  • FUEL SAVINGS: Route optimization could save $23.50\n  • OVERTIME: No driver overtime risks detected\n\n🧠 AI INSIGHTS:\n  • Processed 4 raw addresses into 8 delivery stops\n  • AI estimated data for 6 stops (pallets, time windows, constraints)\n  • Auto-generated 3 truck fleet with specialized vehicle types\n  • Cost efficiency: $31.50 per stop delivered"
}
```

## Configuration

### Environment Variables

- `GRAPHHOPPER_API_KEY`: Optional, for enhanced route optimization
- `OPENAI_API_KEY`: Optional, for improved natural language explanations
- `LOG_LEVEL`: Default INFO

### 🧠 Advanced Natural Language Understanding

The AI understands complex routing instructions:

**Traffic & Geography:**
- "Avoid I-285 during rush hour"
- "Skip downtown Atlanta from 4-6 PM"  
- "Use surface streets only"
- "Avoid toll roads"

**Time & Scheduling:**
- "All deliveries before noon"
- "Morning routes only" 
- "Stagger deliveries every 30 minutes"
- "Complete by 3 PM to avoid school traffic"

**Load & Capacity:**
- "Keep routes under 150 miles"
- "Maximum 8 stops per truck"
- "Fill trucks to 90% capacity"
- "Balance loads evenly"

**Special Handling:**
- "Frozen goods go first"
- "Load fragile items last for easy access"
- "Refrigerated and frozen on same truck"
- "Separate hazmat from food deliveries"

**Efficiency Goals:**
- "Minimize fuel costs"
- "Reduce total driving time"
- "Optimize for driver overtime"
- "Consolidate routes where possible"

### 🤖 AI Auto-Detection

**Business Type Recognition:**
- Walmart/Target → 6 pallets, business hours
- Restaurants → 4 pallets, refrigerated, morning delivery
- Hospitals → 2 pallets, fragile medical supplies
- Warehouses → 12 pallets, heavy goods, flexible timing

**Fleet Auto-Generation:**
- Analyzes cargo requirements across all stops
- Generates optimal mix of truck types (Dry, Refrigerated, Frozen, Hazmat, Flatbed)
- Calculates proper capacity and shift schedules
- Ensures regulatory compliance for special cargo

## Architecture

- **FastAPI**: Web framework and API
- **OR-Tools**: Vehicle routing optimization
- **GraphHopper**: Optional external routing service
- **OpenAI**: Optional enhanced explanations
- **Geopy**: Address geocoding
- **Pydantic**: Data validation

## Development

### Running Tests

```bash
pytest tests/
```

### Code Structure

```
flowlogic_routeai/
├── app/
│   └── main.py              # FastAPI application
├── models/
│   └── models.py            # Pydantic data models
├── services/
│   ├── routing_engine.py    # Core routing logic
│   ├── route_optimizer.py   # External API integration
│   └── natural_language.py  # NLP processing
├── utils/
│   ├── csv_parser.py        # CSV file handling
│   └── geocoding.py         # Address to coordinates
└── tests/
```

### Adding Features

1. **New Constraints**: Add to `routing_engine.py` compatibility rules
2. **New APIs**: Extend `route_optimizer.py` with additional services
3. **Enhanced NLP**: Modify `natural_language.py` for new instruction types

## Production Deployment

### AWS/Cloud Deployment

The Docker container can be deployed to:
- AWS ECS/Fargate
- Google Cloud Run  
- Azure Container Instances
- Any Kubernetes cluster

### Scaling Considerations

- Route optimization is CPU-intensive for large problems
- Consider horizontal scaling for high throughput
- Cache geocoding results in production
- Use Redis for session state if needed

## API Documentation

Full interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

MIT License - see LICENSE file for details.