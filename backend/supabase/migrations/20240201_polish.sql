-- Final Security and Performance Optimizations

-- 1. Refine RLS for monitored_posts
DROP POLICY IF EXISTS "Users can insert monitored posts." ON public.monitored_posts;
CREATE POLICY "Users can insert monitored posts." ON public.monitored_posts
  FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "Users can update monitored posts." ON public.monitored_posts;
CREATE POLICY "Users can update monitored posts." ON public.monitored_posts
  FOR UPDATE USING (auth.uid() IS NOT NULL);

-- 2. Feedback Analysis Indexes
CREATE INDEX IF NOT EXISTS idx_feedback_analysis_comment_id ON public.feedback_analysis(comment_id);
CREATE INDEX IF NOT EXISTS idx_feedback_analysis_category ON public.feedback_analysis(category);

-- 3. Comments Table Indexes
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON public.comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_created_at ON public.comments(created_at DESC);

-- 4. Posts Table Indexes
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON public.posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON public.posts(created_at DESC);

-- 5. Agent Tasks Indexes
CREATE INDEX IF NOT EXISTS idx_agent_tasks_status ON public.agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_agent_tasks_created_at ON public.agent_tasks(created_at DESC);

-- 6. Generated Code Indexes
CREATE INDEX IF NOT EXISTS idx_generated_code_task_id ON public.generated_code(task_id);

-- 7. Ensure RLS on all agent tables
ALTER TABLE public.comment_embeddings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Embeddings are viewable by everyone." ON public.comment_embeddings
  FOR SELECT USING (true);
