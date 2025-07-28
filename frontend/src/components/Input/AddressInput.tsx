import React, { useState, useRef } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { MapPin, Upload, FileText, Copy, Sparkles, Play } from 'lucide-react';
import { cn } from '../../utils/cn';
import { useRouting } from '../../hooks/useRouting';
import toast from 'react-hot-toast';

const AddressInput: React.FC = () => {
  const [activeMethod, setActiveMethod] = useState<'manual' | 'paste' | 'csv'>('manual');
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const {
    addresses,
    setAddresses,
    constraints,
    setConstraints,
    depotAddress,
    setDepotAddress,
    csvFile,
    setCsvFile,
    isLoading
  } = useAppStore();
  
  const { performAutonomousRouting } = useRouting();

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.type !== 'text/csv' && !file.name.endsWith('.csv')) {
        toast.error('Please upload a CSV file');
        return;
      }
      setCsvFile(file);
      toast.success('CSV file uploaded successfully');
    }
  };

  const handlePasteAddresses = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setAddresses(text);
      setActiveMethod('paste');
      toast.success('Addresses pasted from clipboard');
    } catch (error) {
      toast.error('Failed to read from clipboard');
    }
  };

  const handleGenerateRoutes = async () => {
    if (!addresses.trim() && !csvFile) {
      toast.error('Please provide addresses or upload a CSV file');
      return;
    }

    try {
      await performAutonomousRouting(addresses, constraints, depotAddress);
    } catch (error) {
      console.error('Routing error:', error);
    }
  };

  const exampleAddresses = `Walmart Supercenter, 2801 Biscayne Blvd, Miami, FL
Home Depot, 1250 NW 167th St, Miami Gardens, FL
Publix, 1776 Alton Rd, Miami Beach, FL
Target, 18001 Biscayne Blvd, Aventura, FL
Kroger, 1045 Kane Concourse, Bay Harbor Islands, FL`;

  return (
    <div className="space-y-4">
      {/* Input method tabs */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
        <button
          onClick={() => setActiveMethod('manual')}
          className={cn(
            "flex-1 flex items-center justify-center space-x-1 py-2 px-3 rounded-md text-sm font-medium transition-colors",
            activeMethod === 'manual'
              ? "bg-white text-gray-900 shadow-sm"
              : "text-gray-600 hover:text-gray-900"
          )}
        >
          <FileText className="h-4 w-4" />
          <span>Manual</span>
        </button>
        
        <button
          onClick={() => setActiveMethod('paste')}
          className={cn(
            "flex-1 flex items-center justify-center space-x-1 py-2 px-3 rounded-md text-sm font-medium transition-colors",
            activeMethod === 'paste'
              ? "bg-white text-gray-900 shadow-sm"
              : "text-gray-600 hover:text-gray-900"
          )}
        >
          <Copy className="h-4 w-4" />
          <span>Paste</span>
        </button>
        
        <button
          onClick={() => setActiveMethod('csv')}
          className={cn(
            "flex-1 flex items-center justify-center space-x-1 py-2 px-3 rounded-md text-sm font-medium transition-colors",
            activeMethod === 'csv'
              ? "bg-white text-gray-900 shadow-sm"
              : "text-gray-600 hover:text-gray-900"
          )}
        >
          <Upload className="h-4 w-4" />
          <span>CSV</span>
        </button>
      </div>

      {/* Manual input */}
      {activeMethod === 'manual' && (
        <div className="space-y-3">
          <textarea
            value={addresses}
            onChange={(e) => setAddresses(e.target.value)}
            placeholder="Enter delivery addresses (one per line)&#10;&#10;Example:&#10;123 Main St, Atlanta, GA&#10;456 Oak Ave, Marietta, GA&#10;789 Pine Rd, Decatur, GA"
            className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none text-sm"
            disabled={isLoading}
          />
          
          <button
            onClick={() => setAddresses(exampleAddresses)}
            className="text-xs text-primary-600 hover:text-primary-700 flex items-center space-x-1"
            disabled={isLoading}
          >
            <Sparkles className="h-3 w-3" />
            <span>Use example addresses</span>
          </button>
        </div>
      )}

      {/* Paste input */}
      {activeMethod === 'paste' && (
        <div className="space-y-3">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <Copy className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-3">
              Copy addresses from any source and paste them here
            </p>
            <button
              onClick={handlePasteAddresses}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm"
              disabled={isLoading}
            >
              Paste from Clipboard
            </button>
          </div>
          
          {addresses && (
            <textarea
              value={addresses}
              onChange={(e) => setAddresses(e.target.value)}
              className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none text-sm"
              disabled={isLoading}
            />
          )}
        </div>
      )}

      {/* CSV upload */}
      {activeMethod === 'csv' && (
        <div className="space-y-3">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-600 mb-3">
              Upload a CSV file with delivery addresses
            </p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm"
              disabled={isLoading}
            >
              Choose CSV File
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>
          
          {csvFile && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex items-center space-x-2">
                <FileText className="h-4 w-4 text-green-600" />
                <span className="text-sm text-green-800 font-medium">{csvFile.name}</span>
                <span className="text-xs text-green-600">
                  ({(csvFile.size / 1024).toFixed(1)} KB)
                </span>
              </div>
            </div>
          )}
          
          <div className="text-xs text-gray-500">
            <p className="font-medium">Expected CSV format:</p>
            <code className="bg-gray-100 px-1 rounded text-xs">
              Address, Pallets, Special, TimeWindow
            </code>
          </div>
        </div>
      )}

      {/* Optional settings */}
      <div className="space-y-3 pt-2 border-t border-gray-200">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Depot Address (Optional)
          </label>
          <input
            type="text"
            value={depotAddress}
            onChange={(e) => setDepotAddress(e.target.value)}
            placeholder="Starting warehouse or depot location"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
            disabled={isLoading}
          />
        </div>
        
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Additional Constraints
          </label>
          <textarea
            value={constraints}
            onChange={(e) => setConstraints(e.target.value)}
            placeholder="e.g., 'Avoid highways during rush hour' or 'Deliver frozen goods first'"
            className="w-full h-16 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none text-sm"
            disabled={isLoading}
          />
        </div>
      </div>

      {/* Generate routes button */}
      <button
        onClick={handleGenerateRoutes}
        disabled={(!addresses.trim() && !csvFile) || isLoading}
        className={cn(
          "w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-lg font-medium transition-colors",
          (!addresses.trim() && !csvFile) || isLoading
            ? "bg-gray-300 text-gray-500 cursor-not-allowed"
            : "bg-primary-600 text-white hover:bg-primary-700"
        )}
      >
        {isLoading ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            <span>Optimizing Routes...</span>
          </>
        ) : (
          <>
            <Play className="h-4 w-4" />
            <span>Generate Optimal Routes</span>
          </>
        )}
      </button>
    </div>
  );
};

export default AddressInput;