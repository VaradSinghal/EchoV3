-- Add approval workflow to agent_tasks

-- 1. Add approval_status column
alter table public.agent_tasks 
add column if not exists approval_status text default 'auto' 
check (approval_status in ('auto', 'pending_approval', 'approved', 'rejected'));

-- 2. Add pending_since to track when approval was requested
alter table public.agent_tasks 
add column if not exists pending_since timestamp with time zone;

-- 3. Add last_heartbeat if not exists (for stall detection)
alter table public.agent_tasks 
add column if not exists last_heartbeat timestamp with time zone;
