import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { X, Download, FileText, Image, CheckCircle } from 'lucide-react';
import { cn } from '../../utils/cn';
import { useExport } from '../../hooks/useExport';
import toast from 'react-hot-toast';

const ExportModal: React.FC = () => {
  const [format, setFormat] = useState<'csv' | 'pdf'>('csv');
  const [includeMap, setIncludeMap] = useState(true);
  const [includeSummary, setIncludeSummary] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  
  const { setShowExportModal, currentRoutes } = useAppStore();
  const { exportRoutes } = useExport();

  const handleExport = async () => {
    setIsExporting(true);
    
    try {
      await exportRoutes({
        format,
        includeMap,
        includeSummary
      });
      
      toast.success(`Routes exported as ${format.toUpperCase()}`);
      setShowExportModal(false);
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
            onClick={() => setShowExportModal(false)}
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
            onClick={() => setShowExportModal(false)}
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