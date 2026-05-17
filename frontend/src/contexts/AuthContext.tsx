"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { auth as authApi } from "@/lib/api";
import type { AuthState, User } from "@/lib/types";

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore session from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem("barkmind_token");
    if (stored) {
      setToken(stored);
      authApi
        .me()
        .then(setUser)
        .catch(() => {
          localStorage.removeItem("barkmind_token");
          localStorage.removeItem("barkmind_refresh_token");
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await authApi.login(email, password);
    localStorage.setItem("barkmind_token", res.access_token);
    localStorage.setItem("barkmind_refresh_token", res.refresh_token);
    setToken(res.access_token);
    const me = await authApi.me();
    setUser(me);
  }, []);

  const register = useCallback(
    async (
      email: string,
      username: string,
      password: string,
      displayName?: string
    ) => {
      const res = await authApi.register({
        email,
        username,
        password,
        display_name: displayName,
      });
      localStorage.setItem("barkmind_token", res.access_token);
      localStorage.setItem("barkmind_refresh_token", res.refresh_token);
      setToken(res.access_token);
      const me = await authApi.me();
      setUser(me);
    },
    []
  );

  const logout = useCallback(() => {
    authApi.logout().catch(() => {});
    localStorage.removeItem("barkmind_token");
    localStorage.removeItem("barkmind_refresh_token");
    setToken(null);
    setUser(null);
    window.location.href = "/";
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
