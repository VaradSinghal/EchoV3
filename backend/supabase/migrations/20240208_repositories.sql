-- Repository Tables Migration for Echov3
-- This migration creates the required tables for repository management

-- Create repositories table
CREATE TABLE IF NOT EXISTS public.repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- GitHub data
    github_id INTEGER NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(512) NOT NULL UNIQUE,
    description TEXT,
    url VARCHAR(512) NOT NULL,
    html_url VARCHAR(512) NOT NULL,
    clone_url VARCHAR(512),
    
    -- Owner info
    owner_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    owner_github_login VARCHAR(255) NOT NULL,
    
    -- Repository metadata
    visibility VARCHAR(20) DEFAULT 'public',
    default_branch VARCHAR(255) DEFAULT 'main',
    language VARCHAR(100),
    
    -- Stats
    stars_count INTEGER DEFAULT 0,
    forks_count INTEGER DEFAULT 0,
    open_issues_count INTEGER DEFAULT 0,
    watchers_count INTEGER DEFAULT 0,
    
    -- Sync status
    is_active BOOLEAN DEFAULT TRUE,
    last_synced_at TIMESTAMPTZ,
    sync_error TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    github_created_at TIMESTAMPTZ,
    github_updated_at TIMESTAMPTZ
);

-- Create repository_members table
CREATE TABLE IF NOT EXISTS public.repository_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES public.repositories(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    role VARCHAR(20) DEFAULT 'member',
    permissions JSONB DEFAULT '{}',
    
    invited_by_id UUID REFERENCES auth.users(id),
    invited_at TIMESTAMPTZ,
    accepted_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(repository_id, user_id)
);

-- Create webhooks table
CREATE TABLE IF NOT EXISTS public.webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES public.repositories(id) ON DELETE CASCADE,
    
    github_hook_id INTEGER,
    url VARCHAR(512) NOT NULL,
    secret VARCHAR(255) NOT NULL,
    
    events JSONB DEFAULT '["push", "pull_request", "issues"]',
    content_type VARCHAR(50) DEFAULT 'json',
    
    is_active BOOLEAN DEFAULT TRUE,
    last_delivery_at TIMESTAMPTZ,
    last_delivery_status VARCHAR(50),
    delivery_error TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create repository_settings table
CREATE TABLE IF NOT EXISTS public.repository_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES public.repositories(id) ON DELETE CASCADE UNIQUE,
    
    -- Sync settings
    auto_sync BOOLEAN DEFAULT TRUE,
    sync_interval_minutes INTEGER DEFAULT 60,
    sync_branches BOOLEAN DEFAULT TRUE,
    sync_contributors BOOLEAN DEFAULT TRUE,
    
    -- Notification settings
    notifications_enabled BOOLEAN DEFAULT TRUE,
    notify_on_push BOOLEAN DEFAULT FALSE,
    notify_on_pr BOOLEAN DEFAULT TRUE,
    notify_on_issues BOOLEAN DEFAULT TRUE,
    notify_on_discussions BOOLEAN DEFAULT TRUE,
    
    -- Agent settings
    agent_enabled BOOLEAN DEFAULT TRUE,
    auto_create_issues BOOLEAN DEFAULT FALSE,
    auto_respond_to_discussions BOOLEAN DEFAULT FALSE,
    
    -- Analysis settings
    analyze_codebase BOOLEAN DEFAULT TRUE,
    analyze_contributors BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_repositories_owner_id ON public.repositories(owner_id);
CREATE INDEX IF NOT EXISTS idx_repositories_github_id ON public.repositories(github_id);
CREATE INDEX IF NOT EXISTS idx_repositories_full_name ON public.repositories(full_name);
CREATE INDEX IF NOT EXISTS idx_repository_members_repo_id ON public.repository_members(repository_id);
CREATE INDEX IF NOT EXISTS idx_repository_members_user_id ON public.repository_members(user_id);
CREATE INDEX IF NOT EXISTS idx_webhooks_repository_id ON public.webhooks(repository_id);
CREATE INDEX IF NOT EXISTS idx_webhooks_github_hook_id ON public.webhooks(github_hook_id);

-- RLS Policies
ALTER TABLE public.repositories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.repository_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.webhooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.repository_settings ENABLE ROW LEVEL SECURITY;

-- Repositories: Users can only see their own repositories
CREATE POLICY "Users can view own repos" ON public.repositories
    FOR SELECT USING (auth.uid() = owner_id);

CREATE POLICY "Users can insert own repos" ON public.repositories
    FOR INSERT WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update own repos" ON public.repositories
    FOR UPDATE USING (auth.uid() = owner_id);

CREATE POLICY "Users can delete own repos" ON public.repositories
    FOR DELETE USING (auth.uid() = owner_id);

-- Repository members: Users can see members of their repos
CREATE POLICY "Users can view repo members" ON public.repository_members
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.repositories WHERE id = repository_id AND owner_id = auth.uid())
        OR user_id = auth.uid()
    );

-- Webhooks: Users can manage webhooks for their repos
CREATE POLICY "Users can manage webhooks" ON public.webhooks
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.repositories WHERE id = repository_id AND owner_id = auth.uid())
    );

-- Settings: Users can manage settings for their repos
CREATE POLICY "Users can manage repo settings" ON public.repository_settings
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.repositories WHERE id = repository_id AND owner_id = auth.uid())
    );

-- Updated_at trigger
DROP TRIGGER IF EXISTS update_repositories_updated_at ON public.repositories;
CREATE TRIGGER update_repositories_updated_at
    BEFORE UPDATE ON public.repositories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_webhooks_updated_at ON public.webhooks;
CREATE TRIGGER update_webhooks_updated_at
    BEFORE UPDATE ON public.webhooks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_repository_settings_updated_at ON public.repository_settings;
CREATE TRIGGER update_repository_settings_updated_at
    BEFORE UPDATE ON public.repository_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
