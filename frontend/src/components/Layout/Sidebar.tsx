import React from 'react';
import ChatInput from '../Chat/ChatInput';
import AddressInput from '../Input/AddressInput';
import { useAppStore } from '../../store/useAppStore';

const Sidebar: React.FC = () => {
  const { activeTab } = useAppStore();

  if (activeTab !== 'input') {
    return null;
  }

  return (
    <div className="h-full bg-white border-r border-gray-200 flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Route Planning</h2>
        <p className="text-sm text-gray-600 mt-1">
          Enter addresses and constraints to generate optimal routes
        </p>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 space-y-6">
          {/* Chat interface */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              🤖 AI Assistant
            </h3>
            <ChatInput />
          </div>
          
          {/* Address input */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              📍 Delivery Addresses
            </h3>
            <AddressInput />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;