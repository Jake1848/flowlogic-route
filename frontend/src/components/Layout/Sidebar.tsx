import React from 'react';
import ChatInput from '../Chat/ChatInput';
import AddressInput from '../Input/AddressInput';
import { useAppStore } from '../../store/useAppStore';
import { Bot, MapPin } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';

const Sidebar: React.FC = () => {
  const { activeTab } = useAppStore();

  if (activeTab !== 'input') {
    return null;
  }

  return (
    <div className="h-full bg-card border-r border-border flex flex-col">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold text-foreground">Route Planning</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Enter addresses and constraints to generate optimal routes
        </p>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-6">
          {/* Chat interface */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center space-x-2">
                <Bot className="h-4 w-4" />
                <span>AI Assistant</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ChatInput />
            </CardContent>
          </Card>
          
          {/* Address input */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center space-x-2">
                <MapPin className="h-4 w-4" />
                <span>Delivery Addresses</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <AddressInput />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;