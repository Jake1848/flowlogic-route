import React from 'react';
import { Toaster } from 'react-hot-toast';
import { ThemeProvider } from './components/theme-provider';
import Layout from './components/Layout/Layout';

function App() {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem={false}
      disableTransitionOnChange
    >
      <div className="min-h-screen bg-background">
        <Layout />
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            className: 'bg-card text-card-foreground border border-border',
            style: {
              background: 'hsl(var(--card))',
              color: 'hsl(var(--card-foreground))',
              borderColor: 'hsl(var(--border))',
            },
            success: {
              className: 'bg-green-600 text-white',
            },
            error: {
              className: 'bg-red-600 text-white',
            },
          }}
        />
      </div>
    </ThemeProvider>
  );
}

export default App;