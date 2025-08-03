// API Types
export interface Stop {
  stop_id: number;
  address: string;
  time_window_start: string;
  time_window_end: string;
  pallets: number;
  special_constraint: 'None' | 'Fragile' | 'Refrigerated' | 'Frozen' | 'Hazmat' | 'Heavy';
  service_time_minutes: number;
  latitude?: number;
  longitude?: number;
}

export interface Truck {
  truck_id: string;
  depot_address: string;
  max_pallets: number;
  truck_type: 'Dry' | 'Refrigerated' | 'Frozen' | 'Hazmat' | 'Flatbed';
  shift_start: string;
  shift_end: string;
  cost_per_mile: number;
  avg_speed_mph: number;
  depot_latitude?: number;
  depot_longitude?: number;
}

export interface RouteStop {
  stop_id: number;
  eta: string;
  arrival_time: string;
  departure_time: string;
  distance_from_previous: number;
  notes: string;
  latitude?: number;
  longitude?: number;
  address?: string;
  pallets?: number;
  time_window_start?: string;
  time_window_end?: string;
  estimated_arrival?: string;
}

export interface TruckRoute {
  truck_id: string;
  stops: RouteStop[];
  total_miles: number;
  total_time_hours: number;
  fuel_estimate: number;
  utilization_percent: number;
  reasoning: string;
  depot_latitude?: number;
  depot_longitude?: number;
  depot_address?: string;
}

export interface RoutingResponse {
  routes: TruckRoute[];
  unassigned_stops: number[];
  total_miles: number;
  total_fuel_cost: number;
  average_utilization: number;
  routing_time_seconds: number;
  natural_language_summary: string;
}

// Frontend State Types
export interface AppState {
  // Input data
  addresses: string;
  constraints: string;
  depotAddress: string;
  csvFile: File | null;
  
  // Routing results
  currentRoutes: TruckRoute[];
  routingSummary: string;
  isLoading: boolean;
  error: string | null;
  
  // UI state
  activeTab: 'input' | 'results' | 'map';
  showExportModal: boolean;
  chatHistory: ChatMessage[];
  
  // Actions
  setAddresses: (addresses: string) => void;
  setConstraints: (constraints: string) => void;
  setDepotAddress: (depot: string) => void;
  setCsvFile: (file: File | null) => void;
  setCurrentRoutes: (routes: TruckRoute[]) => void;
  setRoutingSummary: (summary: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setActiveTab: (tab: 'input' | 'results' | 'map') => void;
  setShowExportModal: (show: boolean) => void;
  addChatMessage: (message: ChatMessage) => void;
  clearResults: () => void;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

export interface MapViewport {
  latitude: number;
  longitude: number;
  zoom: number;
}

// API Request Types
export interface AutoRoutingRequest {
  addresses: string;
  constraints?: string;
  depot_address?: string;
}

export interface ReRoutingRequest {
  original_routes: TruckRoute[];
  stops: Stop[];
  trucks: Truck[];
  changes: Record<string, any>;
  reason?: string;
}

// Export Types
export interface ExportOptions {
  format: 'csv' | 'pdf';
  includeMap: boolean;
  includeSummary: boolean;
}