import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Download, FileText, Map, Truck, Clock, DollarSign, BarChart3, AlertTriangle } from 'lucide-react';
import { cn } from '../../utils/cn';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
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
      <div className="h-full flex items-center justify-center bg-background">
        <div className="text-center">
          <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h3 className="text-lg font-medium text-foreground mb-2">No Routes Generated</h3>
          <p className="text-muted-foreground mb-4">Create routes to see detailed analysis and recommendations.</p>
          <Button onClick={() => setActiveTab('input')}>
            Start Planning Routes
          </Button>
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
    <div className="h-full overflow-y-auto bg-background">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Route Analysis</h1>
            <p className="text-muted-foreground">Optimized delivery routes and recommendations</p>
          </div>
          
          <div className="flex space-x-3">
            <Button
              variant="outline"
              onClick={() => setActiveTab('map')}
              className="flex items-center space-x-2"
            >
              <Map className="h-4 w-4" />
              <span>View Map</span>
            </Button>
            
            <Button
              onClick={() => setShowExportModal(true)}
              className="flex items-center space-x-2"
            >
              <Download className="h-4 w-4" />
              <span>Export</span>
            </Button>
          </div>
        </div>

        {/* Key metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <Truck className="h-6 w-6 text-primary" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-muted-foreground">Total Routes</p>
                  <p className="text-2xl font-bold text-foreground">{currentRoutes.length}</p>
                  <p className="text-xs text-muted-foreground">{totalStops} stops</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-2 bg-green-500/10 rounded-lg">
                  <Map className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-muted-foreground">Total Distance</p>
                  <p className="text-2xl font-bold text-foreground">{totalMiles.toFixed(1)}</p>
                  <p className="text-xs text-muted-foreground">miles</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-500/10 rounded-lg">
                  <DollarSign className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-muted-foreground">Fuel Cost</p>
                  <p className="text-2xl font-bold text-foreground">${totalCost.toFixed(2)}</p>
                  <p className="text-xs text-muted-foreground">${(totalCost/totalStops).toFixed(2)} per stop</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-2 bg-purple-500/10 rounded-lg">
                  <Clock className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-muted-foreground">Total Time</p>
                  <p className="text-2xl font-bold text-foreground">{totalTime.toFixed(1)}</p>
                  <p className="text-xs text-muted-foreground">hours</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Route details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Individual routes */}
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-lg font-semibold text-foreground">Route Details</h2>
            
            {currentRoutes.map((route, index) => (
              <Card key={route.truck_id}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={cn("w-4 h-4 rounded-full", truckColors[index % truckColors.length])} />
                      <CardTitle className="text-base">Truck {route.truck_id}</CardTitle>
                      <span className="text-sm text-muted-foreground">
                        {route.stops.length} stops
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                      <span>{route.total_miles.toFixed(1)} mi</span>
                      <span>{route.total_time_hours.toFixed(1)}h</span>
                      <span>${route.fuel_estimate.toFixed(2)}</span>
                    </div>
                  </div>
                  
                  {/* Utilization bar */}
                  <div className="mt-3">
                    <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                      <span>Capacity Utilization</span>
                      <span>{route.utilization_percent}%</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
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
                </CardHeader>
                
                <CardContent>
                  <div className="space-y-2">
                    {route.stops.map((stop, stopIndex) => (
                      <div key={stop.stop_id} className="flex items-center space-x-3 py-2">
                        <div className="flex-shrink-0 w-6 h-6 bg-muted rounded-full flex items-center justify-center text-xs font-medium text-muted-foreground">
                          {stopIndex + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium text-foreground">
                              Stop #{stop.stop_id}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              ETA: {stop.eta}
                            </span>
                          </div>
                          {stop.notes && (
                            <p className="text-xs text-muted-foreground mt-1">{stop.notes}</p>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {stop.distance_from_previous.toFixed(1)} mi
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {route.reasoning && (
                    <div className="mt-4 p-3 bg-muted rounded-lg">
                      <p className="text-xs text-muted-foreground">
                        <span className="font-medium">Routing Logic:</span> {route.reasoning}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {/* AI Summary and recommendations */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-muted-foreground">Average Utilization</span>
                    <span className="font-medium text-foreground">{avgUtilization.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div 
                      className="bg-primary h-2 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(avgUtilization, 100)}%` }}
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Cost per Mile</span>
                    <p className="font-medium text-foreground">${(totalCost/totalMiles).toFixed(2)}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Stops per Hour</span>
                    <p className="font-medium text-foreground">{(totalStops/totalTime).toFixed(1)}</p>
                  </div>
                </div>
                
                {/* Performance indicators */}
                <div className="space-y-2 pt-2 border-t border-border">
                  <div className="flex items-center space-x-2">
                    <div className={cn(
                      "w-2 h-2 rounded-full",
                      avgUtilization > 80 ? "bg-green-500" : avgUtilization > 60 ? "bg-yellow-500" : "bg-red-500"
                    )} />
                    <span className="text-xs text-muted-foreground">
                      Capacity efficiency {avgUtilization > 80 ? "excellent" : avgUtilization > 60 ? "good" : "needs improvement"}
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <div className={cn(
                      "w-2 h-2 rounded-full",
                      totalTime <= currentRoutes.length * 8 ? "bg-green-500" : "bg-yellow-500"
                    )} />
                    <span className="text-xs text-muted-foreground">
                      {totalTime <= currentRoutes.length * 8 ? "No overtime risk" : "Potential overtime"}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* AI Summary */}
            {routingSummary && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <FileText className="h-5 w-5" />
                    <span>AI Analysis</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm max-w-none">
                    <pre className="whitespace-pre-wrap text-sm text-foreground leading-relaxed">
                      {routingSummary}
                    </pre>
                  </div>
                </CardContent>
              </Card>
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