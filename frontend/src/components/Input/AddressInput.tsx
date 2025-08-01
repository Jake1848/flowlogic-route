import React, { useState, useRef } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { MapPin, Upload, FileText, Copy, Play } from 'lucide-react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Card, CardContent } from '../ui/card';
import { useRouting } from '../../hooks/useRouting';
import toast from 'react-hot-toast';

const AddressInput: React.FC = () => {
  const [activeMethod, setActiveMethod] = useState<'manual' | 'paste' | 'csv'>('manual');
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const {
    addresses,
    setAddresses,
    specialInstructions,
    setSpecialInstructions,
    depotAddress,
    setDepotAddress
  } = useAppStore();
  
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const isLoading = false;
  
  const { generateRoutes } = useRouting();

  const convertTextToAddresses = (text: string) => {
    const lines = text.split('\n').filter(line => line.trim());
    return lines.map((line) => ({
      Address: line.trim(),
      Pallets: Math.floor(Math.random() * 10) + 1,
      Special: 'Standard',
      TimeWindow: '8:00-17:00'
    }));
  };

  const convertAddressesToText = (addresses: any[]) => {
    return addresses.map(addr => addr.Address).join('\n');
  };

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
      const lines = text.split('\n').filter(line => line.trim());
      if (lines.length === 0) {
        toast.error('No addresses found in clipboard');
        return;
      }
      
      const addressArray = lines.map((line, index) => ({
        Address: line.trim(),
        Pallets: Math.floor(Math.random() * 10) + 1,
        Special: 'Standard',
        TimeWindow: '8:00-17:00'
      }));
      
      setAddresses(addressArray);
      setActiveMethod('paste');
      toast.success(`Pasted ${addressArray.length} addresses from clipboard`);
    } catch (error) {
      toast.error('Failed to read from clipboard');
    }
  };

  const handleGenerateRoutes = async () => {
    if (addresses.length === 0 && !csvFile) {
      toast.error('Please provide addresses or upload a CSV file');
      return;
    }

    try {
      await generateRoutes();
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
    <div className="space-y-6">
      {/* Input method tabs */}
      <Tabs value={activeMethod} onValueChange={(value) => setActiveMethod(value as any)}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="manual" className="flex items-center space-x-2">
            <FileText className="h-4 w-4" />
            <span>Manual</span>
          </TabsTrigger>
          <TabsTrigger value="paste" className="flex items-center space-x-2">
            <Copy className="h-4 w-4" />
            <span>Paste</span>
          </TabsTrigger>
          <TabsTrigger value="csv" className="flex items-center space-x-2">
            <Upload className="h-4 w-4" />
            <span>CSV</span>
          </TabsTrigger>
        </TabsList>

        {/* Manual input */}
        <TabsContent value="manual" className="space-y-3">
          <Textarea
            value={convertAddressesToText(addresses)}
            onChange={(e) => setAddresses(convertTextToAddresses(e.target.value))}
            placeholder="Enter delivery addresses (one per line)

Example:
123 Main St, Atlanta, GA
456 Oak Ave, Marietta, GA
789 Pine Rd, Decatur, GA"
            className="min-h-[128px] resize-none"
            disabled={isLoading}
          />
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setAddresses(exampleAddresses)}
            disabled={isLoading}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            Use example addresses
          </Button>
        </TabsContent>

        {/* Paste input */}
        <TabsContent value="paste" className="space-y-3">
          <Card>
            <CardContent className="p-6 text-center">
              <Copy className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-muted-foreground mb-3">
                Copy addresses from any source and paste them here
              </p>
              <Button
                onClick={handlePasteAddresses}
                disabled={isLoading}
              >
                Paste from Clipboard
              </Button>
            </CardContent>
          </Card>
          
          {addresses.length > 0 && (
            <Textarea
              value={convertAddressesToText(addresses)}
              onChange={(e) => setAddresses(convertTextToAddresses(e.target.value))}
              className="min-h-[96px] resize-none"
              disabled={isLoading}
            />
          )}
        </TabsContent>

        {/* CSV upload */}
        <TabsContent value="csv" className="space-y-3">
          <Card>
            <CardContent className="p-6 text-center">
              <Upload className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-muted-foreground mb-3">
                Upload a CSV file with delivery addresses
              </p>
              <Button
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
              >
                Choose CSV File
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleFileUpload}
                className="hidden"
              />
            </CardContent>
          </Card>
          
          {csvFile && (
            <Card className="border-green-200 bg-green-50/50">
              <CardContent className="p-3">
                <div className="flex items-center space-x-2">
                  <FileText className="h-4 w-4 text-green-600" />
                  <span className="text-sm text-green-800 font-medium">{csvFile.name}</span>
                  <span className="text-xs text-green-600">
                    ({(csvFile.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
              </CardContent>
            </Card>
          )}
          
          <div className="text-xs text-muted-foreground">
            <p className="font-medium">Expected CSV format:</p>
            <code className="bg-muted px-1 rounded text-xs">
              Address, Pallets, Special, TimeWindow
            </code>
          </div>
        </TabsContent>
      </Tabs>

      {/* Optional settings */}
      <div className="space-y-4 pt-4 border-t border-border">
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Depot Address (Optional)
          </label>
          <input
            type="text"
            value={depotAddress}
            onChange={(e) => setDepotAddress(e.target.value)}
            placeholder="Starting warehouse or depot location"
            className="w-full px-3 py-2 bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent text-sm"
            disabled={isLoading}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Additional Constraints
          </label>
          <Textarea
            value={specialInstructions}
            onChange={(e) => setSpecialInstructions(e.target.value)}
            placeholder="e.g., 'Avoid highways during rush hour' or 'Deliver frozen goods first'"
            className="min-h-[64px] resize-none"
            disabled={isLoading}
          />
        </div>
      </div>

      {/* Generate routes button */}
      <Button
        onClick={handleGenerateRoutes}
        disabled={(addresses.length === 0 && !csvFile) || isLoading}
        size="lg"
        className="w-full"
      >
        {isLoading ? (
          <>
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
            <span>Optimizing Routes...</span>
          </>
        ) : (
          <>
            <Play className="h-4 w-4 mr-2" />
            <span>Generate Optimal Routes</span>
          </>
        )}
      </Button>
    </div>
  );
};

export default AddressInput;