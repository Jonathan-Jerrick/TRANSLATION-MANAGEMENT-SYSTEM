import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import NotificationCenter from '../components/NotificationCenter';
import { useStore } from '../store/useStore';

const AppLayout: React.FC = () => {
  const { isLoading } = useStore();

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="content-area">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="loading-spinner" />
          </div>
        ) : (
          <Outlet />
        )}
      </main>
      <NotificationCenter />
    </div>
  );
};

export default AppLayout;
