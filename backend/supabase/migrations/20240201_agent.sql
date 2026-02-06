-- Agent monitoring tables

create table if not exists public.monitored_posts (
  id uuid default gen_random_uuid() primary key,
  post_id uuid references public.posts(id) on delete cascade not null,
  repo_id text, -- GitHub repo full_name (owner/repo)
  is_active boolean default true,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create table if not exists public.feedback_analysis (
  id uuid default gen_random_uuid() primary key,
  comment_id uuid references public.comments(id) on delete cascade not null,
  sentiment_score float,
  category text, -- 'feature_request', 'bug', 'question', 'feedback'
  keywords text[],
  embedding_id uuid references public.comment_embeddings(comment_id),
  analyzed_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create table if not exists public.agent_tasks (
  id uuid default gen_random_uuid() primary key,
  monitored_post_id uuid references public.monitored_posts(id) on delete cascade,
  task_type text, -- 'analyze', 'generate_code', 'create_pr'
  status text default 'pending', -- pending, processing, completed, failed
  logs jsonb[] default array[]::jsonb[], -- Array of log objects {timestamp, message, status}
  current_step text,
  result jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create table if not exists public.generated_code (
  id uuid default gen_random_uuid() primary key,
  task_id uuid references public.agent_tasks(id) on delete cascade not null,
  file_path text not null,
  old_code text,
  new_code text,
  explanation text,
  status text default 'draft', -- draft, ready, applied
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

create table if not exists public.github_prs (
  id uuid default gen_random_uuid() primary key,
  generated_code_id uuid references public.generated_code(id) on delete cascade not null,
  pr_number integer,
  pr_url text,
  status text default 'open',
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Generated Code Policies
alter table public.generated_code enable row level security;
create policy "Generated code viewable by everyone" on public.generated_code for select using (true);

-- GitHub PRs Policies
alter table public.github_prs enable row level security;
create policy "PRs viewable by everyone" on public.github_prs for select using (true);


-- RLS Policies

-- Monitored Posts
alter table public.monitored_posts enable row level security;

create policy "Monitored posts are viewable by everyone." on public.monitored_posts
  for select using (true);

create policy "Users can insert monitored posts." on public.monitored_posts
  for insert with check (auth.uid() is not null); -- Allow authenticated users for now

create policy "Users can update monitored posts." on public.monitored_posts
  for update using (auth.uid() is not null);

-- Feedback Analysis
alter table public.feedback_analysis enable row level security;

create policy "Feedback analysis is viewable by everyone." on public.feedback_analysis
  for select using (true);

-- Agent Tasks
alter table public.agent_tasks enable row level security;

create policy "Agent tasks are viewable by everyone." on public.agent_tasks
  for select using (true);

-- Realtime
alter publication supabase_realtime add table public.agent_tasks;
