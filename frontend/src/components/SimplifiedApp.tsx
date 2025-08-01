import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Textarea } from './ui/textarea';
import { Upload, FileText, Copy, Play, MapPin, Package, Clock } from 'lucide-react';
import { useRouting } from '../hooks/useRouting';
import toast from 'react-hot-toast';
import RouteMap from './Map/RouteMap';
import ResultsSummary from './Results/ResultsSummary';

const SimplifiedApp: React.FC = () => {
  const [inputMethod, setInputMethod] = useState<'paste' | 'upload'>('paste');
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  
  const {
    addresses,
    setAddresses,
    specialInstructions,
    setSpecialInstructions,
    depotAddress,
    setDepotAddress,
    routes
  } = useAppStore();
  
  // Local state for CSV and loading since they're not in the new store
  const [csvFile, setCsvFile] = React.useState<File | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const currentRoutes = routes;
  
  const { generateRoutes, isLoading: routingLoading } = useRouting();

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

  const exampleAddresses = `123 Main Street, Atlanta, GA 30303
456 Peachtree Street NE, Atlanta, GA 30308
789 Ponce de Leon Ave, Atlanta, GA 30306
1010 West Peachtree St NW, Atlanta, GA 30309
2020 Marietta Street NW, Atlanta, GA 30318`;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b border-border px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <img src="/logo.png" alt="FlowLogic RouteAI" className="h-12 w-12 object-contain" />
            <div>
              <h1 className="text-2xl font-bold text-foreground">FlowLogic RouteAI</h1>
              <p className="text-sm text-muted-foreground">Autonomous Truck Routing</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        {!currentRoutes.length ? (
          /* Input Section */
          <div className="space-y-6">
            {/* Step 1: Add Addresses */}
            <Card>
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground font-bold">
                    1
                  </div>
                  <CardTitle>Add Delivery Addresses</CardTitle>
                </div>
                <CardDescription>
                  Enter your delivery locations by pasting addresses or uploading a CSV file
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs value={inputMethod} onValueChange={(v) => setInputMethod(v as any)}>
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="paste">
                      <Copy className="h-4 w-4 mr-2" />
                      Paste Addresses
                    </TabsTrigger>
                    <TabsTrigger value="upload">
                      <Upload className="h-4 w-4 mr-2" />
                      Upload CSV
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="paste" className="space-y-4">
                    <Textarea
                      value={convertAddressesToText(addresses)}
                      onChange={(e) => setAddresses(convertTextToAddresses(e.target.value))}
                      placeholder="Enter delivery addresses (one per line)

Example:
123 Main St, Atlanta, GA 30303
456 Oak Ave, Marietta, GA 30060
789 Pine Rd, Decatur, GA 30030"
                      className="min-h-[200px] font-mono text-sm"
                      disabled={isLoading}
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setAddresses(exampleAddresses)}
                      disabled={isLoading}
                    >
                      Use Example Addresses
                    </Button>
                  </TabsContent>

                  <TabsContent value="upload" className="space-y-4">
                    <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
                      <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                      <p className="text-sm text-muted-foreground mb-4">
                        Upload a CSV file with delivery addresses
                      </p>
                      <Button onClick={() => fileInputRef.current?.click()} disabled={isLoading}>
                        Choose CSV File
                      </Button>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".csv"
                        onChange={handleFileUpload}
                        className="hidden"
                      />
                    </div>
                    
                    {csvFile && (
                      <div className="flex items-center space-x-2 p-3 bg-green-500/10 text-green-600 rounded-lg">
                        <FileText className="h-5 w-5" />
                        <span className="font-medium">{csvFile.name}</span>
                        <span className="text-sm">({(csvFile.size / 1024).toFixed(1)} KB)</span>
                      </div>
                    )}
                    
                    <div className="text-xs text-muted-foreground bg-muted p-3 rounded">
                      <p className="font-medium mb-1">CSV Format:</p>
                      <code>Address, Pallets, Special, TimeWindow</code>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>

            {/* Step 2: Optional Settings */}
            <Card>
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-muted text-muted-foreground font-bold">
                    2
                  </div>
                  <CardTitle>Optional Settings</CardTitle>
                </div>
                <CardDescription>
                  Add constraints and specify your depot location (optional)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    <MapPin className="inline h-4 w-4 mr-1" />
                    Depot/Warehouse Address
                  </label>
                  <input
                    type="text"
                    value={depotAddress}
                    onChange={(e) => setDepotAddress(e.target.value)}
                    placeholder="e.g., 500 Distribution Way, Atlanta, GA 30336"
                    className="w-full px-3 py-2 bg-background border border-input rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                    disabled={isLoading}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">
                    <Package className="inline h-4 w-4 mr-1" />
                    Special Instructions
                  </label>
                  <Textarea
                    value={specialInstructions}
                    onChange={(e) => setSpecialInstructions(e.target.value)}
                    placeholder="e.g., 'Avoid highways during rush hour' or 'Deliver frozen goods first'"
                    className="min-h-[80px]"
                    disabled={isLoading}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Step 3: Generate Routes */}
            <Card>
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground font-bold">
                    3
                  </div>
                  <CardTitle>Generate Optimal Routes</CardTitle>
                </div>
                <CardDescription>
                  Click below to optimize your delivery routes
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={handleGenerateRoutes}
                  disabled={(!addresses.trim() && !csvFile) || isLoading}
                  size="lg"
                  className="w-full"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2" />
                      <span>Optimizing Routes...</span>
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      <span>Generate Optimal Routes</span>
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Quick Tips */}
            <Card className="bg-muted/50">
              <CardHeader>
                <CardTitle className="text-base">Quick Tips</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <div className="flex items-start space-x-2">
                  <Clock className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <p>Add time windows in your CSV for specific delivery times</p>
                </div>
                <div className="flex items-start space-x-2">
                  <Package className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <p>Include special handling requirements like "Refrigerated" or "Fragile"</p>
                </div>
                <div className="flex items-start space-x-2">
                  <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <p>Specify a depot address to optimize routes from your warehouse</p>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          /* Results Section */
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold">Route Optimization Results</h2>
              <Button
                variant="outline"
                onClick={() => {
                  useAppStore.getState().setCurrentRoutes([]);
                  useAppStore.getState().setAddresses('');
                  useAppStore.getState().setCsvFile(null);
                }}
              >
                Start New Route
              </Button>
            </div>
            
            <Tabs defaultValue="summary" className="space-y-4">
              <TabsList>
                <TabsTrigger value="summary">Summary</TabsTrigger>
                <TabsTrigger value="map">Map View</TabsTrigger>
              </TabsList>
              
              <TabsContent value="summary">
                <ResultsSummary />
              </TabsContent>
              
              <TabsContent value="map">
                <Card>
                  <CardContent className="p-0">
                    <div className="h-[600px]">
                      <RouteMap />
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        )}
      </main>
    </div>
  );
};

export default SimplifiedApp;