'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/lib/store/authStore';
import { User } from '@/lib/types';

/**
 * Hook to access the current auth state and actions.
 */
export function useAuth() {
    const store = useAuthStore();

    return {
        user: store.user,
        isLoading: store.isLoading,
        isAuthenticated: store.isAuthenticated,
        login: store.login,
        signup: store.signup,
        logout: store.logout,
        refreshTokens: store.refreshTokens,
    };
}

/**
 * Hook to get the current user.
 * Returns null if not authenticated.
 */
export function useUser(): User | null {
    return useAuthStore((state) => state.user);
}

/**
 * Hook to check if the user is authenticated.
 */
export function useIsAuthenticated(): boolean {
    return useAuthStore((state) => state.isAuthenticated);
}

/**
 * Hook to initialize auth state on app load.
 * Should be used in the root layout.
 */
export function useAuthInit() {
    const checkAuth = useAuthStore((state) => state.checkAuth);
    const isLoading = useAuthStore((state) => state.isLoading);

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    return { isLoading };
}
