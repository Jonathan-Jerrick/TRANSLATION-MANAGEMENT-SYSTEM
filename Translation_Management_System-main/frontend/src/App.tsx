import React, { useEffect } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { useStore } from './store/useStore';
import { apiService } from './services/api';
import { wsService } from './services/websocket';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import TranslateStudio from './pages/TranslateStudio';
import Analytics from './pages/Analytics';
import Login from './pages/Login';
import Register from './pages/Register';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './layouts/AppLayout';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

const BLOCKED_ROUTES = ['/login', '/register'];

const resolveRedirectRoute = (route?: string) => {
  if (!route) {
    return '/dashboard';
  }
  const [pathOnly] = route.split(/[?#]/);
  if (!pathOnly || BLOCKED_ROUTES.includes(pathOnly)) {
    return '/dashboard';
  }
  return route;
};

const HomeRedirect: React.FC = () => {
  const isAuthenticated = useStore((state) => state.isAuthenticated);
  const lastVisitedRoute = useStore((state) => state.lastVisitedRoute);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const targetRoute = resolveRedirectRoute(lastVisitedRoute);

  return <Navigate to={targetRoute} replace />;
};

const App = () => {
  const user = useStore((state) => state.user);
  const isAuthenticated = useStore((state) => state.isAuthenticated);
  const token = useStore((state) => state.token);
  const setUser = useStore((state) => state.setUser);
  const setToken = useStore((state) => state.setToken);
  const setLoading = useStore((state) => state.setLoading);
  const setLastVisitedRoute = useStore((state) => state.setLastVisitedRoute);
  const lastVisitedRoute = useStore((state) => state.lastVisitedRoute);
  const location = useLocation();

  useEffect(() => {
    if (!token || user) {
      return;
    }
    setLoading(true);
    apiService
      .getCurrentUser()
      .then((data) => {
        setUser(data);
      })
      .catch(() => {
        setToken(null);
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, [token, user, setUser, setToken, setLoading]);

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }
    if (!BLOCKED_ROUTES.includes(location.pathname)) {
      const composedRoute = `${location.pathname}${location.search}${location.hash}`;
      if (composedRoute !== lastVisitedRoute) {
        setLastVisitedRoute(composedRoute || '/dashboard');
      }
    }
  }, [isAuthenticated, location, lastVisitedRoute, setLastVisitedRoute]);

  useEffect(() => {
    // Connect to WebSocket when user is authenticated
    if (isAuthenticated && user) {
      try {
        wsService.connect(user.id);
      } catch (error) {
        console.warn('WebSocket connection failed:', error);
      }
    } else {
      wsService.disconnect();
    }

    return () => {
      wsService.disconnect();
    };
  }, [isAuthenticated, user]);

  return (
    <QueryClientProvider client={queryClient}>
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<HomeRedirect />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/studio" element={<TranslateStudio />} />
            <Route path="/analytics" element={<Analytics />} />
          </Route>
        </Route>
        <Route
          path="/login"
          element={
            isAuthenticated ? <Navigate to={resolveRedirectRoute(lastVisitedRoute)} replace /> : <Login />
          }
        />
        <Route
          path="/register"
          element={
            isAuthenticated ? (
              <Navigate to={resolveRedirectRoute(lastVisitedRoute)} replace />
            ) : (
              <Register />
            )
          }
        />
        <Route
          path="*"
          element={<Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />}
        />
      </Routes>
      <Toaster position="top-right" />
    </QueryClientProvider>
  );
};

export default App;
