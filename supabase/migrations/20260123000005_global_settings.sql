-- Global settings: admin-managed configuration replacing per-user settings

-- 1. Create user_profiles table
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_read_own_profile" ON user_profiles FOR SELECT USING (auth.uid() = user_id);

-- 2. Trigger to auto-create profile on user signup
CREATE OR REPLACE FUNCTION create_user_profile()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_profiles (user_id, is_admin)
    VALUES (NEW.id, false)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION create_user_profile();

-- 3. Back-fill existing users
INSERT INTO user_profiles (user_id, is_admin)
SELECT id, false FROM auth.users
ON CONFLICT (user_id) DO NOTHING;

-- 4. Set test@user.com as admin
UPDATE user_profiles SET is_admin = true
WHERE user_id = (SELECT id FROM auth.users WHERE email = 'test@user.com');

-- 5. Create global_settings table (single row)
CREATE TABLE global_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    llm_model TEXT,
    llm_base_url TEXT,
    llm_api_key TEXT,
    embedding_model TEXT,
    embedding_base_url TEXT,
    embedding_api_key TEXT,
    embedding_dimensions INTEGER,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE global_settings ENABLE ROW LEVEL SECURITY;

-- 6. RLS: all authenticated users can read global settings
CREATE POLICY "authenticated_read_global_settings" ON global_settings
    FOR SELECT USING (auth.role() = 'authenticated');

-- 7. Seed global_settings from first user_settings row if any exist
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'user_settings') THEN
        INSERT INTO global_settings (llm_model, llm_base_url, llm_api_key, embedding_model, embedding_base_url, embedding_api_key, embedding_dimensions)
        SELECT llm_model, llm_base_url, llm_api_key, embedding_model, embedding_base_url, embedding_api_key, embedding_dimensions
        FROM user_settings
        LIMIT 1;
    END IF;
END $$;

-- 8. Insert an empty row if no seed data was inserted
INSERT INTO global_settings (id)
SELECT gen_random_uuid()
WHERE NOT EXISTS (SELECT 1 FROM global_settings);

-- 9. Drop user_settings table if it exists
DROP TABLE IF EXISTS user_settings;
