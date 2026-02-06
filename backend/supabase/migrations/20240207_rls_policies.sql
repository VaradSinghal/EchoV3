-- Row Level Security (RLS) Policies for Echov3
-- Run these in Supabase SQL Editor

-- Enable RLS on user_profiles table
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own profile
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can update their own profile
CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can insert their own profile (on signup)
CREATE POLICY "Users can insert own profile" ON public.user_profiles
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Enable RLS on api_keys table
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;

-- Policy: Users can manage their own API keys
CREATE POLICY "Users can view own API keys" ON public.api_keys
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own API keys" ON public.api_keys
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own API keys" ON public.api_keys
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own API keys" ON public.api_keys
    FOR DELETE
    USING (auth.uid() = user_id);

-- Enable RLS on user_sessions table
ALTER TABLE public.user_sessions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can manage their own sessions
CREATE POLICY "Users can view own sessions" ON public.user_sessions
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own sessions" ON public.user_sessions
    FOR DELETE
    USING (auth.uid() = user_id);

-- Grant service role full access (for backend operations)
-- Note: The service role bypasses RLS by default in Supabase
