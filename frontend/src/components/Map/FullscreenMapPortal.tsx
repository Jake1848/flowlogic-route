import React, { useEffect } from 'react';
import ReactDOM from 'react-dom';
import RouteMap from './CleanRouteMap';

interface FullscreenMapPortalProps {
  routes: any[];
  onClose: () => void;
}

const FullscreenMapPortal: React.FC<FullscreenMapPortalProps> = ({ routes, onClose }) => {
  useEffect(() => {
    // Handle ESC key
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'auto';
    };
  }, [onClose]);

  // Create portal content
  const content = (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 999999,
        backgroundColor: 'white'
      }}
    >
      {/* Close button */}
      <button
        onClick={onClose}
        style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          zIndex: 1000000,
          backgroundColor: 'white',
          border: '2px solid #374151',
          borderRadius: '8px',
          padding: '8px 16px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '14px',
          fontWeight: 'bold',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
        }}
      >
        <span>✕</span>
        <span>Close Map (ESC)</span>
      </button>

      {/* Map */}
      <RouteMap routes={routes} isFullscreen={true} />
    </div>
  );

  // Render to body using portal
  return ReactDOM.createPortal(content, document.body);
};

export default FullscreenMapPortal;