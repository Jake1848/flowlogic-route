import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Menu, X, BarChart3, Map, MessageSquare } from 'lucide-react';
import { Button } from '../ui/button';
import { cn } from '../../utils/cn';

const Header: React.FC = () => {
  const { activeTab, setActiveTab, isLoading } = useAppStore();

  const tabs = [
    { id: 'input' as const, label: 'Input', icon: MessageSquare },
    { id: 'results' as const, label: 'Results', icon: BarChart3 },
    { id: 'map' as const, label: 'Map', icon: Map },
  ];

  return (
    <header className="bg-card border-b border-border px-4 py-3">
      <div className="flex items-center justify-between">
        {/* Logo and title */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <img 
              src="/logo.png" 
              alt="FlowLogic RouteAI" 
              className="h-8 w-8 object-contain"
            />
            <div>
              <h1 className="text-xl font-bold text-foreground">FlowLogic RouteAI</h1>
              <p className="text-xs text-muted-foreground">Autonomous Truck Routing</p>
            </div>
          </div>
          
          {isLoading && (
            <div className="flex items-center space-x-2 ml-6">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
              <span className="text-sm text-muted-foreground">Optimizing routes...</span>
            </div>
          )}
        </div>

        {/* Navigation tabs - desktop */}
        <nav className="hidden md:flex space-x-1">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <Button
                key={tab.id}
                variant={activeTab === tab.id ? "default" : "ghost"}
                onClick={() => setActiveTab(tab.id)}
                className="flex items-center space-x-2"
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </Button>
            );
          })}
        </nav>

        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={() => setActiveTab(activeTab === 'input' ? 'results' : 'input')}
        >
          {activeTab === 'input' ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </div>

      {/* Mobile tabs */}
      <nav className="md:hidden mt-3 flex space-x-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <Button
              key={tab.id}
              variant={activeTab === tab.id ? "default" : "ghost"}
              onClick={() => setActiveTab(tab.id)}
              className="flex-1 flex items-center justify-center space-x-1"
              size="sm"
            >
              <Icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </Button>
          );
        })}
      </nav>
    </header>
  );
};

export default Header;