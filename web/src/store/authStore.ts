import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AuthState, User } from '../types/auth';
import { api } from '../services/api';

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isLoading: false,

      async login(email: string, password: string) {
        set({ isLoading: true });
        try {
          const response = await api.post('/auth/login', { email, password });
          const { access_token, refresh_token, user } = response.data;
          
          set({
            accessToken: access_token,
            refreshToken: refresh_token,
            user,
            isLoading: false
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout() {
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isLoading: false
        });
      },

      async fetchMe() {
        const { accessToken } = get();
        if (!accessToken) return;

        try {
          const response = await api.get('/auth/me', {
            headers: { Authorization: `Bearer ${accessToken}` }
          });
          set({ user: response.data });
        } catch (error) {
          // Token might be expired, logout
          get().logout();
          throw error;
        }
      },

      setTokens(access: string, refresh: string) {
        set({ accessToken: access, refreshToken: refresh });
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user
      })
    }
  )
);