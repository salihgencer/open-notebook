import { useState, useCallback } from "react";

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  locale: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
}

const TOKEN_KEY = "notebooklm_access_token";
const REFRESH_KEY = "notebooklm_refresh_token";
const USER_KEY = "notebooklm_user";

export function useAuth() {
  const [state, setState] = useState<AuthState>(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    const user = localStorage.getItem(USER_KEY);
    return {
      accessToken: token,
      refreshToken: localStorage.getItem(REFRESH_KEY),
      user: user ? JSON.parse(user) : null,
      isAuthenticated: !!token,
    };
  });

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch("/api/ext/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Login failed");
    }

    const data = await res.json();
    const user: User = {
      id: data.email,
      email: data.email,
      name: data.name,
      role: data.role,
      locale: data.locale,
    };

    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(REFRESH_KEY, data.refresh_token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));

    setState({
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      user,
      isAuthenticated: true,
    });
  }, []);

  const register = useCallback(
    async (email: string, name: string, password: string) => {
      const res = await fetch("/api/ext/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name, password }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Registration failed");
      }

      const data = await res.json();
      const user: User = {
        id: data.email,
        email: data.email,
        name: data.name,
        role: data.role,
        locale: data.locale,
      };

      localStorage.setItem(TOKEN_KEY, data.access_token);
      localStorage.setItem(REFRESH_KEY, data.refresh_token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));

      setState({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        user,
        isAuthenticated: true,
      });
    },
    []
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    setState({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
    });
  }, []);

  return { ...state, login, register, logout };
}
