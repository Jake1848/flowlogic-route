import React from 'react';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout/Layout';
import './App.css';

function App() {
  return (
    <div className="App min-h-screen bg-gray-50">
      <Layout />
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            style: {
              background: '#10b981',
            },
          },
          error: {
            style: {
              background: '#ef4444',
            },
          },
        }}
      />
    </div>
  );
}

export default App;