import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Download, FileText, Map, Truck, Clock, DollarSign, BarChart3, AlertTriangle } from 'lucide-react';
import { cn } from '../../utils/cn';
import ExportModal from './ExportModal';

const ResultsSummary: React.FC = () => {
  const { 
    currentRoutes, 
    routingSummary, 
    setShowExportModal, 
    showExportModal,
    setActiveTab 
  } = useAppStore();

  if (!currentRoutes.length) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Routes Generated</h3>
          <p className="text-gray-600 mb-4">Create routes to see detailed analysis and recommendations.</p>
          <button
            onClick={() => setActiveTab('input')}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Start Planning Routes
          </button>
        </div>
      </div>
    );
  }

  // Calculate summary statistics
  const totalStops = currentRoutes.reduce((sum, route) => sum + route.stops.length, 0);
  const totalMiles = currentRoutes.reduce((sum, route) => sum + route.total_miles, 0);
  const totalCost = currentRoutes.reduce((sum, route) => sum + route.fuel_estimate, 0);
  const totalTime = currentRoutes.reduce((sum, route) => sum + route.total_time_hours, 0);
  const avgUtilization = currentRoutes.reduce((sum, route) => sum + route.utilization_percent, 0) / currentRoutes.length;

  const truckColors = [
    'bg-blue-500', 'bg-red-500', 'bg-green-500', 
    'bg-orange-500', 'bg-purple-500', 'bg-pink-500'
  ];

  return (
    <div className="h-full overflow-y-auto bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Route Analysis</h1>
            <p className="text-gray-600">Optimized delivery routes and recommendations</p>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={() => setActiveTab('map')}
              className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Map className="h-4 w-4" />
              <span>View Map</span>
            </button>
            
            <button
              onClick={() => setShowExportModal(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              <Download className="h-4 w-4" />
              <span>Export</span>
            </button>
          </div>
        </div>

        {/* Key metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Truck className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Routes</p>
                <p className="text-2xl font-bold text-gray-900">{currentRoutes.length}</p>
                <p className="text-xs text-gray-500">{totalStops} stops</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <Map className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Distance</p>
                <p className="text-2xl font-bold text-gray-900">{totalMiles.toFixed(1)}</p>
                <p className="text-xs text-gray-500">miles</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <DollarSign className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Fuel Cost</p>
                <p className="text-2xl font-bold text-gray-900">${totalCost.toFixed(2)}</p>
                <p className="text-xs text-gray-500">${(totalCost/totalStops).toFixed(2)} per stop</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Clock className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Time</p>
                <p className="text-2xl font-bold text-gray-900">{totalTime.toFixed(1)}</p>
                <p className="text-xs text-gray-500">hours</p>
              </div>
            </div>
          </div>
        </div>

        {/* Route details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Individual routes */}
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Route Details</h2>
            
            {currentRoutes.map((route, index) => (
              <div key={route.truck_id} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="p-4 border-b border-gray-100">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={cn("w-4 h-4 rounded-full", truckColors[index % truckColors.length])} />
                      <h3 className="font-medium text-gray-900">Truck {route.truck_id}</h3>
                      <span className="text-sm text-gray-500">
                        {route.stops.length} stops
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span>{route.total_miles.toFixed(1)} mi</span>
                      <span>{route.total_time_hours.toFixed(1)}h</span>
                      <span>${route.fuel_estimate.toFixed(2)}</span>
                    </div>
                  </div>
                  
                  {/* Utilization bar */}
                  <div className="mt-3">
                    <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                      <span>Capacity Utilization</span>
                      <span>{route.utilization_percent}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={cn(
                          "h-2 rounded-full transition-all duration-300",
                          route.utilization_percent > 90 ? "bg-red-500" :
                          route.utilization_percent > 75 ? "bg-yellow-500" : "bg-green-500"
                        )}
                        style={{ width: `${Math.min(route.utilization_percent, 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
                
                {/* Route stops */}
                <div className="p-4">
                  <div className="space-y-2">
                    {route.stops.map((stop, stopIndex) => (
                      <div key={stop.stop_id} className="flex items-center space-x-3 py-2">
                        <div className="flex-shrink-0 w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center text-xs font-medium text-gray-600">
                          {stopIndex + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-gray-900">
                              Stop #{stop.stop_id}
                            </span>
                            <span className="text-xs text-gray-500">
                              ETA: {stop.eta}
                            </span>
                          </div>
                          {stop.notes && (
                            <p className="text-xs text-gray-500 mt-1">{stop.notes}</p>
                          )}
                        </div>
                        <div className="text-xs text-gray-400">
                          {stop.distance_from_previous.toFixed(1)} mi
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {route.reasoning && (
                    <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                      <p className="text-xs text-gray-600">
                        <span className="font-medium">Routing Logic:</span> {route.reasoning}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* AI Summary and recommendations */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h3>
              
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-600">Average Utilization</span>
                    <span className="font-medium text-gray-900">{avgUtilization.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(avgUtilization, 100)}%` }}
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Cost per Mile</span>
                    <p className="font-medium text-gray-900">${(totalCost/totalMiles).toFixed(2)}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Stops per Hour</span>
                    <p className="font-medium text-gray-900">{(totalStops/totalTime).toFixed(1)}</p>
                  </div>
                </div>
                
                {/* Performance indicators */}
                <div className="space-y-2 pt-2 border-t border-gray-100">
                  <div className="flex items-center space-x-2">
                    <div className={cn(
                      "w-2 h-2 rounded-full",
                      avgUtilization > 80 ? "bg-green-500" : avgUtilization > 60 ? "bg-yellow-500" : "bg-red-500"
                    )} />
                    <span className="text-xs text-gray-600">
                      Capacity efficiency {avgUtilization > 80 ? "excellent" : avgUtilization > 60 ? "good" : "needs improvement"}
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <div className={cn(
                      "w-2 h-2 rounded-full",
                      totalTime <= currentRoutes.length * 8 ? "bg-green-500" : "bg-yellow-500"
                    )} />
                    <span className="text-xs text-gray-600">
                      {totalTime <= currentRoutes.length * 8 ? "No overtime risk" : "Potential overtime"}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* AI Summary */}
            {routingSummary && (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
                  <FileText className="h-5 w-5" />
                  <span>AI Analysis</span>
                </h3>
                
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed">
                    {routingSummary}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Export Modal */}
      {showExportModal && <ExportModal />}
    </div>
  );
};

export default ResultsSummary;