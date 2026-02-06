-- Function for similarity search
CREATE OR REPLACE FUNCTION match_comments(
  query_embedding vector(768),
  match_threshold FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  comment_id UUID,
  content TEXT,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    ce.comment_id,
    c.content,
    1 - (ce.embedding <=> query_embedding) as similarity
  FROM comment_embeddings ce
  JOIN comments c ON ce.comment_id = c.id
  WHERE 1 - (ce.embedding <=> query_embedding) > match_threshold
  ORDER BY ce.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Index for performance
CREATE INDEX IF NOT EXISTS comment_embeddings_embedding_idx ON comment_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Helper for K-means clustering (basic logic)
-- This assumes we want to cluster embeddings into K groups
CREATE OR REPLACE FUNCTION cluster_comments(k_count INT)
RETURNS TABLE (
  comment_id UUID,
  cluster_id INT
) 
LANGUAGE plpgsql
AS $$
BEGIN
  -- Simple implementation: using pgvector's built-in support or a manual approach
  -- For now, we'll return a placeholder or a simple grouping logic if possible.
  -- pgvector doesn't have a native 'CLUSTER' function like some specialized DBs, 
  -- but we can use an iterative approach or a specific migration for it if needed.
  -- For this MVP, we'll implement a simple grouping by similarity to centroids.
  RETURN QUERY
  WITH RECURSIVE
  centroids AS (
    SELECT embedding as centroid, row_number() over() as id
    FROM comment_embeddings
    ORDER BY random()
    LIMIT k_count
  )
  SELECT 
    ce.comment_id,
    (SELECT c.id FROM centroids c ORDER BY ce.embedding <=> c.centroid LIMIT 1)::INT as cluster_id
  FROM comment_embeddings ce;
END;
$$;

-- Duplicate detection system
CREATE OR REPLACE FUNCTION find_duplicate_comments(
  threshold FLOAT DEFAULT 0.95
)
RETURNS TABLE (
  comment_id_1 UUID,
  comment_id_2 UUID,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    ce1.comment_id as comment_id_1,
    ce2.comment_id as comment_id_2,
    1 - (ce1.embedding <=> ce2.embedding) as similarity
  FROM comment_embeddings ce1
  JOIN comment_embeddings ce2 ON ce1.comment_id < ce2.comment_id
  WHERE 1 - (ce1.embedding <=> ce2.embedding) > threshold
  ORDER BY similarity DESC;
END;
$$;
