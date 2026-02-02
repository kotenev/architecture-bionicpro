import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

interface User {
  sub?: string;
  email?: string;
  name?: string;
  preferred_username?: string;
  given_name?: string;
  family_name?: string;
}

interface AuthContextType {
  authenticated: boolean;
  initialized: boolean;
  user: User | null;
  login: () => void;
  logout: () => Promise<void>;
  fetchWithAuth: (url: string, options?: RequestInit) => Promise<Response>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_URL = process.env.REACT_APP_AUTH_URL || 'http://localhost:8000';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [authenticated, setAuthenticated] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const [user, setUser] = useState<User | null>(null);

  const checkSession = useCallback(async () => {
    try {
      const response = await fetch(`${AUTH_URL}/auth/session`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setAuthenticated(data.authenticated);
        setUser(data.user);
      } else {
        setAuthenticated(false);
        setUser(null);
      }
    } catch (error) {
      console.error('Session check error:', error);
      setAuthenticated(false);
      setUser(null);
    } finally {
      setInitialized(true);
    }
  }, []);

  useEffect(() => {
    // Check if we just returned from OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    const authParam = urlParams.get('auth');
    const errorParam = urlParams.get('error');

    // Clean up URL parameters
    if (authParam || errorParam) {
      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);
    }

    if (errorParam) {
      // OAuth error occurred
      console.error('OAuth error:', errorParam);
      setAuthenticated(false);
      setUser(null);
      setInitialized(true);
    } else if (authParam === 'success') {
      // Give the cookie time to be set, then check session
      setTimeout(() => {
        checkSession();
      }, 100);
    } else {
      // Normal session check
      checkSession();
    }
  }, [checkSession]);

  const login = () => {
    window.location.href = `${AUTH_URL}/auth/login`;
  };

  const logout = async () => {
    try {
      await fetch(`${AUTH_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setAuthenticated(false);
      setUser(null);
    }
  };

  const fetchWithAuth = async (url: string, options: RequestInit = {}): Promise<Response> => {
    const apiUrl = url.startsWith('http') ? url : `${AUTH_URL}/api/proxy${url}`;

    return fetch(apiUrl, {
      ...options,
      credentials: 'include'
    });
  };

  return (
    <AuthContext.Provider
      value={{
        authenticated,
        initialized,
        user,
        login,
        logout,
        fetchWithAuth
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
