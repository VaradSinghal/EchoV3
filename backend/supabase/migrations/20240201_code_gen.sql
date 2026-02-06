-- Database for Code Generation
CREATE TABLE IF NOT EXISTS public.generated_code (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  task_id UUID REFERENCES public.agent_tasks(id) ON DELETE CASCADE,
  feedback_group_id UUID, -- Reference to clustered feedback (cluster_id from cluster_comments)
  file_path TEXT NOT NULL,
  old_code TEXT,
  new_code TEXT NOT NULL,
  explanation TEXT,
  status TEXT DEFAULT 'generated', -- generated, tested, ready, failed
  test_results JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS public.github_prs (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  generated_code_id UUID REFERENCES public.generated_code(id) ON DELETE CASCADE,
  pr_number INTEGER,
  pr_url TEXT,
  status TEXT DEFAULT 'open', -- open, merged, closed
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- RLS Policies
ALTER TABLE public.generated_code ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.github_prs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Generated code is viewable by everyone." ON public.generated_code
  FOR SELECT USING (true);

CREATE POLICY "GitHub PRs are viewable by everyone." ON public.github_prs
  FOR SELECT USING (true);

-- Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE public.generated_code;
ALTER PUBLICATION supabase_realtime ADD TABLE public.github_prs;
