-- 1. Create a function to trigger the agent API
CREATE OR REPLACE FUNCTION public.trigger_agent_run()
RETURNS trigger AS $$
BEGIN
  -- We use the net extension to make an HTTP request
  -- Note: This requires the 'pg_net' extension to be enabled in Supabase
  PERFORM
    net.http_post(
      url := (SELECT value FROM public.system_config WHERE key = 'api_url'),
      headers := '{"Content-Type": "application/json"}'::jsonb,
      body := '{}'::jsonb
    );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. Create a system_config table if it doesn't exist to store the app host
CREATE TABLE IF NOT EXISTS public.system_config (
    key text PRIMARY KEY,
    value text NOT NULL
);

-- Note: User MUST manually set 'api_url' in system_config table for this to work
-- INSERT INTO public.system_config (key, value) VALUES ('api_url', 'https://your-app-url.vercel.app/api/agent/run');

-- 3. Create triggers for new comments and likes
DROP TRIGGER IF EXISTS trigger_agent_on_comment ON public.comments;
CREATE TRIGGER trigger_agent_on_comment
AFTER INSERT ON public.comments
FOR EACH ROW
EXECUTE FUNCTION public.trigger_agent_run();

DROP TRIGGER IF EXISTS trigger_agent_on_like ON public.likes;
CREATE TRIGGER trigger_agent_on_like
AFTER INSERT ON public.likes
FOR EACH ROW
EXECUTE FUNCTION public.trigger_agent_run();
