/**
 * ProtectedRoute.jsx
 *
 * Wraps any route that requires authentication.
 * - If still loading → shows a full-page spinner (avoids flash of /login).
 * - If not authenticated → redirects to /login.
 * - If authenticated → renders children normally.
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="auth-loading-screen">
        <div className="spinner" />
        <p>Loading BookBot…</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
