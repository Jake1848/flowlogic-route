import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { MapPin, Navigation, Truck, AlertCircle, Layers, Play, Pause } from 'lucide-react';
import { cn } from '../../utils/cn';
import { TruckRoute } from '../../types';
import { useGPSTracking } from '../../hooks/useGPSTracking';

// Set Mapbox access token
mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN || '';

interface RouteMapProps {
  routes: TruckRoute[];
  isFullscreen?: boolean;
}

const RouteMap: React.FC<RouteMapProps> = ({ routes, isFullscreen = false }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const liveMarkersRef = useRef<mapboxgl.Marker[]>([]);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  const [showLayers, setShowLayers] = useState(false);
  const [activeLayer, setActiveLayer] = useState('routes');
  const [simulationActive, setSimulationActive] = useState(false);

  // GPS tracking integration
  const { livePositions, isConnected, error: gpsError, startSimulation } = useGPSTracking();

  // Map initialization
  useEffect(() => {
    if (!mapContainerRef.current || !mapboxgl.accessToken) {
      setMapError('Map container or access token not available');
      return;
    }

    try {
      const map = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: 'mapbox://styles/mapbox/streets-v11',
        center: [-84.3880, 33.7490], // Atlanta
        zoom: 10,
        accessToken: mapboxgl.accessToken,
      });

      mapRef.current = map;

      map.on('load', () => {
        setMapLoaded(true);

        // Add test marker
        try {
          const marker = new mapboxgl.Marker({ color: 'red' })
            .setLngLat([-84.3880, 33.7490])
            .addTo(map);
          
          // Force map resize
          setTimeout(() => {
            map.resize();
          }, 100);
        } catch (err) {
          console.error('Error adding marker:', err);
        }
      });

      map.on('error', (e) => {
        console.error('Map error:', e);
        setMapError('Failed to load map');
      });

      map.on('style.load', () => {
        // Style loaded successfully
      });

      return () => {
        // Cleanup markers
        markersRef.current.forEach(marker => marker.remove());
        markersRef.current = [];
        liveMarkersRef.current.forEach(marker => marker.remove());
        liveMarkersRef.current = [];
        
        if (mapRef.current) {
          mapRef.current.remove();
        }
      };
    } catch (error) {
      console.error('Error initializing map:', error);
      setMapError('Failed to initialize map');
    }
  }, []);

  // Update routes when they change
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;

    const map = mapRef.current;
    
    // Clear existing markers
    markersRef.current.forEach(marker => marker.remove());
    markersRef.current = [];

    const currentRoutes = routes.filter(route => 
      route.stops && route.stops.length > 0 &&
      route.stops.some(stop => stop.latitude && stop.longitude)
    );

    if (currentRoutes.length === 0) return;

    // Add markers for each route
    currentRoutes.forEach((route, routeIndex) => {
      const routeColor = routeIndex === 0 ? '#FF6B6B' : '#4ECDC4';
      
      // Add depot marker if available
      if (route.depot && route.depot.latitude && route.depot.longitude) {
        const depotMarker = new mapboxgl.Marker({ 
          color: routeColor,
          scale: 1.2
        })
          .setLngLat([route.depot.longitude, route.depot.latitude])
          .setPopup(new mapboxgl.Popup().setHTML(`
            <div class="p-2">
              <strong>Depot</strong><br/>
              ${route.depot.address || 'Distribution Center'}
            </div>
          `))
          .addTo(map);

        markersRef.current.push(depotMarker);
      }

      // Add stop markers
      route.stops.forEach((stop, stopIndex) => {
        if (!stop.latitude || !stop.longitude) return;

        const stopMarker = new mapboxgl.Marker({
          color: routeColor
        })
          .setLngLat([stop.longitude, stop.latitude])
          .setPopup(new mapboxgl.Popup().setHTML(`
            <div class="p-2">
              <strong>Stop ${stopIndex + 1}</strong><br/>
              ${stop.address}<br/>
              <small>Route ${route.truck}</small>
            </div>
          `))
          .addTo(map);

        markersRef.current.push(stopMarker);
      });
    });

    // Fit map to show all markers
    if (markersRef.current.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      markersRef.current.forEach(marker => {
        bounds.extend(marker.getLngLat());
      });
      
      map.fitBounds(bounds, {
        padding: 50,
        maxZoom: 15
      });
    }
  }, [routes, mapLoaded]);

  // Add live truck positions from GPS tracking
  useEffect(() => {
    if (!mapRef.current || !mapLoaded) return;

    const map = mapRef.current;

    // Clear existing live markers
    liveMarkersRef.current.forEach(marker => marker.remove());
    liveMarkersRef.current = [];

    // Add live truck markers
    livePositions.forEach(position => {
      const truckColor = position.is_moving ? '#22C55E' : '#F59E0B'; // Green if moving, amber if stopped
      const truckMarker = new mapboxgl.Marker({
        color: truckColor,
        rotation: position.heading || 0,
        scale: 1.2
      })
        .setLngLat([position.longitude, position.latitude])
        .setPopup(new mapboxgl.Popup().setHTML(`
          <div class="p-3">
            <strong>🚛 Truck ${position.vehicle_id}</strong><br/>
            <div class="text-sm space-y-1 mt-2">
              <div>Status: <span class="font-medium">${position.status}</span></div>
              <div>Speed: ${position.speed ? `${Math.round(position.speed)} mph` : 'N/A'}</div>
              <div>Heading: ${position.heading ? `${Math.round(position.heading)}°` : 'N/A'}</div>
              ${position.fuel_level ? `<div>Fuel: ${Math.round(position.fuel_level)}%</div>` : ''}
              ${position.battery_level ? `<div>Battery: ${Math.round(position.battery_level)}%</div>` : ''}
              <div class="text-xs text-gray-500 mt-1">
                Last update: ${new Date(position.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        `))
        .addTo(map);

      liveMarkersRef.current.push(truckMarker);
    });
  }, [livePositions, mapLoaded]);

  if (!mapboxgl.accessToken) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center p-6">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Map Not Available</h3>
          <p className="text-sm text-gray-600">
            Mapbox access token is not configured. Please check your environment variables.
          </p>
        </div>
      </div>
    );
  }

  if (mapError) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center p-6">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Map Error</h3>
          <p className="text-sm text-gray-600">{mapError}</p>
        </div>
      </div>
    );
  }

  const validRoutes = routes.filter(route => 
    route.stops && route.stops.length > 0 &&
    route.stops.some(stop => stop.latitude && stop.longitude)
  );

  return (
    <div className="h-full relative bg-gray-100">
      {/* Loading overlay */}
      {!mapLoaded && !mapError && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 z-10">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p className="text-sm text-gray-600">Loading map...</p>
          </div>
        </div>
      )}

      {/* Map container */}
      <div
        ref={mapContainerRef}
        className="w-full h-full"
        style={isFullscreen ? 
          { width: '100vw', height: '100vh', position: 'absolute', top: 0, left: 0 } : 
          { minHeight: '400px', position: 'relative' }
        }
      />

      {/* Map controls */}
      <div className="absolute top-4 right-4 flex flex-col space-y-2">
        {/* Layer toggle */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <button
            onClick={() => setShowLayers(!showLayers)}
            className="p-3 text-gray-700 hover:bg-gray-50 flex items-center space-x-2 w-full"
            title="Toggle Layers"
          >
            <Layers className="h-4 w-4" />
            <span className="text-sm font-medium">Layers</span>
          </button>

          {showLayers && (
            <div className="border-t border-gray-200">
              <button
                onClick={() => setActiveLayer('routes')}
                className={cn(
                  "p-3 text-sm w-full text-left hover:bg-gray-50",
                  activeLayer === 'routes' && "bg-blue-50 text-blue-700"
                )}
              >
                <span className="flex items-center space-x-2">
                  <MapPin className="h-4 w-4" />
                  <span>Routes & Stops</span>
                </span>
              </button>
              <button
                onClick={() => setActiveLayer('live')}
                className={cn(
                  "p-3 text-sm w-full text-left hover:bg-gray-50",
                  activeLayer === 'live' && "bg-blue-50 text-blue-700"
                )}
              >
                <span className="flex items-center space-x-2">
                  <Truck className="h-4 w-4" />
                  <span>Live Tracking</span>
                </span>
              </button>
            </div>
          )}
        </div>

        {/* Map info */}
        {/* GPS Status */}
        <div className="bg-white p-3 rounded-lg shadow-lg">
          <div className="text-xs space-y-1">
            <div className="flex items-center justify-between">
              <span>GPS Tracking</span>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            </div>
            <div className="text-gray-600">
              <div>Routes: {validRoutes.length}</div>
              <div>Stops: {validRoutes.reduce((acc, route) => acc + route.stops.length, 0)}</div>
              <div>Live Trucks: {livePositions.length}</div>
            </div>
            {gpsError && (
              <div className="text-red-500 text-xs">{gpsError}</div>
            )}
          </div>
        </div>

        {/* Simulation Controls */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <button
            onClick={async () => {
              if (!simulationActive) {
                try {
                  await startSimulation('A');
                  await startSimulation('B');
                  setSimulationActive(true);
                } catch (err) {
                  console.error('Failed to start simulation:', err);
                }
              }
            }}
            className={cn(
              "p-3 text-sm w-full text-left hover:bg-gray-50 flex items-center space-x-2",
              simulationActive ? "bg-green-50 text-green-700" : "text-gray-700"
            )}
            disabled={simulationActive}
          >
            {simulationActive ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            <span>{simulationActive ? 'Simulation Active' : 'Start GPS Simulation'}</span>
          </button>
        </div>
      </div>

      {/* No routes message */}
      {validRoutes.length === 0 && mapLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-20 z-20">
          <div className="bg-white p-6 rounded-lg shadow-lg text-center max-w-sm">
            <Navigation className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Routes to Display</h3>
            <p className="text-sm text-gray-600">
              Generate some routes to see them on the map with live truck tracking.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default RouteMap;