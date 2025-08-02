import { useCallback, useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { TruckRoute } from '../types';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const useRouting = () => {
  const [isLoading, setIsLoading] = useState(false);
  const { 
    addresses, 
    depotAddress, 
    specialInstructions,
    setRoutes,
    setRoutingSummary,
  } = useAppStore();

  const generateRoutes = useCallback(async () => {
    if (addresses.length === 0) {
      toast.error('Please add delivery addresses first');
      return false;
    }

    setIsLoading(true);

    try {
      // Convert addresses array to a string format
      const addressString = addresses
        .map(addr => addr.Address)
        .join('\n');

      // Build the request
      const request = {
        addresses: addressString,
        constraints: specialInstructions || undefined,
        depot_address: depotAddress || undefined,
      };

      const response = await axios.post<{
        routes: TruckRoute[];
        natural_language_summary: string;
      }>(`${API_BASE_URL}/route/auto`, request, {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 60000,
      });

      const { routes, natural_language_summary } = response.data;

      // Store the results
      setRoutes(routes);
      setRoutingSummary(natural_language_summary);

      toast.success(`Generated ${routes.length} optimized routes!`);
      return true;

    } catch (error: any) {
      console.error('Routing error:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response,
        status: error.response?.status,
        data: error.response?.data
      });
      
      let errorMessage = 'Failed to generate routes';
      
      if (error.response?.status === 400) {
        errorMessage = error.response.data?.detail || 'Invalid input data';
      } else if (error.response?.status === 500) {
        errorMessage = 'Server error - please try again';
      } else if (error.code === 'ECONNABORTED') {
        errorMessage = 'Request timeout - please try with fewer addresses';
      } else if (!error.response) {
        errorMessage = 'Cannot connect to routing service. Please check your connection.';
      }

      toast.error(errorMessage);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [addresses, depotAddress, specialInstructions, setRoutes, setRoutingSummary]);

  return {
    generateRoutes,
    isLoading,
  };
};