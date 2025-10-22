import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './styles.css';

const API_BASE =
  (typeof window !== 'undefined' && (window as any).__TMS_API_URL) ||
  import.meta.env.VITE_API_URL ||
  'http://localhost:4001';

if (typeof window !== 'undefined') {
  const sendClientLog = (payload: Record<string, unknown>) => {
    fetch(`${API_BASE.replace(/\/$/, '')}/client-log`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...payload,
        userAgent: navigator.userAgent,
        href: window.location.href,
        timestamp: new Date().toISOString(),
      }),
    }).catch(() => undefined);
  };

  window.addEventListener('error', (event) => {
    sendClientLog({
      type: 'error',
      message: event.message,
      source: event.filename,
      line: event.lineno,
      column: event.colno,
    });
  });

  window.addEventListener('unhandledrejection', (event) => {
    sendClientLog({
      type: 'unhandledrejection',
      reason:
        event.reason instanceof Error
          ? { message: event.reason.message, stack: event.reason.stack }
          : event.reason,
    });
  });
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
