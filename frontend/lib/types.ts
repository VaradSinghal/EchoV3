export interface User {
    id: string;
    email: string;
    display_name?: string;
    github_username?: string;
    github_avatar_url?: string;
}

export interface AuthResponse {
    user: User;
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export interface AuthState {
    user: User | null;
    accessToken: string | null;
    refreshToken: string | null;
    isLoading: boolean;
    isAuthenticated: boolean;
}

export interface LoginCredentials {
    email: string;
    password: string;
}

export interface SignupCredentials extends LoginCredentials {
    display_name?: string;
}

export interface AuthError {
    message: string;
    code?: string;
}
