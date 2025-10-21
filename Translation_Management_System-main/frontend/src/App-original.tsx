import React, { useEffect } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { useStore } from './store/useStore';
import { wsService } from './services/websocket';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import TranslateStudio from './pages/TranslateStudio';
import Analytics from './pages/Analytics';
import Login from './pages/Login';
import Register from './pages/Register';
import LoadingSpinner from './components/LoadingSpinner';
import NotificationCenter from './components/NotificationCenter';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

const App = () => {
  const { user, isAuthenticated, token, setUser, setToken, setLoading } = useStore();

  useEffect(() => {
    // Check if user is already authenticated
    if (token && !user) {
      setLoading(true);
      // Try to get user info from token
      // This would typically be done in a useEffect in a higher component
    }
  }, [token, user, setLoading]);

  useEffect(() => {
    // Connect to WebSocket when user is authenticated
    if (isAuthenticated && user) {
      wsService.connect(user.id);
    } else {
      wsService.disconnect();
    }

    return () => {
      wsService.disconnect();
    };
  }, [isAuthenticated, user]);

  if (!isAuthenticated) {
    return (
      <QueryClientProvider client={queryClient}>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
          <Toaster position="top-right" />
        </div>
      </QueryClientProvider>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="app-shell">
        <Sidebar />
        <main className="content-area">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/studio" element={<TranslateStudio />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </main>
        <NotificationCenter />
        <Toaster position="top-right" />
      </div>
    </QueryClientProvider>
  );
};

export default App;
