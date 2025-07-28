import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Truck, Menu, X, BarChart3, Map, MessageSquare } from 'lucide-react';
import { cn } from '../../utils/cn';

const Header: React.FC = () => {
  const { activeTab, setActiveTab, isLoading } = useAppStore();

  const tabs = [
    { id: 'input' as const, label: 'Input', icon: MessageSquare },
    { id: 'results' as const, label: 'Results', icon: BarChart3 },
    { id: 'map' as const, label: 'Map', icon: Map },
  ];

  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="flex items-center justify-between">
        {/* Logo and title */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <Truck className="h-8 w-8 text-primary-600" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">FlowLogic RouteAI</h1>
              <p className="text-xs text-gray-500">Autonomous Truck Routing</p>
            </div>
          </div>
          
          {isLoading && (
            <div className="flex items-center space-x-2 ml-6">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
              <span className="text-sm text-gray-600">Optimizing routes...</span>
            </div>
          )}
        </div>

        {/* Navigation tabs - desktop */}
        <nav className="hidden md:flex space-x-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors",
                  activeTab === tab.id
                    ? "bg-primary-100 text-primary-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Mobile menu button */}
        <button
          className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100"
          onClick={() => setActiveTab(activeTab === 'input' ? 'results' : 'input')}
        >
          {activeTab === 'input' ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile tabs */}
      <nav className="md:hidden mt-3 flex space-x-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex-1 flex items-center justify-center space-x-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors",
                activeTab === tab.id
                  ? "bg-primary-100 text-primary-700"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </header>
  );
};

export default Header;