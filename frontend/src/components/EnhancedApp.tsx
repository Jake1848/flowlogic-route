import React, { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Textarea } from './ui/textarea';
import { 
  Upload, 
  FileText, 
  Copy, 
  Play, 
  MapPin, 
  Package, 
  Clock,
  Truck,
  ArrowRight,
  CheckCircle,
  Info,
  Building,
  Navigation,
  Target,
  Calculator,
  Route,
  HelpCircle
} from 'lucide-react';
import { useRouting } from '../hooks/useRouting';
import toast from 'react-hot-toast';
import RouteMap from './Map/RouteMap';
import ResultsSummary from './Results/ResultsSummary';
import Papa from 'papaparse';

interface Address {
  Address: string;
  Pallets: number;
  Special: string;
  TimeWindow: string;
}

const EnhancedApp: React.FC = () => {
  const [currentView, setCurrentView] = useState<'home' | 'input' | 'results'>('home');
  const [inputMethod, setInputMethod] = useState<'paste' | 'upload'>('paste');
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const {
    addresses,
    depotAddress,
    specialInstructions,
    routes,
    routingSummary,
    setAddresses,
    setDepotAddress,
    setSpecialInstructions,
    clearAll,
  } = useAppStore();

  const { generateRoutes, isLoading } = useRouting();

  const handleGenerateRoutes = async () => {
    if (addresses.length === 0) {
      toast.error('Please add delivery addresses first');
      return;
    }

    const result = await generateRoutes();
    if (result) {
      setCurrentView('results');
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    Papa.parse(file, {
      complete: (results) => {
        const validRows = results.data.filter((row: any) => 
          row.Address && row.Address.trim() !== ''
        ).map((row: any) => ({
          Address: row.Address?.trim() || '',
          Pallets: parseInt(row.Pallets) || Math.floor(Math.random() * 10) + 1,
          Special: row.Special || 'Standard',
          TimeWindow: row.TimeWindow || '8:00-17:00'
        }));
        
        if (validRows.length > 0) {
          setAddresses(validRows);
          toast.success(`Loaded ${validRows.length} addresses`);
        } else {
          toast.error('No valid addresses found in CSV');
        }
      },
      header: true,
      skipEmptyLines: true,
    });
  };

  const handlePasteAddresses = (text: string) => {
    const lines = text.split('\n').filter(line => line.trim());
    if (lines.length === 0) {
      toast.error('No addresses found');
      return;
    }

    const newAddresses = lines.map((line, index) => ({
      Address: line.trim(),
      Pallets: Math.floor(Math.random() * 10) + 1,
      Special: 'Standard',
      TimeWindow: '8:00-17:00'
    }));

    setAddresses(newAddresses);
    toast.success(`Added ${newAddresses.length} addresses`);
  };

  const loadExampleAddresses = () => {
    const exampleText = `123 Main Street, Atlanta, GA 30303
456 Peachtree Street NE, Atlanta, GA 30308
789 Ponce de Leon Ave, Atlanta, GA 30306
1010 West Peachtree St NW, Atlanta, GA 30309
2020 Marietta Street NW, Atlanta, GA 30318`;
    
    handlePasteAddresses(exampleText);
  };

  const startNewRoute = () => {
    clearAll();
    setCurrentView('home');
  };

  if (currentView === 'home') {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        {/* Header */}
        <header className="border-b border-border bg-card">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <img src="/logo.png" alt="FlowLogic RouteAI" className="h-12 w-12" />
              <h1 className="text-2xl font-bold text-foreground">FlowLogic RouteAI</h1>
            </div>
          </div>
        </header>

        {/* Hero Section */}
        <div className="flex-1 max-w-7xl mx-auto px-4 py-12">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-foreground mb-4">
              Optimize Your Delivery Routes with AI
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Turn your delivery addresses into optimized routes in seconds. Save time, fuel, and money.
            </p>
          </div>

          {/* How It Works */}
          <div className="mb-12">
            <h3 className="text-2xl font-semibold text-center mb-8">How It Works</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <MapPin className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle>1. Add Delivery Addresses</CardTitle>
                  <CardDescription>
                    Input your delivery locations. Each address represents a stop on your route.
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground">
                  <ul className="space-y-2">
                    <li>• Paste addresses directly from your system</li>
                    <li>• Upload a CSV file with addresses</li>
                    <li>• Include special instructions per stop</li>
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <Calculator className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle>2. AI Optimization</CardTitle>
                  <CardDescription>
                    Our AI analyzes all possible routes and finds the most efficient path.
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground">
                  <ul className="space-y-2">
                    <li>• Minimizes total distance and time</li>
                    <li>• Considers traffic patterns</li>
                    <li>• Respects time windows & constraints</li>
                  </ul>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <Route className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle>3. Get Optimized Routes</CardTitle>
                  <CardDescription>
                    Receive turn-by-turn directions with ETAs for each stop.
                  </CardDescription>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground">
                  <ul className="space-y-2">
                    <li>• Routes assigned to available trucks</li>
                    <li>• Estimated arrival times per stop</li>
                    <li>• Total cost and distance metrics</li>
                  </ul>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Key Concepts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building className="h-5 w-5" />
                  What is a Depot?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-3">
                  The depot is your starting location - typically your warehouse, distribution center, or business location.
                </p>
                <div className="bg-muted rounded-lg p-4">
                  <p className="text-sm font-medium mb-2">Example:</p>
                  <p className="text-sm text-muted-foreground">
                    "500 Industrial Way, Atlanta, GA 30318"
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    All routes start and end at the depot
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Navigation className="h-5 w-5" />
                  Understanding Routes
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-3">
                  Each route is a sequence of stops assigned to one truck, optimized for efficiency.
                </p>
                <div className="bg-muted rounded-lg p-4">
                  <p className="text-sm font-medium mb-2">Route includes:</p>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• Depot → Stop 1 → Stop 2 → ... → Depot</li>
                    <li>• Estimated time at each stop</li>
                    <li>• Total distance and duration</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Example Use Cases */}
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Common Use Cases</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-start gap-3">
                  <Package className="h-5 w-5 text-primary mt-1" />
                  <div>
                    <p className="font-medium">E-commerce Delivery</p>
                    <p className="text-sm text-muted-foreground">
                      Optimize daily package deliveries to customers
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Truck className="h-5 w-5 text-primary mt-1" />
                  <div>
                    <p className="font-medium">Fleet Management</p>
                    <p className="text-sm text-muted-foreground">
                      Assign routes to multiple trucks efficiently
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Clock className="h-5 w-5 text-primary mt-1" />
                  <div>
                    <p className="font-medium">Service Calls</p>
                    <p className="text-sm text-muted-foreground">
                      Plan technician routes with time windows
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* CTA */}
          <div className="text-center">
            <Button 
              size="lg" 
              onClick={() => setCurrentView('input')}
              className="gap-2"
            >
              Start Planning Routes
              <ArrowRight className="h-5 w-5" />
            </Button>
            <p className="text-sm text-muted-foreground mt-4">
              No sign-up required • Free to use
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (currentView === 'results' && routes.length > 0) {
    return (
      <div className="min-h-screen bg-background flex flex-col">
        {/* Header */}
        <header className="border-b border-border bg-card">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <img src="/logo.png" alt="FlowLogic RouteAI" className="h-12 w-12" />
              <h1 className="text-2xl font-bold text-foreground">Route Results</h1>
            </div>
            <Button onClick={startNewRoute} variant="outline">
              Start New Route
            </Button>
          </div>
        </header>

        {/* Results */}
        <div className="flex-1">
          <Tabs defaultValue="summary" className="h-full">
            <div className="border-b border-border">
              <div className="max-w-7xl mx-auto px-4">
                <TabsList className="h-12">
                  <TabsTrigger value="summary">Summary</TabsTrigger>
                  <TabsTrigger value="map">Map View</TabsTrigger>
                </TabsList>
              </div>
            </div>
            
            <TabsContent value="summary" className="m-0 h-[calc(100%-3rem)]">
              <div className="h-full overflow-y-auto">
                <div className="max-w-7xl mx-auto p-4">
                  <ResultsSummary routes={routes} routingSummary={routingSummary} />
                </div>
              </div>
            </TabsContent>
            
            <TabsContent value="map" className="m-0 h-[calc(100%-3rem)]">
              <RouteMap routes={routes} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    );
  }

  // Input View
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <img src="/logo.png" alt="FlowLogic RouteAI" className="h-12 w-12" />
            <h1 className="text-2xl font-bold text-foreground">Plan Your Routes</h1>
          </div>
          <Button onClick={() => setCurrentView('home')} variant="outline">
            Back to Home
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 max-w-5xl mx-auto px-4 py-8 space-y-6">
        {/* Step 1: Addresses */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-semibold">
                1
              </div>
              <div>
                <CardTitle>Add Delivery Addresses</CardTitle>
                <CardDescription>
                  Each address is a delivery stop. The system will optimize the order.
                </CardDescription>
              </div>
            </div>
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

              <TabsContent value="paste">
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Paste your delivery addresses (one per line)
                    </label>
                    <Textarea
                      placeholder="123 Main St, Atlanta, GA 30303
456 Oak Ave, Decatur, GA 30030
789 Pine St, Marietta, GA 30060"
                      className="min-h-[200px] font-mono text-sm"
                      onChange={(e) => {
                        if (e.target.value) {
                          handlePasteAddresses(e.target.value);
                        }
                      }}
                    />
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={loadExampleAddresses}
                  >
                    <FileText className="h-4 w-4 mr-2" />
                    Load Example Addresses
                  </Button>
                </div>
              </TabsContent>

              <TabsContent value="upload">
                <div className="space-y-4">
                  <div className="border-2 border-dashed border-border rounded-lg p-8 text-center">
                    <Upload className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-sm text-muted-foreground mb-4">
                      Upload a CSV file with delivery information
                    </p>
                    <Button onClick={() => fileInputRef.current?.click()}>
                      Choose File
                    </Button>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".csv"
                      className="hidden"
                      onChange={handleFileUpload}
                    />
                  </div>
                  <div className="bg-muted rounded-lg p-4">
                    <p className="text-sm font-medium mb-2">CSV Format:</p>
                    <pre className="text-xs text-muted-foreground">
Address,Pallets,Special,TimeWindow
"123 Main St, City, State ZIP",5,Standard,8:00-17:00
"456 Oak Ave, City, State ZIP",3,Refrigerated,9:00-12:00</pre>
                  </div>
                </div>
              </TabsContent>
            </Tabs>

            {addresses.length > 0 && (
              <div className="mt-4 p-3 bg-muted rounded-lg">
                <p className="text-sm font-medium">
                  <CheckCircle className="h-4 w-4 text-green-500 inline mr-2" />
                  {addresses.length} addresses loaded
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Step 2: Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center text-muted-foreground font-semibold">
                2
              </div>
              <div>
                <CardTitle>Configure Settings (Optional)</CardTitle>
                <CardDescription>
                  Set your starting point and any special requirements
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                <Building className="h-4 w-4" />
                Depot Address
                <span className="text-muted-foreground font-normal">(where trucks start/end)</span>
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 bg-background border border-input rounded-md"
                placeholder="500 Industrial Way, Atlanta, GA 30318"
                value={depotAddress}
                onChange={(e) => setDepotAddress(e.target.value)}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block flex items-center gap-2">
                <Info className="h-4 w-4" />
                Special Instructions
              </label>
              <Textarea
                placeholder="e.g., Avoid highways, Prioritize refrigerated items, Max 8 hours per route"
                value={specialInstructions}
                onChange={(e) => setSpecialInstructions(e.target.value)}
                className="min-h-[80px]"
              />
            </div>
          </CardContent>
        </Card>

        {/* Step 3: Generate */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center text-muted-foreground font-semibold">
                3
              </div>
              <div>
                <CardTitle>Generate Optimized Routes</CardTitle>
                <CardDescription>
                  Click below to optimize your delivery routes
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Button
              size="lg"
              className="w-full"
              onClick={handleGenerateRoutes}
              disabled={addresses.length === 0 || isLoading}
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                  Optimizing Routes...
                </>
              ) : (
                <>
                  <Play className="h-5 w-5 mr-2" />
                  Generate Routes
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Help Section */}
        <Card className="bg-muted/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <HelpCircle className="h-4 w-4" />
              Quick Tips
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>• Routes automatically start and end at your depot (if specified)</li>
              <li>• The AI will create multiple routes if you have many stops</li>
              <li>• Each route is optimized for one truck/driver</li>
              <li>• Time windows and special requirements are respected</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default EnhancedApp;