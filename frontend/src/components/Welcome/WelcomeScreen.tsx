import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Truck, MessageSquare, MapPin, Sparkles, ArrowRight, Zap, Brain } from 'lucide-react';

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
    <div className="h-full overflow-y-auto bg-gradient-to-br from-blue-50 via-white to-green-50">
      <div className="max-w-6xl mx-auto p-8">
        {/* Hero section */}
        <div className="text-center py-12">
          <div className="flex justify-center mb-6">
            <div className="relative">
              <Truck className="h-16 w-16 text-primary-600" />
              <div className="absolute -top-2 -right-2 h-6 w-6 bg-yellow-400 rounded-full flex items-center justify-center">
                <Sparkles className="h-3 w-3 text-yellow-800" />
              </div>
            </div>
          </div>
          
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to FlowLogic RouteAI
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            The world's first fully autonomous truck routing system. Just provide addresses and watch AI create 
            optimized delivery routes with zero configuration required.
          </p>
          
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => setActiveTab('input')}
              className="flex items-center space-x-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-lg font-medium"
            >
              <span>Start Planning Routes</span>
              <ArrowRight className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Features grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div key={index} className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 p-3 bg-primary-100 rounded-lg">
                    <Icon className="h-6 w-6 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                    <p className="text-gray-600 leading-relaxed">{feature.description}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* How it works */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-lg font-bold text-blue-600">1</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Enter Addresses</h3>
              <p className="text-gray-600 text-sm">
                Type, paste, or upload delivery addresses. AI automatically enriches missing data.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-lg font-bold text-green-600">2</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Add Constraints</h3>
              <p className="text-gray-600 text-sm">
                Describe routing preferences in natural language. AI understands complex instructions.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-lg font-bold text-purple-600">3</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Get Optimized Routes</h3>
              <p className="text-gray-600 text-sm">
                AI generates fleet, optimizes routes, and provides actionable recommendations.
              </p>
            </div>
          </div>
        </div>

        {/* Example scenarios */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">Real-World Examples</h2>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {examples.map((example, index) => (
              <div key={index} className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow">
                <h3 className="font-semibold text-gray-900 mb-3">{example.title}</h3>
                
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="text-gray-500 font-medium">Addresses:</span>
                    <p className="text-gray-700">{example.addresses}</p>
                  </div>
                  
                  <div>
                    <span className="text-gray-500 font-medium">Constraints:</span>
                    <p className="text-gray-700">{example.constraints}</p>
                  </div>
                  
                  <div className="pt-2 border-t border-gray-100">
                    <span className="text-green-600 font-medium">Result:</span>
                    <p className="text-gray-700">{example.result}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick start CTA */}
        <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-xl p-8 text-center text-white">
          <h2 className="text-2xl font-bold mb-4">Ready to Optimize Your Deliveries?</h2>
          <p className="text-primary-100 mb-6 max-w-2xl mx-auto">
            Join thousands of logistics professionals using AI to reduce costs, save time, and improve delivery efficiency.
          </p>
          <button
            onClick={() => setActiveTab('input')}
            className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
          >
            Get Started Now
          </button>
        </div>
      </div>
    </div>
  );
};

export default WelcomeScreen;