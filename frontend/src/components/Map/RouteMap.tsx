import React, { useEffect, useRef, useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { MapPin, Navigation, Truck, AlertCircle, Layers } from 'lucide-react';
import { cn } from '../../utils/cn';

// Mock Mapbox implementation for development
const RouteMap: React.FC = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [showLayers, setShowLayers] = useState(false);
  const [activeLayer, setActiveLayer] = useState('routes');
  
  const { currentRoutes, isLoading } = useAppStore();

  useEffect(() => {
    // Simulate map loading
    const timer = setTimeout(() => {
      setMapLoaded(true);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  const truckColors = [
    '#3B82F6', // Blue
    '#EF4444', // Red  
    '#10B981', // Green
    '#F59E0B', // Orange
    '#8B5CF6', // Purple
    '#EC4899', // Pink
  ];

  const layers = [
    { id: 'routes', label: 'Routes', icon: Navigation },
    { id: 'stops', label: 'Stops', icon: MapPin },
    { id: 'trucks', label: 'Trucks', icon: Truck },
  ];

  if (!currentRoutes.length) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Routes to Display</h3>
          <p className="text-gray-600">Generate routes first to see them on the map.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full relative bg-gray-100">
      {/* Map container */}
      <div 
        ref={mapContainerRef}
        className="w-full h-full relative overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        }}
      >
        {!mapLoaded ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center text-white">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
              <p>Loading map...</p>
            </div>
          </div>
        ) : (
          <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-green-50">
            {/* Mock map content */}
            <div className="relative w-full h-full">
              {/* Grid pattern for map effect */}
              <div 
                className="absolute inset-0 opacity-10"
                style={{
                  backgroundImage: `
                    linear-gradient(rgba(0,0,0,0.1) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(0,0,0,0.1) 1px, transparent 1px)
                  `,
                  backgroundSize: '50px 50px'
                }}
              />
              
              {/* Route visualization */}
              <svg className="absolute inset-0 w-full h-full">
                {currentRoutes.map((route, index) => {
                  const color = truckColors[index % truckColors.length];
                  const startX = 100 + index * 150;
                  const startY = 150;
                  
                  return (
                    <g key={route.truck_id}>
                      {/* Route path */}
                      <path
                        d={`M ${startX} ${startY} Q ${startX + 100} ${startY + 50} ${startX + 200} ${startY + 100} Q ${startX + 300} ${startY + 150} ${startX + 400} ${startY + 200}`}
                        stroke={color}
                        strokeWidth="3"
                        fill="none"
                        strokeDasharray={activeLayer === 'routes' ? 'none' : '5,5'}
                        className="transition-all duration-300"
                      />
                      
                      {/* Truck icon */}
                      <circle
                        cx={startX}
                        cy={startY}
                        r="8"
                        fill={color}
                        className="animate-pulse-soft"
                      />
                      <text
                        x={startX}
                        y={startY + 25}
                        textAnchor="middle"
                        className="text-sm font-medium fill-gray-700"
                      >
                        Truck {route.truck_id}
                      </text>
                      
                      {/* Stops */}
                      {route.stops.map((stop, stopIndex) => {
                        const stopX = startX + (stopIndex + 1) * 100;
                        const stopY = startY + (stopIndex + 1) * 50;
                        
                        return (
                          <g key={stop.stop_id}>
                            <circle
                              cx={stopX}
                              cy={stopY}
                              r="6"
                              fill="white"
                              stroke={color}
                              strokeWidth="2"
                              className={cn(
                                "transition-opacity duration-300",
                                activeLayer === 'stops' ? 'opacity-100' : 'opacity-70'
                              )}
                            />
                            <text
                              x={stopX}
                              y={stopY + 20}
                              textAnchor="middle"
                              className="text-xs fill-gray-600"
                            >
                              #{stop.stop_id}
                            </text>
                          </g>
                        );
                      })}
                    </g>
                  );
                })}
              </svg>
              
              {/* Legend */}
              <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-4 max-w-xs">
                <h4 className="font-medium text-gray-900 mb-2">Route Legend</h4>
                <div className="space-y-2">
                  {currentRoutes.map((route, index) => (
                    <div key={route.truck_id} className="flex items-center space-x-2">
                      <div 
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: truckColors[index % truckColors.length] }}
                      />
                      <span className="text-sm text-gray-700">
                        Truck {route.truck_id} - {route.stops.length} stops
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Map controls */}
      <div className="absolute top-4 right-4 flex flex-col space-y-2">
        {/* Layer toggle */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <button
            onClick={() => setShowLayers(!showLayers)}
            className="flex items-center space-x-2 px-3 py-2 text-gray-700 hover:bg-gray-50 w-full"
          >
            <Layers className="h-4 w-4" />
            <span className="text-sm">Layers</span>
          </button>
          
          {showLayers && (
            <div className="border-t border-gray-200">
              {layers.map((layer) => {
                const Icon = layer.icon;
                return (
                  <button
                    key={layer.id}
                    onClick={() => setActiveLayer(layer.id)}
                    className={cn(
                      "flex items-center space-x-2 px-3 py-2 text-sm w-full text-left transition-colors",
                      activeLayer === layer.id
                        ? "bg-primary-50 text-primary-700"
                        : "text-gray-700 hover:bg-gray-50"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{layer.label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Zoom controls */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <button className="block px-3 py-2 text-gray-700 hover:bg-gray-50 w-full border-b border-gray-200">
            <span className="text-lg font-medium">+</span>
          </button>
          <button className="block px-3 py-2 text-gray-700 hover:bg-gray-50 w-full">
            <span className="text-lg font-medium">−</span>
          </button>
        </div>
      </div>

      {/* Route stats overlay */}
      <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 min-w-64">
        <h3 className="font-medium text-gray-900 mb-3">Route Overview</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Total Routes:</span>
            <span className="font-medium text-gray-900 ml-1">{currentRoutes.length}</span>
          </div>
          <div>
            <span className="text-gray-600">Total Stops:</span>
            <span className="font-medium text-gray-900 ml-1">
              {currentRoutes.reduce((sum, route) => sum + route.stops.length, 0)}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Total Miles:</span>
            <span className="font-medium text-gray-900 ml-1">
              {currentRoutes.reduce((sum, route) => sum + route.total_miles, 0).toFixed(1)}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Fuel Cost:</span>
            <span className="font-medium text-gray-900 ml-1">
              ${currentRoutes.reduce((sum, route) => sum + route.fuel_estimate, 0).toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      {/* Development notice */}
      <div className="absolute bottom-4 right-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3 max-w-xs">
        <div className="flex items-start space-x-2">
          <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm">
            <p className="text-yellow-800 font-medium">Development Mode</p>
            <p className="text-yellow-700 text-xs mt-1">
              This is a mock map visualization. In production, integrate with Mapbox GL JS for real maps.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RouteMap;