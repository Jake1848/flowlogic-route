import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import { MapPin, Navigation, Truck, AlertCircle, Layers } from 'lucide-react';
import { cn } from '../../utils/cn';
import { TruckRoute } from '../../types';

// Set Mapbox access token
mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN || '';

interface RouteMapProps {
  routes: TruckRoute[];
}

const RouteMap: React.FC<RouteMapProps> = ({ routes }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [showLayers, setShowLayers] = useState(false);
  const [activeLayer, setActiveLayer] = useState('routes');
  
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
    if (!mapContainerRef.current || !mapboxgl.accessToken) return;

    // Initialize map
    const map = new mapboxgl.Map({
      container: mapContainerRef.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [-98.5795, 39.8283], // Center of USA
      zoom: 4,
    });

    mapRef.current = map;

    map.on('load', () => {
      setMapLoaded(true);
      
      // Add navigation controls
      map.addControl(new mapboxgl.NavigationControl(), 'top-right');
      
      // Add scale control
      map.addControl(new mapboxgl.ScaleControl(), 'bottom-right');
    });

    return () => {
      map.remove();
    };
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
      {/* Map container */}
      <div 
        ref={mapContainerRef}
        className="w-full h-full"
      />

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