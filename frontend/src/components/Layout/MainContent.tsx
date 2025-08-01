import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import RouteMap from '../Map/RouteMap';
import ResultsSummary from '../Results/ResultsSummary';
import WelcomeScreen from '../Welcome/WelcomeScreen';

const MainContent: React.FC = () => {
  const { activeTab, currentRoutes } = useAppStore();

  const renderContent = () => {
    switch (activeTab) {
      case 'input':
        return currentRoutes.length > 0 ? <ResultsSummary /> : <WelcomeScreen />;
      case 'results':
        return <ResultsSummary />;
      case 'map':
        return <RouteMap />;
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