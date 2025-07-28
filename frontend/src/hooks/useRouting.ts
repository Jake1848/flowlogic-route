import { useCallback } from 'react';
import { useAppStore } from '../store/useAppStore';
import { AutoRoutingRequest, RoutingResponse } from '../types';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const useRouting = () => {
  const {
    setCurrentRoutes,
    setRoutingSummary,
    setLoading,
    setError,
    setActiveTab,
    addChatMessage,
  } = useAppStore();

  const performAutonomousRouting = useCallback(async (
    addresses: string,
    constraints?: string,
    depotAddress?: string
  ) => {
    if (!addresses.trim()) {
      toast.error('Please provide delivery addresses');
      return;
    }

    setLoading(true);
    setError(null);

    // Add system message to chat
    addChatMessage({
      id: Date.now().toString(),
      type: 'system',
      content: '🤖 Generating optimal routes with AI...',
      timestamp: new Date(),
    });

    try {
      const request: AutoRoutingRequest = {
        addresses: addresses.trim(),
        constraints: constraints?.trim() || undefined,
        depot_address: depotAddress?.trim() || undefined,
      };

      const response = await axios.post<RoutingResponse>(
        `${API_BASE_URL}/route/auto`,
        request,
        {
          headers: {
            'Content-Type': 'application/json',
          },
          timeout: 60000, // 60 second timeout
        }
      );

      const { routes, natural_language_summary } = response.data;

      setCurrentRoutes(routes);
      setRoutingSummary(natural_language_summary);
      setActiveTab('results');

      // Add success message to chat
      addChatMessage({
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `✅ Successfully generated ${routes.length} optimized routes with ${routes.reduce((sum, route) => sum + route.stops.length, 0)} total stops!`,
        timestamp: new Date(),
      });

      toast.success('Routes optimized successfully!');

    } catch (error: any) {
      console.error('Routing error:', error);
      
      let errorMessage = 'Failed to generate routes';
      
      if (error.response?.status === 400) {
        errorMessage = error.response.data?.detail || 'Invalid input data';
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error - please try again';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Request timeout - please try with fewer addresses';
      } else if (!error.response) {
        errorMessage = 'Cannot connect to routing service';
      }

      setError(errorMessage);
      
      // Add error message to chat
      addChatMessage({
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: `❌ Routing failed: ${errorMessage}`,
        timestamp: new Date(),
      });

      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [setCurrentRoutes, setRoutingSummary, setLoading, setError, setActiveTab, addChatMessage]);

  const uploadAndRoute = useCallback(async (
    stopsFile: File,
    trucksFile: File,
    constraints?: string
  ) => {
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('stops_file', stopsFile);
      formData.append('trucks_file', trucksFile);
      if (constraints?.trim()) {
        formData.append('constraints', constraints.trim());
      }

      const response = await axios.post<RoutingResponse>(
        `${API_BASE_URL}/route/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          timeout: 60000,
        }
      );

      const { routes, natural_language_summary } = response.data;

      setCurrentRoutes(routes);
      setRoutingSummary(natural_language_summary);
      setActiveTab('results');

      toast.success('CSV files processed and routes optimized!');

    } catch (error: any) {
      console.error('Upload routing error:', error);
      
      let errorMessage = 'Failed to process CSV files';
      
      if (error.response?.status === 400) {
        errorMessage = error.response.data?.detail || 'Invalid CSV format';
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error processing files';
      }

      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [setCurrentRoutes, setRoutingSummary, setLoading, setError, setActiveTab]);

  const clearRoutes = useCallback(() => {
    setCurrentRoutes([]);
    setRoutingSummary('');
    setError(null);
    setActiveTab('input');
  }, [setCurrentRoutes, setRoutingSummary, setError, setActiveTab]);

  return {
    performAutonomousRouting,
    uploadAndRoute,
    clearRoutes,
  };
};