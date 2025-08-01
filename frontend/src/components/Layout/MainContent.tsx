import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import RouteMap from '../Map/RouteMap';
import ResultsSummary from '../Results/ResultsSummary';
import WelcomeScreen from '../Welcome/WelcomeScreen';

const MainContent: React.FC = () => {
  // Component not used in new structure - using local state to avoid TypeScript errors
  const [activeTab] = React.useState<'input' | 'results' | 'map'>('input');
  const currentRoutes: any[] = [];

  const renderContent = () => {
    switch (activeTab) {
      case 'input':
        return currentRoutes.length > 0 ? <ResultsSummary routes={currentRoutes} routingSummary="" /> : <WelcomeScreen />;
      case 'results':
        return <ResultsSummary routes={currentRoutes} routingSummary="" />;
      case 'map':
        return <RouteMap routes={currentRoutes} />;
      default:
        return <WelcomeScreen />;
    }
  };

  return (
    <div className="h-full flex flex-col bg-background">
      {renderContent()}
    </div>
  );
};

export default MainContent;