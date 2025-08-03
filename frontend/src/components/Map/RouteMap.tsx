import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { MapPin, Navigation, Truck, AlertCircle, Layers } from 'lucide-react';
import { cn } from '../../utils/cn';
import { TruckRoute } from '../../types';

// Set Mapbox access token
mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN || '';
console.log('Mapbox token:', mapboxgl.accessToken ? 'Token is set' : 'NO TOKEN!');

interface RouteMapProps {
  routes: TruckRoute[];
  isFullscreen?: boolean;
}

const RouteMap: React.FC<RouteMapProps> = ({ routes, isFullscreen = false }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  const [showLayers, setShowLayers] = useState(false);
  const [activeLayer, setActiveLayer] = useState('routes');
  const [showOverview, setShowOverview] = useState(true);
  const [showLegend, setShowLegend] = useState(true);
  const [truckPositions, setTruckPositions] = useState<{[truckId: string]: {lat: number, lng: number, heading: number}}>({});

  // Handle escape key to exit fullscreen
  useEffect(() => {
    if (!isFullscreen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        // Switch back to summary tab
        const summaryButton = document.querySelector('[data-value="summary"]') as HTMLButtonElement;
        if (summaryButton) {
          summaryButton.click();
        }
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isFullscreen]);
  
  const currentRoutes = routes;
  const isLoading = false;

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

  useEffect(() => {
    console.log('Map initialization attempt:', {
      container: !!mapContainerRef.current,
      token: !!mapboxgl.accessToken,
      tokenValue: mapboxgl.accessToken ? 'Token set' : 'NO TOKEN'
    });
    
    if (!mapContainerRef.current || !mapboxgl.accessToken) {
      console.error('Map initialization failed - missing requirements');
      return;
    }

    try {
      // Initialize map with minimal config
      console.log('Creating Mapbox GL map...');
      const map = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: 'mapbox://styles/mapbox/streets-v11',
        center: [-84.3880, 33.7490], // Atlanta, GA (default)
        zoom: 10,
        accessToken: mapboxgl.accessToken,
      });
      
      console.log('Map instance created:', map);

      mapRef.current = map;

      map.on('load', () => {
        console.log('Map loaded successfully');
        setMapLoaded(true);
        
        // Add a simple test marker
        try {
          const marker = new mapboxgl.Marker({ color: 'red' })
            .setLngLat([-84.3880, 33.7490])
            .addTo(map);
          console.log('Test marker added:', marker);
        } catch (err) {
          console.error('Error adding marker:', err);
        }
      });

      map.on('error', (e) => {
        console.error('Map error:', e);
        setMapError(`Map loading failed: ${e.error?.message || 'Unknown error'}`);
      });

      map.on('style.load', () => {
        console.log('Map style loaded successfully');
      });

      return () => {
        if (map) {
          map.remove();
        }
      };
    } catch (error) {
      console.error('Map initialization failed:', error);
      setMapError(`Map initialization failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, []);

  useEffect(() => {
    if (!mapRef.current || !mapLoaded || !currentRoutes.length) return;
    
    // Debug logging
    console.log('RouteMap: Processing routes:', currentRoutes);
    console.log('First route stops:', currentRoutes[0]?.stops);
    console.log('First stop coordinates:', {
      lat: currentRoutes[0]?.stops[0]?.latitude,
      lng: currentRoutes[0]?.stops[0]?.longitude
    });
    console.log('First route depot coordinates:', {
      lat: currentRoutes[0]?.depot_latitude,
      lng: currentRoutes[0]?.depot_longitude
    });

    const map = mapRef.current;
    const bounds = new mapboxgl.LngLatBounds();

    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Clear existing layers and sources
    ['route', 'stop', 'depot'].forEach(type => {
      currentRoutes.forEach((_, index) => {
        const sourceId = `${type}-${index}`;
        if (map.getLayer(sourceId)) map.removeLayer(sourceId);
        if (map.getLayer(`${sourceId}-symbol`)) map.removeLayer(`${sourceId}-symbol`);
        if (map.getSource(sourceId)) map.removeSource(sourceId);
      });
    });

    // Check if we have real coordinates
    const hasRealCoordinates = currentRoutes.some(route => 
      (route.depot_latitude && route.depot_longitude) || 
      route.stops.some(stop => stop.latitude && stop.longitude)
    );

    // Add routes to map
    currentRoutes.forEach((route, index) => {
      const color = truckColors[index % truckColors.length];
      
      // Create route line from stops
      if (route.stops.length > 0) {
        const coordinates: [number, number][] = [];
        
        // Use real or mock depot coordinates
        let depotLng = route.depot_longitude || -98.5795 + (index * 0.1);
        let depotLat = route.depot_latitude || 39.8283 + (index * 0.1);
        coordinates.push([depotLng, depotLat]);
        bounds.extend([depotLng, depotLat]);
        
        // Add depot marker
        const depotMarker = new mapboxgl.Marker({ color })
          .setLngLat([depotLng, depotLat])
          .setPopup(new mapboxgl.Popup().setHTML(`
            <strong>Depot - Truck ${route.truck_id}</strong><br/>
            ${route.depot_address || 'Main Depot'}
          `))
          .addTo(map);
        markersRef.current.push(depotMarker);
        
        // Add stop coordinates
        route.stops.forEach((stop, stopIndex) => {
          // Use real coordinates if available, otherwise use mock
          let lng: number, lat: number;
          
          if (stop.longitude && stop.latitude) {
            lng = stop.longitude;
            lat = stop.latitude;
          } else {
            // Generate mock coordinates in a pattern
            lng = depotLng + (stopIndex + 1) * 0.2 * Math.cos(stopIndex * 0.5);
            lat = depotLat + (stopIndex + 1) * 0.15 * Math.sin(stopIndex * 0.5);
          }
          
          coordinates.push([lng, lat]);
          bounds.extend([lng, lat]);
          
          // Add stop marker
          const stopMarker = new mapboxgl.Marker({ 
            color: 'white',
            scale: 0.8
          })
            .setLngLat([lng, lat])
            .setPopup(new mapboxgl.Popup().setHTML(`
              <strong>Stop #${stop.stop_id}</strong><br/>
              ${stop.address || 'Stop ' + stop.stop_id}<br/>
              ${stop.pallets || 0} pallets<br/>
              Window: ${stop.time_window_start || '08:00'}-${stop.time_window_end || '17:00'}<br/>
              ETA: ${stop.estimated_arrival || stop.eta}
            `))
            .addTo(map);
          
          // Add stop number label
          const el = stopMarker.getElement();
          if (el) {
            el.innerHTML = `<div style="background-color: ${color}; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; border: 2px solid white;">${stopIndex + 1}</div>`;
          }
          
          markersRef.current.push(stopMarker);
        });
        
        // Return to depot
        coordinates.push([depotLng, depotLat]);
        
        // Add route line
        map.addSource(`route-${index}`, {
          type: 'geojson',
          data: {
            type: 'Feature',
            properties: {},
            geometry: {
              type: 'LineString',
              coordinates,
            },
          },
        });
        
        map.addLayer({
          id: `route-${index}`,
          type: 'line',
          source: `route-${index}`,
          layout: {
            'line-join': 'round',
            'line-cap': 'round',
          },
          paint: {
            'line-color': color,
            'line-width': 4,
            'line-opacity': activeLayer === 'routes' ? 0.8 : 0.3,
          },
        });
      }
    });

    // Fit map to bounds
    if (!bounds.isEmpty()) {
      map.fitBounds(bounds, { padding: 50 });
    }
  }, [currentRoutes, mapLoaded, activeLayer]);

  // Update layer visibility based on activeLayer
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;
    
    const map = mapRef.current;
    
    currentRoutes.forEach((_, index) => {
      const routeLayer = `route-${index}`;
      if (map.getLayer(routeLayer)) {
        map.setPaintProperty(
          routeLayer,
          'line-opacity',
          activeLayer === 'routes' ? 0.8 : 0.3
        );
      }
    });
  }, [activeLayer, currentRoutes, mapLoaded]);

  // Real-time truck position simulation
  useEffect(() => {
    if (!currentRoutes.length || !mapLoaded) return;

    const interval = setInterval(() => {
      const newPositions: {[truckId: string]: {lat: number, lng: number, heading: number}} = {};

      currentRoutes.forEach(route => {
        if (route.stops.length > 0) {
          try {
            // Simple position simulation - just cycle through stops with time-based progression
            const currentTime = Date.now();
            const startTime = route.stops[0].arrival_time ? new Date(route.stops[0].arrival_time).getTime() : currentTime;
            const elapsedMinutes = Math.max(0, (currentTime - startTime) / (1000 * 60));
            
            // Calculate which stop the truck should be at based on elapsed time
            // Use a simple progression: 30 minutes per stop average
            const stopIndex = Math.floor(elapsedMinutes / 30) % route.stops.length;
            const stop = route.stops[stopIndex];
            
            if (stop && stop.latitude && stop.longitude) {
              // Add small random offset to simulate movement around the stop area
              const offset = 0.002;
              newPositions[route.truck_id] = {
                lat: stop.latitude + (Math.random() - 0.5) * offset,
                lng: stop.longitude + (Math.random() - 0.5) * offset,
                heading: Math.random() * 360
              };
            }
          } catch (error) {
            console.warn('Error in truck position simulation for truck', route.truck_id, error);
            // Fallback to first stop position if available
            const firstStop = route.stops[0];
            if (firstStop && firstStop.latitude && firstStop.longitude) {
              newPositions[route.truck_id] = {
                lat: firstStop.latitude,
                lng: firstStop.longitude,
                heading: 0
              };
            }
          }
        }
      });

      setTruckPositions(newPositions);
    }, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, [currentRoutes, mapLoaded]);

  // Update truck markers based on real-time positions
  useEffect(() => {
    if (!mapRef.current || !mapLoaded || !Object.keys(truckPositions).length) return;

    const map = mapRef.current;

    // Clear existing truck markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    // Add truck markers
    Object.entries(truckPositions).forEach(([truckId, position], index) => {
      const color = truckColors[index % truckColors.length];
      
      // Create custom truck marker
      const el = document.createElement('div');
      el.className = 'truck-marker';
      el.style.cssText = `
        width: 30px;
        height: 30px;
        background-color: ${color};
        border: 2px solid white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 12px;
        cursor: pointer;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        transform: rotate(${position.heading}deg);
      `;
      el.textContent = '🚛';
      
      const marker = new mapboxgl.Marker(el)
        .setLngLat([position.lng, position.lat])
        .setPopup(new mapboxgl.Popup().setHTML(`
          <div class="p-2">
            <h3 class="font-semibold">Truck ${truckId}</h3>
            <p class="text-sm text-gray-600">Live Position</p>
            <p class="text-xs">Lat: ${position.lat.toFixed(4)}</p>
            <p class="text-xs">Lng: ${position.lng.toFixed(4)}</p>
          </div>
        `))
        .addTo(map);

      markersRef.current.push(marker);
    });
  }, [truckPositions, mapLoaded]);

  if (!mapboxgl.accessToken) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Mapbox Token Missing</h3>
          <p className="text-gray-600">Please add REACT_APP_MAPBOX_TOKEN to environment variables.</p>
        </div>
      </div>
    );
  }

  if (mapError) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Map Error</h3>
          <p className="text-gray-600">{mapError}</p>
          <button 
            onClick={() => {
              setMapError(null);
              setMapLoaded(false);
              window.location.reload();
            }}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

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

  // Check if we're using real coordinates
  const hasRealCoordinates = currentRoutes.some(route => 
    (route.depot_latitude && route.depot_longitude) || 
    route.stops.some(stop => stop.latitude && stop.longitude)
  );

  return (
    <div className="h-full relative bg-gray-100">
      {/* Loading overlay */}
      {!mapLoaded && !mapError && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 z-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
            <span className="text-sm text-gray-600">Loading map...</span>
          </div>
        </div>
      )}
      
      {/* Map container */}
      <div 
        ref={mapContainerRef}
        className="w-full h-full"
        style={{ minHeight: '400px', position: 'relative' }}
      />

      {/* Map controls */}
      <div className="absolute top-4 right-4 flex flex-col space-y-2">
        {/* Close button (fullscreen only) */}
        {isFullscreen && (
          <button
            onClick={() => {
              const summaryButton = document.querySelector('[data-value="summary"]') as HTMLButtonElement;
              if (summaryButton) {
                summaryButton.click();
              }
            }}
            className="bg-white hover:bg-gray-100 text-gray-700 p-3 rounded-lg shadow-lg flex items-center space-x-2 transition-colors"
            title="Exit Fullscreen (ESC)"
          >
            <span className="text-lg">✕</span>
            <span className="text-sm font-medium">Close Map</span>
          </button>
        )}

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
      </div>

      {/* Route stats overlay - Compact in fullscreen */}
      {isFullscreen ? (
        <div className="absolute top-4 left-4 bg-white bg-opacity-90 rounded-lg shadow-lg overflow-hidden max-w-xs">
          <button
            onClick={() => setShowOverview(!showOverview)}
            className="w-full px-3 py-2 text-left hover:bg-gray-50 flex items-center justify-between"
          >
            <span className="font-medium text-gray-900 text-sm">📊 Overview</span>
            <span className="text-gray-400 text-xs">
              {showOverview ? '−' : '+'}
            </span>
          </button>
          
          {showOverview && (
            <div className="px-3 pb-3">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div><span className="text-gray-600">Routes:</span> <span className="font-medium">{currentRoutes.length}</span></div>
                <div><span className="text-gray-600">Stops:</span> <span className="font-medium">{currentRoutes.reduce((sum, route) => sum + route.stops.length, 0)}</span></div>
                <div><span className="text-gray-600">Miles:</span> <span className="font-medium">{currentRoutes.reduce((sum, route) => sum + route.total_miles, 0).toFixed(0)}</span></div>
                <div><span className="text-gray-600">Cost:</span> <span className="font-medium">${currentRoutes.reduce((sum, route) => sum + route.fuel_estimate, 0).toFixed(0)}</span></div>
              </div>
              <div className="mt-2 pt-2 border-t border-gray-200">
                <div className="flex items-center space-x-1">
                  <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-xs text-gray-600">Live Tracking</span>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg overflow-hidden">
          <button
            onClick={() => setShowOverview(!showOverview)}
            className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center justify-between"
          >
            <h3 className="font-medium text-gray-900">Route Overview</h3>
            <span className="text-gray-400">
              {showOverview ? '−' : '+'}
            </span>
          </button>
          
          {showOverview && (
            <div className="px-4 pb-4 min-w-64">
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
              
              {/* Real-time status */}
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-xs text-gray-600">Live Tracking Active</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Legend - Compact in fullscreen */}
      {isFullscreen ? (
        <div className="absolute bottom-4 left-4 bg-white bg-opacity-90 rounded-lg shadow-lg overflow-hidden max-w-xs">
          <button
            onClick={() => setShowLegend(!showLegend)}
            className="w-full px-3 py-2 text-left hover:bg-gray-50 flex items-center justify-between"
          >
            <span className="font-medium text-gray-900 text-sm">🚛 Trucks</span>
            <span className="text-gray-400 text-xs">
              {showLegend ? '−' : '+'}
            </span>
          </button>
          
          {showLegend && (
            <div className="px-3 pb-3">
              <div className="space-y-1">
                {currentRoutes.map((route, index) => (
                  <div key={route.truck_id} className="flex items-center space-x-2">
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: truckColors[index % truckColors.length] }}
                    />
                    <span className="text-xs">🚛</span>
                    <div className="flex-1">
                      <span className="text-xs text-gray-700 font-medium">
                        {route.truck_id}
                      </span>
                      <span className="text-xs text-gray-500 ml-1">
                        ({route.stops.length})
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg overflow-hidden max-w-xs">
          <button
            onClick={() => setShowLegend(!showLegend)}
            className="w-full px-4 py-2 text-left hover:bg-gray-50 flex items-center justify-between"
          >
            <h4 className="font-medium text-gray-900">Route Legend</h4>
            <span className="text-gray-400">
              {showLegend ? '−' : '+'}
            </span>
          </button>
          
          {showLegend && (
            <div className="px-4 pb-4">
              <div className="space-y-2">
                {currentRoutes.map((route, index) => (
                  <div key={route.truck_id} className="flex items-center space-x-2">
                    <div className="flex items-center space-x-1">
                      <div 
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: truckColors[index % truckColors.length] }}
                      />
                      <span className="text-xs">🚛</span>
                    </div>
                    <div className="flex-1">
                      <span className="text-sm text-gray-700">
                        Truck {route.truck_id}
                      </span>
                      <div className="text-xs text-gray-500">
                        {route.stops.length} stops • Live tracking
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Note about geocoding if using mock coordinates */}
      {!hasRealCoordinates && (
        <div className="absolute bottom-4 right-4 bg-blue-50 border border-blue-200 rounded-lg p-3 max-w-xs">
          <div className="flex items-start space-x-2">
            <AlertCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <p className="text-blue-800 font-medium">Note</p>
              <p className="text-blue-700 text-xs mt-1">
                Using mock coordinates. Real addresses require geocoding from the backend.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RouteMap;