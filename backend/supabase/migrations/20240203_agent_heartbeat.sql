-- Add last_heartbeat column to agent_tasks for monitoring
ALTER TABLE public.agent_tasks 
ADD COLUMN IF NOT EXISTS last_heartbeat timestamp with time zone DEFAULT timezone('utc'::text, now());

-- Update column description
COMMENT ON COLUMN public.agent_tasks.last_heartbeat IS 'Timestamp of the last progress update from the agent to detect hangs.';
