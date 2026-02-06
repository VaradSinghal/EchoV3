'use client';

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { User, AuthState, AuthResponse } from '@/lib/types';
import { authApi } from '@/lib/supabase';

interface AuthStore extends AuthState {
    // Actions
    setUser: (user: User | null) => void;
    setTokens: (accessToken: string, refreshToken: string) => void;
    login: (email: string, password: string) => Promise<void>;
    signup: (email: string, password: string, displayName?: string) => Promise<void>;
    logout: () => Promise<void>;
    refreshTokens: () => Promise<boolean>;
    checkAuth: () => Promise<void>;
    handleOAuthCallback: (accessToken: string, refreshToken: string) => Promise<void>;
}

export const useAuthStore = create<AuthStore>()(
    persist(
        (set, get) => ({
            // Initial state
            user: null,
            accessToken: null,
            refreshToken: null,
            isLoading: true,
            isAuthenticated: false,

            // Actions
            setUser: (user) => set({
                user,
                isAuthenticated: !!user,
                isLoading: false
            }),

            setTokens: (accessToken, refreshToken) => set({
                accessToken,
                refreshToken
            }),

            login: async (email, password) => {
                set({ isLoading: true });
                try {
                    const response: AuthResponse = await authApi.login(email, password);
                    set({
                        user: response.user,
                        accessToken: response.access_token,
                        refreshToken: response.refresh_token,
                        isAuthenticated: true,
                        isLoading: false,
                    });
                } catch (error) {
                    set({ isLoading: false });
                    throw error;
                }
            },

            signup: async (email, password, displayName) => {
                set({ isLoading: true });
                try {
                    const response: AuthResponse = await authApi.signup(email, password, displayName);
                    set({
                        user: response.user,
                        accessToken: response.access_token,
                        refreshToken: response.refresh_token,
                        isAuthenticated: true,
                        isLoading: false,
                    });
                } catch (error) {
                    set({ isLoading: false });
                    throw error;
                }
            },

            logout: async () => {
                const { accessToken } = get();
                set({ isLoading: true });

                try {
                    if (accessToken) {
                        await authApi.logout(accessToken);
                    }
                } catch (error) {
                    console.error('Logout error:', error);
                } finally {
                    set({
                        user: null,
                        accessToken: null,
                        refreshToken: null,
                        isAuthenticated: false,
                        isLoading: false,
                    });
                }
            },

            refreshTokens: async () => {
                const { refreshToken } = get();
                if (!refreshToken) return false;

                try {
                    const response = await authApi.refreshToken(refreshToken);
                    set({
                        accessToken: response.access_token,
                        refreshToken: response.refresh_token,
                    });
                    return true;
                } catch (error) {
                    console.error('Token refresh failed:', error);
                    set({
                        user: null,
                        accessToken: null,
                        refreshToken: null,
                        isAuthenticated: false,
                    });
                    return false;
                }
            },

            checkAuth: async () => {
                const { accessToken, refreshTokens } = get();
                set({ isLoading: true });

                if (!accessToken) {
                    set({ isLoading: false });
                    return;
                }

                try {
                    const user = await authApi.getMe(accessToken);
                    set({
                        user,
                        isAuthenticated: true,
                        isLoading: false,
                    });
                } catch (error) {
                    // Token might be expired, try to refresh
                    const refreshed = await refreshTokens();
                    if (refreshed) {
                        const newToken = get().accessToken;
                        if (newToken) {
                            try {
                                const user = await authApi.getMe(newToken);
                                set({
                                    user,
                                    isAuthenticated: true,
                                    isLoading: false,
                                });
                                return;
                            } catch {
                                // Refresh didn't help
                            }
                        }
                    }

                    set({
                        user: null,
                        accessToken: null,
                        refreshToken: null,
                        isAuthenticated: false,
                        isLoading: false,
                    });
                }
            },

            handleOAuthCallback: async (accessToken, refreshToken) => {
                set({ isLoading: true });
                try {
                    set({
                        accessToken,
                        refreshToken,
                    });

                    const user = await authApi.getMe(accessToken);
                    set({
                        user,
                        isAuthenticated: true,
                        isLoading: false,
                    });
                } catch (error) {
                    set({
                        isLoading: false,
                        isAuthenticated: false,
                    });
                    throw error;
                }
            },
        }),
        {
            name: 'echo-auth-storage',
            storage: createJSONStorage(() => localStorage),
            partialize: (state) => ({
                accessToken: state.accessToken,
                refreshToken: state.refreshToken,
                user: state.user,
            }),
        }
    )
);

// Hook for syncing auth state across tabs
if (typeof window !== 'undefined') {
    window.addEventListener('storage', (event) => {
        if (event.key === 'echo-auth-storage') {
            // Reload the page to sync state
            window.location.reload();
        }
    });
}
