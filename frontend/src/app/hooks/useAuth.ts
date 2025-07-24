'use client';
import { useEffect, useState } from 'react';

export function useAuth() {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setLoading] = useState(true);

  useEffect(() => {
    const t = localStorage.getItem('token');
    setToken(t);
    setLoading(false);
  }, []);

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
  };

  return {
    token,
    isAuthenticated: !!token,
    logout,
    isLoading,
  };
}
