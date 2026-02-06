-- Create a table for public profiles without needing a trigger based on Auth,
-- as we can just insert/update it on login callback or manual creation if needed,
-- or use a trigger if preferred. For simple OAuth, we often sync on login.

create table if not exists public.profiles (
  id uuid references auth.users on delete cascade not null primary key,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  email text,
  username text,
  avatar_url text,
  github_id text
);

-- Enable Row Level Security (RLS)
alter table public.profiles enable row level security;

create policy "Public profiles are viewable by everyone." on public.profiles
  for select using (true);

create policy "Users can insert their own profile." on public.profiles
  for insert with check (auth.uid() = id);

create policy "Users can update own profile." on public.profiles
  for update using (auth.uid() = id);

-- Table for storing GitHub Tokens (Encrypted ideally, but for now standard text or use pgsodium)
-- Warning: Storing tokens in plain text is risky. Ensure RLS is strict.
create table if not exists public.github_tokens (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users on delete cascade not null,
  access_token text not null,
  refresh_token text,
  expires_at bigint, -- Timestamp or seconds
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  
  unique(user_id)
);

alter table public.github_tokens enable row level security;

create policy "Users can view their own tokens." on public.github_tokens
  for select using (auth.uid() = user_id);

-- Only allowing the application (service role) or the user themselves to manage?
-- Ideally, this is managed by the server-side callback.
create policy "Users can insert/update their own tokens." on public.github_tokens
  for all using (auth.uid() = user_id);
