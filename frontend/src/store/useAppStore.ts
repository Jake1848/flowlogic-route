import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { AppState, TruckRoute, ChatMessage } from '../types';

export const useAppStore = create<AppState>()(
  devtools(
    (set, get) => ({
      // Input data
      addresses: '',
      constraints: '',
      depotAddress: '',
      csvFile: null,
      
      // Routing results
      currentRoutes: [],
      routingSummary: '',
      isLoading: false,
      error: null,
      
      // UI state
      activeTab: 'input',
      showExportModal: false,
      chatHistory: [],
      
      // Actions
      setAddresses: (addresses: string) => set({ addresses }),
      
      setConstraints: (constraints: string) => set({ constraints }),
      
      setDepotAddress: (depotAddress: string) => set({ depotAddress }),
      
      setCsvFile: (csvFile: File | null) => set({ csvFile }),
      
      setCurrentRoutes: (currentRoutes: TruckRoute[]) => set({ currentRoutes }),
      
      setRoutingSummary: (routingSummary: string) => set({ routingSummary }),
      
      setLoading: (isLoading: boolean) => set({ isLoading }),
      
      setError: (error: string | null) => set({ error }),
      
      setActiveTab: (activeTab: 'input' | 'results' | 'map') => set({ activeTab }),
      
      setShowExportModal: (showExportModal: boolean) => set({ showExportModal }),
      
      addChatMessage: (message: ChatMessage) => {
        const { chatHistory } = get();
        set({ chatHistory: [...chatHistory, message] });
      },
      
      clearResults: () => set({
        currentRoutes: [],
        routingSummary: '',
        error: null,
        chatHistory: []
      }),
    }),
    {
      name: 'flowlogic-app-store',
    }
  )
);