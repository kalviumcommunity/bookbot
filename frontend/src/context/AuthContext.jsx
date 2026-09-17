/**
 * AuthContext.jsx
 *
 * Provides global authentication state and actions to the entire React app.
 *
 * Exposes via useAuth():
 *   user          — { id, name, email } | null
 *   isAuthenticated — boolean
 *   loading       — boolean (true during initial session restore)
 *   login(email, password)       — async, throws on failure
 *   signup(name, email, password) — async, throws on failure
 *   logout()                     — clears state + redirects to /login
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';

// ─── Context ──────────────────────────────────────────────────────────────────

const AuthContext = createContext(null);

// ─── Token storage key ────────────────────────────────────────────────────────

const TOKEN_KEY = 'bookbot_token';

// ─── Provider ─────────────────────────────────────────────────────────────────

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // true while restoring session
  const [showWelcome, setShowWelcome] = useState(false); // true only after live login/signup
  const [isNewUser, setIsNewUser]   = useState(false); // true for signup, false for login
  const navigate = useNavigate();

  // ── Session restore on mount ────────────────────────────────────────────────
  useEffect(() => {
    const restoreSession = async () => {
      const token = localStorage.getItem(TOKEN_KEY);
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const userData = await apiService.getCurrentUser();
        setUser(userData);
      } catch {
        // Token invalid or expired — clear it silently
        localStorage.removeItem(TOKEN_KEY);
      } finally {
        setLoading(false);
      }
    };

    restoreSession();
  }, []);

  // ── login ───────────────────────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    const { access_token } = await apiService.login(email, password);
    localStorage.setItem(TOKEN_KEY, access_token);

    const userData = await apiService.getCurrentUser();
    setUser(userData);

    // Fire the welcome transition (existing user)
    setIsNewUser(false);
    setShowWelcome(true);

    navigate('/');
  }, [navigate]);

  // ── signup ──────────────────────────────────────────────────────────────────
  const signup = useCallback(async (name, email, password) => {
    const { access_token } = await apiService.signup(name, email, password);
    localStorage.setItem(TOKEN_KEY, access_token);

    const userData = await apiService.getCurrentUser();
    setUser(userData);

    // Fire the welcome transition (brand-new user)
    setIsNewUser(true);
    setShowWelcome(true);

    navigate('/');
  }, [navigate]);

  // ── logout ──────────────────────────────────────────────────────────────────
  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
    setShowWelcome(false);
    navigate('/login');
  }, [navigate]);

  // ── clearWelcome — called by WelcomeTransition when animation finishes ───────
  const clearWelcome = useCallback(() => {
    setShowWelcome(false);
    setIsNewUser(false);
  }, []);

  // ── Context value ───────────────────────────────────────────────────────────
  const value = {
    user,
    isAuthenticated: user !== null,
    loading,
    login,
    signup,
    logout,
    showWelcome,
    isNewUser,
    clearWelcome,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>');
  }
  return ctx;
}
