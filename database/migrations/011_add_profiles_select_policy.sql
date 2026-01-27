-- Migration: Add RLS policy to allow anonymous read access to profiles
-- This allows the mobile app to fetch user profiles using the anon key

-- Enable RLS on profiles if not already enabled
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if it exists (to allow re-running migration)
DROP POLICY IF EXISTS "Allow anonymous read access to profiles" ON profiles;

-- Create policy to allow anyone to read all profiles
-- This is safe because profiles only contain public information (no sensitive data)
CREATE POLICY "Allow anonymous read access to profiles"
ON profiles
FOR SELECT
TO anon
USING (true);

-- Grant select permission to anon role
GRANT SELECT ON profiles TO anon;

COMMENT ON POLICY "Allow anonymous read access to profiles" ON profiles IS
    'Allows the mobile app to fetch user profiles using the anon key. This is safe because profiles only contain non-sensitive public information.';
