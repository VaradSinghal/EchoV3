ALTER TABLE public.agent_tasks ADD COLUMN IF NOT EXISTS logs JSONB DEFAULT '[]'::jsonb; ALTER TABLE public.agent_tasks ADD COLUMN IF NOT EXISTS current_step TEXT;
