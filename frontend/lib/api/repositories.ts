import { Repository, RepositorySettings, Branch, Webhook } from '@/lib/types/repository';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchWithAuth(url: string, options: RequestInit = {}) {
    const token = typeof window !== 'undefined'
        ? JSON.parse(localStorage.getItem('echo-auth-storage') || '{}')?.state?.accessToken
        : null;

    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...options.headers,
        },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || 'Request failed');
    }

    return response.json();
}

export const repositoriesApi = {
    async list(includeInactive = false): Promise<Repository[]> {
        return fetchWithAuth(`${API_BASE_URL}/api/repositories?include_inactive=${includeInactive}`);
    },

    async add(fullName: string): Promise<Repository> {
        return fetchWithAuth(`${API_BASE_URL}/api/repositories`, {
            method: 'POST',
            body: JSON.stringify({ full_name: fullName }),
        });
    },

    async get(id: string): Promise<Repository> {
        return fetchWithAuth(`${API_BASE_URL}/api/repositories/${id}`);
    },

    async update(id: string, settings: RepositorySettings): Promise<void> {
        return fetchWithAuth(`${API_BASE_URL}/api/repositories/${id}`, {
            method: 'PUT',
            body: JSON.stringify(settings),
        });
    },

    async delete(id: string): Promise<void> {
        return fetchWithAuth(`${API_BASE_URL}/api/repositories/${id}`, {
            method: 'DELETE',
        });
    },

    async sync(id: string): Promise<{ message: string; last_synced_at: string }> {
        return fetchWithAuth(`${API_BASE_URL}/api/repositories/${id}/sync`, {
            method: 'POST',
        });
    },

    async getBranches(id: string): Promise<Branch[]> {
        return fetchWithAuth(`${API_BASE_URL}/api/repositories/${id}/branches`);
    },

    async getWebhooks(id: string): Promise<Webhook[]> {
        return fetchWithAuth(`${API_BASE_URL}/api/repositories/${id}/webhooks`);
    },
};
