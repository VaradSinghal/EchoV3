-- Enable pgVector
create extension if not exists vector;

-- Posts table
create table if not exists public.posts (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.profiles(id) on delete cascade not null,
  title text not null,
  content text not null,
  repo_link text, -- GitHub repo URL
  tags text[], -- Array of tags
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Comments table
create table if not exists public.comments (
  id uuid default gen_random_uuid() primary key,
  post_id uuid references public.posts(id) on delete cascade not null,
  user_id uuid references public.profiles(id) on delete cascade not null,
  parent_id uuid references public.comments(id) on delete cascade, -- For nested replies
  content text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Likes table
create table if not exists public.likes (
  post_id uuid references public.posts(id) on delete cascade not null,
  user_id uuid references public.profiles(id) on delete cascade not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  primary key (post_id, user_id)
);

-- Comments embedding table for semantic search
create table if not exists public.comment_embeddings (
  comment_id uuid references public.comments(id) on delete cascade primary key,
  embedding vector(768), -- For Gemini embeddings
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- RLS Policies

-- Posts
alter table public.posts enable row level security;

create policy "Posts are viewable by everyone." on public.posts
  for select using (true);

create policy "Users can insert their own posts." on public.posts
  for insert with check (auth.uid() = user_id);

create policy "Users can update their own posts." on public.posts
  for update using (auth.uid() = user_id);

create policy "Users can delete their own posts." on public.posts
  for delete using (auth.uid() = user_id);

-- Comments
alter table public.comments enable row level security;

create policy "Comments are viewable by everyone." on public.comments
  for select using (true);

create policy "Users can insert their own comments." on public.comments
  for insert with check (auth.uid() = user_id);

create policy "Users can update their own comments." on public.comments
  for update using (auth.uid() = user_id);

create policy "Users can delete their own comments." on public.comments
  for delete using (auth.uid() = user_id);

-- Likes
alter table public.likes enable row level security;

create policy "Likes are viewable by everyone." on public.likes
  for select using (true);

create policy "Users can insert/delete their own likes." on public.likes
  for all using (auth.uid() = user_id);

-- Realtime
alter publication supabase_realtime add table public.posts;
alter publication supabase_realtime add table public.comments;
alter publication supabase_realtime add table public.likes;
