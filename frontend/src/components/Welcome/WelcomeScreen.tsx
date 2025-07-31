import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Truck, MessageSquare, MapPin, ArrowRight, Zap, Brain } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';

const WelcomeScreen: React.FC = () => {
  const { setActiveTab } = useAppStore();

  const features = [
    {
      icon: Brain,
      title: "AI-Powered Intelligence",
      description: "Advanced AI automatically estimates pallets, time windows, and special handling requirements from just addresses."
    },
    {
      icon: Zap,
      title: "Autonomous Fleet Generation",
      description: "Smart algorithms analyze your stops and automatically generate the optimal truck fleet composition."
    },
    {
      icon: MessageSquare,
      title: "Natural Language Processing",
      description: "Describe complex routing constraints in plain English like 'avoid highways during rush hour'."
    },
    {
      icon: MapPin,
      title: "Real-time Optimization",
      description: "Dynamic re-routing for cancellations, delays, and emergency deliveries with instant impact analysis."
    }
  ];

  const examples = [
    {
      title: "Retail Chain Delivery",
      addresses: "Walmart, Target, Home Depot in Atlanta metro area",
      constraints: "Frozen goods first, avoid I-285 during rush hour",
      result: "3 trucks, 85% utilization, $234 fuel cost"
    },
    {
      title: "Restaurant Supply Route",
      addresses: "5 restaurants in downtown Miami",
      constraints: "All deliveries before 11 AM, refrigerated truck only",
      result: "1 truck, 12 stops, completed by 10:30 AM"
    },
    {
      title: "Medical Supply Emergency",
      addresses: "3 hospitals, 2 clinics in urgent need",
      constraints: "Fragile handling, priority delivery under 2 hours",
      result: "2 trucks, specialized routing, 98 minutes total"
    }
  ];

  return (
    <div className="h-full overflow-y-auto bg-background">
      <div className="max-w-6xl mx-auto p-8">
        {/* Hero section */}
        <div className="text-center py-12">
          <div className="flex justify-center mb-6">
            <div className="relative">
              <img 
                src="/logo.png" 
                alt="FlowLogic RouteAI" 
                className="h-32 w-32 object-contain"
              />
            </div>
          </div>
          
          <h1 className="text-4xl font-bold text-foreground mb-4">
            Welcome to FlowLogic RouteAI
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-3xl mx-auto">
            The world's first fully autonomous truck routing system. Just provide addresses and watch AI create 
            optimized delivery routes with zero configuration required.
          </p>
          
          <div className="flex justify-center space-x-4">
            <Button
              onClick={() => setActiveTab('input')}
              size="lg"
              className="flex items-center space-x-2"
            >
              <span>Start Planning Routes</span>
              <ArrowRight className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* Features grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 p-3 bg-primary/10 rounded-lg">
                      <Icon className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{feature.title}</CardTitle>
                      <CardDescription className="mt-2">{feature.description}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
              </Card>
            );
          })}
        </div>

        {/* How it works */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-foreground text-center mb-8">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-lg font-bold text-primary">1</span>
              </div>
              <h3 className="font-semibold text-foreground mb-2">Enter Addresses</h3>
              <p className="text-muted-foreground text-sm">
                Type, paste, or upload delivery addresses. AI automatically enriches missing data.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-lg font-bold text-primary">2</span>
              </div>
              <h3 className="font-semibold text-foreground mb-2">Add Constraints</h3>
              <p className="text-muted-foreground text-sm">
                Describe routing preferences in natural language. AI understands complex instructions.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-lg font-bold text-primary">3</span>
              </div>
              <h3 className="font-semibold text-foreground mb-2">Get Optimized Routes</h3>
              <p className="text-muted-foreground text-sm">
                AI generates fleet, optimizes routes, and provides actionable recommendations.
              </p>
            </div>
          </div>
        </div>

        {/* Example scenarios */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-foreground text-center mb-8">Real-World Examples</h2>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {examples.map((example, index) => (
              <Card key={index} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="text-lg">{example.title}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div>
                    <span className="text-muted-foreground font-medium">Addresses:</span>
                    <p className="text-foreground">{example.addresses}</p>
                  </div>
                  
                  <div>
                    <span className="text-muted-foreground font-medium">Constraints:</span>
                    <p className="text-foreground">{example.constraints}</p>
                  </div>
                  
                  <div className="pt-2 border-t border-border">
                    <span className="text-green-600 font-medium">Result:</span>
                    <p className="text-foreground">{example.result}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Quick start CTA */}
        <Card className="bg-primary text-primary-foreground">
          <CardContent className="p-8 text-center">
            <h2 className="text-2xl font-bold mb-4">Ready to Optimize Your Deliveries?</h2>
            <p className="text-primary-foreground/80 mb-6 max-w-2xl mx-auto">
              Join thousands of logistics professionals using AI to reduce costs, save time, and improve delivery efficiency.
            </p>
            <Button
              onClick={() => setActiveTab('input')}
              variant="secondary"
              size="lg"
            >
              Get Started Now
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default WelcomeScreen;