// Repository types

export interface Repository {
    id: string;
    github_id: number;
    name: string;
    full_name: string;
    description?: string;
    html_url: string;
    visibility: 'public' | 'private' | 'internal';
    default_branch: string;
    language?: string;
    stars_count: number;
    forks_count: number;
    open_issues_count: number;
    is_active: boolean;
    last_synced_at?: string;
}

export interface RepositorySettings {
    auto_sync?: boolean;
    sync_interval_minutes?: number;
    notifications_enabled?: boolean;
    notify_on_push?: boolean;
    notify_on_pr?: boolean;
    notify_on_issues?: boolean;
    agent_enabled?: boolean;
    auto_create_issues?: boolean;
}

export interface Branch {
    name: string;
    protected: boolean;
}

export interface Webhook {
    id: string;
    github_hook_id?: number;
    events: string[];
    is_active: boolean;
    last_delivery_at?: string;
    last_delivery_status?: string;
}

export interface GitHubRepo {
    id: number;
    name: string;
    full_name: string;
    description?: string;
    html_url: string;
    visibility: string;
    default_branch: string;
    language?: string;
    stargazers_count: number;
    forks_count: number;
    open_issues_count: number;
}
