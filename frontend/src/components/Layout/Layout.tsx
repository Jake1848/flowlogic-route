import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import Header from './Header';
import Sidebar from './Sidebar';
import MainContent from './MainContent';
import { cn } from '../../utils/cn';

const Layout: React.FC = () => {
  const { activeTab } = useAppStore();

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar for larger screens */}
        <div className="hidden lg:flex lg:flex-shrink-0">
          <div className="w-80">
            <Sidebar />
          </div>
        </div>
        
        {/* Main content area */}
        <div className="flex-1 overflow-hidden">
          <MainContent />
        </div>
      </div>
      
      {/* Mobile sidebar overlay */}
      <div className={cn(
        "lg:hidden fixed inset-0 z-50 bg-black/50 transition-opacity",
        activeTab === 'input' ? "opacity-100" : "opacity-0 pointer-events-none"
      )}>
        <div className={cn(
          "absolute inset-y-0 left-0 w-80 bg-white shadow-xl transform transition-transform",
          activeTab === 'input' ? "translate-x-0" : "-translate-x-full"
        )}>
          <Sidebar />
        </div>
      </div>
    </div>
  );
};

export default Layout;