import { useState, useEffect, useRef } from 'react';

interface GPSPosition {
  vehicle_id: string;
  latitude: number;
  longitude: number;
  heading?: number;
  speed?: number;
  timestamp: string;
  status: string;
  route_id?: string;
  current_stop?: string;
  is_moving: boolean;
  fuel_level?: number;
  battery_level?: number;
}

interface VehicleStats {
  vehicle_id: string;
  period_hours: number;
  total_distance_miles: number;
  average_speed_mph: number;
  moving_time_percent: number;
  stationary_time_percent: number;
  latest_position: {
    latitude: number;
    longitude: number;
    timestamp: string;
    speed?: number;
    heading?: number;
  };
  fuel_level?: number;
  battery_level?: number;
  total_positions: number;
}

export const useGPSTracking = () => {
  const [livePositions, setLivePositions] = useState<GPSPosition[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [vehicleStats, setVehicleStats] = useState<Record<string, VehicleStats>>({});
  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket connection for real-time updates
  const connectWebSocket = () => {
    try {
      const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/api/gps/ws/live-tracking';
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('🔗 GPS WebSocket connected');
        setIsConnected(true);
        setError(null);
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          if (message.type === 'initial_positions') {
            setLivePositions(message.data);
          } else if (message.type === 'position_update') {
            const updatedPosition = message.data;
            setLivePositions(prev => {
              const existing = prev.findIndex(pos => pos.vehicle_id === updatedPosition.vehicle_id);
              if (existing >= 0) {
                const updated = [...prev];
                updated[existing] = updatedPosition;
                return updated;
              } else {
                return [...prev, updatedPosition];
              }
            });
          } else if (message.type === 'keepalive' || message.type === 'pong') {
            // Keep connection alive
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };
      
      ws.onclose = () => {
        console.log('🔌 GPS WebSocket disconnected');
        setIsConnected(false);
        // Attempt to reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };
      
      ws.onerror = (error) => {
        console.error('GPS WebSocket error:', error);
        setError('WebSocket connection failed');
        setIsConnected(false);
      };
      
      wsRef.current = ws;
      
      // Send periodic ping to keep connection alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);
      
      return () => {
        clearInterval(pingInterval);
        ws.close();
      };
      
    } catch (err) {
      console.error('Error establishing WebSocket connection:', err);
      setError('Failed to connect to GPS tracking service');
    }
  };

  // Fetch initial live positions
  const fetchLivePositions = async (vehicleIds?: string[], routeId?: string) => {
    try {
      const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      let url = `${baseUrl}/api/gps/live`;
      
      const params = new URLSearchParams();
      if (vehicleIds && vehicleIds.length > 0) {
        vehicleIds.forEach(id => params.append('vehicle_ids', id));
      }
      if (routeId) {
        params.append('route_id', routeId);
      }
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch live positions');
      
      const positions: GPSPosition[] = await response.json();
      setLivePositions(positions);
      setError(null);
    } catch (err) {
      console.error('Error fetching live positions:', err);
      setError('Failed to fetch GPS data');
    }
  };

  // Fetch vehicle statistics
  const fetchVehicleStats = async (vehicleId: string) => {
    try {
      const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/api/gps/vehicles/${vehicleId}/stats`);
      if (!response.ok) throw new Error('Failed to fetch vehicle stats');
      
      const stats: VehicleStats = await response.json();
      setVehicleStats(prev => ({
        ...prev,
        [vehicleId]: stats
      }));
      
      return stats;
    } catch (err) {
      console.error(`Error fetching stats for vehicle ${vehicleId}:`, err);
      return null;
    }
  };

  // Start GPS simulation for testing
  const startSimulation = async (vehicleId: string, routePoints?: Array<{lat: number, lng: number}>) => {
    try {
      const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/api/gps/vehicles/${vehicleId}/simulate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ route_points: routePoints })
      });
      
      if (!response.ok) throw new Error('Failed to start simulation');
      
      const result = await response.json();
      console.log(`🚛 Started GPS simulation for ${vehicleId}:`, result);
      return result;
    } catch (err) {
      console.error(`Error starting simulation for ${vehicleId}:`, err);
      throw err;
    }
  };

  // Send GPS position (for testing or mobile app)
  const sendGPSPosition = async (position: {
    vehicle_id: string;
    latitude: number;
    longitude: number;
    heading?: number;
    speed?: number;
    is_moving?: boolean;
    route_id?: string;
    fuel_level?: number;
    battery_level?: number;
  }) => {
    try {
      const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const gpsData = {
        ...position,
        gps_timestamp: new Date().toISOString(),
        is_moving: position.is_moving ?? true,
        is_online: true
      };
      
      const response = await fetch(`${baseUrl}/api/gps/positions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(gpsData)
      });
      
      if (!response.ok) throw new Error('Failed to send GPS position');
      
      return await response.json();
    } catch (err) {
      console.error('Error sending GPS position:', err);
      throw err;
    }
  };

  // Get vehicle position history
  const getVehicleHistory = async (vehicleId: string, hours: number = 24) => {
    try {
      const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/api/gps/vehicles/${vehicleId}/history?hours=${hours}`);
      
      if (!response.ok) throw new Error('Failed to fetch vehicle history');
      
      return await response.json();
    } catch (err) {
      console.error(`Error fetching history for vehicle ${vehicleId}:`, err);
      return [];
    }
  };

  // Initialize connection on mount
  useEffect(() => {
    fetchLivePositions();
    const cleanup = connectWebSocket();
    
    return cleanup;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return {
    livePositions,
    isConnected,
    error,
    vehicleStats,
    fetchLivePositions,
    fetchVehicleStats,
    startSimulation,
    sendGPSPosition,
    getVehicleHistory,
    connectWebSocket
  };
};