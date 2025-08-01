import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { TruckRoute } from '../types';

interface Address {
  Address: string;
  Pallets: number;
  Special: string;
  TimeWindow: string;
}

interface AppState {
  // Input data
  addresses: Address[];
  depotAddress: string;
  specialInstructions: string;
  
  // Routing results
  routes: TruckRoute[];
  routingSummary: string;
  
  // Actions
  setAddresses: (addresses: Address[]) => void;
  setDepotAddress: (depotAddress: string) => void;
  setSpecialInstructions: (instructions: string) => void;
  setRoutes: (routes: TruckRoute[]) => void;
  setRoutingSummary: (summary: string) => void;
  clearAll: () => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    (set) => ({
      // Initial state
      addresses: [],
      depotAddress: '',
      specialInstructions: '',
      routes: [],
      routingSummary: '',
      
      // Actions
      setAddresses: (addresses) => set({ addresses }),
      setDepotAddress: (depotAddress) => set({ depotAddress }),
      setSpecialInstructions: (instructions) => set({ specialInstructions: instructions }),
      setRoutes: (routes) => set({ routes }),
      setRoutingSummary: (summary) => set({ routingSummary: summary }),
      clearAll: () => set({
        addresses: [],
        depotAddress: '',
        specialInstructions: '',
        routes: [],
        routingSummary: '',
      }),
    }),
    {
      name: 'flowlogic-app-store',
    }
  )
);