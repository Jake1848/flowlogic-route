import React, { useState, useEffect } from 'react';
import { Building2, Plug, CheckCircle, XCircle, ExternalLink, DollarSign, Clock, Zap } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { toast } from 'react-hot-toast';
import axios from 'axios';

interface Platform {
  id: string;
  name: string;
  description: string;
  features: string[];
  pricing: string;
}

interface EnterpriseIntegrationProps {
  onOrdersImported?: (orders: any[]) => void;
}

const EnterpriseIntegration: React.FC<EnterpriseIntegrationProps> = ({ onOrdersImported }) => {
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [advantages, setAdvantages] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [connected, setConnected] = useState<string | null>(null);

  useEffect(() => {
    fetchPlatforms();
  }, []);

  const fetchPlatforms = async () => {
    try {
      const response = await axios.get('/enterprise/platforms');
      setPlatforms(response.data.platforms);
      setAdvantages(response.data.flowlogic_advantages);
    } catch (error) {
      console.error('Error fetching platforms:', error);
      toast.error('Failed to load enterprise platforms');
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (platform: Platform) => {
    setConnecting(platform.id);
    
    // Mock connection config - in real app, this would be a form
    const mockConfig = {
      platform: platform.id,
      config: {
        api_url: `https://api.${platform.id}.com`,
        api_key: 'demo_key',
        username: 'demo_user',
        password: 'demo_pass'
      }
    };

    try {
      const response = await axios.post('/enterprise/connect', mockConfig);
      
      if (response.data.success) {
        setConnected(platform.id);
        toast.success(`Connected to ${platform.name}!`);
        
        // Import orders if available
        if (response.data.imported_orders > 0) {
          const ordersResponse = await axios.post('/enterprise/import-orders', mockConfig);
          if (ordersResponse.data.success && onOrdersImported) {
            onOrdersImported(ordersResponse.data.stops);
            toast.success(`Imported ${ordersResponse.data.imported_orders} orders`);
          }
        }
      }
    } catch (error: any) {
      console.error('Connection error:', error);
      toast.error(`Failed to connect to ${platform.name}: ${error.response?.data?.detail || 'Connection failed'}`);
    } finally {
      setConnecting(null);
    }
  };

  const getPlatformIcon = (platformId: string) => {
    const icons: { [key: string]: string } = {
      descartes: '🚛',
      sap_tm: '🏢',
      oracle_otm: '🔷',
      manhattan: '🏙️'
    };
    return icons[platformId] || '🔌';
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center space-x-2">
            <Building2 className="h-6 w-6 text-primary" />
            <CardTitle>Enterprise TMS Integration</CardTitle>
          </div>
          <CardDescription>
            Connect FlowLogic RouteAI with your existing Transportation Management System
          </CardDescription>
        </CardHeader>
      </Card>

      {/* FlowLogic Advantages */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="h-5 w-5 text-yellow-500" />
            <span>Why Choose FlowLogic Over Enterprise TMS?</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {advantages.map((advantage, index) => (
              <div key={index} className="flex items-center space-x-2">
                <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
                <span className="text-sm">{advantage}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Platform Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {platforms.map((platform) => (
          <Card key={platform.id} className="relative">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{getPlatformIcon(platform.id)}</span>
                  <div>
                    <CardTitle className="text-lg">{platform.name}</CardTitle>
                    <CardDescription>{platform.description}</CardDescription>
                  </div>
                </div>
                {connected === platform.id && (
                  <Badge variant="default" className="bg-green-500">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Connected
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Features */}
              <div>
                <h4 className="text-sm font-medium mb-2">Key Features:</h4>
                <div className="flex flex-wrap gap-1">
                  {platform.features.map((feature, index) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      {feature}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Pricing */}
              <div className="flex items-center space-x-2 text-sm">
                <DollarSign className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">{platform.pricing}</span>
              </div>

              {/* Action Button */}
              <Button
                onClick={() => handleConnect(platform)}
                disabled={connecting === platform.id || connected === platform.id}
                className="w-full"
                variant={connected === platform.id ? "outline" : "default"}
              >
                {connecting === platform.id ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Connecting...
                  </>
                ) : connected === platform.id ? (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Connected
                  </>
                ) : (
                  <>
                    <Plug className="h-4 w-4 mr-2" />
                    Connect & Import Orders
                  </>
                )}
              </Button>

              {/* Additional Actions for Connected Platforms */}
              {connected === platform.id && (
                <div className="grid grid-cols-2 gap-2 pt-2">
                  <Button variant="outline" size="sm">
                    <ExternalLink className="h-3 w-3 mr-1" />
                    Sync Routes
                  </Button>
                  <Button variant="outline" size="sm">
                    <Clock className="h-3 w-3 mr-1" />
                    Real-time Sync
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Integration Benefits */}
      <Card>
        <CardHeader>
          <CardTitle>Integration Benefits</CardTitle>
          <CardDescription>
            How FlowLogic enhances your existing enterprise systems
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center space-y-2">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto">
                <Zap className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="font-medium">AI-Powered Optimization</h3>
              <p className="text-sm text-muted-foreground">
                Our AI continuously optimizes routes in real-time, improving upon static enterprise TMS solutions
              </p>
            </div>
            
            <div className="text-center space-y-2">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto">
                <DollarSign className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="font-medium">Cost Reduction</h3>
              <p className="text-sm text-muted-foreground">
                Reduce fuel costs by 15-30% and eliminate expensive enterprise TMS licensing fees
              </p>
            </div>
            
            <div className="text-center space-y-2">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto">
                <Clock className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="font-medium">Rapid Implementation</h3>
              <p className="text-sm text-muted-foreground">
                Deploy in days, not months. Our API-first architecture integrates seamlessly
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EnterpriseIntegration;