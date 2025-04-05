TRUNCATE TABLE
  public.tweets,
  public.graph_data,
  public.analyses
RESTART IDENTITY CASCADE;

-- This will:
-- Delete all rows from all three tables
-- Reset any auto-incrementing IDs
-- Handle all foreign key relationships properly