import React, { useState } from 'react';
import { X, Download, FileText, Image, CheckCircle } from 'lucide-react';
import { cn } from '../../utils/cn';
import toast from 'react-hot-toast';
import Papa from 'papaparse';

interface ExportModalProps {
  onClose: () => void;
  routes: any[];
  routingSummary: string;
}

const ExportModal: React.FC<ExportModalProps> = ({ onClose, routes, routingSummary }) => {
  const [format, setFormat] = useState<'csv' | 'pdf'>('csv');
  const [includeMap, setIncludeMap] = useState(true);
  const [includeSummary, setIncludeSummary] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  
  // Component not using store anymore - using props instead
  const currentRoutes = routes;

  const handleExport = async () => {
    setIsExporting(true);
    
    try {
      if (format === 'csv') {
        // Enhanced CSV export with stop details
        const csvData: any[] = [];
        
        // Add summary row first
        csvData.push(['ROUTE SUMMARY']);
        csvData.push(['Truck ID', 'Total Stops', 'Total Miles', 'Total Hours', 'Fuel Cost', 'Utilization %']);
        
        currentRoutes.forEach(route => {
          csvData.push([
            route.truck_id || 'Unknown',
            route.stops?.length || 0,
            route.total_miles?.toFixed(1) || '0',
            route.total_time_hours?.toFixed(1) || '0',
            `$${route.fuel_estimate?.toFixed(2) || '0.00'}`,
            `${route.utilization_percent?.toFixed(1) || '0'}%`
          ]);
        });
        
        // Add stop details
        csvData.push(['']); // Empty row
        csvData.push(['STOP DETAILS']);
        csvData.push(['Truck ID', 'Stop #', 'Address', 'ETA', 'Pallets', 'Time Window', 'Service Time']);
        
        currentRoutes.forEach(route => {
          route.stops?.forEach((stop: any, index: number) => {
            csvData.push([
              route.truck_id || 'Unknown',
              index + 1,
              stop.address || `Stop ${stop.stop_id}`,
              stop.eta || stop.estimated_arrival || 'N/A',
              stop.pallets || 0,
              `${stop.time_window_start || '08:00'} - ${stop.time_window_end || '17:00'}`,
              `${stop.service_time_minutes || 15} min`
            ]);
          });
        });
        
        const csv = Papa.unparse(csvData);
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        link.setAttribute('href', url);
        link.setAttribute('download', `routes_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else {
        // PDF export using simple HTML to PDF approach
        const printWindow = window.open('', '_blank');
        if (!printWindow) {
          toast.error('Please allow popups to export PDF');
          return;
        }
        
        const htmlContent = `
          <!DOCTYPE html>
          <html>
          <head>
            <title>FlowLogic Route Report</title>
            <style>
              body { font-family: Arial, sans-serif; margin: 20px; }
              .header { text-align: center; margin-bottom: 30px; }
              .summary { background: #f5f5f5; padding: 15px; margin-bottom: 20px; }
              .route { margin-bottom: 30px; }
              .route h3 { color: #333; border-bottom: 2px solid #007bff; }
              .stop { margin: 10px 0; padding: 10px; background: #f9f9f9; }
              table { width: 100%; border-collapse: collapse; margin: 20px 0; }
              th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
              th { background-color: #f2f2f2; }
            </style>
          </head>
          <body>
            <div class="header">
              <h1>FlowLogic Route Optimization Report</h1>
              <p>Generated on ${new Date().toLocaleDateString()}</p>
            </div>
            
            <div class="summary">
              <h2>Executive Summary</h2>
              <table>
                <tr><th>Total Routes</th><td>${currentRoutes.length}</td></tr>
                <tr><th>Total Stops</th><td>${totalStops}</td></tr>
                <tr><th>Total Distance</th><td>${totalMiles.toFixed(1)} miles</td></tr>
                <tr><th>Total Fuel Cost</th><td>$${currentRoutes.reduce((sum, route) => sum + route.fuel_estimate, 0).toFixed(2)}</td></tr>
              </table>
            </div>
            
            ${currentRoutes.map(route => `
              <div class="route">
                <h3>Truck ${route.truck_id} - ${route.stops.length} Stops</h3>
                <p><strong>Distance:</strong> ${route.total_miles.toFixed(1)} mi | 
                   <strong>Time:</strong> ${route.total_time_hours.toFixed(1)}h | 
                   <strong>Fuel:</strong> $${route.fuel_estimate.toFixed(2)} | 
                   <strong>Utilization:</strong> ${route.utilization_percent}%</p>
                
                <h4>Stop Details:</h4>
                ${route.stops.map((stop: any, index: number) => `
                  <div class="stop">
                    <strong>${index + 1}. ${stop.address || `Stop #${stop.stop_id}`}</strong><br>
                    ETA: ${stop.eta} | Pallets: ${stop.pallets} | 
                    Window: ${stop.time_window_start} - ${stop.time_window_end}
                    ${stop.notes ? `<br><em>${stop.notes}</em>` : ''}
                  </div>
                `).join('')}
              </div>
            `).join('')}
            
            ${includeSummary && routingSummary ? `
              <div class="summary">
                <h2>AI Analysis & Recommendations</h2>
                <pre style="white-space: pre-wrap; font-family: inherit;">${routingSummary}</pre>
              </div>
            ` : ''}
          </body>
          </html>
        `;
        
        printWindow.document.write(htmlContent);
        printWindow.document.close();
        printWindow.focus();
        
        // Give the content time to load before printing
        setTimeout(() => {
          printWindow.print();
        }, 500);
      }
      
      toast.success(`Routes exported as ${format.toUpperCase()}`);
      onClose();
    } catch (error) {
      toast.error('Export failed. Please try again.');
      console.error('Export error:', error);
    } finally {
      setIsExporting(false);
    }
  };

  const totalStops = currentRoutes.reduce((sum, route) => sum + route.stops.length, 0);
  const totalMiles = currentRoutes.reduce((sum, route) => sum + route.total_miles, 0);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Export Routes</h2>
          <button
            onClick={() => onClose()}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Export summary */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-2">Export Summary</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Routes:</span>
                <span className="font-medium text-gray-900 ml-1">{currentRoutes.length}</span>
              </div>
              <div>
                <span className="text-gray-600">Stops:</span>
                <span className="font-medium text-gray-900 ml-1">{totalStops}</span>
              </div>
              <div>
                <span className="text-gray-600">Distance:</span>
                <span className="font-medium text-gray-900 ml-1">{totalMiles.toFixed(1)} mi</span>
              </div>
              <div>
                <span className="text-gray-600">Format:</span>
                <span className="font-medium text-gray-900 ml-1">{format.toUpperCase()}</span>
              </div>
            </div>
          </div>

          {/* Format selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Export Format
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setFormat('csv')}
                className={cn(
                  "flex items-center space-x-3 p-4 border rounded-lg transition-colors",
                  format === 'csv'
                    ? "border-primary-500 bg-primary-50 text-primary-700"
                    : "border-gray-200 hover:border-gray-300"
                )}
              >
                <FileText className="h-5 w-5" />
                <div className="text-left">
                  <div className="font-medium">CSV</div>
                  <div className="text-xs text-gray-500">Spreadsheet data</div>
                </div>
                {format === 'csv' && <CheckCircle className="h-4 w-4 text-primary-600" />}
              </button>

              <button
                onClick={() => setFormat('pdf')}
                className={cn(
                  "flex items-center space-x-3 p-4 border rounded-lg transition-colors",
                  format === 'pdf'
                    ? "border-primary-500 bg-primary-50 text-primary-700"
                    : "border-gray-200 hover:border-gray-300"
                )}
              >
                <Image className="h-5 w-5" />
                <div className="text-left">
                  <div className="font-medium">PDF</div>
                  <div className="text-xs text-gray-500">Report format</div>
                </div>
                {format === 'pdf' && <CheckCircle className="h-4 w-4 text-primary-600" />}
              </button>
            </div>
          </div>

          {/* Export options */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Include in Export
            </label>
            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeSummary}
                  onChange={(e) => setIncludeSummary(e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-3 text-sm text-gray-700">AI Analysis & Recommendations</span>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeMap}
                  onChange={(e) => setIncludeMap(e.target.checked)}
                  disabled={format === 'csv'}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500 disabled:opacity-50"
                />
                <span className={cn(
                  "ml-3 text-sm",
                  format === 'csv' ? "text-gray-400" : "text-gray-700"
                )}>
                  Route Map Visualization
                  {format === 'csv' && (
                    <span className="text-xs text-gray-400 block">PDF only</span>
                  )}
                </span>
              </label>
            </div>
          </div>

          {/* Preview */}
          {format === 'csv' && (
            <div className="text-xs text-gray-600">
              <p className="font-medium mb-1">CSV will include:</p>
              <ul className="list-disc list-inside space-y-1 text-gray-500">
                <li>Route assignments and stop sequences</li>
                <li>Truck details and capacities</li>
                <li>Distance and time estimates</li>
                <li>Cost calculations</li>
                {includeSummary && <li>AI recommendations and insights</li>}
              </ul>
            </div>
          )}

          {format === 'pdf' && (
            <div className="text-xs text-gray-600">
              <p className="font-medium mb-1">PDF will include:</p>
              <ul className="list-disc list-inside space-y-1 text-gray-500">
                <li>Executive summary with key metrics</li>
                <li>Detailed route breakdown by truck</li>
                <li>Performance analysis and KPIs</li>
                {includeMap && <li>Route map visualization</li>}
                {includeSummary && <li>AI-generated insights and recommendations</li>}
              </ul>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200">
          <button
            onClick={() => onClose()}
            className="px-4 py-2 text-gray-700 hover:text-gray-900 transition-colors"
            disabled={isExporting}
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={isExporting}
            className={cn(
              "flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors",
              isExporting
                ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                : "bg-primary-600 text-white hover:bg-primary-700"
            )}
          >
            {isExporting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Exporting...</span>
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                <span>Export {format.toUpperCase()}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExportModal;