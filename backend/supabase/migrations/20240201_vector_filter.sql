-- Drop the old version first since we are changing the return signature
DROP FUNCTION IF EXISTS match_comments(vector,double precision,integer);

-- Update match_comments to include repo_link for easier filtering
CREATE OR REPLACE FUNCTION match_comments(
  query_embedding vector(768),
  match_threshold FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  comment_id UUID,
  content TEXT,
  similarity FLOAT,
  repo_link TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    ce.comment_id,
    c.content,
    1 - (ce.embedding <=> query_embedding) as similarity,
    p.repo_link
  FROM comment_embeddings ce
  JOIN comments c ON ce.comment_id = c.id
  JOIN posts p ON c.post_id = p.id
  WHERE 1 - (ce.embedding <=> query_embedding) > match_threshold
  ORDER BY ce.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
